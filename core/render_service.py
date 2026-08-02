import logging
import time
from threading import Event, Thread
from typing import Optional

from core.display_buffer import display_buffer
from core.frame_buffer import frame_buffer
from hud.render import render


logger = logging.getLogger(__name__)


class RenderService:
    """
    Servicio central de renderizado de RoadEye.

    Flujo:

        CameraService
            ↓
        frame_buffer (imagen RAW)
            ↓
        RenderService
            ↓
        HUD / ADAS / capas visuales
            ↓
        display_buffer (imagen final)
            ↓
        Web / HDMI / grabación / capturas

    El HUD se dibuja una sola vez por frame.
    """

    def __init__(self, target_fps: float = 30.0):
        self.target_fps = max(1.0, float(target_fps))
        self.frame_interval = 1.0 / self.target_fps

        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._last_raw_frame_number = -1

    @property
    def running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )

    def start(self) -> None:
        """
        Inicia el hilo de renderizado.
        """

        if self.running:
            return

        self._stop_event.clear()

        self._thread = Thread(
            target=self._render_loop,
            name="roadeye-render-service",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "RenderService iniciado a %.1f FPS",
            self.target_fps,
        )

    def stop(self) -> None:
        """
        Detiene el servicio de renderizado.
        """

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=2.0)

        self._thread = None

        logger.info("RenderService detenido")

    def _render_loop(self) -> None:
        """
        Renderiza únicamente cuando existe un frame nuevo.
        """

        while not self._stop_event.is_set():
            loop_started_at = time.monotonic()

            raw_frame_number = frame_buffer.get_frame_number()

            if raw_frame_number == self._last_raw_frame_number:
                time.sleep(0.002)
                continue

            frame = frame_buffer.get_frame()

            if frame is None:
                time.sleep(0.01)
                continue

            try:
                rendered_frame = render(frame)

                if rendered_frame is not None:
                    display_buffer.set_frame(rendered_frame)

                self._last_raw_frame_number = raw_frame_number

            except Exception:
                logger.exception(
                    "Error al renderizar un frame de RoadEye"
                )

                time.sleep(0.05)
                continue

            elapsed = time.monotonic() - loop_started_at
            remaining = self.frame_interval - elapsed

            if remaining > 0:
                time.sleep(remaining)


render_service = RenderService(target_fps=30.0)