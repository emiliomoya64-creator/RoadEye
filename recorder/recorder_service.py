from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from threading import Event, RLock, Thread
from typing import Optional

import cv2

from core.config_manager import PROJECT_DIR, config
from core.frame_buffer import frame_buffer
from core.system_state import system_state
from recorder.recording_session import RecordingSession
from trip.trip_manager import trip_manager


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
            subprocess.Popen
        ] = None

        self._video_encoder = (
            self._detect_h264_encoder()
        )

        self._segment_start: Optional[
            float
        ] = None

        self._current_file: Optional[
            Path
        ] = None

        self._current_session: Optional[
            RecordingSession
        ] = None

        self._last_completed_metadata_path: Optional[
            Path
        ] = None

        self._pending_protected_segments = 0
        self._pending_protection_reasons: list[str] = []

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

    def start_recording(
        self,
        *,
        trip_type: str = "driving",
    ) -> bool:
        """
        Comienza la grabación.

        trip_type permite que servicios especializados,
        como RoadEye Sentinel, creen viajes Parking sin
        alterar la grabación normal.
        """

        if not self.running:
            logger.warning(
                "No se puede grabar: "
                "RecorderService no está iniciado"
            )

            return False

        if self.recording:
            return True

        # El viaje se abre antes de activar la grabación.
        normalized_trip_type = str(
            trip_type
        ).strip().lower()

        if normalized_trip_type not in {
            "driving",
            "parking",
            "event",
        }:
            normalized_trip_type = "driving"

        trip_manager.ensure_trip(
            trip_type=normalized_trip_type,
            started_at=datetime.now(),
        )

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

        # Detener manualmente la grabación finaliza el viaje.
        if was_recording:
            try:
                trip_manager.close_trip()

            except Exception:
                logger.exception(
                    "No se pudo cerrar el viaje activo"
                )

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

            if (
                self._current_session
                is not None
            ):
                self._current_session.update(
                    frame,
                    latitude=system_state.get(
                        "latitude"
                    ),
                    longitude=system_state.get(
                        "longitude"
                    ),
                    gps_fix=system_state.get(
                        "gps_fix"
                    ),
                    speed=system_state.get(
                        "speed"
                    ),
                )

            if self._writer is not None:
                if self._writer.poll() is not None:
                    raise RuntimeError(
                        "FFmpeg terminó inesperadamente "
                        f"con código {self._writer.returncode}"
                    )

                if self._writer.stdin is None:
                    raise RuntimeError(
                        "FFmpeg no tiene entrada de vídeo."
                    )

                try:
                    self._writer.stdin.write(
                        frame.tobytes()
                    )

                except BrokenPipeError as exc:
                    raise RuntimeError(
                        "FFmpeg cerró la entrada de vídeo."
                    ) from exc

    # ---------------------------------------------------------
    # Segmentos
    # ---------------------------------------------------------

    def _detect_h264_encoder(
        self,
    ) -> str:
        """
        Selecciona el mejor codificador H.264 disponible.

        Prioridad:
        1. h264_v4l2m2m: hardware Raspberry Pi.
        2. libx264: software, como respaldo.
        """

        if shutil.which(
            "ffmpeg"
        ) is None:
            raise RuntimeError(
                "FFmpeg no está instalado."
            )

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-encoders",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

        except (
            subprocess.SubprocessError,
            OSError,
        ) as exc:
            raise RuntimeError(
                "No se pudieron consultar "
                "los codificadores de FFmpeg."
            ) from exc

        encoders = (
            result.stdout
            + result.stderr
        )

        if "h264_v4l2m2m" in encoders:
            return "h264_v4l2m2m"

        if "libx264" in encoders:
            return "libx264"

        raise RuntimeError(
            "FFmpeg no dispone de un codificador H.264."
        )

    def _build_ffmpeg_command(
        self,
        *,
        output_path: Path,
        width: int,
        height: int,
    ) -> list[str]:
        """
        Construye el comando que recibe frames BGR por stdin
        y produce un MP4 H.264 compatible con navegador.
        """

        fps_text = (
            f"{self.fps:.3f}"
        )

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-video_size",
            f"{width}x{height}",
            "-framerate",
            fps_text,
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            self._video_encoder,
        ]

        if (
            self._video_encoder
            == "h264_v4l2m2m"
        ):
            command.extend(
                [
                    "-b:v",
                    "6000k",
                    "-g",
                    str(
                        max(
                            1,
                            int(
                                round(
                                    self.fps * 2
                                )
                            ),
                        )
                    ),
                ]
            )

        else:
            command.extend(
                [
                    "-preset",
                    "ultrafast",
                    "-crf",
                    "24",
                    "-tune",
                    "zerolatency",
                ]
            )

        command.extend(
            [
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-f",
                "mp4",
                str(
                    output_path
                ),
            ]
        )

        return command

    def _open_writer_locked(
        self,
        frame,
    ) -> None:
        """
        Abre FFmpeg para crear directamente un MP4 H.264.

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

        command = self._build_ffmpeg_command(
            output_path=output_path,
            width=width,
            height=height,
        )

        logger.info(
            "Abriendo FFmpeg con codificador %s",
            self._video_encoder,
        )

        writer = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        # Detectar fallos inmediatos de FFmpeg.
        time.sleep(
            0.15
        )

        if writer.poll() is not None:
            error_text = ""

            if writer.stderr is not None:
                error_text = writer.stderr.read().decode(
                    "utf-8",
                    errors="replace",
                )

            raise RuntimeError(
                "No se pudo iniciar FFmpeg: "
                f"{error_text.strip()}"
            )

        self._writer = writer
        self._segment_start = (
            time.monotonic()
        )
        self._current_file = output_path

        self._current_session = (
            RecordingSession(
                output_path,
                recording_type=(
                    "parking"
                    if bool(
                        getattr(
                            system_state,
                            "parking_motion",
                            False,
                        )
                    )
                    else "normal"
                ),
                protected=False,
            )
        )

        if self._pending_protected_segments > 0:
            for reason in self._pending_protection_reasons:
                self._current_session.protect(
                    reason
                )

            self._pending_protected_segments -= 1

            if self._pending_protected_segments <= 0:
                self._pending_protected_segments = 0
                self._pending_protection_reasons.clear()

        logger.info(
            "Grabando segmento H.264: %s",
            output_path,
        )

        print(
            f"● Grabando H.264 {output_path}"
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
        current_session = (
            self._current_session
        )

        self._writer = None
        self._segment_start = None
        self._current_file = None
        self._current_session = None

        if writer is None:
            return

        try:
            if writer.stdin is not None:
                try:
                    writer.stdin.flush()
                except (
                    BrokenPipeError,
                    OSError,
                ):
                    pass

                try:
                    writer.stdin.close()
                except OSError:
                    pass

            try:
                writer.wait(
                    timeout=12.0
                )

            except subprocess.TimeoutExpired:
                logger.warning(
                    "FFmpeg no terminó a tiempo; "
                    "se enviará terminate()."
                )

                writer.terminate()

                try:
                    writer.wait(
                        timeout=3.0
                    )

                except subprocess.TimeoutExpired:
                    writer.kill()
                    writer.wait(
                        timeout=2.0
                    )

            if writer.returncode not in (
                0,
                None,
            ):
                error_text = ""

                if writer.stderr is not None:
                    try:
                        error_text = writer.stderr.read().decode(
                            "utf-8",
                            errors="replace",
                        )
                    except OSError:
                        pass

                logger.error(
                    "FFmpeg terminó con código %s: %s",
                    writer.returncode,
                    error_text.strip(),
                )

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

        if (
            current_session is not None
            and current_file is not None
            and current_file.exists()
        ):
            try:
                metadata = (
                    current_session.finalize()
                )

                trip_manager.add_segment(
                    metadata,
                    current_session.metadata_path,
                )

                self._last_completed_metadata_path = (
                    current_session.metadata_path
                )

                logger.info(
                    "Metadatos guardados: "
                    "duración=%.2fs, "
                    "velocidad máxima=%.1f km/h",
                    metadata["duration"],
                    metadata["speed"]["max"],
                )

            except Exception:
                logger.exception(
                    "No se pudieron generar "
                    "los metadatos multimedia de %s",
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

    def protect_current_segment(
        self,
        *,
        reason: str = "event",
    ) -> bool:
        """
        Mantiene compatibilidad con la protección simple.
        """

        result = self.protect_event_context(
            reason=reason,
            protect_previous=False,
            protect_next=0,
        )

        return bool(
            result["current"]
        )

    def protect_event_context(
        self,
        *,
        reason: str = "event",
        protect_previous: bool = True,
        protect_next: int = 1,
    ) -> dict:
        """
        Protege el segmento anterior, el actual y los siguientes.
        """

        normalized_reason = str(
            reason
        ).strip().lower() or "event"

        result = {
            "previous": False,
            "current": False,
            "next_count": max(
                0,
                int(
                    protect_next
                ),
            ),
            "reason": normalized_reason,
        }

        with self._lock:
            if (
                protect_previous
                and self._last_completed_metadata_path is not None
            ):
                result["previous"] = (
                    self._protect_completed_segment_locked(
                        self._last_completed_metadata_path,
                        normalized_reason,
                    )
                )

            if self._current_session is not None:
                self._current_session.protect(
                    normalized_reason
                )

                result["current"] = True

            requested_next = max(
                0,
                int(
                    protect_next
                ),
            )

            self._pending_protected_segments = max(
                self._pending_protected_segments,
                requested_next,
            )

            if (
                requested_next > 0
                and normalized_reason
                not in self._pending_protection_reasons
            ):
                self._pending_protection_reasons.append(
                    normalized_reason
                )

            logger.info(
                "Contexto protegido: anterior=%s, "
                "actual=%s, siguientes=%d, motivo=%s",
                result["previous"],
                result["current"],
                requested_next,
                normalized_reason,
            )

        return result

    def _protect_completed_segment_locked(
        self,
        metadata_path: Path,
        reason: str,
    ) -> bool:
        """
        Protege un JSON de segmento que ya se cerró.
        """

        try:
            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(
                metadata,
                dict,
            ):
                return False

            metadata["protected"] = True

            reasons = metadata.get(
                "protection_reasons",
                [],
            )

            if not isinstance(
                reasons,
                list,
            ):
                reasons = []

            if reason not in reasons:
                reasons.append(
                    reason
                )

            metadata[
                "protection_reasons"
            ] = reasons

            temporary_path = (
                metadata_path.with_suffix(
                    ".json.protection.tmp"
                )
            )

            temporary_path.write_text(
                json.dumps(
                    metadata,
                    indent=4,
                    ensure_ascii=False,
                ) + "\n",
                encoding="utf-8",
            )

            temporary_path.replace(
                metadata_path
            )

            filename = str(
                metadata.get(
                    "filename",
                    "",
                )
            )

            if filename:
                trip_manager.protect_segment(
                    filename,
                    reason,
                )

            return True

        except (
            OSError,
            json.JSONDecodeError,
        ):
            logger.exception(
                "No se pudo proteger el segmento anterior: %s",
                metadata_path,
            )

            return False


    # ---------------------------------------------------------
    # Información pública
    # ---------------------------------------------------------

    def status(self) -> dict:
        with self._lock:
            current_file = self._current_file

            segment_elapsed = 0.0

            if self._segment_start is not None:
                segment_elapsed = max(
                    0.0,
                    time.monotonic()
                    - self._segment_start,
                )

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
                "segment_elapsed": round(
                    segment_elapsed,
                    2,
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