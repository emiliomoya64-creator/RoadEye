from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from threading import Event, RLock, Thread
from typing import Optional

import cv2

from core.config_manager import PROJECT_DIR, config
from core.frame_buffer import frame_buffer
from core.system_state import system_state


logger = logging.getLogger(__name__)


class RecorderService:
    """
    Servicio de grabación de RoadEye.

    Estados independientes:

    - running:
      El servicio está inicializado y su hilo está funcionando.

    - recording:
      El servicio está escribiendo vídeo en el SSD.

    ServiceManager controla start() y stop().
    La interfaz web controla start_recording() y stop_recording().
    """

    def __init__(self) -> None:
        configured_folder = str(
            config.get(
                "recording.folder",
                "videos",
            )
        ).strip()

        folder_path = Path(
            configured_folder or "videos"
        )

        if not folder_path.is_absolute():
            folder_path = (
                PROJECT_DIR
                / folder_path
            )

        self.video_dir = folder_path.resolve()

        self.fps = self._positive_float(
            config.get(
                "recording.fps",
                20,
            ),
            default=20.0,
        )

        self.segment_seconds = self._positive_float(
            config.get(
                "recording.segment_seconds",
                30,
            ),
            default=30.0,
        )

        self.auto_record = bool(
            config.get(
                "recording.enabled",
                False,
            )
        )

        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._recording_event = Event()
        self._lock = RLock()

        self._writer: Optional[
            cv2.VideoWriter
        ] = None

        self._segment_start: Optional[
            float
        ] = None

        self._current_file: Optional[
            Path
        ] = None

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

    @property
    def recording(self) -> bool:
        return self._recording_event.is_set()

    @property
    def current_file(
        self,
    ) -> Optional[Path]:
        with self._lock:
            return self._current_file

    # ---------------------------------------------------------
    # Ciclo de vida del servicio
    # ---------------------------------------------------------

    def start(self) -> None:
        """
        Inicializa el servicio.

        No comienza a grabar salvo que recording.enabled sea true.
        """

        if self.running:
            return

        self.video_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._stop_event.clear()
        self._recording_event.clear()

        system_state.set(
            "recording",
            False,
        )

        self._thread = Thread(
            target=self._record_loop,
            name="roadeye-recorder",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "RecorderService iniciado: "
            "carpeta=%s, FPS=%.1f, segmento=%.1fs",
            self.video_dir,
            self.fps,
            self.segment_seconds,
        )

        if self.auto_record:
            self.start_recording()

    def stop(self) -> None:
        """
        Detiene completamente el servicio.
        """

        self.stop_recording()

        self._stop_event.set()
        self._recording_event.clear()

        if self._thread is not None:
            self._thread.join(
                timeout=3.0
            )

        self._thread = None

        self._close_writer()

        system_state.set(
            "recording",
            False,
        )

        logger.info(
            "RecorderService detenido"
        )

    # ---------------------------------------------------------
    # Control de grabación
    # ---------------------------------------------------------

    def start_recording(self) -> bool:
        """
        Comienza la grabación.
        """

        if not self.running:
            logger.warning(
                "No se puede grabar: "
                "RecorderService no está iniciado"
            )

            return False

        if self.recording:
            return True

        self._recording_event.set()

        system_state.set(
            "recording",
            True,
        )

        logger.info(
            "Grabación activada"
        )

        print(
            "▶ Grabador iniciado"
        )

        return True

    def stop_recording(self) -> bool:
        """
        Detiene la grabación sin detener el servicio.
        """

        was_recording = self.recording

        # Primero se impide que el hilo abra o escriba otro segmento.
        self._recording_event.clear()

        system_state.set(
            "recording",
            False,
        )

        # Después se cierra el escritor bajo el mismo bloqueo.
        self._close_writer()

        if was_recording:
            logger.info(
                "Grabación detenida"
            )

            print(
                "⏹ Grabación detenida"
            )

        return True

    # ---------------------------------------------------------
    # Bucle principal
    # ---------------------------------------------------------

    def _record_loop(self) -> None:
        frame_interval = (
            1.0 / self.fps
        )

        while not self._stop_event.is_set():
            loop_started_at = time.monotonic()

            if not self.recording:
                self._close_writer()

                self._stop_event.wait(
                    0.05
                )

                continue

            frame = frame_buffer.get_frame()

            if frame is None:
                self._stop_event.wait(
                    0.01
                )

                continue

            try:
                self._write_frame_if_recording(
                    frame
                )

            except Exception:
                logger.exception(
                    "Error grabando vídeo"
                )

                self._recording_event.clear()

                system_state.set(
                    "recording",
                    False,
                )

                self._close_writer()

                self._stop_event.wait(
                    0.1
                )

            elapsed = (
                time.monotonic()
                - loop_started_at
            )

            remaining = (
                frame_interval
                - elapsed
            )

            if remaining > 0:
                self._stop_event.wait(
                    remaining
                )

        self._close_writer()

    def _write_frame_if_recording(
        self,
        frame,
    ) -> None:
        """
        Comprueba de nuevo el estado dentro del bloqueo.

        Esto evita abrir un segmento nuevo cuando la orden de parada
        llega mientras el hilo ya estaba procesando un frame.
        """

        with self._lock:
            if (
                not self._recording_event.is_set()
                or self._stop_event.is_set()
            ):
                return

            if self._writer is None:
                self._open_writer_locked(
                    frame
                )

            elif self._segment_expired_locked():
                self._close_writer_locked()

                if (
                    not self._recording_event.is_set()
                    or self._stop_event.is_set()
                ):
                    return

                self._open_writer_locked(
                    frame
                )

            if (
                not self._recording_event.is_set()
                or self._stop_event.is_set()
            ):
                return

            if self._writer is not None:
                self._writer.write(
                    frame
                )

    # ---------------------------------------------------------
    # Segmentos
    # ---------------------------------------------------------

    def _open_writer_locked(
        self,
        frame,
    ) -> None:
        """
        Debe ejecutarse con self._lock adquirido.
        """

        if (
            not self._recording_event.is_set()
            or self._stop_event.is_set()
        ):
            return

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = (
            self.video_dir
            / f"{timestamp}.mp4"
        )

        height, width = frame.shape[:2]

        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(
                *"mp4v"
            ),
            self.fps,
            (
                width,
                height,
            ),
        )

        if not writer.isOpened():
            writer.release()

            raise RuntimeError(
                "No se pudo crear el vídeo: "
                f"{output_path}"
            )

        self._writer = writer
        self._segment_start = (
            time.monotonic()
        )
        self._current_file = output_path

        logger.info(
            "Grabando segmento: %s",
            output_path,
        )

        print(
            f"● Grabando {output_path}"
        )

    def _close_writer(self) -> None:
        with self._lock:
            self._close_writer_locked()

    def _close_writer_locked(self) -> None:
        """
        Debe ejecutarse con self._lock adquirido.
        """

        writer = self._writer
        current_file = self._current_file

        self._writer = None
        self._segment_start = None
        self._current_file = None

        if writer is None:
            return

        try:
            writer.release()

            logger.info(
                "Vídeo guardado: %s",
                current_file,
            )

            print(
                "■ Vídeo guardado"
            )

        except Exception:
            logger.exception(
                "No se pudo cerrar el vídeo: %s",
                current_file,
            )

    def _segment_expired_locked(
        self,
    ) -> bool:
        if self._segment_start is None:
            return True

        return (
            time.monotonic()
            - self._segment_start
            >= self.segment_seconds
        )

    # ---------------------------------------------------------
    # Información pública
    # ---------------------------------------------------------

    def status(self) -> dict:
        with self._lock:
            current_file = self._current_file

            return {
                "service_running": self.running,
                "recording": self.recording,
                "folder": str(
                    self.video_dir
                ),
                "fps": self.fps,
                "segment_seconds": (
                    self.segment_seconds
                ),
                "current_file": (
                    str(current_file)
                    if current_file is not None
                    else None
                ),
            }

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
            logger.warning(
                "Valor de grabación inválido '%s'. "
                "Se usará %.1f",
                value,
                default,
            )

            return default