from __future__ import annotations

import logging
import time
from enum import Enum
from threading import Event, RLock, Thread
from typing import Optional

from core.display_buffer import display_buffer
from startup.boot_checks import BootChecks
from startup.boot_screen import (
    BootCheckState,
    BootScreen,
)


logger = logging.getLogger(__name__)


class BootManagerState(str, Enum):
    """
    Estados del proceso visual de arranque.
    """

    IDLE = "idle"
    SPLASH = "splash"
    CHECKING = "checking"
    READY = "ready"
    ERROR = "error"
    FINISHED = "finished"
    STOPPED = "stopped"


class BootManager:
    """
    Coordina la pantalla visual de arranque de RoadEye.

    Responsabilidades:

    - generar el splash inicial;
    - ejecutar comprobaciones rápidas;
    - actualizar BootScreen;
    - publicar frames en DisplayBuffer;
    - indicar si el arranque puede continuar.

    No arranca CameraService.
    No arranca HDMI.
    No sustituye a ServiceManager.
    """

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        splash_seconds: float = 1.2,
        ready_seconds: float = 1.5,
        check_delay_seconds: float = 0.20,
        publish_fps: float = 15.0,
    ) -> None:
        self.screen = BootScreen(
            width=width,
            height=height,
        )

        self.checks = BootChecks()

        self.splash_seconds = self._non_negative_float(
            splash_seconds,
            default=1.2,
        )

        self.ready_seconds = self._non_negative_float(
            ready_seconds,
            default=1.5,
        )

        self.check_delay_seconds = self._non_negative_float(
            check_delay_seconds,
            default=0.20,
        )

        self.publish_fps = self._positive_float(
            publish_fps,
            default=15.0,
        )

        self._frame_interval = (
            1.0 / self.publish_fps
        )

        self._state = BootManagerState.IDLE
        self._thread: Optional[Thread] = None

        self._stop_event = Event()
        self._finished_event = Event()
        self._lock = RLock()

        self._critical_error = False
        self._last_error: Optional[str] = None

    # ---------------------------------------------------------
    # Estado público
    # ---------------------------------------------------------

    @property
    def state(self) -> BootManagerState:
        with self._lock:
            return self._state

    @property
    def running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )

    @property
    def finished(self) -> bool:
        return self._finished_event.is_set()

    @property
    def critical_error(self) -> bool:
        with self._lock:
            return self._critical_error

    @property
    def last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    @property
    def can_continue(self) -> bool:
        return (
            self.finished
            and not self.critical_error
        )

    # ---------------------------------------------------------
    # Control
    # ---------------------------------------------------------

    def start(self) -> None:
        """
        Inicia BootManager en segundo plano.
        """

        if self.running:
            return

        self._stop_event.clear()
        self._finished_event.clear()

        with self._lock:
            self._critical_error = False
            self._last_error = None
            self._state = BootManagerState.SPLASH

        self._thread = Thread(
            target=self._run,
            name="roadeye-boot-manager",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "BootManager iniciado"
        )

    def stop(self) -> None:
        """
        Detiene BootManager.
        """

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=3.0
            )

        self._thread = None

        with self._lock:
            if self._state != BootManagerState.FINISHED:
                self._state = BootManagerState.STOPPED

        logger.info(
            "BootManager detenido"
        )

    def wait(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Espera hasta que termine el arranque visual.

        Devuelve True si terminó antes del timeout.
        """

        return self._finished_event.wait(
            timeout=timeout
        )

    def run_blocking(self) -> bool:
        """
        Ejecuta BootManager en el hilo actual.

        Resulta útil para pruebas manuales.
        """

        if self.running:
            raise RuntimeError(
                "BootManager ya está ejecutándose"
            )

        self._stop_event.clear()
        self._finished_event.clear()

        with self._lock:
            self._critical_error = False
            self._last_error = None
            self._state = BootManagerState.SPLASH

        self._run()

        return self.can_continue

    # ---------------------------------------------------------
    # Secuencia principal
    # ---------------------------------------------------------

    def _run(self) -> None:
        try:
            self._show_splash()

            if self._stop_event.is_set():
                return

            self._run_checks()

            if self._stop_event.is_set():
                return

            if self.critical_error:
                self._show_error()
            else:
                self._show_ready()

        except Exception as exc:
            logger.exception(
                "Error interno en BootManager"
            )

            with self._lock:
                self._critical_error = True
                self._last_error = (
                    f"{type(exc).__name__}: {exc}"
                )
                self._state = BootManagerState.ERROR

            self.screen.set_phase(
                "ERROR DE ARRANQUE"
            )

            self.screen.set_footer_message(
                "Ejecuta: roadeye doctor"
            )

            self._publish_for(
                2.0
            )

        finally:
            with self._lock:
                if self._state not in {
                    BootManagerState.ERROR,
                    BootManagerState.STOPPED,
                }:
                    self._state = BootManagerState.FINISHED

            self._finished_event.set()

            logger.info(
                "BootManager finalizado: "
                "estado=%s error_critico=%s",
                self.state.value,
                self.critical_error,
            )

    # ---------------------------------------------------------
    # Fases
    # ---------------------------------------------------------

    def _show_splash(self) -> None:
        with self._lock:
            self._state = BootManagerState.SPLASH

        self.screen.set_checks(
            []
        )

        self.screen.set_phase(
            "Inicializando sistema..."
        )

        self.screen.set_footer_message(
            "Preparando RoadEye"
        )

        self._publish_for(
            self.splash_seconds
        )

    def _run_checks(self) -> None:
        with self._lock:
            self._state = BootManagerState.CHECKING

        initial_checks = (
            self.checks.initial_checks()
        )

        self.screen.set_checks(
            initial_checks
        )

        self.screen.set_phase(
            "Comprobando sistema..."
        )

        self.screen.set_footer_message(
            "Diagnóstico rápido de arranque"
        )

        self._publish_once()

        for definition in self.checks.definitions():
            if self._stop_event.is_set():
                return

            self.screen.update_check(
                definition.key,
                state=BootCheckState.RUNNING,
                detail="Comprobando...",
            )

            self._publish_for(
                self.check_delay_seconds
            )

            (
                state,
                detail,
                critical,
            ) = self.checks.run(
                definition.key
            )

            self.screen.update_check(
                definition.key,
                state=state,
                detail=detail,
            )

            if (
                critical
                and state == BootCheckState.ERROR
            ):
                with self._lock:
                    self._critical_error = True
                    self._last_error = (
                        f"{definition.label}: {detail}"
                    )

            self._publish_for(
                self.check_delay_seconds
            )

    def _show_ready(self) -> None:
        with self._lock:
            self._state = BootManagerState.READY

        self.screen.set_phase(
            "ROAD EYE PREPARADO"
        )

        self.screen.set_footer_message(
            "Iniciando cámara y servicios"
        )

        self._publish_for(
            self.ready_seconds
        )

    def _show_error(self) -> None:
        with self._lock:
            self._state = BootManagerState.ERROR

        self.screen.set_phase(
            "ERROR CRÍTICO"
        )

        self.screen.set_footer_message(
            "Ejecuta: roadeye doctor"
        )

        self._publish_for(
            max(
                3.0,
                self.ready_seconds,
            )
        )

    # ---------------------------------------------------------
    # Publicación de frames
    # ---------------------------------------------------------

    def _publish_once(self) -> None:
        frame = self.screen.render()

        display_buffer.set_frame(
            frame
        )

    def _publish_for(
        self,
        duration_seconds: float,
    ) -> None:
        duration = max(
            0.0,
            float(duration_seconds),
        )

        if duration == 0:
            self._publish_once()
            return

        end_time = (
            time.monotonic()
            + duration
        )

        while (
            not self._stop_event.is_set()
            and time.monotonic() < end_time
        ):
            loop_started_at = time.monotonic()

            self._publish_once()

            elapsed = (
                time.monotonic()
                - loop_started_at
            )

            remaining = (
                self._frame_interval
                - elapsed
            )

            if remaining > 0:
                self._stop_event.wait(
                    remaining
                )

    # ---------------------------------------------------------
    # Validación
    # ---------------------------------------------------------

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


boot_manager = BootManager()
