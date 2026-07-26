import time
from threading import Thread

from picamera2 import Picamera2

from core.frame_buffer import frame_buffer


class CameraService:

    def __init__(self):

        self.picam2 = Picamera2()

        config = self.picam2.create_video_configuration(
            main={
                "size": (1280, 720),
                "format": "RGB888"
            }
        )

        self.picam2.configure(config)

        self.running = False

    def start(self):

        self.picam2.start()

        self.running = True

        Thread(target=self.capture_loop, daemon=True).start()

    def capture_loop(self):

        while self.running:

            frame = self.picam2.capture_array()

            frame_buffer.set_frame(frame)

            time.sleep(0.001)