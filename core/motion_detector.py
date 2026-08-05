from __future__ import annotations

import cv2
import numpy as np


class MotionDetector:
    """
    Detector visual ligero para RoadEye Sentinel.

    Reduce la imagen antes de comparar para limitar el consumo de CPU.
    """

    def __init__(
        self,
        sensitivity: float = 0.55,
    ) -> None:
        self._previous = None
        self.set_sensitivity(
            sensitivity
        )

    def set_sensitivity(
        self,
        sensitivity: float,
    ) -> None:
        value = max(
            0.05,
            min(
                1.0,
                float(sensitivity),
            ),
        )

        self.sensitivity = value

        # Sensibilidad alta:
        # menor área necesaria para detectar movimiento.
        self.minimum_ratio = (
            0.075
            - value * 0.065
        )

        self.pixel_threshold = int(
            42 - value * 22
        )

    def reset(self) -> None:
        self._previous = None

    def detect(
        self,
        frame,
    ) -> dict:
        if frame is None:
            return {
                "motion": False,
                "ratio": 0.0,
            }

        small = cv2.resize(
            frame,
            (320, 180),
            interpolation=cv2.INTER_AREA,
        )

        gray = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2GRAY,
        )

        gray = cv2.GaussianBlur(
            gray,
            (9, 9),
            0,
        )

        previous = self._previous
        self._previous = gray

        if previous is None:
            return {
                "motion": False,
                "ratio": 0.0,
            }

        difference = cv2.absdiff(
            previous,
            gray,
        )

        _, threshold = cv2.threshold(
            difference,
            self.pixel_threshold,
            255,
            cv2.THRESH_BINARY,
        )

        threshold = cv2.dilate(
            threshold,
            None,
            iterations=2,
        )

        changed = int(
            cv2.countNonZero(
                threshold
            )
        )

        ratio = (
            changed
            / float(
                threshold.shape[0]
                * threshold.shape[1]
            )
        )

        return {
            "motion": bool(
                ratio >= self.minimum_ratio
            ),
            "ratio": round(
                ratio,
                5,
            ),
        }
