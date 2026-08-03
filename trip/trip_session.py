from __future__ import annotations

import json
import math
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class TripSession:
    """
    Representa un viaje completo formado por uno o más segmentos.

    El viaje se guarda en:

        trips/trip_YYYYMMDD_HHMMSS.json
    """

    VERSION = 1

    def __init__(
        self,
        trips_directory: Path,
        *,
        trip_type: str = "driving",
        started_at: Optional[datetime] = None,
    ) -> None:
        self.trips_directory = Path(
            trips_directory
        ).resolve()

        self.trips_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.started_at = (
            started_at
            if started_at is not None
            else datetime.now()
        )

        self.finished_at: Optional[datetime] = None

        self.trip_id = str(
            uuid.uuid4()
        )

        timestamp = self.started_at.strftime(
            "%Y%m%d_%H%M%S"
        )

        self.trip_name = (
            f"trip_{timestamp}"
        )

        self.path = (
            self.trips_directory
            / f"{self.trip_name}.json"
        )

        self.trip_type = self._normalize_type(
            trip_type
        )

        self.segments: list[dict[str, Any]] = []
        self.route: list[dict[str, float]] = []

        self.total_size_bytes = 0
        self.total_duration = 0.0
        self.max_speed = 0.0

        self._weighted_speed_sum = 0.0
        self._weighted_speed_duration = 0.0

    # ---------------------------------------------------------
    # Segmentos
    # ---------------------------------------------------------

    def add_segment(
        self,
        metadata: dict[str, Any],
    ) -> None:
        if not isinstance(
            metadata,
            dict,
        ):
            raise TypeError(
                "Los metadatos del segmento "
                "deben ser un diccionario."
            )

        filename = str(
            metadata.get(
                "filename",
                "",
            )
        ).strip()

        if not filename:
            raise ValueError(
                "El segmento no contiene filename."
            )

        if any(
            segment.get("filename") == filename
            for segment in self.segments
        ):
            return

        duration = self._safe_float(
            metadata.get(
                "duration",
                0,
            )
        )

        size_bytes = self._safe_int(
            metadata.get(
                "size_bytes",
                0,
            )
        )

        speed_data = metadata.get(
            "speed",
            {},
        )

        if not isinstance(
            speed_data,
            dict,
        ):
            speed_data = {}

        maximum_speed = self._safe_float(
            speed_data.get(
                "max",
                0,
            )
        )

        average_speed = self._safe_float(
            speed_data.get(
                "average",
                0,
            )
        )

        segment = {
            "filename": filename,
            "thumbnail": metadata.get(
                "thumbnail"
            ),
            "created": metadata.get(
                "created"
            ),
            "finished": metadata.get(
                "finished"
            ),
            "duration": round(
                duration,
                2,
            ),
            "size_bytes": size_bytes,
            "type": metadata.get(
                "type",
                "normal",
            ),
            "protected": bool(
                metadata.get(
                    "protected",
                    False,
                )
            ),
            "speed": {
                "max": round(
                    maximum_speed,
                    1,
                ),
                "average": round(
                    average_speed,
                    1,
                ),
            },
            "gps": metadata.get(
                "gps",
                {
                    "start": None,
                    "end": None,
                },
            ),
        }

        self.segments.append(
            segment
        )

        self.total_duration += duration
        self.total_size_bytes += size_bytes

        self.max_speed = max(
            self.max_speed,
            maximum_speed,
        )

        if duration > 0:
            self._weighted_speed_sum += (
                average_speed
                * duration
            )

            self._weighted_speed_duration += (
                duration
            )

        self._append_segment_route(
            metadata.get(
                "track",
                [],
            )
        )

        self.save()

    # ---------------------------------------------------------
    # Ruta
    # ---------------------------------------------------------

    def _append_segment_route(
        self,
        track,
    ) -> None:
        if not isinstance(
            track,
            list,
        ):
            return

        offset = 0.0

        if self.route:
            offset = self._safe_float(
                self.route[-1].get(
                    "time",
                    0,
                )
            )

        for raw_point in track:
            if not isinstance(
                raw_point,
                dict,
            ):
                continue

            latitude = self._optional_float(
                raw_point.get(
                    "lat"
                )
            )

            longitude = self._optional_float(
                raw_point.get(
                    "lon"
                )
            )

            if (
                latitude is None
                or longitude is None
            ):
                continue

            relative_time = self._safe_float(
                raw_point.get(
                    "time",
                    0,
                )
            )

            point = {
                "time": round(
                    offset + relative_time,
                    2,
                ),
                "lat": round(
                    latitude,
                    7,
                ),
                "lon": round(
                    longitude,
                    7,
                ),
                "speed": round(
                    max(
                        0.0,
                        self._safe_float(
                            raw_point.get(
                                "speed",
                                0,
                            )
                        ),
                    ),
                    1,
                ),
            }

            if self.route:
                previous = self.route[-1]

                if (
                    previous["lat"]
                    == point["lat"]
                    and previous["lon"]
                    == point["lon"]
                    and abs(
                        previous["time"]
                        - point["time"]
                    ) < 0.01
                ):
                    continue

            self.route.append(
                point
            )

    # ---------------------------------------------------------
    # Finalización
    # ---------------------------------------------------------

    def finalize(self) -> dict[str, Any]:
        if self.finished_at is None:
            self.finished_at = datetime.now()

        metadata = self.as_dict()

        self._atomic_write(
            metadata
        )

        return metadata

    def save(self) -> None:
        self._atomic_write(
            self.as_dict()
        )

    # ---------------------------------------------------------
    # Metadatos
    # ---------------------------------------------------------

    def as_dict(self) -> dict[str, Any]:
        average_speed = 0.0

        if self._weighted_speed_duration > 0:
            average_speed = (
                self._weighted_speed_sum
                / self._weighted_speed_duration
            )

        gps_start = None
        gps_end = None

        if self.route:
            gps_start = [
                self.route[0]["lat"],
                self.route[0]["lon"],
            ]

            gps_end = [
                self.route[-1]["lat"],
                self.route[-1]["lon"],
            ]

        return {
            "version": self.VERSION,
            "trip_id": self.trip_id,
            "trip_name": self.trip_name,
            "type": self.trip_type,
            "status": (
                "finished"
                if self.finished_at is not None
                else "open"
            ),
            "started": (
                self.started_at.isoformat()
            ),
            "finished": (
                self.finished_at.isoformat()
                if self.finished_at is not None
                else None
            ),
            "duration": round(
                self.total_duration,
                2,
            ),
            "size_bytes": int(
                self.total_size_bytes
            ),
            "segment_count": len(
                self.segments
            ),
            "segments": list(
                self.segments
            ),
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
            "gps": {
                "start": gps_start,
                "end": gps_end,
            },
            "route": list(
                self.route
            ),
            "route_points": len(
                self.route
            ),
        }

    # ---------------------------------------------------------
    # Escritura atómica
    # ---------------------------------------------------------

    def _atomic_write(
        self,
        data: dict[str, Any],
    ) -> None:
        serialized = json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ) + "\n"

        temporary_path: Optional[Path] = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.trips_directory,
                prefix=f".{self.path.name}.",
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
                self.path,
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
            "driving",
            "parking",
            "event",
        }:
            return "driving"

        return normalized

    @staticmethod
    def _safe_float(
        value,
    ) -> float:
        try:
            converted = float(
                value
            )

            if not math.isfinite(
                converted
            ):
                return 0.0

            return converted

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @classmethod
    def _safe_int(
        cls,
        value,
    ) -> int:
        return max(
            0,
            int(
                round(
                    cls._safe_float(
                        value
                    )
                )
            ),
        )

    @staticmethod
    def _optional_float(
        value,
    ) -> Optional[float]:
        try:
            converted = float(
                value
            )

            if not math.isfinite(
                converted
            ):
                return None

            return converted

        except (
            TypeError,
            ValueError,
        ):
            return None
