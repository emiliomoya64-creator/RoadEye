import os
import cv2
import numpy as np


class IconManager:

    def __init__(self):

        self.cache = {}

        self.icons_path = os.path.join(
            os.path.dirname(__file__),
            "icons"
        )

    def load(self, name):

        if name in self.cache:
            return self.cache[name]

        filename = os.path.join(
            self.icons_path,
            f"{name}.png"
        )

        if not os.path.exists(filename):

            print(f"⚠ Icono no encontrado: {filename}")
            return None

        icon = cv2.imread(
            filename,
            cv2.IMREAD_UNCHANGED
        )

        if icon is None:

            print(f"⚠ No se pudo cargar {filename}")
            return None

        self.cache[name] = icon

        return icon

    def draw(
        self,
        frame,
        name,
        x,
        y,
        size=32,
        color=None
    ):

        icon = self.load(name)

        if icon is None:
            return

        icon = cv2.resize(
            icon,
            (size, size),
            interpolation=cv2.INTER_AREA
        )

        h, w = icon.shape[:2]

        if (
            y + h > frame.shape[0]
            or
            x + w > frame.shape[1]
        ):
            return

        # Si el PNG no tiene canal alpha
        if icon.shape[2] == 3:

            alpha = np.ones((h, w), dtype=np.float32)

            rgb = icon

        else:

            alpha = icon[:, :, 3].astype(np.float32) / 255.0
            rgb = icon[:, :, :3]

        # Cambiar color manteniendo el alpha
        if color is not None:

            rgb = np.zeros_like(rgb)

            rgb[:, :, 0] = color[0]
            rgb[:, :, 1] = color[1]
            rgb[:, :, 2] = color[2]

        roi = frame[y:y+h, x:x+w]

        alpha = alpha[:, :, np.newaxis]

        roi[:] = (
            alpha * rgb +
            (1 - alpha) * roi
        ).astype(np.uint8)


icon = IconManager()