import cv2

from hud.hud_engine import hud
from hud.layout import Layout


class GPSWidget:
    """
    Widget visual del GPS.

    Muestra:
    - Cuatro barras de señal.
    - Estado GPS.
    - Número de satélites.

    Verde:
        GPS con posición válida.

    Gris:
        GPS sin posición válida.
    """

    MAX_BARS = 4

    def draw(self, frame, gps_fix, satellites):
        gps_fix = bool(gps_fix)
        satellites = self._safe_int(satellites)

        x, y = Layout.GPS

        self._draw_bars(
            frame=frame,
            x=x,
            y=y,
            gps_fix=gps_fix,
            satellites=satellites,
        )

        separator_x = x + hud.scale(88)

        self._draw_separator(
            frame=frame,
            x=separator_x,
            y=y,
        )

        self._draw_text(
            frame=frame,
            x=separator_x + hud.scale(22),
            y=y,
            gps_fix=gps_fix,
            satellites=satellites,
        )

    # -------------------------------------------------
    # Barras de señal
    # -------------------------------------------------

    def _draw_bars(
        self,
        frame,
        x,
        y,
        gps_fix,
        satellites,
    ):
        active_bars = self._active_bars(
            gps_fix,
            satellites,
        )

        bar_width = hud.scale(11)
        bar_gap = hud.scale(9)

        for index in range(self.MAX_BARS):
            height = hud.scale(13 + index * 10)

            x1 = x + index * (bar_width + bar_gap)
            y1 = y - height
            x2 = x1 + bar_width
            y2 = y

            color = (
                (0, 210, 0)
                if index < active_bars
                else (70, 70, 70)
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
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
                y - hud.scale(45),
            ),
            (
                x,
                y + hud.scale(9),
            ),
            (105, 105, 105),
            max(1, hud.scale(2)),
            cv2.LINE_AA,
        )

    # -------------------------------------------------
    # Texto
    # -------------------------------------------------

    def _draw_text(
        self,
        frame,
        x,
        y,
        gps_fix,
        satellites,
    ):
        title_color = (
            (245, 245, 245)
            if gps_fix
            else (145, 145, 145)
        )

        hud.shadow_text(
            frame,
            "GPS",
            (
                x,
                y - hud.scale(13),
            ),
            scale=0.60,
            thickness=2,
            color=title_color,
        )

        status_text = (
            f"{satellites} SAT"
            if gps_fix
            else "SIN FIJAR"
        )

        status_color = (
            (205, 205, 205)
            if gps_fix
            else (120, 120, 120)
        )

        hud.shadow_text(
            frame,
            status_text,
            (
                x,
                y + hud.scale(14),
            ),
            scale=0.43,
            thickness=1,
            color=status_color,
        )

    # -------------------------------------------------
    # Intensidad según satélites
    # -------------------------------------------------

    @staticmethod
    def _active_bars(gps_fix, satellites):
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
            return max(
                0,
                int(round(float(value))),
            )
        except (TypeError, ValueError):
            return 0


gps_widget = GPSWidget()