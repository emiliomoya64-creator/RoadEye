from __future__ import annotations

import json
import shutil

import cv2
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from core.config_manager import PROJECT_DIR, config
from core.frame_buffer import frame_buffer
from core.system_state import system_state
from recorder.recorder_service import RecorderService
from trip.trip_manager import trip_manager


router = APIRouter()

recorder: Optional[RecorderService] = None
storage_manager = None


def _videos_directory() -> Path:
    configured_folder = Path(
        str(
            config.get(
                "recording.folder",
                "videos",
            )
        )
    )

    if not configured_folder.is_absolute():
        configured_folder = (
            PROJECT_DIR
            / configured_folder
        )

    return configured_folder.resolve()


@router.get("/api/status")
async def status():
    total, used, free = shutil.disk_usage(
        PROJECT_DIR
    )

    disk_percent = round(
        used / total * 100
    )

    videos_directory = (
        _videos_directory()
    )

    video_count = 0

    if videos_directory.exists():
        video_count = len(
            list(
                videos_directory.glob(
                    "*.mp4"
                )
            )
        )

    recorder_status = (
        recorder.status()
        if recorder is not None
        else {
            "service_running": False,
            "recording": False,
            "current_file": None,
        }
    )

    return {
        "recording": recorder_status[
            "recording"
        ],
        "recorder": recorder_status,
        "gps_fix": system_state.get(
            "gps_fix"
        ),
        "speed": system_state.get(
            "speed"
        ),
        "cpu": system_state.get(
            "cpu"
        ),
        "temp": system_state.get(
            "temp"
        ),
        "disk": disk_percent,
        "videos": video_count,
    }


@router.get("/api/record/start")
async def record_start():
    if recorder is None:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está disponible",
        )

    if storage_manager is not None:
        capacity = storage_manager.ensure_capacity(
            reason="before_recording",
        )

        if (
            not capacity.get(
                "ok",
                False,
            )
        ):
            raise HTTPException(
                status_code=507,
                detail=(
                    "No se pudo comprobar "
                    "el almacenamiento."
                ),
            )

        after = capacity.get(
            "after",
            {},
        )

        if bool(
            after.get(
                "cleanup_required",
                False,
            )
        ):
            raise HTTPException(
                status_code=507,
                detail=(
                    "No hay espacio suficiente "
                    "y no existen vídeos normales "
                    "que puedan eliminarse."
                ),
            )

    started = recorder.start_recording()

    if not started:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está iniciado",
        )

    return {
        "ok": True,
        "recording": True,
        "recorder": recorder.status(),
    }


@router.get("/api/record/stop")
async def record_stop():
    if recorder is None:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está disponible",
        )

    recorder.stop_recording()

    return {
        "ok": True,
        "recording": False,
        "recorder": recorder.status(),
    }


@router.get("/api/record/status")
async def record_status():
    if recorder is None:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está disponible",
        )

    return recorder.status()

# ============================================================
# Configuración del HUD RoadEye 0.6
# ============================================================

HUD_WIDGETS = {
    "recording",
    "parking",
    "gps",
    "speed",
    "snapshot",
    "gallery",
    "speed_limit",
    "road",
    "coordinates",
    "date",
    "time",
    "settings",
}


def _hud_configuration():
    return {
        "enabled": bool(
            config.get(
                "hud.enabled",
                True,
            )
        ),
        "profile": str(
            config.get(
                "hud.profile",
                "normal",
            )
        ),
        "info_position": str(
            config.get(
                "hud.info_position",
                "bottom",
            )
        ),
        "top_opacity": float(
            config.get(
                "hud.top_opacity",
                0.66,
            )
        ),
        "info_opacity": float(
            config.get(
                "hud.info_opacity",
                0.58,
            )
        ),
        "icon_scale": float(
            config.get(
                "hud.icon_scale",
                1.0,
            )
        ),
        "text_scale": float(
            config.get(
                "hud.text_scale",
                1.0,
            )
        ),
        "font": str(
            config.get(
                "hud.font",
                "duplex",
            )
        ),
        "color": str(
            config.get(
                "hud.color",
                "white",
            )
        ),
        "top_bar_scale": float(
            config.get(
                "hud.top_bar_scale",
                1.0,
            )
        ),
        "info_bar_scale": float(
            config.get(
                "hud.info_bar_scale",
                1.0,
            )
        ),
        "bar_color": str(
            config.get(
                "hud.bar_color",
                "black",
            )
        ),
        "mode": str(
            config.get(
                "hud.mode",
                "auto",
            )
        ),
        "show": {
            name: bool(
                config.get(
                    f"hud.show.{name}",
                    True,
                )
            )
            for name in sorted(
                HUD_WIDGETS
            )
        },
    }


def _validate_opacity(
    value,
    field_name,
):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail=(
                f"{field_name} debe ser un número."
            ),
        )

    if not 0.0 <= result <= 1.0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{field_name} debe estar entre 0 y 1."
            ),
        )

    return result


@router.get("/api/hud/settings")
async def hud_settings_get():
    return {
        "ok": True,
        "hud": _hud_configuration(),
    }


@router.put("/api/hud/settings")
async def hud_settings_update(
    payload: dict,
):
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=422,
            detail="La configuración debe ser un objeto JSON.",
        )

    current = _hud_configuration()

    enabled = bool(
        payload.get(
            "enabled",
            current["enabled"],
        )
    )

    profile = str(
        payload.get(
            "profile",
            current["profile"],
        )
    ).strip().lower()

    if profile not in {
        "minimal",
        "normal",
        "professional",
    }:
        raise HTTPException(
            status_code=422,
            detail="Perfil de HUD no válido.",
        )

    info_position = str(
        payload.get(
            "info_position",
            current["info_position"],
        )
    ).strip().lower()

    if info_position not in {
        "top",
        "bottom",
    }:
        raise HTTPException(
            status_code=422,
            detail=(
                "info_position debe ser top o bottom."
            ),
        )

    top_opacity = _validate_opacity(
        payload.get(
            "top_opacity",
            current["top_opacity"],
        ),
        "top_opacity",
    )

    info_opacity = _validate_opacity(
        payload.get(
            "info_opacity",
            current["info_opacity"],
        ),
        "info_opacity",
    )

    try:
        icon_scale = float(
            payload.get(
                "icon_scale",
                current["icon_scale"],
            )
        )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="icon_scale debe ser un número.",
        )

    if not 0.80 <= icon_scale <= 2.00:
        raise HTTPException(
            status_code=422,
            detail=(
                "icon_scale debe estar "
                "entre 0.80 y 2.00."
            ),
        )

    try:
        text_scale = float(
            payload.get(
                "text_scale",
                current["text_scale"],
            )
        )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="text_scale debe ser un número.",
        )

    if not 0.80 <= text_scale <= 2.00:
        raise HTTPException(
            status_code=422,
            detail=(
                "text_scale debe estar "
                "entre 0.80 y 2.00."
            ),
        )

    font = str(
        payload.get(
            "font",
            current.get("font", "duplex"),
        )
    ).strip().lower()

    if font not in {
        "simplex",
        "duplex",
        "triplex",
        "complex",
        "plain",
        "complex_small",
        "script",
        "script_complex",
    }:
        raise HTTPException(
            status_code=422,
            detail="Fuente HUD no válida.",
        )

    color = str(
        payload.get(
            "color",
            current.get("color", "white"),
        )
    ).strip().lower()

    if color not in {
        "white",
        "green",
        "amber",
        "ice_blue",
        "red",
    }:
        raise HTTPException(
            status_code=422,
            detail="Color HUD no válido.",
        )

    mode = str(
        payload.get(
            "mode",
            current.get("mode", "auto"),
        )
    ).strip().lower()

    if mode not in {
        "day",
        "night",
        "auto",
    }:
        raise HTTPException(
            status_code=422,
            detail="Modo HUD no válido.",
        )

    bar_color = str(
        payload.get(
            "bar_color",
            current.get(
                "bar_color",
                "black",
            ),
        )
    ).strip().lower()

    if bar_color not in {
        "black",
        "white",
    }:
        raise HTTPException(
            status_code=422,
            detail="Color de franjas no válido.",
        )

    try:
        top_bar_scale = float(
            payload.get(
                "top_bar_scale",
                current.get(
                    "top_bar_scale",
                    1.0,
                ),
            )
        )

        info_bar_scale = float(
            payload.get(
                "info_bar_scale",
                current.get(
                    "info_bar_scale",
                    1.0,
                ),
            )
        )

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail=(
                "La escala de las franjas "
                "debe ser numérica."
            ),
        )

    if not 0.70 <= top_bar_scale <= 1.60:
        raise HTTPException(
            status_code=422,
            detail=(
                "top_bar_scale debe estar "
                "entre 0.70 y 1.60."
            ),
        )

    if not 0.70 <= info_bar_scale <= 1.60:
        raise HTTPException(
            status_code=422,
            detail=(
                "info_bar_scale debe estar "
                "entre 0.70 y 1.60."
            ),
        )

    requested_show = payload.get(
        "show",
        {},
    )

    if not isinstance(
        requested_show,
        dict,
    ):
        raise HTTPException(
            status_code=422,
            detail="show debe ser un objeto JSON.",
        )

    updated_show = dict(
        current["show"]
    )

    for name, value in requested_show.items():
        if name not in HUD_WIDGETS:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Widget desconocido: {name}"
                ),
            )

        updated_show[name] = bool(
            value
        )

    config.update(
        {
            "hud": {
                "enabled": enabled,
                "profile": profile,
                "info_position": info_position,
                "top_opacity": top_opacity,
                "info_opacity": info_opacity,
                "icon_scale": icon_scale,
                "text_scale": text_scale,
                "font": font,
                "color": color,
                "mode": mode,
                "bar_color": bar_color,
                "top_bar_scale": top_bar_scale,
                "info_bar_scale": info_bar_scale,
                "show": updated_show,
            }
        },
        save=True,
    )

    return {
        "ok": True,
        "message": (
            "Configuración del HUD guardada."
        ),
        "hud": _hud_configuration(),
    }


@router.post("/api/hud/settings/reset")
async def hud_settings_reset():
    defaults = {
        "enabled": True,
        "profile": "normal",
        "info_position": "bottom",
        "top_opacity": 0.66,
        "info_opacity": 0.58,
        "icon_scale": 1.0,
        "text_scale": 1.0,
        "font": "duplex",
        "color": "white",
        "mode": "auto",
        "show": {
            name: True
            for name in HUD_WIDGETS
        },
    }

    config.update(
        {
            "hud": defaults
        },
        save=True,
    )

    return {
        "ok": True,
        "message": (
            "Configuración predeterminada restaurada."
        ),
        "hud": _hud_configuration(),
    }


# ============================================================
# Explorador de vídeos RoadEye 0.6
# ============================================================

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
}


def _safe_video_path(
    filename: str,
) -> Path:
    """
    Devuelve una ruta segura dentro de la carpeta de vídeos.

    Impide acceder a archivos situados fuera de esa carpeta.
    """

    clean_name = Path(
        str(filename)
    ).name

    if not clean_name:
        raise HTTPException(
            status_code=400,
            detail="Nombre de vídeo no válido.",
        )

    videos_directory = (
        _videos_directory()
    )

    candidate = (
        videos_directory
        / clean_name
    ).resolve()

    try:
        candidate.relative_to(
            videos_directory
        )
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Ruta de vídeo no permitida.",
        )

    if (
        not candidate.exists()
        or not candidate.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="El vídeo no existe.",
        )

    if (
        candidate.suffix.lower()
        not in VIDEO_EXTENSIONS
    ):
        raise HTTPException(
            status_code=415,
            detail="Formato de vídeo no compatible.",
        )

    return candidate


def _human_size(
    size_bytes: int,
) -> str:
    value = float(
        max(
            0,
            size_bytes,
        )
    )

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"

            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{size_bytes} B"


def _video_kind(
    filename: str,
) -> str:
    """
    Clasificación de respaldo para vídeos antiguos
    que todavía no tengan archivo JSON.
    """

    normalized = filename.lower()

    if (
        "parking" in normalized
        or "park" in normalized
    ):
        return "parking"

    if (
        "event" in normalized
        or "evento" in normalized
        or "protected" in normalized
    ):
        return "event"

    return "normal"


def _load_video_metadata(
    video_path: Path,
) -> dict:
    """
    Lee el JSON asociado al vídeo.

    Si no existe o está dañado, devuelve un diccionario vacío
    y el explorador utiliza los datos básicos del archivo.
    """

    metadata_path = (
        video_path.with_suffix(
            ".json"
        )
    )

    if not metadata_path.exists():
        return {}

    try:
        loaded = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        logger.warning(
            "No se pudieron leer los metadatos de %s",
            metadata_path,
        )

        return {}

    if not isinstance(
        loaded,
        dict,
    ):
        return {}

    return loaded


def _safe_number(
    value,
    default=0.0,
) -> float:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return float(default)


def _format_duration(
    seconds,
) -> str:
    total_seconds = max(
        0,
        int(
            round(
                _safe_number(
                    seconds,
                    0,
                )
            )
        ),
    )

    hours, remainder = divmod(
        total_seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if hours > 0:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def _coordinate_text(
    value,
):
    if (
        not isinstance(
            value,
            list,
        )
        or len(value) != 2
    ):
        return None

    try:
        return (
            f"{float(value[0]):.6f}, "
            f"{float(value[1]):.6f}"
        )
    except (
        TypeError,
        ValueError,
    ):
        return None


def _video_item(
    path: Path,
) -> dict:
    stat = path.stat()

    metadata = _load_video_metadata(
        path
    )

    created_value = metadata.get(
        "created"
    )

    created_at = None

    if created_value:
        try:
            created_at = (
                datetime.fromisoformat(
                    str(created_value)
                )
            )
        except ValueError:
            created_at = None

    if created_at is None:
        created_at = datetime.fromtimestamp(
            stat.st_mtime
        )

    video_type = str(
        metadata.get(
            "type",
            _video_kind(
                path.name
            ),
        )
    ).strip().lower()

    if video_type not in {
        "normal",
        "event",
        "parking",
    }:
        video_type = "normal"

    speed_data = metadata.get(
        "speed",
        {},
    )

    if not isinstance(
        speed_data,
        dict,
    ):
        speed_data = {}

    gps_data = metadata.get(
        "gps",
        {},
    )

    if not isinstance(
        gps_data,
        dict,
    ):
        gps_data = {}

    thumbnail_path = (
        path.with_suffix(
            ".jpg"
        )
    )

    has_thumbnail = (
        thumbnail_path.exists()
        and thumbnail_path.is_file()
    )

    duration = _safe_number(
        metadata.get(
            "duration",
            0,
        ),
        0,
    )

    size_bytes = int(
        metadata.get(
            "size_bytes",
            stat.st_size,
        )
        or stat.st_size
    )

    return {
        "name": path.name,
        "metadata_version": metadata.get(
            "version"
        ),
        "has_metadata": bool(
            metadata
        ),
        "has_thumbnail": has_thumbnail,
        "thumbnail_url": (
            f"/api/videos/thumbnail/{path.name}"
            if has_thumbnail
            else None
        ),
        "size_bytes": size_bytes,
        "size": _human_size(
            size_bytes
        ),
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime
        ).isoformat(),
        "created": created_at.isoformat(),
        "date": created_at.strftime(
            "%d/%m/%Y"
        ),
        "time": created_at.strftime(
            "%H:%M:%S"
        ),
        "duration_seconds": round(
            duration,
            2,
        ),
        "duration": _format_duration(
            duration
        ),
        "kind": video_type,
        "protected": bool(
            metadata.get(
                "protected",
                False,
            )
        ),
        "speed": {
            "max": round(
                _safe_number(
                    speed_data.get(
                        "max",
                        0,
                    )
                ),
                1,
            ),
            "average": round(
                _safe_number(
                    speed_data.get(
                        "average",
                        0,
                    )
                ),
                1,
            ),
        },
        "gps": {
            "start": gps_data.get(
                "start"
            ),
            "end": gps_data.get(
                "end"
            ),
            "start_text": _coordinate_text(
                gps_data.get(
                    "start"
                )
            ),
            "end_text": _coordinate_text(
                gps_data.get(
                    "end"
                )
            ),
        },
        "track": (
            metadata.get(
                "track",
                [],
            )
            if isinstance(
                metadata.get(
                    "track",
                    [],
                ),
                list,
            )
            else []
        ),
        "track_points": int(
            metadata.get(
                "track_points",
                len(
                    metadata.get(
                        "track",
                        [],
                    )
                    if isinstance(
                        metadata.get(
                            "track",
                            [],
                        ),
                        list,
                    )
                    else []
                ),
            )
            or 0
        ),
        "stream_url": (
            f"/api/videos/file/{path.name}"
        ),
        "download_url": (
            f"/api/videos/file/{path.name}"
            "?download=1"
        ),
    }


@router.get("/api/videos")
async def videos_list():
    videos_directory = (
        _videos_directory()
    )

    videos_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = [
        path
        for path in videos_directory.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in VIDEO_EXTENSIONS
        )
    ]

    files.sort(
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return {
        "ok": True,
        "folder": str(
            videos_directory
        ),
        "count": len(
            files
        ),
        "videos": [
            _video_item(
                path
            )
            for path in files
        ],
    }


@router.get(
    "/api/videos/file/{filename}"
)
async def video_file(
    filename: str,
    download: bool = False,
):
    path = _safe_video_path(
        filename
    )

    disposition = (
        "attachment"
        if download
        else "inline"
    )

    return FileResponse(
        path=path,
        media_type="video/mp4",
        filename=(
            path.name
            if download
            else None
        ),
        content_disposition_type=disposition,
    )


@router.delete(
    "/api/videos/{filename}"
)
async def video_delete(
    filename: str,
):
    path = _safe_video_path(
        filename
    )

    metadata = _load_video_metadata(
        path
    )

    if bool(
        metadata.get(
            "protected",
            False,
        )
    ):
        raise HTTPException(
            status_code=423,
            detail=(
                "Este vídeo está protegido. "
                "Debes quitar la protección antes de borrarlo."
            ),
        )

    current_file = None

    if recorder is not None:
        current_file = recorder.status().get(
            "current_file"
        )

    if (
        current_file
        and Path(
            str(current_file)
        ).resolve() == path
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "No se puede borrar el vídeo "
                "que está grabándose."
            ),
        )

    related_files = [
        path,
        path.with_suffix(
            ".json"
        ),
        path.with_suffix(
            ".jpg"
        ),
    ]

    deleted_files = []

    try:
        for related_path in related_files:
            if related_path.exists():
                related_path.unlink()

                deleted_files.append(
                    related_path.name
                )

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo borrar "
                "la sesión multimedia completa."
            ),
        ) from exc

    return {
        "ok": True,
        "message": (
            "Sesión multimedia eliminada."
        ),
        "name": path.name,
        "deleted": deleted_files,
    }


@router.get(
    "/api/videos/thumbnail/{filename}"
)
async def video_thumbnail(
    filename: str,
):
    video_path = _safe_video_path(
        filename
    )

    thumbnail_path = (
        video_path.with_suffix(
            ".jpg"
        )
    )

    if (
        not thumbnail_path.exists()
        or not thumbnail_path.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="La miniatura no existe.",
        )

    return FileResponse(
        path=thumbnail_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": (
                "public, max-age=3600"
            )
        },
    )


# ============================================================
# Explorador de viajes RoadEye 0.6
# ============================================================

def _trips_directory() -> Path:
    configured_folder = Path(
        str(
            config.get(
                "trips.folder",
                "trips",
            )
        )
    )

    if not configured_folder.is_absolute():
        configured_folder = (
            PROJECT_DIR
            / configured_folder
        )

    return configured_folder.resolve()


def _load_trip_file(
    path: Path,
) -> dict:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        logger.warning(
            "No se pudo leer el viaje %s: %s",
            path,
            exc,
        )

        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def _safe_trip_path(
    filename: str,
) -> Path:
    clean_name = Path(
        str(filename)
    ).name

    if not clean_name.endswith(
        ".json"
    ):
        raise HTTPException(
            status_code=400,
            detail="Nombre de viaje no válido.",
        )

    directory = _trips_directory()

    candidate = (
        directory
        / clean_name
    ).resolve()

    try:
        candidate.relative_to(
            directory
        )

    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Ruta de viaje no permitida.",
        )

    if (
        not candidate.exists()
        or not candidate.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="El viaje no existe.",
        )

    return candidate


def _trip_item(
    path: Path,
    *,
    include_route: bool = False,
) -> dict:
    data = _load_trip_file(
        path
    )

    started_text = data.get(
        "started"
    )

    started_at = None

    if started_text:
        try:
            started_at = datetime.fromisoformat(
                str(started_text)
            )
        except ValueError:
            started_at = None

    if started_at is None:
        started_at = datetime.fromtimestamp(
            path.stat().st_mtime
        )

    duration = _safe_number(
        data.get(
            "duration",
            0,
        )
    )

    speed = data.get(
        "speed",
        {},
    )

    if not isinstance(
        speed,
        dict,
    ):
        speed = {}

    gps = data.get(
        "gps",
        {},
    )

    if not isinstance(
        gps,
        dict,
    ):
        gps = {}

    distance = data.get(
        "distance",
        {},
    )

    if not isinstance(
        distance,
        dict,
    ):
        distance = {}

    motion = data.get(
        "motion",
        {},
    )

    if not isinstance(
        motion,
        dict,
    ):
        motion = {}

    segments = data.get(
        "segments",
        [],
    )

    if not isinstance(
        segments,
        list,
    ):
        segments = []

    route = data.get(
        "route",
        [],
    )

    if not isinstance(
        route,
        list,
    ):
        route = []

    result = {
        "filename": path.name,
        "trip_id": data.get(
            "trip_id"
        ),
        "trip_name": data.get(
            "trip_name",
            path.stem,
        ),
        "type": data.get(
            "type",
            "driving",
        ),
        "status": data.get(
            "status",
            "finished",
        ),
        "started": started_at.isoformat(),
        "finished": data.get(
            "finished"
        ),
        "date": started_at.strftime(
            "%d/%m/%Y"
        ),
        "time": started_at.strftime(
            "%H:%M:%S"
        ),
        "duration_seconds": round(
            duration,
            2,
        ),
        "duration": _format_duration(
            duration
        ),
        "size_bytes": int(
            data.get(
                "size_bytes",
                0,
            )
            or 0
        ),
        "size": _human_size(
            int(
                data.get(
                    "size_bytes",
                    0,
                )
                or 0
            )
        ),
        "segment_count": int(
            data.get(
                "segment_count",
                len(segments),
            )
            or len(segments)
        ),
        "segments": segments,
        "speed": {
            "max": round(
                _safe_number(
                    speed.get(
                        "max",
                        0,
                    )
                ),
                1,
            ),
            "average": round(
                _safe_number(
                    speed.get(
                        "average",
                        0,
                    )
                ),
                1,
            ),
            "average_moving": round(
                _safe_number(
                    speed.get(
                        "average_moving",
                        0,
                    )
                ),
                1,
            ),
        },
        "distance": {
            "meters": round(
                _safe_number(
                    distance.get(
                        "meters",
                        0,
                    )
                ),
                1,
            ),
            "kilometers": round(
                _safe_number(
                    distance.get(
                        "kilometers",
                        0,
                    )
                ),
                3,
            ),
        },
        "motion": {
            "threshold_kmh": round(
                _safe_number(
                    motion.get(
                        "threshold_kmh",
                        3.0,
                    )
                ),
                1,
            ),
            "moving_seconds": round(
                _safe_number(
                    motion.get(
                        "moving_seconds",
                        0,
                    )
                ),
                2,
            ),
            "stopped_seconds": round(
                _safe_number(
                    motion.get(
                        "stopped_seconds",
                        duration,
                    )
                ),
                2,
            ),
            "moving_percent": round(
                _safe_number(
                    motion.get(
                        "moving_percent",
                        0,
                    )
                ),
                1,
            ),
        },
        "gps": {
            "start": gps.get(
                "start"
            ),
            "end": gps.get(
                "end"
            ),
            "start_text": _coordinate_text(
                gps.get(
                    "start"
                )
            ),
            "end_text": _coordinate_text(
                gps.get(
                    "end"
                )
            ),
        },
        "route_points": int(
            data.get(
                "route_points",
                len(route),
            )
            or len(route)
        ),
        "event_count": int(
            data.get(
                "event_count",
                len(
                    data.get(
                        "events",
                        [],
                    )
                    if isinstance(
                        data.get(
                            "events",
                            [],
                        ),
                        list,
                    )
                    else []
                ),
            )
            or 0
        ),
        "events": (
            data.get(
                "events",
                [],
            )
            if isinstance(
                data.get(
                    "events",
                    [],
                ),
                list,
            )
            else []
        ),
    }

    if include_route:
        result["route"] = route

    return result


@router.get("/api/trips")
async def trips_list():
    directory = _trips_directory()

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        directory.glob(
            "trip_*.json"
        ),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    return {
        "ok": True,
        "folder": str(
            directory
        ),
        "count": len(
            files
        ),
        "trips": [
            _trip_item(
                path,
                include_route=False,
            )
            for path in files
        ],
    }


@router.get(
    "/api/trips/{filename}"
)
async def trip_details(
    filename: str,
):
    path = _safe_trip_path(
        filename
    )

    return {
        "ok": True,
        "trip": _trip_item(
            path,
            include_route=True,
        ),
    }


# ============================================================
# Eventos del viaje
# ============================================================

EVENT_TYPES = {
    "manual": {
        "label": "Evento manual",
        "severity": "info",
    },
    "photo": {
        "label": "Fotografía",
        "severity": "info",
    },
    "braking": {
        "label": "Frenazo fuerte",
        "severity": "warning",
    },
    "impact": {
        "label": "Posible impacto",
        "severity": "critical",
    },
    "overspeed": {
        "label": "Exceso de velocidad",
        "severity": "warning",
    },
    "parking": {
        "label": "Movimiento en aparcamiento",
        "severity": "warning",
    },
    "adas": {
        "label": "Aviso ADAS",
        "severity": "warning",
    },
}


@router.post("/api/events")
async def create_trip_event(
    payload: dict,
):
    if not isinstance(
        payload,
        dict,
    ):
        raise HTTPException(
            status_code=422,
            detail="El evento debe ser un objeto JSON.",
        )

    event_type = str(
        payload.get(
            "type",
            "manual",
        )
    ).strip().lower()

    if event_type not in EVENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Tipo de evento no válido: {event_type}"
            ),
        )

    defaults = EVENT_TYPES[
        event_type
    ]

    current_file = None
    segment_time = 0.0

    if recorder is not None:
        recorder_status = recorder.status()

        current_file = recorder_status.get(
            "current_file"
        )

        segment_time = max(
            0.0,
            _safe_number(
                recorder_status.get(
                    "segment_elapsed",
                    0,
                ),
                0,
            ),
        )

        if current_file:
            current_file = Path(
                str(current_file)
            ).name

    event_protected = bool(
        payload.get(
            "protected",
            event_type in {
                "impact",
                "parking",
            },
        )
    )

    protection_context = {
        "previous": False,
        "current": False,
        "next_count": 0,
        "reason": event_type,
    }

    if (
        event_protected
        and recorder is not None
    ):
        protection_context = (
            recorder.protect_event_context(
                reason=event_type,
                protect_previous=True,
                protect_next=1,
            )
        )

    result = trip_manager.add_event(
        event_type=event_type,
        label=str(
            payload.get(
                "label",
                defaults["label"],
            )
        ),
        source=str(
            payload.get(
                "source",
                "web",
            )
        ),
        severity=str(
            payload.get(
                "severity",
                defaults["severity"],
            )
        ),
        protected=event_protected,
        segment=current_file,
        segment_time=segment_time,
        latitude=system_state.get(
            "latitude"
        ),
        longitude=system_state.get(
            "longitude"
        ),
        speed=system_state.get(
            "speed"
        ),
        data=payload.get(
            "data",
            {},
        ),
    )

    return {
        "ok": True,
        "message": "Evento registrado.",
        "segment_protected": bool(
            protection_context.get(
                "current",
                False,
            )
        ),
        "protection_context": protection_context,
        **result,
    }


# ============================================================
# Fotografías inteligentes RoadEye
# ============================================================

def _photos_directory() -> Path:
    configured_folder = Path(
        str(
            config.get(
                "photos.folder",
                "photos",
            )
        )
    )

    if not configured_folder.is_absolute():
        configured_folder = (
            PROJECT_DIR
            / configured_folder
        )

    directory = configured_folder.resolve()

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def _safe_photo_path(
    filename: str,
) -> Path:
    clean_name = Path(
        str(filename)
    ).name

    if not clean_name.lower().endswith(
        (
            ".jpg",
            ".jpeg",
            ".png",
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Nombre de fotografía no válido.",
        )

    directory = _photos_directory()

    candidate = (
        directory
        / clean_name
    ).resolve()

    try:
        candidate.relative_to(
            directory
        )

    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Ruta de fotografía no permitida.",
        )

    if (
        not candidate.exists()
        or not candidate.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="La fotografía no existe.",
        )

    return candidate


def _create_photo_thumbnail(
    frame,
    output_path: Path,
) -> bool:
    height, width = frame.shape[:2]

    if width <= 0 or height <= 0:
        return False

    configured_width = int(
        config.get(
            "photos.thumbnail_width",
            480,
        )
    )

    target_width = max(
        120,
        min(
            configured_width,
            width,
        ),
    )

    target_height = max(
        1,
        int(
            height
            * target_width
            / width
        ),
    )

    thumbnail = cv2.resize(
        frame,
        (
            target_width,
            target_height,
        ),
        interpolation=cv2.INTER_AREA,
    )

    quality = int(
        config.get(
            "photos.thumbnail_quality",
            82,
        )
    )

    quality = max(
        1,
        min(
            100,
            quality,
        ),
    )

    return bool(
        cv2.imwrite(
            str(output_path),
            thumbnail,
            [
                int(
                    cv2.IMWRITE_JPEG_QUALITY
                ),
                quality,
            ],
        )
    )


@router.post("/api/photos/capture")
async def capture_photo():
    frame = frame_buffer.get_frame()

    if frame is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "La cámara todavía no dispone "
                "de un fotograma."
            ),
        )

    photos_directory = (
        _photos_directory()
    )

    timestamp = datetime.now()

    unique_name = timestamp.strftime(
        "photo_%Y%m%d_%H%M%S_%f"
    )

    photo_path = (
        photos_directory
        / f"{unique_name}.jpg"
    )

    thumbnail_path = (
        photos_directory
        / f"{unique_name}_thumb.jpg"
    )

    jpeg_quality = int(
        config.get(
            "photos.jpeg_quality",
            95,
        )
    )

    jpeg_quality = max(
        1,
        min(
            100,
            jpeg_quality,
        ),
    )

    photo_saved = cv2.imwrite(
        str(photo_path),
        frame,
        [
            int(
                cv2.IMWRITE_JPEG_QUALITY
            ),
            jpeg_quality,
        ],
    )

    if not photo_saved:
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar la fotografía.",
        )

    thumbnail_saved = (
        _create_photo_thumbnail(
            frame,
            thumbnail_path,
        )
    )

    recorder_status = (
        recorder.status()
        if recorder is not None
        else {}
    )

    current_file = recorder_status.get(
        "current_file"
    )

    if current_file:
        current_file = Path(
            str(current_file)
        ).name

    segment_time = max(
        0.0,
        _safe_number(
            recorder_status.get(
                "segment_elapsed",
                0,
            ),
            0,
        ),
    )

    latitude = system_state.get(
        "latitude"
    )

    longitude = system_state.get(
        "longitude"
    )

    speed = system_state.get(
        "speed"
    )

    event_result = trip_manager.add_event(
        event_type="photo",
        label="Fotografía",
        source="web",
        severity="info",
        protected=False,
        created=timestamp,
        segment=current_file,
        segment_time=segment_time,
        latitude=latitude,
        longitude=longitude,
        speed=speed,
        data={
            "photo": {
                "filename": photo_path.name,
                "thumbnail": (
                    thumbnail_path.name
                    if thumbnail_saved
                    else None
                ),
                "url": (
                    f"/api/photos/file/"
                    f"{photo_path.name}"
                ),
                "thumbnail_url": (
                    f"/api/photos/file/"
                    f"{thumbnail_path.name}"
                    if thumbnail_saved
                    else None
                ),
                "width": int(
                    frame.shape[1]
                ),
                "height": int(
                    frame.shape[0]
                ),
                "size_bytes": int(
                    photo_path.stat().st_size
                ),
            }
        },
    )

    return {
        "ok": True,
        "message": "Fotografía guardada.",
        "photo": {
            "filename": photo_path.name,
            "thumbnail": (
                thumbnail_path.name
                if thumbnail_saved
                else None
            ),
            "url": (
                f"/api/photos/file/"
                f"{photo_path.name}"
            ),
            "thumbnail_url": (
                f"/api/photos/file/"
                f"{thumbnail_path.name}"
                if thumbnail_saved
                else None
            ),
        },
        **event_result,
    }


@router.get(
    "/api/photos/file/{filename}"
)
async def photo_file(
    filename: str,
    download: bool = False,
):
    path = _safe_photo_path(
        filename
    )

    return FileResponse(
        path=path,
        media_type="image/jpeg",
        filename=(
            path.name
            if download
            else None
        ),
        content_disposition_type=(
            "attachment"
            if download
            else "inline"
        ),
        headers={
            "Cache-Control": (
                "public, max-age=3600"
            )
        },
    )


@router.put(
    "/api/videos/{filename}/protection"
)
async def video_protection_update(
    filename: str,
    payload: dict,
):
    path = _safe_video_path(
        filename
    )

    protected = bool(
        payload.get(
            "protected",
            True,
        )
    )

    metadata_path = path.with_suffix(
        ".json"
    )

    metadata = _load_video_metadata(
        path
    )

    if not metadata:
        metadata = {
            "version": 1,
            "filename": path.name,
        }

    metadata["protected"] = protected

    temporary_path = (
        metadata_path.with_suffix(
            ".json.tmp"
        )
    )

    temporary_path.write_text(
        json.dumps(
            metadata,
            indent=4,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(
        metadata_path
    )

    return {
        "ok": True,
        "name": path.name,
        "protected": protected,
        "message": (
            "Vídeo protegido."
            if protected
            else "Protección retirada."
        ),
    }


# ============================================================
# Gestión de almacenamiento
# ============================================================

@router.get(
    "/api/storage/status"
)
async def storage_status():
    if storage_manager is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "StorageManager no está disponible."
            ),
        )

    return {
        "ok": True,
        "storage": storage_manager.status(),
    }


@router.post(
    "/api/storage/cleanup"
)
async def storage_cleanup(
    payload: dict | None = None,
):
    if storage_manager is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "StorageManager no está disponible."
            ),
        )

    payload = (
        payload
        if isinstance(
            payload,
            dict,
        )
        else {}
    )

    result = storage_manager.cleanup(
        reason="api",
        force=bool(
            payload.get(
                "force",
                False,
            )
        ),
        dry_run=(
            bool(
                payload.get(
                    "dry_run"
                )
            )
            if "dry_run" in payload
            else None
        ),
    )

    return {
        "ok": bool(
            result.get(
                "ok",
                False,
            )
        ),
        "result": result,
    }


# ============================================================
# RoadEye Control Center
# ============================================================

def _settings_config_path() -> Path:
    return (
        PROJECT_DIR
        / "config"
        / "config.json"
    ).resolve()


def _settings_read_config() -> dict:
    path = _settings_config_path()

    try:
        loaded = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo leer la configuración."
            ),
        ) from exc

    if not isinstance(
        loaded,
        dict,
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "El archivo de configuración "
                "no contiene un objeto válido."
            ),
        )

    return loaded


def _settings_atomic_write(
    data: dict,
) -> None:
    path = _settings_config_path()

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_path = path.with_suffix(
        ".json.last-good"
    )

    if path.exists():
        try:
            backup_path.write_bytes(
                path.read_bytes()
            )
        except OSError:
            logger.warning(
                "No se pudo crear la copia "
                "last-good de configuración."
            )

    temporary_path = path.with_suffix(
        ".json.tmp"
    )

    try:
        temporary_path.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        temporary_path.replace(
            path
        )

    except OSError as exc:
        temporary_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "No se pudo guardar "
                "la configuración."
            ),
        ) from exc


def _settings_number(
    value,
    *,
    minimum: float,
    maximum: float,
    field: str,
    integer: bool = False,
):
    try:
        number = (
            int(value)
            if integer
            else float(value)
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"El valor de {field} "
                "no es válido."
            ),
        ) from exc

    if (
        number < minimum
        or number > maximum
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                f"{field} debe estar entre "
                f"{minimum} y {maximum}."
            ),
        )

    return number


def _settings_validate(
    payload: dict,
) -> dict:
    if not isinstance(
        payload,
        dict,
    ):
        raise HTTPException(
            status_code=422,
            detail="Configuración no válida.",
        )

    storage_raw = payload.get(
        "storage",
        {},
    )

    recording_raw = payload.get(
        "recording",
        {},
    )

    parking_raw = payload.get(
        "parking",
        {},
    )

    for section_name, section in (
        ("storage", storage_raw),
        ("recording", recording_raw),
        ("parking", parking_raw),
    ):
        if not isinstance(
            section,
            dict,
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"La sección {section_name} "
                    "no es válida."
                ),
            )

    trigger = str(
        parking_raw.get(
            "trigger",
            "motion_or_impact",
        )
    ).strip().lower()

    allowed_triggers = {
        "motion",
        "impact",
        "motion_or_impact",
    }

    if trigger not in allowed_triggers:
        raise HTTPException(
            status_code=422,
            detail=(
                "El disparador de Parking "
                "no es válido."
            ),
        )

    return {
        "storage": {
            "enabled": bool(
                storage_raw.get(
                    "enabled",
                    True,
                )
            ),
            "max_usage_percent": (
                _settings_number(
                    storage_raw.get(
                        "max_usage_percent",
                        85,
                    ),
                    minimum=40,
                    maximum=98,
                    field=(
                        "Uso máximo del disco"
                    ),
                )
            ),
            "minimum_free_gb": (
                _settings_number(
                    storage_raw.get(
                        "minimum_free_gb",
                        10,
                    ),
                    minimum=1,
                    maximum=500,
                    field=(
                        "Espacio libre mínimo"
                    ),
                )
            ),
            "check_interval_seconds": (
                _settings_number(
                    storage_raw.get(
                        "check_interval_seconds",
                        60,
                    ),
                    minimum=10,
                    maximum=86400,
                    field=(
                        "Intervalo de comprobación"
                    ),
                    integer=True,
                )
            ),
            "clean_on_start": bool(
                storage_raw.get(
                    "clean_on_start",
                    True,
                )
            ),
            "clean_before_recording": bool(
                storage_raw.get(
                    "clean_before_recording",
                    True,
                )
            ),
            "delete_oldest_normal": bool(
                storage_raw.get(
                    "delete_oldest_normal",
                    True,
                )
            ),
            "never_delete_protected": True,
            "clean_video_orphans": bool(
                storage_raw.get(
                    "clean_video_orphans",
                    True,
                )
            ),
            "delete_empty_trips": bool(
                storage_raw.get(
                    "delete_empty_trips",
                    True,
                )
            ),
            "dry_run": bool(
                storage_raw.get(
                    "dry_run",
                    False,
                )
            ),
        },
        "recording": {
            "enabled": bool(
                recording_raw.get(
                    "enabled",
                    False,
                )
            ),
            "fps": (
                _settings_number(
                    recording_raw.get(
                        "fps",
                        20,
                    ),
                    minimum=5,
                    maximum=30,
                    field="FPS",
                )
            ),
            "segment_seconds": (
                _settings_number(
                    recording_raw.get(
                        "segment_seconds",
                        30,
                    ),
                    minimum=10,
                    maximum=600,
                    field=(
                        "Duración del segmento"
                    ),
                )
            ),
        },
        "parking": {
            "enabled": bool(
                parking_raw.get(
                    "enabled",
                    False,
                )
            ),
            "trigger": trigger,
            "pre_event_seconds": (
                _settings_number(
                    parking_raw.get(
                        "pre_event_seconds",
                        10,
                    ),
                    minimum=0,
                    maximum=120,
                    field=(
                        "Segundos anteriores"
                    ),
                )
            ),
            "record_seconds": (
                _settings_number(
                    parking_raw.get(
                        "record_seconds",
                        30,
                    ),
                    minimum=5,
                    maximum=600,
                    field=(
                        "Duración inicial Parking"
                    ),
                )
            ),
            "extend_seconds": (
                _settings_number(
                    parking_raw.get(
                        "extend_seconds",
                        15,
                    ),
                    minimum=0,
                    maximum=300,
                    field=(
                        "Extensión por movimiento"
                    ),
                )
            ),
            "max_event_seconds": (
                _settings_number(
                    parking_raw.get(
                        "max_event_seconds",
                        120,
                    ),
                    minimum=10,
                    maximum=3600,
                    field=(
                        "Duración máxima del evento"
                    ),
                )
            ),
            "cooldown_seconds": (
                _settings_number(
                    parking_raw.get(
                        "cooldown_seconds",
                        5,
                    ),
                    minimum=0,
                    maximum=300,
                    field=(
                        "Tiempo de espera Parking"
                    ),
                )
            ),
            "motion_sensitivity": (
                _settings_number(
                    parking_raw.get(
                        "motion_sensitivity",
                        0.55,
                    ),
                    minimum=0.05,
                    maximum=1,
                    field=(
                        "Sensibilidad de movimiento"
                    ),
                )
            ),
            "protect_recording": bool(
                parking_raw.get(
                    "protect_recording",
                    True,
                )
            ),
            "capture_photo": bool(
                parking_raw.get(
                    "capture_photo",
                    False,
                )
            ),
        },
    }


@router.get(
    "/api/settings"
)
async def settings_get():
    data = _settings_read_config()

    return {
        "ok": True,
        "settings": {
            "storage": data.get(
                "storage",
                {},
            ),
            "recording": data.get(
                "recording",
                {},
            ),
            "parking": data.get(
                "parking",
                {},
            ),
        },
        "restart_required_after_save": True,
    }


@router.put(
    "/api/settings"
)
async def settings_update(
    payload: dict,
):
    validated = _settings_validate(
        payload
    )

    data = _settings_read_config()

    for section, values in validated.items():
        current = data.get(
            section,
            {},
        )

        if not isinstance(
            current,
            dict,
        ):
            current = {}

        current.update(
            values
        )

        data[
            section
        ] = current

    _settings_atomic_write(
        data
    )

    return {
        "ok": True,
        "settings": validated,
        "restart_required": True,
        "message": (
            "Configuración guardada. "
            "Reinicia RoadEye para aplicar "
            "todos los cambios."
        ),
    }
# ============================================================
# RoadEye Sentinel · Modo Parking
# ============================================================

parking_service = None


@router.get(
    "/api/parking/status"
)
async def parking_status():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "parking": parking_service.status(),
    }


@router.post(
    "/api/parking/activate"
)
async def parking_activate():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "parking": parking_service.activate(),
    }


@router.post(
    "/api/parking/deactivate"
)
async def parking_deactivate():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "parking": parking_service.deactivate(),
    }


@router.post(
    "/api/parking/simulate"
)
async def parking_simulate():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "message": "Evento Parking simulado.",
        "parking": parking_service.simulate_event(),
    }
# ============================================================
# RoadEye Sentinel · Historial Parking
# ============================================================

@router.get(
    "/api/parking/history"
)
async def parking_history(
    limit: int = 20,
):
    safe_limit = max(
        1,
        min(
            100,
            int(limit),
        ),
    )

    trips_directory = (
        PROJECT_DIR / "trips"
    )

    history = []

    if trips_directory.exists():
        paths = sorted(
            trips_directory.glob(
                "trip_*.json"
            ),
            key=lambda item: (
                item.stat().st_mtime
            ),
            reverse=True,
        )

        for path in paths:
            try:
                trip = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

            except (
                OSError,
                json.JSONDecodeError,
            ):
                continue

            if not isinstance(
                trip,
                dict,
            ):
                continue

            for event in trip.get(
                "events",
                [],
            ):
                if not isinstance(
                    event,
                    dict,
                ):
                    continue

                if str(
                    event.get(
                        "type",
                        "",
                    )
                ).lower() != "parking":
                    continue

                data = event.get(
                    "data",
                    {},
                )

                if not isinstance(
                    data,
                    dict,
                ):
                    data = {}

                history.append(
                    {
                        "event_id": event.get(
                            "event_id"
                        ),
                        "created": event.get(
                            "created"
                        ),
                        "label": event.get(
                            "label",
                            "Evento Parking",
                        ),
                        "source": event.get(
                            "source"
                        ),
                        "protected": bool(
                            event.get(
                                "protected",
                                False,
                            )
                        ),
                        "segment": event.get(
                            "segment"
                        ),
                        "segment_time": event.get(
                            "segment_time",
                            0,
                        ),
                        "trip_id": trip.get(
                            "trip_id"
                        ),
                        "trip_type": trip.get(
                            "type"
                        ),
                        "motion_ratio": data.get(
                            "motion_ratio"
                        ),
                        "simulation": bool(
                            data.get(
                                "simulation",
                                False,
                            )
                        ),
                        "photo": data.get(
                            "photo"
                        ),
                    }
                )

    history.sort(
        key=lambda item: str(
            item.get(
                "created",
                "",
            )
        ),
        reverse=True,
    )

    return {
        "ok": True,
        "count": min(
            len(history),
            safe_limit,
        ),
        "events": history[
            :safe_limit
        ],
    }
