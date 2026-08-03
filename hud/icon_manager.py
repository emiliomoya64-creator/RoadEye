from __future__ import annotations

import logging
from pathlib import Path
from threading import RLock
from typing import Optional

import cv2
import numpy as np


logger = logging.getLogger(__name__)


PROJECT_DIR = Path(__file__).resolve().parent.parent
ICONS_DIR = PROJECT_DIR / "hud" / "icons"


class IconManager:
    """
    Gestor central de iconos PNG para el HUD.

    Características:

    - Carga cada icono una sola vez.
    - Conserva el canal alfa.
    - Redimensiona los iconos según el tamaño solicitado.
    - Mantiene una caché de versiones redimensionadas.
    - Permite aplicar opacidad.
    - Permite colorear iconos mediante una máscara opcional.
    """

    def __init__(self) -> None:
        self._originals: dict[str, np.ndarray] = {}
        self._resized: dict[
            tuple[str, int, int],
            np.ndarray,
        ] = {}

        self._lock = RLock()

    # ---------------------------------------------------------
    # Información pública
    # ---------------------------------------------------------

    def exists(
        self,
        name: str,
    ) -> bool:
        return self._resolve_path(
            name
        ).exists()

    def draw_centered(
        self,
        frame: np.ndarray,
        name: str,
        center: tuple[int, int],
        size: int | tuple[int, int],
        *,
        opacity: float = 1.0,
        tint: Optional[
            tuple[int, int, int]
        ] = None,
    ) -> bool:
        """
        Dibuja un icono centrado sobre el frame.

        tint debe estar expresado en BGR, como OpenCV.
        """

        width, height = self._normalize_size(
            size
        )

        icon = self.get(
            name,
            width=width,
            height=height,
            tint=tint,
        )

        if icon is None:
            return False

        center_x, center_y = center

        x = int(
            center_x - width // 2
        )

        y = int(
            center_y - height // 2
        )

        return self.draw(
            frame,
            icon,
            x=x,
            y=y,
            opacity=opacity,
        )

    def get(
        self,
        name: str,
        *,
        width: int,
        height: int,
        tint: Optional[
            tuple[int, int, int]
        ] = None,
    ) -> Optional[np.ndarray]:
        """
        Obtiene un icono BGRA ya redimensionado.
        """

        normalized_name = self._normalize_name(
            name
        )

        width = max(
            1,
            int(width),
        )

        height = max(
            1,
            int(height),
        )

        cache_key = (
            normalized_name,
            width,
            height,
        )

        with self._lock:
            resized = self._resized.get(
                cache_key
            )

            if resized is None:
                original = self._load_original(
                    normalized_name
                )

                if original is None:
                    return None

                interpolation = (
                    cv2.INTER_AREA
                    if width <= original.shape[1]
                    and height <= original.shape[0]
                    else cv2.INTER_CUBIC
                )

                resized = cv2.resize(
                    original,
                    (
                        width,
                        height,
                    ),
                    interpolation=interpolation,
                )

                self._resized[
                    cache_key
                ] = resized

            result = resized.copy()

        if tint is not None:
            result = self._apply_tint(
                result,
                tint,
            )

        return result

    def draw(
        self,
        frame: np.ndarray,
        icon: np.ndarray,
        *,
        x: int,
        y: int,
        opacity: float = 1.0,
    ) -> bool:
        """
        Mezcla un icono BGRA sobre un frame BGR.
        """

        if frame is None or icon is None:
            return False

        if frame.ndim != 3:
            return False

        if icon.ndim != 3:
            return False

        if icon.shape[2] != 4:
            return False

        frame_height, frame_width = (
            frame.shape[:2]
        )

        icon_height, icon_width = (
            icon.shape[:2]
        )

        destination_x1 = max(
            0,
            int(x),
        )

        destination_y1 = max(
            0,
            int(y),
        )

        destination_x2 = min(
            frame_width,
            int(x) + icon_width,
        )

        destination_y2 = min(
            frame_height,
            int(y) + icon_height,
        )

        if (
            destination_x1 >= destination_x2
            or destination_y1 >= destination_y2
        ):
            return False

        source_x1 = (
            destination_x1
            - int(x)
        )

        source_y1 = (
            destination_y1
            - int(y)
        )

        source_x2 = (
            source_x1
            + destination_x2
            - destination_x1
        )

        source_y2 = (
            source_y1
            + destination_y2
            - destination_y1
        )

        icon_region = icon[
            source_y1:source_y2,
            source_x1:source_x2,
        ]

        frame_region = frame[
            destination_y1:destination_y2,
            destination_x1:destination_x2,
        ]

        alpha = (
            icon_region[:, :, 3:4].astype(
                np.float32
            )
            / 255.0
        )

        alpha *= max(
            0.0,
            min(
                1.0,
                float(opacity),
            ),
        )

        icon_bgr = icon_region[
            :,
            :,
            :3,
        ].astype(
            np.float32
        )

        frame_bgr = frame_region.astype(
            np.float32
        )

        blended = (
            icon_bgr * alpha
            + frame_bgr * (1.0 - alpha)
        )

        frame_region[:] = np.clip(
            blended,
            0,
            255,
        ).astype(
            np.uint8
        )

        return True

    def clear_cache(self) -> None:
        with self._lock:
            self._originals.clear()
            self._resized.clear()

    # ---------------------------------------------------------
    # Carga
    # ---------------------------------------------------------

    def _load_original(
        self,
        normalized_name: str,
    ) -> Optional[np.ndarray]:
        cached = self._originals.get(
            normalized_name
        )

        if cached is not None:
            return cached

        path = self._resolve_path(
            normalized_name
        )

        if not path.exists():
            logger.warning(
                "No existe el icono HUD: %s",
                path,
            )
            return None

        image = cv2.imread(
            str(path),
            cv2.IMREAD_UNCHANGED,
        )

        if image is None:
            logger.warning(
                "No se pudo cargar el icono: %s",
                path,
            )
            return None

        image = self._ensure_bgra(
            image
        )

        self._originals[
            normalized_name
        ] = image

        return image

    @staticmethod
    def _ensure_bgra(
        image: np.ndarray,
    ) -> np.ndarray:
        if image.ndim == 2:
            return cv2.cvtColor(
                image,
                cv2.COLOR_GRAY2BGRA,
            )

        channels = image.shape[2]

        if channels == 4:
            return image

        if channels == 3:
            return cv2.cvtColor(
                image,
                cv2.COLOR_BGR2BGRA,
            )

        raise ValueError(
            "Formato de icono no compatible"
        )

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    @staticmethod
    def _apply_tint(
        icon: np.ndarray,
        tint: tuple[int, int, int],
    ) -> np.ndarray:
        """
        Conserva la transparencia y utiliza el brillo original
        como intensidad del color seleccionado.
        """

        blue, green, red = (
            max(
                0,
                min(
                    255,
                    int(channel),
                ),
            )
            for channel in tint
        )

        alpha = icon[
            :,
            :,
            3,
        ].copy()

        original_bgr = icon[
            :,
            :,
            :3,
        ]

        intensity = cv2.cvtColor(
            original_bgr,
            cv2.COLOR_BGR2GRAY,
        ).astype(
            np.float32
        )

        intensity = (
            intensity / 255.0
        )[:, :, None]

        tint_array = np.array(
            [
                blue,
                green,
                red,
            ],
            dtype=np.float32,
        ).reshape(
            1,
            1,
            3,
        )

        tinted_bgr = (
            intensity
            * tint_array
        )

        result = np.empty_like(
            icon
        )

        result[
            :,
            :,
            :3,
        ] = np.clip(
            tinted_bgr,
            0,
            255,
        ).astype(
            np.uint8
        )

        result[
            :,
            :,
            3,
        ] = alpha

        return result

    @staticmethod
    def _normalize_size(
        size: int | tuple[int, int],
    ) -> tuple[int, int]:
        if isinstance(
            size,
            tuple,
        ):
            width, height = size

            return (
                max(
                    1,
                    int(width),
                ),
                max(
                    1,
                    int(height),
                ),
            )

        normalized = max(
            1,
            int(size),
        )

        return (
            normalized,
            normalized,
        )

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        normalized = str(
            name
        ).strip()

        if not normalized.lower().endswith(
            ".png"
        ):
            normalized += ".png"

        return normalized

    @staticmethod
    def _resolve_path(
        name: str,
    ) -> Path:
        normalized = str(
            name
        ).strip()

        if not normalized.lower().endswith(
            ".png"
        ):
            normalized += ".png"

        return (
            ICONS_DIR
            / normalized
        )


icons = IconManager()
