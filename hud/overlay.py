import datetime

from core.system_state import system_state
from hud.hud_engine import hud
from hud.layout import Layout


class HUDOverlay:

    def draw(self, frame):

        # ---------------------------------
        # Fecha y hora
        # ---------------------------------

        ahora = datetime.datetime.now()

        hud.shadow_text(
            frame,
            ahora.strftime("%d/%m/%Y   %H:%M:%S"),
            Layout.DATE,
            scale=0.65,
        )

        # ---------------------------------
        # REC
        # ---------------------------------

        rec_color = (0, 0, 255) if system_state.recording else (90, 90, 90)

        hud.filled_circle(
            frame,
            Layout.REC,
            8,
            rec_color,
        )

        hud.shadow_text(
            frame,
            "REC",
            (Layout.REC[0] + 18, Layout.REC[1] + 6),
            scale=0.65,
        )

        # ---------------------------------
        # GPS
        # ---------------------------------

        x, y = Layout.GPS

        hud.gps_bars(
            frame,
            x,
            y,
            system_state.satellites,
        )

        gps_color = (
            (255, 255, 255)
            if system_state.gps_fix
            else
            (140, 140, 140)
        )

        hud.shadow_text(
            frame,
            f"GPS {system_state.satellites}",
            (x + 45, y + 6),
            scale=0.65,
            color=gps_color,
        )

        # ---------------------------------
        # VELOCIDAD
        # ---------------------------------

        velocidad = int(system_state.speed)

        hud.shadow_text(
            frame,
            str(velocidad),
            Layout.SPEED,
            scale=2.0,
            thickness=4,
        )

        hud.shadow_text(
            frame,
            "km/h",
            (Layout.SPEED[0] + 95, Layout.SPEED[1] + 5),
            scale=0.75,
        )

        if system_state.speed_limit > 0:
            hud.speed_sign(
                frame,
                Layout.SPEED_SIGN[0],
                Layout.SPEED_SIGN[1],
                system_state.speed_limit,
            )


overlay = HUDOverlay()