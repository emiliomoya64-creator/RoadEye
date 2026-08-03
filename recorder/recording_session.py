from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import cv2


logger = logging.getLogger(__name__)


class RecordingSession:
    """
    Metadatos asociados a un segmento de vídeo RoadEye.

    Archivos producidos:

        segmento.mp4
        segmento.json
        segmento.jpg
    """

    METADATA_VERSION = 1

    def __init__(
        self,
        video_path: Path,
        *,
        recording_type: str = "normal",
        protected: bool = False,
    ) -> None:
        self.video_path = Path(
            video_path
        ).resolve()

        self.metadata_path = (
            self.video_path.with_suffix(
                ".json"
            )
        )

        self.thumbnail_path = (
            self.video_path.with_suffix(
                ".jpg"
            )
        )

        self.recording_type = (
            self._normalize_type(
                recording_type
            )
        )

        self.protected = bool(
            protected
        )

        self.protection_reasons: list[str] = []

        self.started_at = datetime.now()
        self.finished_at: Optional[
            datetime
        ] = None

        self.start_latitude: Optional[
            float
        ] = None

        self.start_longitude: Optional[
            float
        ] = None

        self.end_latitude: Optional[
            float
        ] = None

        self.end_longitude: Optional[
            float
        ] = None

        self.speed_samples = 0
        self.speed_sum = 0.0
        self.max_speed = 0.0

        # Recorrido GPS: un punto por segundo aproximadamente.
        self.track: list[dict[str, float]] = []
        self._last_track_sample_at: Optional[float] = None
        self._track_interval_seconds = 1.0

        self._thumbnail_frame = None

    def protect(
        self,
        reason: str,
    ) -> None:
        """
        Protege el segmento y conserva el motivo.
        """

        normalized_reason = str(
            reason
        ).strip().lower()

        if not normalized_reason:
            normalized_reason = "event"

        self.protected = True

        if normalized_reason not in self.protection_reasons:
            self.protection_reasons.append(
                normalized_reason
            )

    # ---------------------------------------------------------
    # Actualización durante la grabación
    # ---------------------------------------------------------

    def update(
        self,
        frame,
        *,
        latitude,
        longitude,
        gps_fix,
        speed,
    ) -> None:
        """
        Actualiza estadísticas de la sesión con un nuevo frame.
        """

        if (
            self._thumbnail_frame is None
            and frame is not None
        ):
            self._thumbnail_frame = (
                frame.copy()
            )

        speed_value = self._safe_float(
            speed,
            default=0.0,
        )

        speed_value = max(
            0.0,
            speed_value,
        )

        self.speed_samples += 1
        self.speed_sum += speed_value
        self.max_speed = max(
            self.max_speed,
            speed_value,
        )

        if not gps_fix:
            return

        latitude_value = self._optional_float(
            latitude
        )

        longitude_value = self._optional_float(
            longitude
        )

        if (
            latitude_value is None
            or longitude_value is None
        ):
            return

        if (
            self.start_latitude is None
            or self.start_longitude is None
        ):
            self.start_latitude = (
                latitude_value
            )

            self.start_longitude = (
                longitude_value
            )

        self.end_latitude = latitude_value
        self.end_longitude = longitude_value

        self._append_track_point(
            latitude=latitude_value,
            longitude=longitude_value,
            speed=speed_value,
        )

    # ---------------------------------------------------------
    # Finalización
    # ---------------------------------------------------------

    def finalize(self) -> dict[str, Any]:
        """
        Cierra la sesión, genera miniatura y guarda metadatos.
        """

        if self.finished_at is None:
            self.finished_at = datetime.now()

        self._create_thumbnail()

        metadata = self.as_dict()

        self._atomic_json_write(
            metadata
        )

        logger.info(
            "Sesión multimedia finalizada: %s",
            self.video_path.name,
        )

        return metadata

    def as_dict(self) -> dict[str, Any]:
        finished_at = (
            self.finished_at
            or datetime.now()
        )

        duration = max(
            0.0,
            (
                finished_at
                - self.started_at
            ).total_seconds(),
        )

        size_bytes = 0

        if self.video_path.exists():
            try:
                size_bytes = (
                    self.video_path.stat().st_size
                )
            except OSError:
                size_bytes = 0

        average_speed = 0.0

        if self.speed_samples > 0:
            average_speed = (
                self.speed_sum
                / self.speed_samples
            )

        return {
            "version": (
                self.METADATA_VERSION
            ),
            "filename": (
                self.video_path.name
            ),
            "thumbnail": (
                self.thumbnail_path.name
                if self.thumbnail_path.exists()
                else None
            ),
            "created": (
                self.started_at.isoformat()
            ),
            "finished": (
                finished_at.isoformat()
            ),
            "duration": round(
                duration,
                2,
            ),
            "size_bytes": int(
                size_bytes
            ),
            "type": (
                self.recording_type
            ),
            "protected": (
                self.protected
            ),
            "protection_reasons": list(
                self.protection_reasons
            ),
            "gps": {
                "start": self._coordinate_pair(
                    self.start_latitude,
                    self.start_longitude,
                ),
                "end": self._coordinate_pair(
                    self.end_latitude,
                    self.end_longitude,
                ),
            },
            "speed": {
                "max": round(
                    self.max_speed,
                    1,
                ),
                "average": round(
                    average_speed,
                    1,
                ),
            },
            "track": list(
                self.track
            ),
            "track_points": len(
                self.track
            ),
        }

    def _append_track_point(
        self,
        *,
        latitude: float,
        longitude: float,
        speed: float,
    ) -> None:
        """
        Añade como máximo un punto GPS por segundo.

        También evita guardar puntos idénticos consecutivos.
        """

        now_monotonic = time.monotonic()

        if (
            self._last_track_sample_at is not None
            and (
                now_monotonic
                - self._last_track_sample_at
            ) < self._track_interval_seconds
        ):
            return

        elapsed = max(
            0.0,
            (
                datetime.now()
                - self.started_at
            ).total_seconds(),
        )

        point = {
            "time": round(
                elapsed,
                2,
            ),
            "lat": round(
                float(latitude),
                7,
            ),
            "lon": round(
                float(longitude),
                7,
            ),
            "speed": round(
                max(
                    0.0,
                    float(speed),
                ),
                1,
            ),
        }

        if self.track:
            previous = self.track[-1]

            same_position = (
                previous["lat"] == point["lat"]
                and previous["lon"] == point["lon"]
            )

            # Si permanece inmóvil, se conserva como máximo
            # un punto cada cinco segundos.
            if (
                same_position
                and (
                    point["time"]
                    - previous["time"]
                ) < 5.0
            ):
                return

        self.track.append(
            point
        )

        self._last_track_sample_at = (
            now_monotonic
        )

    # ---------------------------------------------------------
    # Miniatura
    # ---------------------------------------------------------

    def _create_thumbnail(self) -> None:
        frame = self._thumbnail_frame

        if frame is None:
            frame = self._read_video_frame()

        if frame is None:
            logger.warning(
                "No se pudo crear miniatura para %s",
                self.video_path.name,
            )
            return

        height, width = frame.shape[:2]

        target_width = min(
            480,
            width,
        )

        if width <= 0 or height <= 0:
            return

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

        success = cv2.imwrite(
            str(
                self.thumbnail_path
            ),
            thumbnail,
            [
                int(
                    cv2.IMWRITE_JPEG_QUALITY
                ),
                82,
            ],
        )

        if not success:
            logger.warning(
                "OpenCV no pudo guardar %s",
                self.thumbnail_path,
            )

    def _read_video_frame(self):
        if not self.video_path.exists():
            return None

        capture = cv2.VideoCapture(
            str(
                self.video_path
            )
        )

        try:
            success, frame = (
                capture.read()
            )

            if not success:
                return None

            return frame

        finally:
            capture.release()

    # ---------------------------------------------------------
    # Escritura segura
    # ---------------------------------------------------------

    def _atomic_json_write(
        self,
        metadata: dict[str, Any],
    ) -> None:
        self.metadata_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = json.dumps(
            metadata,
            indent=4,
            ensure_ascii=False,
        ) + "\n"

        temporary_path: Optional[
            Path
        ] = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.metadata_path.parent,
                prefix=(
                    f".{self.metadata_path.name}."
                ),
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_file.write(
                    serialized
                )

                temporary_file.flush()
                os.fsync(
                    temporary_file.fileno()
                )

                temporary_path = Path(
                    temporary_file.name
                )

            os.replace(
                temporary_path,
                self.metadata_path,
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

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_type(
        value,
    ) -> str:
        normalized = str(
            value
        ).strip().lower()

        if normalized not in {
            "normal",
            "event",
            "parking",
        }:
            return "normal"

        return normalized

    @staticmethod
    def _coordinate_pair(
        latitude,
        longitude,
    ):
        if (
            latitude is None
            or longitude is None
        ):
            return None

        return [
            round(
                float(latitude),
                7,
            ),
            round(
                float(longitude),
                7,
            ),
        ]

    @staticmethod
    def _safe_float(
        value,
        *,
        default,
    ) -> float:
        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return float(
                default
            )

    @staticmethod
    def _optional_float(
        value,
    ) -> Optional[float]:
        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None
