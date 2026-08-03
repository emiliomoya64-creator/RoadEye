from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
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
    # Apertura explícita
    # ---------------------------------------------------------

    def ensure_trip(
        self,
        *,
        trip_type: str = "driving",
        started_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Garantiza que exista un viaje activo.

        Se utiliza al comenzar la grabación para poder registrar
        eventos desde el primer segundo.
        """

        with self._lock:
            normalized_type = str(
                trip_type
            ).strip().lower()

            if normalized_type not in {
                "driving",
                "parking",
                "event",
            }:
                normalized_type = "driving"

            if self._active_trip is None:
                self._active_trip = TripSession(
                    self.trips_directory,
                    trip_type=normalized_type,
                    started_at=(
                        started_at
                        if started_at is not None
                        else datetime.now()
                    ),
                )

                self._active_trip.save()

                logger.info(
                    "Viaje abierto: %s",
                    self._active_trip.trip_name,
                )

            return {
                "trip_id": (
                    self._active_trip.trip_id
                ),
                "trip_name": (
                    self._active_trip.trip_name
                ),
                "trip_path": str(
                    self._active_trip.path
                ),
            }

    def add_event(
        self,
        *,
        event_type: str,
        label: str,
        source: str = "system",
        severity: str = "info",
        protected: bool = False,
        created: Optional[datetime] = None,
        segment: Optional[str] = None,
        segment_time: float = 0.0,
        latitude=None,
        longitude=None,
        speed=0.0,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Añade un evento al viaje activo.
        """

        with self._lock:
            if self._active_trip is None:
                self.ensure_trip(
                    trip_type="driving",
                    started_at=(
                        created
                        if created is not None
                        else datetime.now()
                    ),
                )

            trip = self._active_trip

            event_created = (
                created
                if created is not None
                else datetime.now()
            )

            trip_time = max(
                0.0,
                (
                    event_created
                    - trip.started_at
                ).total_seconds(),
            )

            gps = None

            try:
                if (
                    latitude is not None
                    and longitude is not None
                ):
                    gps = [
                        round(
                            float(latitude),
                            7,
                        ),
                        round(
                            float(longitude),
                            7,
                        ),
                    ]
            except (
                TypeError,
                ValueError,
            ):
                gps = None

            event = {
                "event_id": str(
                    uuid.uuid4()
                ),
                "type": str(
                    event_type
                ).strip().lower(),
                "source": str(
                    source
                ).strip().lower(),
                "created": (
                    event_created.isoformat()
                ),
                "trip_time": trip_time,
                "segment": segment,
                "segment_time": segment_time,
                "label": str(
                    label
                ).strip(),
                "severity": str(
                    severity
                ).strip().lower(),
                "protected": bool(
                    protected
                ),
                "gps": gps,
                "speed": speed,
                "data": (
                    data
                    if isinstance(
                        data,
                        dict,
                    )
                    else {}
                ),
            }

            stored_event = trip.add_event(
                event
            )

            logger.info(
                "Evento añadido a %s: %s",
                trip.trip_name,
                stored_event["type"],
            )

            return {
                "trip_id": trip.trip_id,
                "trip_name": trip.trip_name,
                "event": stored_event,
            }

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

            segment_started_at = (
                self._parse_datetime(
                    metadata.get(
                        "created"
                    )
                )
            )

            if self._active_trip is None:
                self._active_trip = (
                    TripSession(
                        self.trips_directory,
                        trip_type=trip_type,
                        started_at=segment_started_at,
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
                        started_at=segment_started_at,
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

    @staticmethod
    def _parse_datetime(
        value,
    ) -> Optional[datetime]:
        if value is None:
            return None

        try:
            return datetime.fromisoformat(
                str(value)
            )

        except ValueError:
            return None

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
