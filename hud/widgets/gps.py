import cv2

from config import (
    COLOR_WHITE,
    COLOR_GREEN,
)

from hud.icon import icon


class GPSWidget:

    def draw(self, frame, gps_fix, satellites):

        # --------------------------
        # Icono GPS
        # --------------------------

        color = COLOR_GREEN if gps_fix else (120, 120, 120)

        icon.draw(
            frame,
            "gps_satellite",
            20,
            42,
            size=22,
            color=color
        )

        # --------------------------
        # Texto
        # --------------------------

        if gps_fix:
            texto = f"{satellites} SAT"
        else:
            texto = "SIN GPS"

        cv2.putText(
            frame,
            texto,
            (50, 60),
            cv2.FONT_HERSHEY_DUPLEX,
            0.60,
            COLOR_WHITE,
            2
        )


gps_widget = GPSWidget()