from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from threading import Event, RLock, Thread
from typing import Any, Callable, Optional

from core.config_manager import PROJECT_DIR, config


logger = logging.getLogger(__name__)


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
}


class StorageManager:
    """
    Gestiona automáticamente el almacenamiento de RoadEye.

    Principios:

    - Nunca borra vídeos protegidos.
    - Nunca borra el archivo que se está grabando.
    - Borra primero el contenido normal más antiguo.
    - Elimina vídeo, JSON y miniatura juntos.
    - Actualiza los archivos de viaje afectados.
    - Puede funcionar en modo simulación.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None

        self._active_file_provider: Optional[
            Callable[[], Optional[str]]
        ] = None

        self._last_check: Optional[str] = None
        self._last_cleanup: Optional[str] = None
        self._last_error: Optional[str] = None
        self._last_result: dict[str, Any] = {}

        self._deleted_total = 0
        self._freed_total_bytes = 0

    # ---------------------------------------------------------
    # Configuración
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return bool(
            config.get(
                "storage.enabled",
                True,
            )
        )

    @property
    def videos_directory(self) -> Path:
        configured = Path(
            str(
                config.get(
                    "recording.folder",
                    "videos",
                )
            )
        )

        if not configured.is_absolute():
            configured = (
                PROJECT_DIR
                / configured
            )

        configured = configured.resolve()

        configured.mkdir(
            parents=True,
            exist_ok=True,
        )

        return configured

    @property
    def trips_directory(self) -> Path:
        configured = Path(
            str(
                config.get(
                    "trips.folder",
                    "trips",
                )
            )
        )

        if not configured.is_absolute():
            configured = (
                PROJECT_DIR
                / configured
            )

        configured = configured.resolve()

        configured.mkdir(
            parents=True,
            exist_ok=True,
        )

        return configured

    def set_active_file_provider(
        self,
        provider: Callable[
            [],
            Optional[str],
        ],
    ) -> None:
        self._active_file_provider = provider

    # ---------------------------------------------------------
    # Ciclo de vida
    # ---------------------------------------------------------

    @property
    def running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )

    def start(self) -> None:
        if self.running:
            return

        self._stop_event.clear()

        self._thread = Thread(
            target=self._loop,
            name="roadeye-storage-manager",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "StorageManager iniciado."
        )

        if bool(
            config.get(
                "storage.clean_on_start",
                True,
            )
        ):
            try:
                self.cleanup(
                    reason="startup",
                )
            except Exception:
                logger.exception(
                    "Falló la limpieza inicial."
                )

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=3.0
            )

        self._thread = None

        logger.info(
            "StorageManager detenido."
        )

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            interval = max(
                10,
                int(
                    config.get(
                        "storage.check_interval_seconds",
                        60,
                    )
                    or 60
                ),
            )

            if self._stop_event.wait(
                interval
            ):
                break

            try:
                self.cleanup(
                    reason="periodic",
                )
            except Exception:
                logger.exception(
                    "Falló la limpieza periódica."
                )

    # ---------------------------------------------------------
    # Estado del disco
    # ---------------------------------------------------------

    def disk_status(self) -> dict[str, Any]:
        usage = shutil.disk_usage(
            self.videos_directory
        )

        used_percent = (
            usage.used
            / usage.total
            * 100
            if usage.total > 0
            else 0.0
        )

        minimum_free_bytes = int(
            max(
                0.0,
                float(
                    config.get(
                        "storage.minimum_free_gb",
                        10,
                    )
                    or 0
                ),
            )
            * 1024**3
        )

        maximum_usage = max(
            1.0,
            min(
                99.0,
                float(
                    config.get(
                        "storage.max_usage_percent",
                        85,
                    )
                    or 85
                ),
            ),
        )

        over_usage_limit = (
            used_percent
            > maximum_usage
        )

        below_free_limit = (
            usage.free
            < minimum_free_bytes
        )

        return {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "used_percent": round(
                used_percent,
                2,
            ),
            "max_usage_percent": maximum_usage,
            "minimum_free_bytes": minimum_free_bytes,
            "minimum_free_gb": round(
                minimum_free_bytes
                / 1024**3,
                2,
            ),
            "over_usage_limit": over_usage_limit,
            "below_free_limit": below_free_limit,
            "cleanup_required": (
                over_usage_limit
                or below_free_limit
            ),
        }

    def status(self) -> dict[str, Any]:
        disk = self.disk_status()

        return {
            "enabled": self.enabled,
            "running": self.running,
            "folder": str(
                self.videos_directory
            ),
            "disk": disk,
            "last_check": self._last_check,
            "last_cleanup": self._last_cleanup,
            "last_error": self._last_error,
            "last_result": self._last_result,
            "deleted_total": self._deleted_total,
            "freed_total_bytes":
                self._freed_total_bytes,
            "freed_total": self._human_size(
                self._freed_total_bytes
            ),
        }

    # ---------------------------------------------------------
    # Limpieza principal
    # ---------------------------------------------------------

    def ensure_capacity(
        self,
        *,
        reason: str = "before_recording",
    ) -> dict[str, Any]:
        if not bool(
            config.get(
                "storage.clean_before_recording",
                True,
            )
        ):
            return {
                "ok": True,
                "skipped": True,
                "reason": (
                    "clean_before_recording_disabled"
                ),
            }

        return self.cleanup(
            reason=reason,
        )

    def cleanup(
        self,
        *,
        reason: str = "manual",
        force: bool = False,
        dry_run: Optional[bool] = None,
    ) -> dict[str, Any]:
        with self._lock:
            started_at = datetime.now()

            self._last_check = (
                started_at.isoformat()
            )

            if not self.enabled:
                result = {
                    "ok": True,
                    "enabled": False,
                    "skipped": True,
                    "reason": "disabled",
                }

                self._last_result = result

                return result

            configured_dry_run = bool(
                config.get(
                    "storage.dry_run",
                    False,
                )
            )

            effective_dry_run = (
                configured_dry_run
                if dry_run is None
                else bool(dry_run)
            )

            before = self.disk_status()

            result: dict[str, Any] = {
                "ok": True,
                "reason": reason,
                "force": bool(force),
                "dry_run": effective_dry_run,
                "before": before,
                "after": before,
                "deleted": [],
                "skipped_protected": 0,
                "skipped_active": 0,
                "freed_bytes": 0,
                "freed": "0 B",
                "orphans_removed": [],
                "trips_updated": [],
                "trips_removed": [],
                "limit_reached": False,
            }

            try:
                if bool(
                    config.get(
                        "storage.clean_video_orphans",
                        True,
                    )
                ):
                    result[
                        "orphans_removed"
                    ] = self._clean_video_orphans(
                        dry_run=effective_dry_run,
                    )

                needs_cleanup = bool(
                    before[
                        "cleanup_required"
                    ]
                )

                if (
                    force
                    or needs_cleanup
                ):
                    candidates = (
                        self._deletion_candidates()
                    )

                    for candidate in candidates:
                        current = self.disk_status()

                        if (
                            not force
                            and not current[
                                "cleanup_required"
                            ]
                        ):
                            break

                        if candidate[
                            "protected"
                        ]:
                            result[
                                "skipped_protected"
                            ] += 1
                            continue

                        if candidate[
                            "active"
                        ]:
                            result[
                                "skipped_active"
                            ] += 1
                            continue

                        deletion = self._delete_video_bundle(
                            candidate["path"],
                            dry_run=effective_dry_run,
                        )

                        if not deletion[
                            "deleted"
                        ]:
                            continue

                        result["deleted"].append(
                            deletion
                        )

                        result[
                            "freed_bytes"
                        ] += deletion[
                            "freed_bytes"
                        ]

                        trip_updates = (
                            self._remove_video_from_trips(
                                candidate["path"].name,
                                dry_run=effective_dry_run,
                            )
                        )

                        result[
                            "trips_updated"
                        ].extend(
                            trip_updates[
                                "updated"
                            ]
                        )

                        result[
                            "trips_removed"
                        ].extend(
                            trip_updates[
                                "removed"
                            ]
                        )

                if bool(
                    config.get(
                        "storage.delete_empty_trips",
                        True,
                    )
                ):
                    empty_result = (
                        self._clean_empty_trips(
                            dry_run=effective_dry_run,
                        )
                    )

                    result[
                        "trips_removed"
                    ].extend(
                        empty_result
                    )

                removed_trips = set(
                    result["trips_removed"]
                )

                result["trips_removed"] = sorted(
                    removed_trips
                )

                result["trips_updated"] = sorted(
                    set(
                        result["trips_updated"]
                    )
                    - removed_trips
                )

                after = self.disk_status()

                result["after"] = after
                result["freed"] = (
                    self._human_size(
                        result[
                            "freed_bytes"
                        ]
                    )
                )

                result[
                    "limit_reached"
                ] = bool(
                    after[
                        "cleanup_required"
                    ]
                )

                if (
                    not effective_dry_run
                    and result["deleted"]
                ):
                    self._last_cleanup = (
                        datetime.now().isoformat()
                    )

                    self._deleted_total += len(
                        result["deleted"]
                    )

                    self._freed_total_bytes += int(
                        result[
                            "freed_bytes"
                        ]
                    )

                if result[
                    "limit_reached"
                ]:
                    logger.warning(
                        "No se pudo alcanzar el margen "
                        "de almacenamiento configurado."
                    )

                self._last_error = None
                self._last_result = result

                logger.info(
                    "Limpieza de almacenamiento: "
                    "%d vídeos, %s liberados, "
                    "dry_run=%s, motivo=%s",
                    len(result["deleted"]),
                    result["freed"],
                    effective_dry_run,
                    reason,
                )

                return result

            except Exception as exc:
                self._last_error = str(
                    exc
                )

                result["ok"] = False
                result["error"] = str(
                    exc
                )

                self._last_result = result

                logger.exception(
                    "Error durante la limpieza "
                    "del almacenamiento."
                )

                return result

    # ---------------------------------------------------------
    # Candidatos
    # ---------------------------------------------------------

    def _deletion_candidates(
        self,
    ) -> list[dict[str, Any]]:
        active_path = (
            self._active_video_path()
        )

        candidates = []

        for path in self.videos_directory.iterdir():
            if (
                not path.is_file()
                or path.suffix.lower()
                not in VIDEO_EXTENSIONS
            ):
                continue

            # Las copias *_web.mp4 son derivados del vídeo
            # original y no candidatos independientes.
            if path.stem.endswith(
                "_web"
            ):
                continue

            metadata = self._load_json(
                path.with_suffix(
                    ".json"
                )
            )

            protected = bool(
                metadata.get(
                    "protected",
                    False,
                )
            )

            video_type = str(
                metadata.get(
                    "type",
                    "normal",
                )
            ).strip().lower()

            if video_type not in {
                "normal",
                "event",
                "parking",
            }:
                video_type = "normal"

            if (
                bool(
                    config.get(
                        "storage.delete_oldest_normal",
                        True,
                    )
                )
                and video_type
                != "normal"
            ):
                continue

            resolved = path.resolve()

            candidates.append(
                {
                    "path": resolved,
                    "protected": protected,
                    "active": (
                        active_path is not None
                        and resolved
                        == active_path
                    ),
                    "created": self._created_timestamp(
                        path,
                        metadata,
                    ),
                }
            )

        candidates.sort(
            key=lambda item: item[
                "created"
            ]
        )

        return candidates

    def _active_video_path(
        self,
    ) -> Optional[Path]:
        if self._active_file_provider is None:
            return None

        try:
            value = (
                self._active_file_provider()
            )
        except Exception:
            logger.exception(
                "No se pudo consultar "
                "el vídeo activo."
            )
            return None

        if not value:
            return None

        try:
            return Path(
                str(value)
            ).resolve()
        except OSError:
            return None

    # ---------------------------------------------------------
    # Borrado multimedia
    # ---------------------------------------------------------

    def _delete_video_bundle(
        self,
        video_path: Path,
        *,
        dry_run: bool,
    ) -> dict[str, Any]:
        web_copy = video_path.with_name(
            f"{video_path.stem}_web"
            f"{video_path.suffix}"
        )

        related = [
            video_path,
            video_path.with_suffix(
                ".json"
            ),
            video_path.with_suffix(
                ".jpg"
            ),
            web_copy,
        ]

        existing = [
            path
            for path in related
            if path.exists()
            and path.is_file()
        ]

        freed_bytes = sum(
            path.stat().st_size
            for path in existing
        )

        deleted_names = [
            path.name
            for path in existing
        ]

        if not dry_run:
            for path in existing:
                path.unlink(
                    missing_ok=True
                )

        return {
            "video": video_path.name,
            "deleted": deleted_names,
            "freed_bytes": freed_bytes,
            "freed": self._human_size(
                freed_bytes
            ),
            "dry_run": dry_run,
        }

    # ---------------------------------------------------------
    # Viajes
    # ---------------------------------------------------------

    def _remove_video_from_trips(
        self,
        filename: str,
        *,
        dry_run: bool,
    ) -> dict[str, list[str]]:
        result = {
            "updated": [],
            "removed": [],
        }

        for path in sorted(
            self.trips_directory.glob(
                "trip_*.json"
            )
        ):
            data = self._load_json(
                path
            )

            if not data:
                continue

            segments = data.get(
                "segments",
                [],
            )

            if not isinstance(
                segments,
                list,
            ):
                continue

            new_segments = [
                segment
                for segment in segments
                if not (
                    isinstance(
                        segment,
                        dict,
                    )
                    and segment.get(
                        "filename"
                    ) == filename
                )
            ]

            if len(new_segments) == len(
                segments
            ):
                continue

            if not new_segments:
                if not dry_run:
                    path.unlink(
                        missing_ok=True
                    )

                result["removed"].append(
                    path.name
                )

                continue

            data["segments"] = new_segments
            data["segment_count"] = len(
                new_segments
            )

            data["size_bytes"] = sum(
                self._safe_int(
                    segment.get(
                        "size_bytes",
                        0,
                    )
                )
                for segment in new_segments
                if isinstance(
                    segment,
                    dict,
                )
            )

            data["duration"] = round(
                sum(
                    self._safe_float(
                        segment.get(
                            "duration",
                            0,
                        )
                    )
                    for segment in new_segments
                    if isinstance(
                        segment,
                        dict,
                    )
                ),
                2,
            )

            events = data.get(
                "events",
                [],
            )

            if isinstance(
                events,
                list,
            ):
                data["events"] = [
                    event
                    for event in events
                    if not (
                        isinstance(
                            event,
                            dict,
                        )
                        and event.get(
                            "segment"
                        ) == filename
                    )
                ]

                data["event_count"] = len(
                    data["events"]
                )

            data[
                "storage_pruned"
            ] = True

            data[
                "storage_pruned_at"
            ] = datetime.now().isoformat()

            if not dry_run:
                self._atomic_json_write(
                    path,
                    data,
                )

            result["updated"].append(
                path.name
            )

        return result

    def _clean_empty_trips(
        self,
        *,
        dry_run: bool,
    ) -> list[str]:
        removed = []

        for path in self.trips_directory.glob(
            "trip_*.json"
        ):
            data = self._load_json(
                path
            )

            segments = data.get(
                "segments",
                [],
            )

            if (
                isinstance(
                    segments,
                    list,
                )
                and segments
            ):
                continue

            if not dry_run:
                path.unlink(
                    missing_ok=True
                )

            removed.append(
                path.name
            )

        return removed

    # ---------------------------------------------------------
    # Huérfanos
    # ---------------------------------------------------------

    def _clean_video_orphans(
        self,
        *,
        dry_run: bool,
    ) -> list[str]:
        removed = []

        for path in self.videos_directory.iterdir():
            if (
                not path.is_file()
                or path.suffix.lower()
                not in {
                    ".json",
                    ".jpg",
                }
            ):
                continue

            video_exists = any(
                path.with_suffix(
                    extension
                ).exists()
                for extension in VIDEO_EXTENSIONS
            )

            if video_exists:
                continue

            # Conservamos copias de prueba y backup.
            if (
                ".before-" in path.name
                or path.name.endswith(
                    ".tmp"
                )
            ):
                continue

            if not dry_run:
                path.unlink(
                    missing_ok=True
                )

            removed.append(
                path.name
            )

        return removed

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    @staticmethod
    def _load_json(
        path: Path,
    ) -> dict[str, Any]:
        if (
            not path.exists()
            or not path.is_file()
        ):
            return {}

        try:
            loaded = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

        return (
            loaded
            if isinstance(
                loaded,
                dict,
            )
            else {}
        )

    @staticmethod
    def _atomic_json_write(
        path: Path,
        data: dict[str, Any],
    ) -> None:
        temporary_path: Optional[
            Path
        ] = None

        serialized = json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ) + "\n"

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(
                    serialized
                )
                temporary.flush()
                os.fsync(
                    temporary.fileno()
                )

                temporary_path = Path(
                    temporary.name
                )

            os.replace(
                temporary_path,
                path,
            )

        except OSError:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink(
                    missing_ok=True
                )

            raise

    @staticmethod
    def _created_timestamp(
        path: Path,
        metadata: dict[str, Any],
    ) -> float:
        created = metadata.get(
            "created"
        )

        if created:
            try:
                return datetime.fromisoformat(
                    str(created)
                ).timestamp()
            except ValueError:
                pass

        return path.stat().st_mtime

    @staticmethod
    def _safe_int(
        value,
    ) -> int:
        try:
            return int(
                value or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _safe_float(
        value,
    ) -> float:
        try:
            return float(
                value or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _human_size(
        value: int,
    ) -> str:
        size = float(
            max(
                0,
                int(
                    value or 0
                ),
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
            if (
                size < 1024
                or unit == units[-1]
            ):
                if unit == "B":
                    return f"{int(size)} {unit}"

                return f"{size:.1f} {unit}"

            size /= 1024

        return f"{size:.1f} TB"


storage_manager = StorageManager()
