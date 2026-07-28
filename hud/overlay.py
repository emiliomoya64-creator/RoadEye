import datetime
import subprocess

import cv2
import psutil

from config import (
    HUD_HEIGHT,
    COLOR_BACKGROUND,
    COLOR_SEPARATOR,
    COLOR_WHITE,
)

from core.system_state import system_state

from hud.widgets.rec import rec_widget
from hud.widgets.gps import gps_widget
from hud.widgets.speed import speed_widget
from hud.widgets.road import road_widget
from hud.widgets.system import system_widget


class Overlay:

    def __init__(self):

        self.blink = False
        self.last_blink = datetime.datetime.now()

    def cpu_temp(self):

        try:

            temp = subprocess.check_output(
                ["vcgencmd", "measure_temp"]
            ).decode()

            return float(
                temp.split("=")[1].replace("'C\n", "")
            )

        except:

            return 0

    def draw(self, frame, fps):

        h, w = frame.shape[:2]

        # --------------------------
        # Actualizar estado sistema
        # --------------------------

        system_state.set("cpu", psutil.cpu_percent())
        system_state.set("temp", self.cpu_temp())

        # --------------------------
        # Fondo HUD
        # --------------------------

        cv2.rectangle(
            frame,
            (0, 0),
            (w, HUD_HEIGHT),
            COLOR_BACKGROUND,
            -1
        )

        cv2.line(
            frame,
            (0, HUD_HEIGHT),
            (w, HUD_HEIGHT),
            COLOR_SEPARATOR,
            1
        )

        # --------------------------
        # Parpadeo
        # --------------------------

        now = datetime.datetime.now()

        if (now - self.last_blink).total_seconds() >= 0.5:

            self.blink = not self.blink
            self.last_blink = now

        # --------------------------
        # Fecha y hora
        # --------------------------

        cv2.putText(
            frame,
            now.strftime("%d/%m/%Y %H:%M:%S"),
            (15, 28),
            cv2.FONT_HERSHEY_DUPLEX,
            0.70,
            COLOR_WHITE,
            2
        )

        # --------------------------
        # Widgets
        # --------------------------

        rec_widget.draw(
            frame,
            system_state.get("recording")
        )

        gps_widget.draw(
            frame,
            system_state.get("gps_fix"),
            system_state.get("satellites")
        )

        speed_widget.draw(
            frame,
            system_state.get("speed"),
            system_state.get("speed_limit"),
            self.blink
        )

        road_widget.draw(
            frame,
            system_state.get("road"),
            system_state.get("road_type"),
            system_state.get("lanes")
        )

        system_widget.draw(
            frame,
            fps,
            system_state.get("cpu"),
            system_state.get("temp")
        )

        return frame


overlay = Overlay()