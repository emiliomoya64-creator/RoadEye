from cameras.base_camera import BaseCamera

import numpy as np
import cv2
import time


class DummyCamera(BaseCamera):

    def __init__(self,name):

        super().__init__(name)

        self.counter = 0


    def update(self):

        while self.running:

            img = np.zeros((720,1280,3),dtype=np.uint8)

            cv2.putText(

                img,

                f"PiDash TEST CAMERA",

                (80,120),

                cv2.FONT_HERSHEY_SIMPLEX,

                2,

                (0,255,0),

                4

            )

            cv2.putText(

                img,

                self.name,

                (80,220),

                cv2.FONT_HERSHEY_SIMPLEX,

                2,

                (255,255,255),

                3

            )

            cv2.putText(

                img,

                str(self.counter),

                (80,340),

                cv2.FONT_HERSHEY_SIMPLEX,

                3,

                (0,255,255),

                4

            )

            self.frame = img

            self.counter += 1

            time.sleep(0.03)
