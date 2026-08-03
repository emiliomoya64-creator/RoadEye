from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from core.config_manager import PROJECT_DIR, config
from core.system_state import system_state
from recorder.recorder_service import RecorderService


router = APIRouter()

recorder: Optional[RecorderService] = None


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
