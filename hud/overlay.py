import datetime

from core.system_state import system_state
from hud.hud_engine import hud
from hud.layout import Layout
from hud.widgets.gps import gps_widget
from hud.widgets.rec import rec_widget


class HUDOverlay:
    """
    Compone las diferentes partes del HUD sobre el frame.

    Widgets ya independizados:
    - Grabación.
    - GPS.

    El resto se migrará progresivamente.
    """

    def draw(self, frame):
        # Actualizar dimensiones y escala.
        Layout.update(frame)

        # Fondos superior e inferior.
        hud.draw_top_bar(frame)
        hud.draw_bottom_bar(frame)

        # Fecha y hora.
        self._draw_datetime(frame)

        # Grabación.
        rec_widget.draw(
            frame,
            recording=bool(
                getattr(system_state, "recording", False)
            ),
        )

        # GPS.
        gps_widget.draw(
            frame,
            gps_fix=bool(
                getattr(system_state, "gps_fix", False)
            ),
            satellites=getattr(
                system_state,
                "satellites",
                0,
            ),
        )

        # Elementos todavía integrados.
        self._draw_speed(frame)
        self._draw_speed_limit(frame)
        self._draw_road(frame)

        return frame

    # -------------------------------------------------
    # Fecha y hora
    # -------------------------------------------------

    def _draw_datetime(self, frame):
        now = datetime.datetime.now()

        hud.shadow_text(
            frame,
            now.strftime("%d/%m/%Y   %H:%M:%S"),
            Layout.DATE,
            scale=0.65,
        )

    # -------------------------------------------------
    # Velocidad
    # -------------------------------------------------

    def _draw_speed(self, frame):
        speed = self._safe_int(
            getattr(system_state, "speed", 0)
        )

        hud.shadow_text(
            frame,
            str(max(0, speed)),
            Layout.SPEED,
            scale=1.15,
            thickness=3,
        )

        hud.shadow_text(
            frame,
            "km/h",
            (
                Layout.SPEED[0] + hud.scale(70),
                Layout.SPEED[1] + hud.scale(3),
            ),
            scale=0.55,
        )

    # -------------------------------------------------
    # Límite de velocidad
    # -------------------------------------------------

    def _draw_speed_limit(self, frame):
        speed_limit = self._safe_int(
            getattr(system_state, "speed_limit", 0)
        )

        if speed_limit <= 0:
            return

        hud.speed_sign(
            frame,
            Layout.SPEED_SIGN[0],
            Layout.SPEED_SIGN[1],
            speed_limit,
        )

    # -------------------------------------------------
    # Información de carretera
    # -------------------------------------------------

    def _draw_road(self, frame):
        road = (
            getattr(system_state, "road", "---")
            or "---"
        )

        road_type = (
            getattr(system_state, "road_type", "---")
            or "---"
        )

        lanes = (
            getattr(system_state, "lanes", "?")
            or "?"
        )

        hud.shadow_text(
            frame,
            road,
            Layout.ROAD,
            scale=0.75,
        )

        hud.shadow_text(
            frame,
            f"{road_type} · {self._format_lanes(lanes)}",
            Layout.ROAD_INFO,
            scale=0.55,
            color=(210, 210, 210),
        )

    # -------------------------------------------------
    # Utilidades
    # -------------------------------------------------

    @staticmethod
    def _safe_int(value):
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _format_lanes(lanes):
        try:
            lanes_number = int(lanes)

            if lanes_number == 1:
                return "1 carril"

            return f"{lanes_number} carriles"

        except (TypeError, ValueError):
            return f"{lanes} carriles"


overlay = HUDOverlay()