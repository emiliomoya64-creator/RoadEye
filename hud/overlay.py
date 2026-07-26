import datetime
import subprocess

import cv2
import psutil

from core.system_state import system_state


class Overlay:

    def cpu_temp(self):

        try:
            temp = subprocess.check_output(
                ["vcgencmd", "measure_temp"]
            ).decode()

            return temp.split("=")[1].replace("'C\n", "")

        except:
            return "--"

    def draw(self, frame, fps):

        h, w = frame.shape[:2]

        system_state.set("cpu", psutil.cpu_percent())
        system_state.set("temp", self.cpu_temp())

        cv2.rectangle(frame, (0, 0), (w, 70), (20, 20, 20), -1)

        now = datetime.datetime.now().strftime("%H:%M:%S")

        rec = "REC ●" if system_state.get("recording") else "REC ○"

        gps = "GPS FIX" if system_state.get("gps_fix") else "GPS ---"

        texto1 = (
            f"{rec}     "
            f"{gps}     "
            f"{system_state.get('speed'):5.1f} km/h"
        )

        texto2 = (
            f"{now}     "
            f"FPS:{fps:4.1f}     "
            f"CPU:{system_state.get('cpu'):2.0f}%     "
            f"TEMP:{system_state.get('temp')}"
        )

        cv2.putText(
            frame,
            texto1,
            (15, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            texto2,
            (15, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        return frame


overlay = Overlay()