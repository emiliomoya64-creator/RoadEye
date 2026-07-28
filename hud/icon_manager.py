import os
import cv2


class IconManager:

    def __init__(self):

        self.icons = {}

    # -------------------------------------------------

    def load_folder(self, folder):

        if not os.path.isdir(folder):
            print(f"⚠ Carpeta de iconos no encontrada: {folder}")
            return

        for file in os.listdir(folder):

            if not file.lower().endswith(".png"):
                continue

            path = os.path.join(folder, file)

            img = cv2.imread(
                path,
                cv2.IMREAD_UNCHANGED
            )

            if img is None:
                continue

            name = os.path.splitext(file)[0]

            self.icons[name] = img

            print(f"🖼 Icono cargado: {name}")

    # -------------------------------------------------

    def get(self, name):

        return self.icons.get(name)

    # -------------------------------------------------

    def has(self, name):

        return name in self.icons


icons = IconManager()