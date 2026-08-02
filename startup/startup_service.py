from __future__ import annotations

import logging
from threading import RLock

from core.config_manager import config
from startup.boot_manager import BootManager


logger = logging.getLogger(__name__)


class StartupService:
    """
    Servicio encargado de ejecutar la secuencia visual de arranque.

    El servicio:

    - muestra el splash de RoadEye;
    - ejecuta las comprobaciones rápidas;
    - publica la pantalla en DisplayBuffer;
    - bloquea el arranque del resto de servicios hasta terminar;
    - permite continuar si no existe ningún error crítico.

    No controla directamente HDMI, cámara ni RenderService.
    """

    def __init__(self) -> None:
        self.enabled = bool(
            config.get(
                "startup.enabled",
                True,
            )
        )

        self.width = self._positive_int(
            config.get(
                "display.hdmi.width",
                1280,
            ),
            default=1280,
        )

        self.height = self._positive_int(
            config.get(
                "display.hdmi.height",
                720,
            ),
            default=720,
        )

        self.splash_seconds = self._non_negative_float(
            config.get(
                "startup.splash_seconds",
                1.2,
            ),
            default=1.2,
        )

        self.ready_seconds = self._non_negative_float(
            config.get(
                "startup.ready_seconds",
                1.8,
            ),
            default=1.8,
        )

        self.check_delay_seconds = self._non_negative_float(
            config.get(
                "startup.check_delay_seconds",
                0.30,
            ),
            default=0.30,
        )

        self.publish_fps = self._positive_float(
            config.get(
                "startup.publish_fps",
                15,
            ),
            default=15.0,
        )

        self.boot_manager = BootManager(
            width=self.width,
            height=self.height,
            splash_seconds=self.splash_seconds,
            ready_seconds=self.ready_seconds,
            check_delay_seconds=self.check_delay_seconds,
            publish_fps=self.publish_fps,
        )

        self._running = False
        self._completed = False
        self._successful = False
        self._lock = RLock()

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def completed(self) -> bool:
        with self._lock:
            return self._completed

    @property
    def successful(self) -> bool:
        with self._lock:
            return self._successful

    def start(self) -> None:
        """
        Ejecuta la secuencia de arranque de forma bloqueante.

        ServiceManager no continuará con la cámara y el resto de
        servicios hasta que BootManager haya terminado.
        """

        if not self.enabled:
            logger.info(
                "StartupService desactivado en config.json"
            )

            with self._lock:
                self._completed = True
                self._successful = True

            return

        with self._lock:
            if self._running:
                return

            self._running = True
            self._completed = False
            self._successful = False

        logger.info(
            "Iniciando pantalla de arranque RoadEye"
        )

        try:
            result = self.boot_manager.run_blocking()

            with self._lock:
                self._successful = bool(
                    result
                )
                self._completed = True

            if not result:
                error = (
                    self.boot_manager.last_error
                    or "Error crítico desconocido"
                )

                raise RuntimeError(
                    "BootManager no permite continuar: "
                    f"{error}"
                )

            logger.info(
                "Pantalla de arranque terminada correctamente"
            )

        finally:
            with self._lock:
                self._running = False

    def stop(self) -> None:
        """
        Detiene BootManager si todavía estuviera activo.
        """

        self.boot_manager.stop()

        with self._lock:
            self._running = False

        logger.info(
            "StartupService detenido"
        )

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "running": self.running,
            "completed": self.completed,
            "successful": self.successful,
            "boot_state": self.boot_manager.state.value,
            "critical_error": self.boot_manager.critical_error,
            "last_error": self.boot_manager.last_error,
        }

    @staticmethod
    def _positive_int(
        value,
        default: int,
    ) -> int:
        try:
            converted = int(
                value
            )

            if converted <= 0:
                raise ValueError

            return converted

        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _positive_float(
        value,
        default: float,
    ) -> float:
        try:
            converted = float(
                value
            )

            if converted <= 0:
                raise ValueError

            return converted

        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _non_negative_float(
        value,
        default: float,
    ) -> float:
        try:
            converted = float(
                value
            )

            if converted < 0:
                raise ValueError

            return converted

        except (
            TypeError,
            ValueError,
        ):
            return default


startup_service = StartupService()
