import cv2
import numpy as np


class HUDEngine:

    def shadow_text(
        self,
        frame,
        text,
        pos,
        scale=0.7,
        color=(255, 255, 255),
        thickness=2,
        shadow=(0, 0, 0),
        font=cv2.FONT_HERSHEY_DUPLEX,
    ):

        x, y = pos

        cv2.putText(
            frame,
            text,
            (x + 2, y + 2),
            font,
            scale,
            shadow,
            thickness + 2,
            cv2.LINE_AA
        )

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
            radius,
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

    def transparent_rect(
        self,
        frame,
        x,
        y,
        w,
        h,
        color=(20, 20, 20),
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
            1 - alpha,
            0,
            frame
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
            (255, 255, 255),
            (0, 0, 255),
            5
        )

        self.shadow_text(
            frame,
            str(limit),
            (x - 13, y + 8),
            0.75,
            (0, 0, 0),
            2,
            (255, 255, 255)
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

            h = 6 + i * 6

            color = (
                (0, 255, 0)
                if i < barras
                else
                (70, 70, 70)
            )

            cv2.rectangle(
                frame,
                (x + i * 9, y - h),
                (x + i * 9 + 6, y),
                color,
                -1
            )


hud = HUDEngine()