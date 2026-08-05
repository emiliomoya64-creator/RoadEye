from __future__ import annotations

import logging
from threading import Event, Thread
from typing import Optional

import requests

from core.config_manager import config
from core.system_state import system_state


logger = logging.getLogger(__name__)


class MapService:
    """
    Servicio cartográfico de RoadEye.

    Obtiene mediante OpenStreetMap:

    - nombre de la vía;
    - ciudad;
    - límite de velocidad;
    - tipo de carretera;
    - carriles;
    - sentido único.

    El servicio solo consulta cuando existe posición GPS válida.
    """

    NOMINATIM_URL = (
        "https://nominatim.openstreetmap.org/reverse"
    )

    OVERPASS_URL = (
        "https://overpass-api.de/api/interpreter"
    )

    USER_AGENT = "RoadEye"

    def __init__(self) -> None:
        self.enabled = bool(
            config.get(
                "gps.map_service",
                True,
            )
        )

        self.last_lat: Optional[float] = None
        self.last_lon: Optional[float] = None

        self._thread: Optional[Thread] = None
        self._stop_event = Event()

        self._session = requests.Session()

        self._session.headers.update(
            {
                "User-Agent": self.USER_AGENT,
            }
        )

    # ---------------------------------------------------------
    # Estado
    # ---------------------------------------------------------

    @property
    def running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )

    # ---------------------------------------------------------
    # Inicio y parada
    # ---------------------------------------------------------

    def start(self) -> None:
        if not self.enabled:
            logger.info(
                "MapService desactivado en config.json"
            )
            return

        if self.running:
            return

        self._stop_event.clear()

        self._thread = Thread(
            target=self._loop,
            name="roadeye-map-service",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "MapService iniciado"
        )

        print(
            "🗺 Map Service iniciado"
        )

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=1.5
            )

            if self._thread.is_alive():
                logger.warning(
                    "MapService no terminó dentro del plazo."
                )

        self._thread = None

        try:
            self._session.close()
        except Exception:
            logger.debug(
                "No se pudo cerrar la sesión de mapas",
                exc_info=True,
            )

        logger.info(
            "MapService detenido"
        )

    # ---------------------------------------------------------
    # Geocodificación inversa
    # ---------------------------------------------------------

    def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
    ) -> None:
        if self._stop_event.is_set():
            return

        try:
            response = self._session.get(
                self.NOMINATIM_URL,
                params={
                    "format": "jsonv2",
                    "lat": latitude,
                    "lon": longitude,
                    "zoom": 18,
                    "addressdetails": 1,
                },
                timeout=(1.5, 2.0),
            )

            if self._stop_event.is_set():
                return

            if response.status_code != 200:
                logger.warning(
                    "Nominatim respondió con HTTP %d",
                    response.status_code,
                )
                return

            data = response.json()
            address = data.get(
                "address",
                {},
            )

            road = (
                address.get("road")
                or address.get("pedestrian")
                or address.get("residential")
                or address.get("suburb")
                or "---"
            )

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or ""
            )

            system_state.set(
                "road",
                road,
            )

            system_state.set(
                "city",
                city,
            )

            print(
                f"🛣 {road}"
            )

        except requests.RequestException:
            logger.debug(
                "No se pudo consultar Nominatim",
                exc_info=True,
            )

        except Exception:
            logger.exception(
                "Error procesando la respuesta de Nominatim"
            )

    # ---------------------------------------------------------
    # Información de carretera
    # ---------------------------------------------------------

    def get_road_info(
        self,
        latitude: float,
        longitude: float,
    ) -> None:
        if self._stop_event.is_set():
            return

        query = f"""
[out:json][timeout:10];

way(around:20,{latitude},{longitude})["highway"];

out tags;
"""

        try:
            response = self._session.post(
                self.OVERPASS_URL,
                data=query,
                timeout=(1.5, 3.0),
            )

            if self._stop_event.is_set():
                return

            if response.status_code != 200:
                logger.warning(
                    "Overpass respondió con HTTP %d",
                    response.status_code,
                )
                return

            data = response.json()
            elements = data.get(
                "elements",
                [],
            )

            if not elements:
                return

            tags = elements[0].get(
                "tags",
                {},
            )

            speed_limit = self._parse_speed(
                tags.get(
                    "maxspeed",
                    "0",
                )
            )

            lanes = tags.get(
                "lanes",
                "?",
            )

            highway = tags.get(
                "highway",
                "?",
            )

            oneway = tags.get(
                "oneway",
                "no",
            )

            road_types = {
                "motorway": "Autovía",
                "trunk": "Vía rápida",
                "primary": "Carretera principal",
                "secondary": "Carretera secundaria",
                "tertiary": "Carretera local",
                "residential": "Calle urbana",
                "living_street": "Zona residencial",
                "service": "Vía de servicio",
                "unclassified": "Carretera",
                "pedestrian": "Zona peatonal",
                "footway": "Vía peatonal",
            }

            road_type = road_types.get(
                highway,
                str(highway)
                .replace("_", " ")
                .capitalize(),
            )

            system_state.set(
                "speed_limit",
                speed_limit,
            )

            system_state.set(
                "lanes",
                lanes,
            )

            system_state.set(
                "road_type",
                road_type,
            )

            system_state.set(
                "oneway",
                oneway,
            )

            print(
                f"🚦 {speed_limit} km/h | "
                f"{road_type} | "
                f"{lanes} carriles"
            )

        except requests.RequestException:
            logger.debug(
                "No se pudo consultar Overpass",
                exc_info=True,
            )

        except Exception:
            logger.exception(
                "Error procesando la respuesta de Overpass"
            )

    # ---------------------------------------------------------
    # Bucle principal
    # ---------------------------------------------------------

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            if not system_state.get(
                "gps_fix"
            ):
                self._stop_event.wait(
                    2.0
                )
                continue

            latitude = float(
                system_state.get(
                    "latitude"
                )
                or 0
            )

            longitude = float(
                system_state.get(
                    "longitude"
                )
                or 0
            )

            if (
                latitude == 0
                or longitude == 0
            ):
                self._stop_event.wait(
                    2.0
                )
                continue

            if (
                self.last_lat is not None
                and self.last_lon is not None
            ):
                movement_is_small = (
                    abs(
                        latitude
                        - self.last_lat
                    )
                    < 0.0002
                    and
                    abs(
                        longitude
                        - self.last_lon
                    )
                    < 0.0002
                )

                if movement_is_small:
                    self._stop_event.wait(
                        5.0
                    )
                    continue

            self.last_lat = latitude
            self.last_lon = longitude

            self.reverse_geocode(
                latitude,
                longitude,
            )

            if self._stop_event.is_set():
                break

            self.get_road_info(
                latitude,
                longitude,
            )

            self._stop_event.wait(
                5.0
            )

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    @staticmethod
    def _parse_speed(
        value,
    ) -> int:
        try:
            first_value = str(
                value
            ).split()[0]

            return max(
                0,
                int(first_value),
            )

        except (
            IndexError,
            TypeError,
            ValueError,
        ):
            return 0