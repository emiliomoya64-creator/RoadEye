import time

import cv2

from hud.hud_engine import hud
from hud.layout import Layout


class SpeedWidget:
    """
    Widget de velocidad y límite de la vía.

    Colores:
    - Blanco: velocidad normal.
    - Amarillo: cerca del límite.
    - Rojo: exceso de velocidad.
    - Rojo intermitente: exceso de 10 km/h o más.
    """

    BLINK_INTERVAL = 0.45
    WARNING_MARGIN = 5
    SERIOUS_EXCESS = 10

    COLOR_NORMAL = (245, 245, 245)
    COLOR_WARNING = (0, 220, 255)
    COLOR_DANGER = (0, 0, 255)
    COLOR_DANGER_OFF = (120, 120, 120)

    def __init__(self):
        self.blink_visible = True
        self.last_blink_time = time.monotonic()

    def draw(self, frame, speed, speed_limit):
        speed = self._safe_int(speed)
        speed_limit = self._safe_int(speed_limit)

        self._update_blink(
            speed=speed,
            speed_limit=speed_limit,
        )

        speed_color = self._get_speed_color(
            speed=speed,
            speed_limit=speed_limit,
        )

        self._draw_speed(
            frame=frame,
            speed=speed,
            color=speed_color,
        )

        self._draw_unit(frame)

        if speed_limit > 0:
            self._draw_speed_limit(
                frame=frame,
                speed_limit=speed_limit,
            )

    # -------------------------------------------------
    # Velocidad
    # -------------------------------------------------

    def _draw_speed(self, frame, speed, color):
        """
        Centra el número de velocidad respecto a Layout.SPEED.
        """

        text = str(max(0, speed))

        font = cv2.FONT_HERSHEY_DUPLEX
        font_scale = max(0.35, 1.55 * Layout.S)
        thickness = max(1, int(4 * Layout.S))

        (text_width, text_height), _ = cv2.getTextSize(
            text,
            font,
            font_scale,
            thickness,
        )

        center_x = Layout.SPEED[0]
        baseline_y = Layout.SPEED[1]

        text_x = center_x - text_width // 2
        text_y = baseline_y

        shadow_offset = hud.scale(3)

        cv2.putText(
            frame,
            text,
            (
                text_x + shadow_offset,
                text_y + shadow_offset,
            ),
            font,
            font_scale,
            (0, 0, 0),
            thickness + 2,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    def _draw_unit(self, frame):
        hud.shadow_text(
            frame,
            "km/h",
            (
                Layout.SPEED[0] - hud.scale(29),
                Layout.SPEED[1] + hud.scale(30),
            ),
            scale=0.48,
            thickness=1,
            color=(220, 220, 220),
        )

    # -------------------------------------------------
    # Señal de límite
    # -------------------------------------------------

    def _draw_speed_limit(self, frame, speed_limit):
        hud.speed_sign(
            frame,
            Layout.SPEED_SIGN[0],
            Layout.SPEED_SIGN[1],
            speed_limit,
        )

    # -------------------------------------------------
    # Color inteligente
    # -------------------------------------------------

    def _get_speed_color(self, speed, speed_limit):
        if speed_limit <= 0:
            return self.COLOR_NORMAL

        difference = speed - speed_limit

        if difference >= self.SERIOUS_EXCESS:
            if self.blink_visible:
                return self.COLOR_DANGER

            return self.COLOR_DANGER_OFF

        if difference > 0:
            return self.COLOR_DANGER

        if speed >= speed_limit - self.WARNING_MARGIN:
            return self.COLOR_WARNING

        return self.COLOR_NORMAL

    # -------------------------------------------------
    # Parpadeo
    # -------------------------------------------------

    def _update_blink(self, speed, speed_limit):
        serious_excess = (
            speed_limit > 0
            and speed >= speed_limit + self.SERIOUS_EXCESS
        )

        if not serious_excess:
            self.blink_visible = True
            self.last_blink_time = time.monotonic()
            return

        now = time.monotonic()

        if now - self.last_blink_time >= self.BLINK_INTERVAL:
            self.blink_visible = not self.blink_visible
            self.last_blink_time = now

    # -------------------------------------------------
    # Utilidades
    # -------------------------------------------------

    @staticmethod
    def _safe_int(value):
        try:
            return max(
                0,
                int(round(float(value))),
            )
        except (TypeError, ValueError):
            return 0


speed_widget = SpeedWidget()