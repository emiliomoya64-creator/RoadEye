from __future__ import annotations

import asyncio
import logging
import queue
import subprocess
import threading
import time

from fractions import Fraction

import av

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)

from aiortc.mediastreams import MediaStreamError
from aiortc.rtcrtpsender import RTCRtpSender

from core.display_buffer import display_buffer


logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURACION WEBRTC
# ============================================================

TARGET_FPS = 25

WIDTH = 1280
HEIGHT = 720

BITRATE = "4000k"

PACKET_TIME_BASE = Fraction(
    1,
    TARGET_FPS,
)


pcs: set[RTCPeerConnection] = set()


# ============================================================
# TRACK H264 HARDWARE
# ============================================================

class RoadEyeH264Track(VideoStreamTrack):
    """
    WebRTC RoadEye con H.264 pre-codificado.

    Flujo:

        display_buffer
              ↓
        BGR 1280x720
              ↓
        FFmpeg persistente
              ↓
        h264_v4l2m2m
              ↓
        /dev/video11
              ↓
        H.264 Annex-B
              ↓
        PyAV parser
              ↓
        av.Packet
              ↓
        aiortc H264Encoder.pack()
              ↓
        RTP / SRTP / WebRTC

    aiortc NO vuelve a codificar el vídeo.
    """

    kind = "video"

    def __init__(self):
        super().__init__()

        self._stop_event = threading.Event()

        self._packet_queue: queue.Queue = (
            queue.Queue(
                maxsize=100
            )
        )

        self._pts = 0

        self._last_frame_number = -1

        self._process: subprocess.Popen | None = None

        self._feeder_thread = None
        self._reader_thread = None

        self._start_encoder()


    # --------------------------------------------------------
    # FFmpeg H264 hardware
    # --------------------------------------------------------

    def _start_encoder(self):

        command = [
            "ffmpeg",

            "-hide_banner",
            "-loglevel",
            "error",

            "-f",
            "rawvideo",

            "-pix_fmt",
            "bgr24",

            "-video_size",
            f"{WIDTH}x{HEIGHT}",

            "-framerate",
            str(TARGET_FPS),

            "-i",
            "pipe:0",

            "-an",

            "-c:v",
            "h264_v4l2m2m",

            "-b:v",
            BITRATE,

            # WebRTC / baja latencia
            "-g",
            str(TARGET_FPS),

            "-bf",
            "0",

            # Dejamos que bcm2835-codec utilice
            # el perfil y nivel soportados por el driver.
            "-pix_fmt",
            "yuv420p",

            # H264 elemental Annex-B.
            "-f",
            "h264",

            "pipe:1",
        ]

        logger.info(
            "Iniciando H264 hardware WebRTC: %s",
            " ".join(command),
        )

        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

        time.sleep(
            0.15
        )

        if self._process.poll() is not None:
            raise RuntimeError(
                "FFmpeg H264 WebRTC no pudo arrancar"
            )

        self._feeder_thread = threading.Thread(
            target=self._feed_frames,
            name="roadeye-webrtc-h264-feed",
            daemon=True,
        )

        self._reader_thread = threading.Thread(
            target=self._read_h264,
            name="roadeye-webrtc-h264-read",
            daemon=True,
        )

        self._feeder_thread.start()
        self._reader_thread.start()

        logger.info(
            "H264 hardware WebRTC activo "
            "%dx%d @ %d FPS, bitrate=%s",
            WIDTH,
            HEIGHT,
            TARGET_FPS,
            BITRATE,
        )


    # --------------------------------------------------------
    # display_buffer -> FFmpeg
    # --------------------------------------------------------

    def _feed_frames(self):

        process = self._process

        if (
            process is None
            or process.stdin is None
        ):
            return

        frame_interval = (
            1.0
            / TARGET_FPS
        )

        next_frame_time = (
            time.monotonic()
        )

        try:

            while not self._stop_event.is_set():

                if process.poll() is not None:
                    break

                frame_number = (
                    display_buffer.get_frame_number()
                )

                if (
                    frame_number
                    == self._last_frame_number
                ):
                    time.sleep(
                        0.002
                    )
                    continue

                now = time.monotonic()

                if now < next_frame_time:
                    time.sleep(
                        min(
                            0.003,
                            next_frame_time - now,
                        )
                    )
                    continue

                frame = (
                    display_buffer.get_frame()
                )

                if frame is None:
                    time.sleep(
                        0.005
                    )
                    continue

                height, width = (
                    frame.shape[:2]
                )

                if (
                    width != WIDTH
                    or height != HEIGHT
                ):
                    logger.error(
                        "WebRTC esperaba %dx%d "
                        "pero recibió %dx%d",
                        WIDTH,
                        HEIGHT,
                        width,
                        height,
                    )

                    time.sleep(
                        0.1
                    )
                    continue

                if (
                    frame.ndim != 3
                    or frame.shape[2] != 3
                ):
                    logger.error(
                        "Frame WebRTC no es BGR"
                    )

                    time.sleep(
                        0.1
                    )
                    continue

                self._last_frame_number = (
                    frame_number
                )

                # Evita frame.tobytes(), que crearía
                # otra copia completa de 2.7 MB.
                data = (
                    memoryview(frame)
                    .cast("B")
                )

                process.stdin.write(
                    data
                )

                next_frame_time = (
                    now
                    + frame_interval
                )

        except (
            BrokenPipeError,
            OSError,
        ):
            logger.warning(
                "FFmpeg H264 WebRTC cerró stdin"
            )

        except Exception:
            logger.exception(
                "Error alimentando H264 WebRTC"
            )

        finally:
            try:
                process.stdin.close()
            except Exception:
                pass


    # --------------------------------------------------------
    # FFmpeg -> PyAV -> packets
    # --------------------------------------------------------

    def _read_h264(self):

        process = self._process

        if (
            process is None
            or process.stdout is None
        ):
            return

        parser = (
            av.CodecContext.create(
                "h264",
                "r",
            )
        )

        try:

            while not self._stop_event.is_set():

                chunk = (
                    process.stdout.read(
                        65536
                    )
                )

                if not chunk:
                    break

                packets = (
                    parser.parse(
                        chunk
                    )
                )

                for packet in packets:
                    if self._stop_event.is_set():
                        break

                    self._queue_packet(
                        packet
                    )

            # Vaciar último access unit.
            for packet in parser.parse(b""):
                self._queue_packet(
                    packet
                )

        except Exception:
            logger.exception(
                "Error leyendo H264 hardware"
            )

        finally:
            # Desbloquear recv()
            try:
                self._packet_queue.put_nowait(
                    None
                )
            except queue.Full:
                pass


    def _queue_packet(
        self,
        packet,
    ):

        try:
            self._packet_queue.put(
                packet,
                timeout=1.0,
            )

        except queue.Full:
            logger.warning(
                "Cola H264 WebRTC llena"
            )


    # --------------------------------------------------------
    # aiortc solicita un packet
    # --------------------------------------------------------

    async def recv(self):

        if self._stop_event.is_set():
            raise MediaStreamError

        packet = await asyncio.to_thread(
            self._packet_queue.get
        )

        if packet is None:
            raise MediaStreamError

        # El bitstream H264 elemental no contiene
        # timestamps. Los generamos a 25 FPS.
        packet.pts = self._pts
        packet.dts = self._pts

        packet.time_base = (
            PACKET_TIME_BASE
        )

        self._pts += 1

        # IMPORTANTE:
        #
        # devolvemos av.Packet,
        # NO av.VideoFrame.
        #
        # aiortc ejecutará:
        #
        # H264Encoder.pack(packet)
        #
        # y NO:
        #
        # H264Encoder.encode(frame)
        #
        return packet


    # --------------------------------------------------------
    # Cierre
    # --------------------------------------------------------

    def stop(self):

        if self._stop_event.is_set():
            return

        self._stop_event.set()

        process = self._process
        self._process = None

        if process is not None:

            try:
                if process.stdin is not None:
                    process.stdin.close()
            except Exception:
                pass

            try:
                process.terminate()
            except Exception:
                pass

            try:
                process.wait(
                    timeout=2.0
                )
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

        try:
            self._packet_queue.put_nowait(
                None
            )
        except queue.Full:
            pass

        logger.info(
            "H264 hardware WebRTC detenido"
        )

        super().stop()


# ============================================================
# PREFERENCIA H264
# ============================================================

def prefer_h264(
    pc: RTCPeerConnection,
) -> None:

    capabilities = (
        RTCRtpSender.getCapabilities(
            "video"
        )
    )

    h264_codecs = [
        codec
        for codec in capabilities.codecs
        if codec.mimeType.lower()
        == "video/h264"
    ]

    if not h264_codecs:
        raise RuntimeError(
            "aiortc no anuncia H264"
        )

    for transceiver in (
        pc.getTransceivers()
    ):
        if transceiver.kind == "video":
            transceiver.setCodecPreferences(
                h264_codecs
            )


# ============================================================
# NUEVA SESION
# ============================================================

async def create_answer(
    sdp: str,
    offer_type: str,
) -> dict:

    # Un único visor RoadEye.
    if pcs:

        old_pcs = tuple(
            pcs
        )

        logger.info(
            "Sustituyendo %d cliente(s) "
            "WebRTC anterior(es)",
            len(old_pcs),
        )

        await asyncio.gather(
            *[
                old_pc.close()
                for old_pc in old_pcs
            ],
            return_exceptions=True,
        )

        pcs.clear()

    pc = RTCPeerConnection()

    pcs.add(
        pc
    )

    track = (
        RoadEyeH264Track()
    )

    pc.addTrack(
        track
    )

    prefer_h264(
        pc
    )

    logger.info(
        "Nuevo cliente WebRTC H264 hardware"
    )


    @pc.on(
        "connectionstatechange"
    )
    async def on_connectionstatechange():

        logger.info(
            "WebRTC connectionState=%s",
            pc.connectionState,
        )

        print(
            "WEBRTC_STATE:",
            pc.connectionState,
            flush=True,
        )

        if pc.connectionState in {
            "failed",
            "closed",
            "disconnected",
        }:

            track.stop()

            await pc.close()

            pcs.discard(
                pc
            )


    offer = RTCSessionDescription(
        sdp=sdp,
        type=offer_type,
    )

    await pc.setRemoteDescription(
        offer
    )

    answer = (
        await pc.createAnswer()
    )

    await pc.setLocalDescription(
        answer
    )

    return {
        "sdp":
            pc.localDescription.sdp,

        "type":
            pc.localDescription.type,
    }


# ============================================================
# APAGADO
# ============================================================

async def close_all() -> None:

    if not pcs:
        return

    logger.info(
        "Cerrando %d conexiones WebRTC",
        len(pcs),
    )

    await asyncio.gather(
        *[
            pc.close()
            for pc in tuple(pcs)
        ],
        return_exceptions=True,
    )

    pcs.clear()
