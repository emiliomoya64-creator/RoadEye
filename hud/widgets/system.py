import cv2

from config import COLOR_WHITE
from hud.layout import layout


class SystemWidget:

    def draw(self, frame, fps, cpu, temp):

        cv2.putText(
            frame,
            f"FPS {fps:.1f}   CPU {cpu:.0f}%   TEMP {temp:.0f}°C",
            layout.SYSTEM,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            COLOR_WHITE,
            1
        )


system_widget = SystemWidget()