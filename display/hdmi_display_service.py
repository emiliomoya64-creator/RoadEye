import logging
import time
from pathlib import Path
from threading import Event, Thread
from typing import Optional

import cv2
import gi
import numpy as np

gi.require_version("Gst", "1.0")

from gi.repository import Gst

from core.display_buffer import display_buffer


logger = logging.getLogger(__name__)


class HDMIDisplayService:
    """
    Salida HDMI nativa de RoadEye mediante GStreamer.

    Flujo:

        display_buffer
            ↓
        Gst.AppSrc
            ↓
        videoconvert
            ↓
        kmssink
            ↓
        DRM/KMS
            ↓
        HDMI

    El servicio no captura la cámara y no vuelve a dibujar el HUD.
    Envía exactamente el mismo frame final que consume la web.
    """

    PIPELINE_RETRY_SECONDS = 3.0
    HDMI_CHECK_SECONDS = 2.0

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        target_fps: int = 30,
    ):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.target_fps = max(1, int(target_fps))

        self.frame_duration_ns = (
            Gst.SECOND // self.target_fps
        )

        self._stop_event = Event()
        self._thread: Optional[Thread] = None

        self._pipeline: Optional[Gst.Pipeline] = None
        self._appsrc: Optional[Gst.Element] = None
        self._bus: Optional[Gst.Bus] = None

        self._last_frame_number = -1
        self._frame_index = 0

        Gst.init(None)

    @property
    def running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )

    def start(self) -> None:
        """
        Inicia la salida HDMI en segundo plano.
        """

        if self.running:
            return

        self._stop_event.clear()
        self._last_frame_number = -1
        self._frame_index = 0

        self._thread = Thread(
            target=self._service_loop,
            name="roadeye-hdmi-display",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "HDMIDisplayService iniciado: %dx%d a %d FPS",
            self.width,
            self.height,
            self.target_fps,
        )

    def stop(self) -> None:
        """
        Detiene el hilo y libera la tubería GStreamer.
        """

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=5.0)

        self._close_pipeline()
        self._thread = None

        logger.info("HDMIDisplayService detenido")

    # -------------------------------------------------
    # Bucle principal
    # -------------------------------------------------

    def _hdmi_connected(self) -> bool:
        """
        Comprueba si existe al menos una salida HDMI conectada.
        """
        drm_path = Path(
            "/sys/class/drm"
        )

        try:
            status_files = list(
                drm_path.glob(
                    "card*-HDMI-A-*/status"
                )
            )

            for status_file in status_files:
                try:
                    status = (
                        status_file
                        .read_text()
                        .strip()
                        .lower()
                    )

                    if status == "connected":
                        return True

                except OSError:
                    continue

        except OSError:
            pass

        return False


    def _service_loop(self) -> None:
        """
        Mantiene la salida HDMI activa.

        Si kmssink todavía no puede abrir DRM durante el arranque,
        espera y vuelve a intentarlo automáticamente.
        """

        while not self._stop_event.is_set():

            if not self._hdmi_connected():

                if self._pipeline is not None:
                    logger.info(
                        "HDMI desconectado. "
                        "Cerrando salida de vídeo."
                    )
                    self._close_pipeline()

                self._stop_event.wait(
                    self.HDMI_CHECK_SECONDS
                )

                continue

            if self._pipeline is None:
                try:
                    self._open_pipeline()

                except Exception:
                    logger.exception(
                        "No se pudo iniciar la salida HDMI. "
                        "Nuevo intento en %.1f segundos",
                        self.PIPELINE_RETRY_SECONDS,
                    )

                    self._close_pipeline()

                    self._stop_event.wait(
                        self.PIPELINE_RETRY_SECONDS
                    )

                    continue

            try:
                self._display_frames()

            except Exception:
                logger.exception(
                    "La salida HDMI se interrumpió"
                )

                self._close_pipeline()

                self._stop_event.wait(
                    self.PIPELINE_RETRY_SECONDS
                )

        self._close_pipeline()

    def _display_frames(self) -> None:
        """
        Envía frames nuevos mientras la tubería esté activa.
        """

        while (
            not self._stop_event.is_set()
            and self._pipeline is not None
            and self._appsrc is not None
        ):
            self._check_bus_messages()

            frame_number = display_buffer.get_frame_number()

            if frame_number == self._last_frame_number:
                time.sleep(0.003)
                continue

            frame = display_buffer.get_frame()

            if frame is None:
                time.sleep(0.01)
                continue

            output_frame = self._prepare_frame(frame)

            self._push_frame(output_frame)

            self._last_frame_number = frame_number

    # -------------------------------------------------
    # Creación de la tubería
    # -------------------------------------------------

    def _open_pipeline(self) -> None:
        """
        Crea y activa la tubería nativa GStreamer.
        """

        self._close_pipeline()

        pipeline_description = (
            "appsrc "
            "name=roadeye_source "
            "is-live=true "
            "block=false "
            "format=time "
            "do-timestamp=true "
            "! queue "
            "max-size-buffers=2 "
            "leaky=downstream "
            "! videoconvert "
            "! video/x-raw,format=BGRx "
            "! kmssink "
            "driver-name=vc4 "
            "sync=false "
            "async=false"
        )

        logger.info(
            "Creando tubería HDMI GStreamer: %s",
            pipeline_description,
        )

        pipeline = Gst.parse_launch(
            pipeline_description
        )

        if pipeline is None:
            raise RuntimeError(
                "GStreamer no pudo crear la tubería HDMI"
            )

        appsrc = pipeline.get_by_name(
            "roadeye_source"
        )

        if appsrc is None:
            pipeline.set_state(Gst.State.NULL)

            raise RuntimeError(
                "No se encontró roadeye_source en la tubería"
            )

        caps = Gst.Caps.from_string(
            "video/x-raw,"
            "format=BGR,"
            f"width={self.width},"
            f"height={self.height},"
            f"framerate={self.target_fps}/1"
        )

        appsrc.set_property("caps", caps)
        appsrc.set_property("is-live", True)
        appsrc.set_property("block", False)
        appsrc.set_property("format", Gst.Format.TIME)
        appsrc.set_property("do-timestamp", True)

        bus = pipeline.get_bus()

        state_result = pipeline.set_state(
            Gst.State.PLAYING
        )

        if state_result == Gst.StateChangeReturn.FAILURE:
            pipeline.set_state(Gst.State.NULL)

            raise RuntimeError(
                "kmssink rechazó el estado PLAYING"
            )

        # Espera brevemente a que la tubería confirme su estado.
        state_result, current_state, pending_state = (
            pipeline.get_state(3 * Gst.SECOND)
        )

        if state_result == Gst.StateChangeReturn.FAILURE:
            pipeline.set_state(Gst.State.NULL)

            raise RuntimeError(
                "La tubería HDMI falló durante el arranque"
            )

        self._pipeline = pipeline
        self._appsrc = appsrc
        self._bus = bus
        self._frame_index = 0

        logger.info(
            "Salida HDMI GStreamer activa en %dx%d",
            self.width,
            self.height,
        )

    # -------------------------------------------------
    # Envío de frames
    # -------------------------------------------------

    def _push_frame(
        self,
        frame: np.ndarray,
    ) -> None:
        """
        Convierte el ndarray en Gst.Buffer y lo entrega a appsrc.
        """

        if self._appsrc is None:
            raise RuntimeError(
                "GStreamer appsrc no está disponible"
            )

        frame_bytes = frame.tobytes()
        frame_size = len(frame_bytes)

        buffer = Gst.Buffer.new_allocate(
            None,
            frame_size,
            None,
        )

        if buffer is None:
            raise RuntimeError(
                "No se pudo reservar Gst.Buffer"
            )

        buffer.fill(
            0,
            frame_bytes,
        )

        # appsrc asigna PTS/DTS usando el reloj real
        # de la tubería. Conservamos únicamente la duración.
        buffer.duration = self.frame_duration_ns

        flow_result = self._appsrc.emit(
            "push-buffer",
            buffer,
        )

        if flow_result != Gst.FlowReturn.OK:
            raise RuntimeError(
                "GStreamer rechazó el frame HDMI: "
                f"{flow_result.value_nick}"
            )

        self._frame_index += 1

    # -------------------------------------------------
    # Preparación del frame
    # -------------------------------------------------

    def _prepare_frame(
        self,
        frame: np.ndarray,
    ) -> np.ndarray:
        """
        Convierte el frame a BGR 1280x720 manteniendo proporción.
        """

        if frame is None or frame.size == 0:
            raise ValueError(
                "El frame recibido está vacío"
            )

        if frame.ndim == 2:
            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_GRAY2BGR,
            )

        elif frame.ndim == 3:
            channel_count = frame.shape[2]

            if channel_count == 4:
                frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGRA2BGR,
                )

            elif channel_count != 3:
                raise ValueError(
                    "Número de canales no compatible: "
                    f"{channel_count}"
                )

        else:
            raise ValueError(
                f"Formato de frame no válido: {frame.shape}"
            )

        source_height, source_width = frame.shape[:2]

        # Camino rápido:
        # RoadEye ya renderiza normalmente a la resolución HDMI.
        # Evitamos resize + canvas + copia completa en cada frame.
        if (
            source_width == self.width
            and source_height == self.height
            and frame.ndim == 3
            and frame.shape[2] == 3
        ):
            return np.ascontiguousarray(frame)

        # Camino de compatibilidad para cualquier resolución distinta.
        scale = min(
            self.width / source_width,
            self.height / source_height,
        )

        resized_width = max(
            1,
            int(round(source_width * scale)),
        )

        resized_height = max(
            1,
            int(round(source_height * scale)),
        )

        resized = cv2.resize(
            frame,
            (resized_width, resized_height),
            interpolation=cv2.INTER_LINEAR,
        )

        canvas = np.zeros(
            (self.height, self.width, 3),
            dtype=np.uint8,
        )

        offset_x = (
            self.width - resized_width
        ) // 2

        offset_y = (
            self.height - resized_height
        ) // 2

        canvas[
            offset_y:offset_y + resized_height,
            offset_x:offset_x + resized_width,
        ] = resized

        return np.ascontiguousarray(
            canvas,
            dtype=np.uint8,
        )

    # -------------------------------------------------
    # Errores y mensajes de GStreamer
    # -------------------------------------------------

    def _check_bus_messages(self) -> None:
        """
        Comprueba errores, fin de flujo y avisos de la tubería.
        """

        if self._bus is None:
            return

        while True:
            message = self._bus.pop_filtered(
                Gst.MessageType.ERROR
                | Gst.MessageType.EOS
                | Gst.MessageType.WARNING
            )

            if message is None:
                return

            if message.type == Gst.MessageType.ERROR:
                error, debug = message.parse_error()

                raise RuntimeError(
                    "Error GStreamer HDMI: "
                    f"{error.message}. Debug: {debug}"
                )

            if message.type == Gst.MessageType.EOS:
                raise RuntimeError(
                    "La tubería HDMI recibió EOS"
                )

            if message.type == Gst.MessageType.WARNING:
                warning, debug = message.parse_warning()

                logger.warning(
                    "Aviso GStreamer HDMI: %s. Debug: %s",
                    warning.message,
                    debug,
                )

    # -------------------------------------------------
    # Liberación
    # -------------------------------------------------

    def _close_pipeline(self) -> None:
        """
        Finaliza appsrc y libera la tubería DRM/KMS.
        """

        appsrc = self._appsrc
        pipeline = self._pipeline

        self._appsrc = None
        self._bus = None
        self._pipeline = None
        self._frame_index = 0

        if appsrc is not None:
            try:
                appsrc.emit("end-of-stream")
            except Exception:
                logger.debug(
                    "No se pudo emitir EOS",
                    exc_info=True,
                )

        if pipeline is not None:
            try:
                pipeline.set_state(
                    Gst.State.NULL
                )

                pipeline.get_state(
                    2 * Gst.SECOND
                )

            except Exception:
                logger.exception(
                    "No se pudo cerrar la tubería HDMI"
                )


hdmi_display_service = HDMIDisplayService(
    width=1280,
    height=720,
    target_fps=30,
)
