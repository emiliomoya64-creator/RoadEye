import threading
import time
import cv2

from picamera2 import Picamera2


class Camera:

    def __init__(self,width,height):

        self.width=width
        self.height=height

        self.frame=None

        self.lock=threading.Lock()

        self.running=False

        self.picam2=Picamera2()

        config=self.picam2.create_video_configuration(

            main={
                "size":(width,height),
                "format":"RGB888"
            }

        )

        self.picam2.configure(config)

    def start(self):

        self.picam2.start()

        self.running=True

        threading.Thread(
            target=self.update,
            daemon=True
        ).start()

    def update(self):

        while self.running:

            frame=self.picam2.capture_array()

            with self.lock:

                self.frame=frame

            time.sleep(0.001)

    def get_frame(self):

        with self.lock:

            if self.frame is None:
                return None

            return self.frame.copy()

    def stop(self):

        self.running=False

        self.picam2.stop()

