from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any, Optional

from core.config_manager import PROJECT_DIR, config
from trip.trip_session import TripSession


logger = logging.getLogger(__name__)


class TripManager:
    """
    Gestiona el viaje activo de RoadEye.

    El RecorderService entrega los metadatos de cada segmento.
    TripManager decide a qué viaje pertenecen.
    """

    def __init__(self) -> None:
        configured_directory = str(
            config.get(
                "trips.folder",
                "trips",
            )
        ).strip()

        directory = Path(
            configured_directory or "trips"
        )

        if not directory.is_absolute():
            directory = (
                PROJECT_DIR
                / directory
            )

        self.trips_directory = (
            directory.resolve()
        )

        self.trips_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = RLock()

        self._active_trip: Optional[
            TripSession
        ] = None

    # ---------------------------------------------------------
    # Estado
    # ---------------------------------------------------------

    @property
    def active(self) -> bool:
        with self._lock:
            return (
                self._active_trip is not None
            )

    @property
    def active_trip_id(
        self,
    ) -> Optional[str]:
        with self._lock:
            if self._active_trip is None:
                return None

            return self._active_trip.trip_id

    # ---------------------------------------------------------
    # Gestión
    # ---------------------------------------------------------

    def add_segment(
        self,
        metadata: dict[str, Any],
        metadata_path: Path,
    ) -> dict[str, Any]:
        """
        Añade un segmento al viaje activo.

        También escribe trip_id y trip_name en el JSON
        individual del segmento.
        """

        with self._lock:
            segment_type = str(
                metadata.get(
                    "type",
                    "normal",
                )
            ).strip().lower()

            trip_type = (
                "parking"
                if segment_type == "parking"
                else "driving"
            )

            if self._active_trip is None:
                self._active_trip = (
                    TripSession(
                        self.trips_directory,
                        trip_type=trip_type,
                    )
                )

                logger.info(
                    "Nuevo viaje iniciado: %s",
                    self._active_trip.trip_name,
                )

            elif (
                self._active_trip.trip_type
                != trip_type
            ):
                self._close_trip_locked()

                self._active_trip = (
                    TripSession(
                        self.trips_directory,
                        trip_type=trip_type,
                    )
                )

            trip = self._active_trip

            trip.add_segment(
                metadata
            )

            enriched_metadata = dict(
                metadata
            )

            enriched_metadata[
                "trip_id"
            ] = trip.trip_id

            enriched_metadata[
                "trip_name"
            ] = trip.trip_name

            self._atomic_json_write(
                Path(
                    metadata_path
                ),
                enriched_metadata,
            )

            logger.info(
                "Segmento %s añadido a %s",
                metadata.get(
                    "filename"
                ),
                trip.trip_name,
            )

            return {
                "trip_id": trip.trip_id,
                "trip_name": trip.trip_name,
                "trip_path": str(
                    trip.path
                ),
            }

    def close_trip(
        self,
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            return self._close_trip_locked()

    def _close_trip_locked(
        self,
    ) -> Optional[dict[str, Any]]:
        if self._active_trip is None:
            return None

        trip = self._active_trip
        self._active_trip = None

        metadata = trip.finalize()

        logger.info(
            "Viaje finalizado: %s · %d segmentos",
            trip.trip_name,
            metadata["segment_count"],
        )

        return metadata

    # ---------------------------------------------------------
    # Escritura del JSON individual
    # ---------------------------------------------------------

    @staticmethod
    def _atomic_json_write(
        path: Path,
        data: dict[str, Any],
    ) -> None:
        path = Path(
            path
        ).resolve()

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
                dir=path.parent,
                prefix=f".{path.name}.",
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


trip_manager = TripManager()
