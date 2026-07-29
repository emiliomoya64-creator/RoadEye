import datetime

from core.system_state import system_state
from hud.hud_engine import hud
from hud.layout import Layout


class HUDOverlay:

    def draw(self, frame):

        # Fecha y hora
        ahora = datetime.datetime.now()

        hud.shadow_text(
            frame,
            ahora.strftime("%d/%m/%Y   %H:%M:%S"),
            Layout.DATE,
            scale=0.65,
        )

        # -----------------------------
        # REC
        # -----------------------------

        color = (0, 0, 255) if system_state.recording else (90, 90, 90)

        hud.filled_circle(
            frame,
            Layout.REC,
            8,
            color,
        )

        hud.shadow_text(
            frame,
            "REC",
            (Layout.REC[0] + 18, Layout.REC[1] + 6),
            scale=0.65,
        )


overlay = HUDOverlay()