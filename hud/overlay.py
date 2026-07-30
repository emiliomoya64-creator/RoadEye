import datetime

from core.system_state import system_state
from hud.hud_engine import hud
from hud.layout import Layout


class HUDOverlay:

    def draw(self, frame):

        # ==========================================
        # Actualizar el layout según la resolución
        # ==========================================

        Layout.update(frame)

        # ==========================================
        # Barras superior e inferior
        # ==========================================

        hud.draw_top_bar(frame)
        hud.draw_bottom_bar(frame)

        # ==========================================
        # Fecha y hora
        # ==========================================

        ahora = datetime.datetime.now()

        hud.shadow_text(
            frame,
            ahora.strftime("%d/%m/%Y   %H:%M:%S"),
            Layout.DATE,
            scale=0.65,
        )

        # ==========================================
        # REC
        # ==========================================

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

        # ==========================================
        # GPS
        # ==========================================

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

        # ==========================================
        # VELOCIDAD
        # ==========================================

        velocidad = int(system_state.speed)

        hud.shadow_text(
            frame,
            str(velocidad),
            Layout.SPEED,
            scale=1.15,
            thickness=3,
        )

        hud.shadow_text(
            frame,
            "km/h",
            (Layout.SPEED[0] + 70, Layout.SPEED[1] + 3),
            scale=0.55,
        )

        # ==========================================
        # Límite de velocidad
        # ==========================================

        if system_state.speed_limit > 0:

            hud.speed_sign(
                frame,
                Layout.SPEED_SIGN[0],
                Layout.SPEED_SIGN[1],
                system_state.speed_limit,
            )

        # ==========================================
        # Carretera
        # ==========================================

        road = getattr(system_state, "road", "---")
        road_type = getattr(system_state, "highway", "---")
        lanes = getattr(system_state, "lanes", "?")

        hud.shadow_text(
            frame,
            road,
            Layout.ROAD,
            scale=0.75,
        )

        hud.shadow_text(
            frame,
            f"{road_type} · {lanes} carriles",
            Layout.ROAD_INFO,
            scale=0.55,
            color=(210, 210, 210),
        )


overlay = HUDOverlay()