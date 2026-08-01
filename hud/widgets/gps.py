import cv2

from hud.hud_engine import hud
from hud.layout import Layout


class GPSWidget:
    """
    Widget de estado GPS.

    Muestra:
    - Cuatro barras de intensidad.
    - Separador vertical.
    - Estado GPS.
    - Número de satélites.

    Colores:
    - Verde cuando existe posición GPS.
    - Gris cuando todavía no existe posición.
    """

    MAX_BARS = 4

    def draw(self, frame, gps_fix, satellites):
        gps_fix = bool(gps_fix)
        satellites = self._safe_int(satellites)

        x, y = Layout.GPS

        self._draw_signal_bars(
            frame,
            x,
            y,
            gps_fix,
            satellites,
        )

        separator_x = x + hud.scale(90)

        self._draw_separator(
            frame,
            separator_x,
            y,
        )

        self._draw_status(
            frame,
            separator_x,
            y,
            gps_fix,
            satellites,
        )

    # -------------------------------------------------
    # Barras de intensidad
    # -------------------------------------------------

    def _draw_signal_bars(
        self,
        frame,
        x,
        y,
        gps_fix,
        satellites,
    ):
        active_bars = self._calculate_active_bars(
            gps_fix,
            satellites,
        )

        bar_width = hud.scale(11)
        bar_gap = hud.scale(9)

        for index in range(self.MAX_BARS):
            bar_height = hud.scale(12 + index * 10)

            bar_x1 = x + index * (bar_width + bar_gap)
            bar_y1 = y - bar_height

            bar_x2 = bar_x1 + bar_width
            bar_y2 = y

            if index < active_bars:
                color = (0, 220, 0)
            else:
                color = (75, 75, 75)

            cv2.rectangle(
                frame,
                (bar_x1, bar_y1),
                (bar_x2, bar_y2),
                color,
                -1,
                cv2.LINE_AA,
            )

    # -------------------------------------------------
    # Separador
    # -------------------------------------------------

    def _draw_separator(self, frame, x, y):
        cv2.line(
            frame,
            (
                x,
                y - hud.scale(43),
            ),
            (
                x,
                y + hud.scale(8),
            ),
            (100, 100, 100),
            max(1, hud.scale(2)),
            cv2.LINE_AA,
        )

    # -------------------------------------------------
    # Texto GPS
    # -------------------------------------------------

    def _draw_status(
        self,
        frame,
        separator_x,
        y,
        gps_fix,
        satellites,
    ):
        text_x = separator_x + hud.scale(23)

        gps_color = (
            (245, 245, 245)
            if gps_fix
            else (145, 145, 145)
        )

        hud.shadow_text(
            frame,
            "GPS",
            (
                text_x,
                y - hud.scale(13),
            ),
            scale=0.61,
            thickness=2,
            color=gps_color,
        )

        if gps_fix:
            satellite_text = f"{satellites} SAT"
        else:
            satellite_text = "SIN FIJAR"

        hud.shadow_text(
            frame,
            satellite_text,
            (
                text_x,
                y + hud.scale(13),
            ),
            scale=0.42,
            thickness=1,
            color=(
                (205, 205, 205)
                if gps_fix
                else (120, 120, 120)
            ),
        )

    # -------------------------------------------------
    # Cálculo de cobertura
    # -------------------------------------------------

    @staticmethod
    def _calculate_active_bars(gps_fix, satellites):
        if not gps_fix or satellites <= 0:
            return 0

        if satellites <= 3:
            return 1

        if satellites <= 6:
            return 2

        if satellites <= 9:
            return 3

        return 4

    @staticmethod
    def _safe_int(value):
        try:
            return max(0, int(round(float(value))))
        except (TypeError, ValueError):
            return 0


gps_widget = GPSWidget()