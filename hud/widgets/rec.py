import datetime
import cv2

from hud.layout import layout


class RecWidget:

    def __init__(self):

        self.visible = True
        self.last = datetime.datetime.now()

    def draw(self, frame, recording):

        now = datetime.datetime.now()

        if (now - self.last).total_seconds() > 0.5:
            self.visible = not self.visible
            self.last = now

        if recording:
            text = "REC ●" if self.visible else "REC"
            color = (0, 0, 255)
        else:
            text = "STOP"
            color = (150, 150, 150)

        cv2.putText(
            frame,
            text,
            layout.REC,
            cv2.FONT_HERSHEY_DUPLEX,
            0.8,
            color,
            2
        )


rec_widget = RecWidget()