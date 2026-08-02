from __future__ import annotations

import logging
from threading import Event, Thread
from typing import Optional

import pynmea2
import serial

from core.config_manager import config
from core.system_state import system_state


logger = logging.getLogger(__name__)


class GPSService:
    """
    Servicio GPS de RoadEye.

    Lee sentencias NMEA desde el puerto serie y actualiza:

    - posición;
    - velocidad;
    - rumbo;
    - altitud;
    - satélites;
    - estado de fijación GPS.

    Configuración utilizada:

        gps.enabled
        gps.port
        gps.baudrate
    """

    def __init__(self) -> None:
        self.enabled = bool(
            config.get(
                "gps.enabled",
                True,
            )
        )

        self.port = str(
            config.get(
                "gps.port",
                "/dev/serial0",
            )
        ).strip()

        self.baudrate = self._positive_int(
            config.get(
                "gps.baudrate",
                9600,
            ),
            default=9600,
        )

        self.serial_connection: Optional[
            serial.Serial
        ] = None

        self._thread: Optional[Thread] = None
        self._stop_event = Event()

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
                "GPSService desactivado en config.json"
            )
            return

        if self.running:
            return

        if not self.port:
            raise ValueError(
                "gps.port no puede estar vacío"
            )

        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
            )

        except Exception as exc:
            self.serial_connection = None

            raise RuntimeError(
                f"No se pudo abrir el GPS en {self.port}: {exc}"
            ) from exc

        self._stop_event.clear()

        self._thread = Thread(
            target=self._loop,
            name="roadeye-gps",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "GPS conectado: %s a %d baudios",
            self.port,
            self.baudrate,
        )

        print(
            f"🛰 GPS conectado ({self.port})"
        )

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=2.0
            )

        self._thread = None

        if self.serial_connection is not None:
            try:
                self.serial_connection.close()
            except Exception:
                logger.exception(
                    "No se pudo cerrar el puerto GPS"
                )

        self.serial_connection = None

        system_state.set(
            "gps_fix",
            False,
        )

        system_state.set(
            "speed",
            0,
        )

        logger.info(
            "GPSService detenido"
        )

    # ---------------------------------------------------------
    # Lectura GPS
    # ---------------------------------------------------------

    def _loop(self) -> None:
        print("🛰 Esperando datos GPS...")

        while not self._stop_event.is_set():
            connection = self.serial_connection

            if connection is None:
                break

            try:
                raw_line = connection.readline()

                line = raw_line.decode(
                    "ascii",
                    errors="ignore",
                ).strip()

                if not line.startswith("$"):
                    continue

                message = pynmea2.parse(
                    line
                )

                self._process_message(
                    message
                )

            except pynmea2.ParseError:
                logger.debug(
                    "Sentencia NMEA no válida",
                    exc_info=True,
                )

            except serial.SerialException:
                logger.exception(
                    "Se perdió la conexión con el GPS"
                )
                break

            except Exception:
                logger.debug(
                    "Error procesando datos GPS",
                    exc_info=True,
                )

            self._stop_event.wait(
                0.01
            )

    def _process_message(
        self,
        message,
    ) -> None:
        if isinstance(
            message,
            pynmea2.types.talker.RMC,
        ):
            self._process_rmc(
                message
            )

        elif isinstance(
            message,
            pynmea2.types.talker.GGA,
        ):
            self._process_gga(
                message
            )

    # ---------------------------------------------------------
    # Sentencia RMC
    # ---------------------------------------------------------

    @staticmethod
    def _process_rmc(
        message,
    ) -> None:
        if message.status != "A":
            system_state.set(
                "gps_fix",
                False,
            )

            system_state.set(
                "speed",
                0,
            )

            return

        latitude = float(
            message.latitude or 0
        )

        longitude = float(
            message.longitude or 0
        )

        speed_kmh = (
            float(
                message.spd_over_grnd or 0
            )
            * 1.852
        )

        course = float(
            message.true_course or 0
        )

        directions = [
            "N",
            "NE",
            "E",
            "SE",
            "S",
            "SW",
            "W",
            "NW",
        ]

        direction_index = (
            int(
                (course + 22.5) / 45
            )
            % 8
        )

        system_state.set(
            "gps_fix",
            True,
        )

        system_state.set(
            "latitude",
            latitude,
        )

        system_state.set(
            "longitude",
            longitude,
        )

        system_state.set(
            "speed",
            speed_kmh,
        )

        system_state.set(
            "heading",
            directions[
                direction_index
            ],
        )

    # ---------------------------------------------------------
    # Sentencia GGA
    # ---------------------------------------------------------

    @staticmethod
    def _process_gga(
        message,
    ) -> None:
        satellites = int(
            message.num_sats or 0
        )

        system_state.set(
            "satellites",
            satellites,
        )

        if message.altitude not in {
            None,
            "",
        }:
            try:
                altitude = float(
                    message.altitude
                )

                system_state.set(
                    "altitude",
                    altitude,
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

    # ---------------------------------------------------------
    # Validación
    # ---------------------------------------------------------

    @staticmethod
    def _positive_int(
        value,
        default: int,
    ) -> int:
        try:
            converted = int(value)

            if converted <= 0:
                raise ValueError

            return converted

        except (
            TypeError,
            ValueError,
        ):
            logger.warning(
                "Baudrate GPS inválido '%s'. "
                "Se usará %d",
                value,
                default,
            )

            return default