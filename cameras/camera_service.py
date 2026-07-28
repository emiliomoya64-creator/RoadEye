import time
from threading import Thread

from picamera2 import Picamera2

from config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FORMAT
from core.frame_buffer import frame_buffer


class CameraService:

    def __init__(self):

        self.picam2 = Picamera2()

        config = self.picam2.create_video_configuration(
            main={
                "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
                "format": CAMERA_FORMAT
            }
        )

        self.picam2.configure(config)

        self.running = False

    def start(self):

        self.picam2.start()

        self.running = True

        Thread(
            target=self.capture_loop,
            daemon=True
        ).start()

    def stop(self):

        self.running = False

        self.picam2.stop()

    def get_camera(self):

        return self.picam2

    def capture_loop(self):

        while self.running:

            frame = self.picam2.capture_array()

            frame_buffer.set_frame(frame)

            time.sleep(0.001)