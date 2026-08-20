import cv2
import datetime
import numpy as np

from core.config_manager import config
from hud.layout import Layout


class HUDEngine:

    # ----------------------------------------------------

    def font_face(self):
        name = str(
            config.get(
                "hud.font",
                "duplex",
            )
        ).strip().lower()

        fonts = {
            "simplex":
                cv2.FONT_HERSHEY_SIMPLEX,

            "duplex":
                cv2.FONT_HERSHEY_DUPLEX,

            "triplex":
                cv2.FONT_HERSHEY_TRIPLEX,

            "complex":
                cv2.FONT_HERSHEY_COMPLEX,

            "plain":
                cv2.FONT_HERSHEY_PLAIN,

            "complex_small":
                cv2.FONT_HERSHEY_COMPLEX_SMALL,

            "script":
                cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,

            "script_complex":
                cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
        }

        return fonts.get(
            name,
            cv2.FONT_HERSHEY_DUPLEX,
        )

    def display_mode(self):
        mode = str(
            config.get(
                "hud.mode",
                "auto",
            )
        ).strip().lower()

        if mode in {"day", "night"}:
            return mode

        hour = datetime.datetime.now().hour

        return (
            "day"
            if 7 <= hour < 20
            else "night"
        )

    def _brightness_factor(self):
        return (
            1.0
            if self.display_mode() == "day"
            else 0.62
        )

    def bar_color(self):
        name = str(
            config.get(
                "hud.bar_color",
                "black",
            )
        ).strip().lower()

        if name == "white":
            return (
                245,
                245,
                245,
            )

        return (
            15,
            15,
            15,
        )

    def primary_color(self):
        name = str(
            config.get(
                "hud.color",
                "white",
            )
        ).strip().lower()

        colors = {
            "white": (255, 255, 255),
            "green": (120, 255, 120),
            "amber": (0, 190, 255),
            "ice_blue": (255, 220, 160),
            "red": (90, 90, 255),
        }

        base = colors.get(
            name,
            colors["white"],
        )

        factor = self._brightness_factor()

        return tuple(
            max(
                0,
                min(
                    255,
                    int(channel * factor),
                ),
            )
            for channel in base
        )

    def muted_color(self):
        return tuple(
            int(channel * 0.62)
            for channel in self.primary_color()
        )

    def scale(self, value):
        return max(1, int(value * Layout.S))

    def text_factor(self):
        factor = float(
            config.get(
                "hud.text_scale",
                1.0,
            )
        )

        return max(
            0.80,
            min(
                2.00,
                factor,
            ),
        )

    def icon_scale(self, value):
        factor = float(
            config.get(
                "hud.icon_scale",
                1.0,
            )
        )

        factor = max(
            0.80,
            min(
                2.00,
                factor,
            ),
        )

        return max(
            1,
            int(
                value
                * Layout.S
                * factor
            ),
        )

    # ----------------------------------------------------

    def shadow_text(
        self,
        frame,
        text,
        pos,
        scale=0.7,
        color=(255, 255, 255),
        thickness=2,
        shadow=(0, 0, 0),
        font=None,
    ):

        x, y = pos

        if font is None:
            font = self.font_face()

        if color == (255, 255, 255):
            color = self.primary_color()

        scale *= (
            Layout.S
            * self.text_factor()
        )
        thickness = max(1, int(thickness * Layout.S))

        cv2.putText(
            frame,
            text,
            (x, y),
            font,
            scale,
            color,
            thickness,
            cv2.LINE_AA
        )

    # ----------------------------------------------------

    def filled_circle(
        self,
        frame,
        center,
        radius,
        color,
    ):

        cv2.circle(
            frame,
            center,
            self.icon_scale(radius),
            color,
            -1,
            cv2.LINE_AA
        )

    # ----------------------------------------------------

    def outlined_circle(
        self,
        frame,
        center,
        radius,
        fill,
        border,
        border_size=4,
    ):

        radius = self.icon_scale(radius)
        border_size = self.icon_scale(border_size)

        cv2.circle(
            frame,
            center,
            radius,
            border,
            -1,
            cv2.LINE_AA
        )

        cv2.circle(
            frame,
            center,
            radius - border_size,
            fill,
            -1,
            cv2.LINE_AA
        )

    # ----------------------------------------------------

    def rounded_rect(
        self,
        frame,
        *,
        x,
        y,
        w,
        h,
        radius=18,
        color=(10, 13, 15),
        alpha=0.65,
    ):
        """
        Rectángulo semitransparente con
        esquinas redondeadas.
        """

        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)

        radius = int(
            max(
                1,
                min(
                    radius,
                    w // 2,
                    h // 2,
                ),
            )
        )

        overlay = frame.copy()

        x2 = x + w
        y2 = y + h

        cv2.rectangle(
            overlay,
            (x + radius, y),
            (x2 - radius, y2),
            color,
            -1,
            cv2.LINE_AA,
        )

        cv2.rectangle(
            overlay,
            (x, y + radius),
            (x2, y2 - radius),
            color,
            -1,
            cv2.LINE_AA,
        )

        cv2.circle(
            overlay,
            (x + radius, y + radius),
            radius,
            color,
            -1,
            cv2.LINE_AA,
        )

        cv2.circle(
            overlay,
            (x2 - radius, y + radius),
            radius,
            color,
            -1,
            cv2.LINE_AA,
        )

        cv2.circle(
            overlay,
            (x + radius, y2 - radius),
            radius,
            color,
            -1,
            cv2.LINE_AA,
        )

        cv2.circle(
            overlay,
            (x2 - radius, y2 - radius),
            radius,
            color,
            -1,
            cv2.LINE_AA,
        )

        cv2.addWeighted(
            overlay,
            max(
                0.0,
                min(
                    1.0,
                    float(alpha),
                ),
            ),
            frame,
            1.0 - max(
                0.0,
                min(
                    1.0,
                    float(alpha),
                ),
            ),
            0,
            frame,
        )



    def transparent_rect(
        self,
        frame,
        x,
        y,
        w,
        h,
        color=(20,20,20),
        alpha=0.45,
    ):

        overlay = frame.copy()

        cv2.rectangle(
            overlay,
            (x, y),
            (x + w, y + h),
            color,
            -1
        )

        cv2.addWeighted(
            overlay,
            alpha,
            frame,
            1-alpha,
            0,
            frame
        )

    # ----------------------------------------------------

    def draw_top_bar(self, frame):

        self.transparent_rect(
            frame,
            0,
            0,
            Layout.W,
            Layout.TOP_BAR,
            self.bar_color(),
            0.45
        )

    # ----------------------------------------------------

    def draw_bottom_bar(self, frame):

        self.transparent_rect(
            frame,
            0,
            Layout.H - Layout.BOTTOM_BAR,
            Layout.W,
            Layout.BOTTOM_BAR,
            self.bar_color(),
            0.45
        )

    # ----------------------------------------------------

    def speed_sign(
        self,
        frame,
        x,
        y,
        limit,
    ):

        if limit <= 0:
            return

        self.outlined_circle(
            frame,
            (x, y),
            28,
            (255,255,255),
            (0,0,255),
            5
        )

        self.shadow_text(
            frame,
            str(limit),
            (
                x - self.scale(13),
                y + self.scale(8)
            ),
            scale=0.75,
            color=(0,0,0),
            thickness=2,
            shadow=(255,255,255)
        )

    # ----------------------------------------------------

    def gps_bars(
        self,
        frame,
        x,
        y,
        satellites,
    ):

        barras = min(4, max(0, satellites // 3))

        for i in range(4):

            h = self.icon_scale(6 + i * 6)

            color = (
                (0,255,0)
                if i < barras
                else
                (70,70,70)
            )

            cv2.rectangle(
                frame,
                (
                    x + self.icon_scale(i * 9),
                    y - h
                ),
                (
                    x + self.icon_scale(i * 9 + 6),
                    y
                ),
                color,
                -1
            )


hud = HUDEngine()