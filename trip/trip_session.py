from __future__ import annotations

import json
import math
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.config_manager import config


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

        self.moving_speed_threshold_kmh = max(
            0.0,
            self._safe_float(
                config.get(
                    "trips.moving_speed_threshold_kmh",
                    3.0,
                )
            ),
        )

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

        route_statistics = (
            self._calculate_route_statistics()
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
                "average_moving": round(
                    route_statistics[
                        "average_moving_speed_kmh"
                    ],
                    1,
                ),
            },
            "distance": {
                "meters": round(
                    route_statistics[
                        "distance_meters"
                    ],
                    1,
                ),
                "kilometers": round(
                    route_statistics[
                        "distance_kilometers"
                    ],
                    3,
                ),
            },
            "motion": {
                "threshold_kmh": (
                    self.moving_speed_threshold_kmh
                ),
                "moving_seconds": round(
                    route_statistics[
                        "moving_seconds"
                    ],
                    2,
                ),
                "stopped_seconds": round(
                    route_statistics[
                        "stopped_seconds"
                    ],
                    2,
                ),
                "moving_percent": round(
                    route_statistics[
                        "moving_percent"
                    ],
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
    # Estadísticas del recorrido
    # ---------------------------------------------------------

    def _calculate_route_statistics(
        self,
    ) -> dict[str, float]:
        distance_meters = 0.0
        moving_seconds = 0.0
        stopped_seconds = 0.0

        moving_speed_sum = 0.0
        moving_speed_duration = 0.0

        if len(self.route) < 2:
            return {
                "distance_meters": 0.0,
                "distance_kilometers": 0.0,
                "moving_seconds": 0.0,
                "stopped_seconds": max(
                    0.0,
                    self.total_duration,
                ),
                "moving_percent": 0.0,
                "average_moving_speed_kmh": 0.0,
            }

        for previous, current in zip(
            self.route,
            self.route[1:],
        ):
            delta_seconds = max(
                0.0,
                self._safe_float(
                    current.get(
                        "time",
                        0,
                    )
                )
                - self._safe_float(
                    previous.get(
                        "time",
                        0,
                    )
                ),
            )

            if delta_seconds <= 0:
                continue

            segment_distance = (
                self._haversine_meters(
                    previous.get(
                        "lat"
                    ),
                    previous.get(
                        "lon"
                    ),
                    current.get(
                        "lat"
                    ),
                    current.get(
                        "lon"
                    ),
                )
            )

            # Filtra saltos GPS claramente imposibles.
            maximum_reasonable_distance = (
                max(
                    50.0,
                    delta_seconds
                    * 80.0,
                )
            )

            if (
                0.0
                <= segment_distance
                <= maximum_reasonable_distance
            ):
                distance_meters += (
                    segment_distance
                )

            current_speed = max(
                0.0,
                self._safe_float(
                    current.get(
                        "speed",
                        0,
                    )
                ),
            )

            if (
                current_speed
                >= self.moving_speed_threshold_kmh
            ):
                moving_seconds += (
                    delta_seconds
                )

                moving_speed_sum += (
                    current_speed
                    * delta_seconds
                )

                moving_speed_duration += (
                    delta_seconds
                )

            else:
                stopped_seconds += (
                    delta_seconds
                )

        tracked_seconds = (
            moving_seconds
            + stopped_seconds
        )

        if self.total_duration > tracked_seconds:
            stopped_seconds += (
                self.total_duration
                - tracked_seconds
            )

        total_motion_seconds = (
            moving_seconds
            + stopped_seconds
        )

        moving_percent = 0.0

        if total_motion_seconds > 0:
            moving_percent = (
                moving_seconds
                / total_motion_seconds
                * 100.0
            )

        average_moving_speed = 0.0

        if moving_speed_duration > 0:
            average_moving_speed = (
                moving_speed_sum
                / moving_speed_duration
            )

        return {
            "distance_meters": (
                distance_meters
            ),
            "distance_kilometers": (
                distance_meters
                / 1000.0
            ),
            "moving_seconds": (
                moving_seconds
            ),
            "stopped_seconds": (
                stopped_seconds
            ),
            "moving_percent": (
                moving_percent
            ),
            "average_moving_speed_kmh": (
                average_moving_speed
            ),
        }

    @classmethod
    def _haversine_meters(
        cls,
        latitude_1,
        longitude_1,
        latitude_2,
        longitude_2,
    ) -> float:
        lat_1 = cls._optional_float(
            latitude_1
        )

        lon_1 = cls._optional_float(
            longitude_1
        )

        lat_2 = cls._optional_float(
            latitude_2
        )

        lon_2 = cls._optional_float(
            longitude_2
        )

        if None in {
            lat_1,
            lon_1,
            lat_2,
            lon_2,
        }:
            return 0.0

        earth_radius_meters = (
            6371008.8
        )

        latitude_delta = math.radians(
            lat_2 - lat_1
        )

        longitude_delta = math.radians(
            lon_2 - lon_1
        )

        latitude_1_radians = math.radians(
            lat_1
        )

        latitude_2_radians = math.radians(
            lat_2
        )

        haversine_value = (
            math.sin(
                latitude_delta / 2.0
            ) ** 2
            + math.cos(
                latitude_1_radians
            )
            * math.cos(
                latitude_2_radians
            )
            * math.sin(
                longitude_delta / 2.0
            ) ** 2
        )

        central_angle = (
            2.0
            * math.atan2(
                math.sqrt(
                    haversine_value
                ),
                math.sqrt(
                    max(
                        0.0,
                        1.0
                        - haversine_value,
                    )
                ),
            )
        )

        return (
            earth_radius_meters
            * central_angle
        )

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
