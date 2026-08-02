from threading import Lock
from typing import Optional

import numpy as np


class DisplayBuffer:
    """
    Almacena el último frame procesado de RoadEye.

    Este frame ya puede contener:

    - HUD.
    - Información GPS.
    - Alertas ADAS.
    - Detecciones.
    - Cualquier otra capa visual.

    Los consumidores, como el servidor web y la salida HDMI,
    leen exactamente la misma imagen.
    """

    def __init__(self):
        self._lock = Lock()
        self._frame: Optional[np.ndarray] = None
        self._frame_number = 0

    def set_frame(self, frame: np.ndarray) -> None:
        """
        Guarda una copia del último frame renderizado.
        """

        if frame is None:
            return

        with self._lock:
            self._frame = frame.copy()
            self._frame_number += 1

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Devuelve una copia del último frame renderizado.
        """

        with self._lock:
            if self._frame is None:
                return None

            return self._frame.copy()

    def get_frame_number(self) -> int:
        """
        Devuelve el número de frames renderizados.
        """

        with self._lock:
            return self._frame_number

    def clear(self) -> None:
        """
        Vacía el buffer.
        """

        with self._lock:
            self._frame = None
            self._frame_number = 0


display_buffer = DisplayBuffer()