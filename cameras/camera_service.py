import logging
import cv2
import time
from threading import Event, Thread
from typing import Optional

from picamera2 import Picamera2

from core.config_manager import config
from core.frame_buffer import frame_buffer


logger = logging.getLogger(__name__)


class CameraService:
    """
    Servicio de captura de la cámara frontal de RoadEye.

    La configuración se obtiene del ConfigManager central:

        camera.front.enabled
        camera.front.width
        camera.front.height
        camera.front.format
        camera.front.fps

    El servicio captura una sola vez y publica los frames RAW
    en core.frame_buffer para que los demás módulos los consuman.
    """

    def __init__(self) -> None:
        self.enabled = bool(
            config.get(
                "camera.front.enabled",
                True,
            )
        )

        self.width = self._positive_int(
            config.get(
                "camera.front.width",
                1280,
            ),
            default=1280,
        )

        self.height = self._positive_int(
            config.get(
                "camera.front.height",
                720,
            ),
            default=720,
        )

        self.pixel_format = str(
            config.get(
                "camera.front.format",
                "RGB888",
            )
        ).strip()

        self.target_fps = self._positive_float(
            config.get(
                "camera.front.fps",
                30,
            ),
            default=30.0,
        )

        self.frame_interval = 1.0 / self.target_fps

        self.flip_horizontal = bool(
            config.get(
                "camera.front.flip_horizontal",
                False,
            )
        )

        self.flip_vertical = bool(
            config.get(
                "camera.front.flip_vertical",
                False,
            )
        )

        self.picam2: Optional[Picamera2] = None
        self._capture_thread: Optional[Thread] = None
        self._stop_event = Event()

        self._configure_camera()

    # ---------------------------------------------------------
    # Estado
    # ---------------------------------------------------------

    @property
    def running(self) -> bool:
        return (
            self._capture_thread is not None
            and self._capture_thread.is_alive()
            and not self._stop_event.is_set()
        )

    # ---------------------------------------------------------
    # Configuración de Picamera2
    # ---------------------------------------------------------

    def _configure_camera(self) -> None:
        """
        Crea y configura Picamera2.

        No inicia todavía la captura.
        """

        if not self.enabled:
            logger.warning(
                "La cámara frontal está desactivada en config.json"
            )
            return

        if not self.pixel_format:
            raise ValueError(
                "camera.front.format no puede estar vacío"
            )

        logger.info(
            "Configurando cámara frontal: %dx%d, %s, %.1f FPS",
            self.width,
            self.height,
            self.pixel_format,
            self.target_fps,
        )

        self.picam2 = Picamera2()

        camera_configuration = (
            self.picam2.create_video_configuration(
                main={
                    "size": (
                        self.width,
                        self.height,
                    ),
                    "format": self.pixel_format,
                },
                controls={
                    "FrameRate": self.target_fps,
                },
            )
        )

        self.picam2.configure(
            camera_configuration
        )

    # ---------------------------------------------------------
    # Inicio y parada
    # ---------------------------------------------------------

    def start(self) -> None:
        """
        Inicia la cámara y el hilo de captura.
        """

        if not self.enabled:
            logger.warning(
                "CameraService no se inicia porque "
                "camera.front.enabled=false"
            )
            return

        if self.running:
            logger.debug(
                "CameraService ya está funcionando"
            )
            return

        if self.picam2 is None:
            self._configure_camera()

        if self.picam2 is None:
            raise RuntimeError(
                "Picamera2 no está disponible"
            )

        self._stop_event.clear()

        self.picam2.start()

        self._capture_thread = Thread(
            target=self._capture_loop,
            name="roadeye-camera-front",
            daemon=True,
        )

        self._capture_thread.start()

        logger.info(
            "CameraService iniciado: %dx%d a %.1f FPS",
            self.width,
            self.height,
            self.target_fps,
        )

    def stop(self) -> None:
        """
        Detiene el hilo y libera Picamera2.
        """

        self._stop_event.set()

        if self._capture_thread is not None:
            self._capture_thread.join(
                timeout=3.0
            )

        self._capture_thread = None

        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except RuntimeError:
                logger.debug(
                    "Picamera2 ya estaba detenida"
                )

        logger.info(
            "CameraService detenido"
        )

    def get_camera(self) -> Optional[Picamera2]:
        """
        Devuelve la instancia de Picamera2.

        Se mantiene para conservar compatibilidad con módulos anteriores.
        """

        return self.picam2

    # ---------------------------------------------------------
    # Captura
    # ---------------------------------------------------------

    def _capture_loop(self) -> None:
        """
        Captura frames y los publica en frame_buffer.
        """

        if self.picam2 is None:
            logger.error(
                "No puede iniciarse el bucle: Picamera2 no existe"
            )
            return

        while not self._stop_event.is_set():
            loop_started_at = time.monotonic()

            try:
                frame = self.picam2.capture_array()

                if frame is not None:

                    if (
                        self.flip_horizontal
                        and self.flip_vertical
                    ):
                        frame = cv2.flip(
                            frame,
                            -1
                        )

                    elif self.flip_horizontal:
                        frame = cv2.flip(
                            frame,
                            1
                        )

                    elif self.flip_vertical:
                        frame = cv2.flip(
                            frame,
                            0
                        )

                    frame_buffer.set_frame(
                        frame
                    )

            except Exception:
                logger.exception(
                    "Error capturando un frame"
                )

                self._stop_event.wait(
                    0.1
                )
                continue

            elapsed = (
                time.monotonic()
                - loop_started_at
            )

            remaining = (
                self.frame_interval
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
    def _positive_int(
        value,
        default: int,
    ) -> int:
        try:
            converted = int(value)

            if converted <= 0:
                raise ValueError

            return converted

        except (TypeError, ValueError):
            logger.warning(
                "Valor entero inválido '%s'. Se usará %d",
                value,
                default,
            )
            return default

    @staticmethod
    def _positive_float(
        value,
        default: float,
    ) -> float:
        try:
            converted = float(value)

            if converted <= 0:
                raise ValueError

            return converted

        except (TypeError, ValueError):
            logger.warning(
                "Valor numérico inválido '%s'. Se usará %.1f",
                value,
                default,
            )
            return default