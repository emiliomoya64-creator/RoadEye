import time
from datetime import datetime
from pathlib import Path
from threading import Thread

import cv2

from config import VIDEO_FOLDER, VIDEO_FPS, VIDEO_SEGMENT_TIME
from core.frame_buffer import frame_buffer
from core.system_state import system_state


class RecorderService:

    SEGMENT_TIME = VIDEO_SEGMENT_TIME
    FPS = VIDEO_FPS

    def __init__(self):

        self.thread_running = False
        self.recording = False

        self.writer = None
        self.segment_start = None

        self.video_dir = Path(VIDEO_FOLDER)
        self.video_dir.mkdir(exist_ok=True)

    def start(self):

        self.recording = True
        system_state.set("recording", True)

        if self.thread_running:
            return

        self.thread_running = True

        Thread(
            target=self.record_loop,
            daemon=True
        ).start()

        print("▶ Grabador iniciado")

    def stop(self):

        self.recording = False
        system_state.set("recording", False)

        print("⏹ Grabación detenida")

    def close_writer(self):

        if self.writer is not None:

            self.writer.release()
            self.writer = None

            print("■ Vídeo guardado")

    def open_writer(self, frame):

        nombre = datetime.now().strftime("%Y%m%d_%H%M%S.mp4")

        ruta = self.video_dir / nombre

        h, w = frame.shape[:2]

        self.writer = cv2.VideoWriter(
            str(ruta),
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.FPS,
            (w, h)
        )

        self.segment_start = time.time()

        print(f"● Grabando {ruta}")

    def record_loop(self):

        while self.thread_running:

            if not self.recording:

                if self.writer is not None:
                    self.close_writer()

                time.sleep(0.1)
                continue

            frame = frame_buffer.get_frame()

            if frame is None:
                time.sleep(0.01)
                continue

            if self.writer is None:

                self.open_writer(frame)

            elif time.time() - self.segment_start >= self.SEGMENT_TIME:

                self.close_writer()
                self.open_writer(frame)

            self.writer.write(frame)

            time.sleep(1 / self.FPS)