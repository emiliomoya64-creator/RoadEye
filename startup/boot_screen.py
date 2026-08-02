from __future__ import annotations

import logging
import socket
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Optional

import cv2
import numpy as np


logger = logging.getLogger(__name__)


PROJECT_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = PROJECT_DIR / "VERSION"


class BootCheckState(str, Enum):
    """
    Estados visuales posibles de una comprobación.
    """

    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class BootCheck:
    """
    Información visual de una comprobación del arranque.
    """

    key: str
    label: str
    state: BootCheckState = BootCheckState.PENDING
    detail: str = ""


class BootScreen:
    """
    Generador de la pantalla de inicio de RoadEye.

    Esta clase solamente dibuja imágenes.

    No abre HDMI.
    No inicia servicios.
    No ejecuta diagnósticos.
    No modifica DisplayBuffer.

    BootManager será el encargado de coordinar esas operaciones.
    """

    COLOR_BACKGROUND = (12, 16, 18)
    COLOR_PANEL = (22, 29, 32)
    COLOR_PANEL_BORDER = (48, 65, 68)

    COLOR_WHITE = (240, 245, 245)
    COLOR_MUTED = (145, 160, 163)
    COLOR_GREEN = (70, 220, 120)
    COLOR_YELLOW = (0, 210, 255)
    COLOR_RED = (70, 70, 240)
    COLOR_BLUE = (230, 170, 60)

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
    ) -> None:
        self.width = max(
            640,
            int(width),
        )

        self.height = max(
            360,
            int(height),
        )

        self._lock = RLock()

        self._title = "ROAD EYE"
        self._subtitle = (
            "Professional Dashcam & ADAS Platform"
        )

        self._phase = "Inicializando sistema..."
        self._footer_message = ""

        self._version = self._read_version()
        self._ip_address = self._detect_ip_address()

        self._checks: list[BootCheck] = []

    # ---------------------------------------------------------
    # Información pública
    # ---------------------------------------------------------

    def set_phase(
        self,
        phase: str,
    ) -> None:
        with self._lock:
            self._phase = str(
                phase
            ).strip()

    def set_footer_message(
        self,
        message: str,
    ) -> None:
        with self._lock:
            self._footer_message = str(
                message
            ).strip()

    def set_checks(
        self,
        checks: list[BootCheck],
    ) -> None:
        with self._lock:
            self._checks = [
                BootCheck(
                    key=check.key,
                    label=check.label,
                    state=check.state,
                    detail=check.detail,
                )
                for check in checks
            ]

    def update_check(
        self,
        key: str,
        *,
        state: Optional[
            BootCheckState
        ] = None,
        detail: Optional[str] = None,
    ) -> bool:
        """
        Actualiza una comprobación por su identificador.
        """

        with self._lock:
            for check in self._checks:
                if check.key != key:
                    continue

                if state is not None:
                    check.state = state

                if detail is not None:
                    check.detail = str(
                        detail
                    ).strip()

                return True

        return False

    def render(self) -> np.ndarray:
        """
        Genera un frame BGR listo para OpenCV, DisplayBuffer o HDMI.
        """

        with self._lock:
            phase = self._phase
            footer_message = self._footer_message

            checks = [
                BootCheck(
                    key=check.key,
                    label=check.label,
                    state=check.state,
                    detail=check.detail,
                )
                for check in self._checks
            ]

        frame = np.full(
            (
                self.height,
                self.width,
                3,
            ),
            self.COLOR_BACKGROUND,
            dtype=np.uint8,
        )

        self._draw_background(
            frame
        )

        self._draw_header(
            frame,
            phase,
        )

        self._draw_checks_panel(
            frame,
            checks,
        )

        self._draw_footer(
            frame,
            footer_message,
        )

        return frame

    def save_preview(
        self,
        output_path: str | Path,
    ) -> Path:
        """
        Guarda una previsualización PNG.
        """

        path = Path(
            output_path
        ).expanduser().resolve()

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        frame = self.render()

        success = cv2.imwrite(
            str(path),
            frame,
        )

        if not success:
            raise RuntimeError(
                "OpenCV no pudo guardar la pantalla: "
                f"{path}"
            )

        return path

    # ---------------------------------------------------------
    # Dibujo
    # ---------------------------------------------------------

    def _draw_background(
        self,
        frame: np.ndarray,
    ) -> None:
        """
        Dibuja una carretera estilizada y discreta.
        """

        center_x = self.width // 2
        horizon_y = int(
            self.height * 0.18
        )

        bottom_y = self.height

        left_top = (
            center_x - 55,
            horizon_y,
        )

        right_top = (
            center_x + 55,
            horizon_y,
        )

        left_bottom = (
            int(
                self.width * 0.18
            ),
            bottom_y,
        )

        right_bottom = (
            int(
                self.width * 0.82
            ),
            bottom_y,
        )

        road_polygon = np.array(
            [
                left_top,
                right_top,
                right_bottom,
                left_bottom,
            ],
            dtype=np.int32,
        )

        overlay = frame.copy()

        cv2.fillConvexPoly(
            overlay,
            road_polygon,
            (
                18,
                23,
                25,
            ),
        )

        cv2.addWeighted(
            overlay,
            0.75,
            frame,
            0.25,
            0,
            frame,
        )

        self._draw_lane_markings(
            frame,
            center_x,
            horizon_y,
        )

    def _draw_lane_markings(
        self,
        frame: np.ndarray,
        center_x: int,
        horizon_y: int,
    ) -> None:
        segments = [
            (
                0.28,
                0.35,
                3,
            ),
            (
                0.42,
                0.52,
                5,
            ),
            (
                0.61,
                0.75,
                8,
            ),
            (
                0.84,
                1.00,
                12,
            ),
        ]

        available_height = (
            self.height
            - horizon_y
        )

        for start_ratio, end_ratio, thickness in segments:
            start_y = int(
                horizon_y
                + available_height
                * start_ratio
            )

            end_y = int(
                horizon_y
                + available_height
                * end_ratio
            )

            cv2.line(
                frame,
                (
                    center_x,
                    start_y,
                ),
                (
                    center_x,
                    end_y,
                ),
                (
                    55,
                    65,
                    67,
                ),
                thickness,
                cv2.LINE_AA,
            )

    def _draw_header(
        self,
        frame: np.ndarray,
        phase: str,
    ) -> None:
        title_scale = self._scale(
            2.0
        )

        subtitle_scale = self._scale(
            0.62
        )

        phase_scale = self._scale(
            0.70
        )

        title_size = cv2.getTextSize(
            self._title,
            cv2.FONT_HERSHEY_DUPLEX,
            title_scale,
            3,
        )[0]

        title_x = (
            self.width
            - title_size[0]
        ) // 2

        title_y = int(
            self.height * 0.12
        )

        cv2.putText(
            frame,
            self._title,
            (
                title_x,
                title_y,
            ),
            cv2.FONT_HERSHEY_DUPLEX,
            title_scale,
            self.COLOR_GREEN,
            3,
            cv2.LINE_AA,
        )

        subtitle_size = cv2.getTextSize(
            self._subtitle,
            cv2.FONT_HERSHEY_SIMPLEX,
            subtitle_scale,
            1,
        )[0]

        subtitle_x = (
            self.width
            - subtitle_size[0]
        ) // 2

        subtitle_y = (
            title_y
            + int(
                self.height * 0.055
            )
        )

        cv2.putText(
            frame,
            self._subtitle,
            (
                subtitle_x,
                subtitle_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            subtitle_scale,
            self.COLOR_MUTED,
            1,
            cv2.LINE_AA,
        )

        phase_size = cv2.getTextSize(
            phase,
            cv2.FONT_HERSHEY_DUPLEX,
            phase_scale,
            2,
        )[0]

        phase_x = (
            self.width
            - phase_size[0]
        ) // 2

        phase_y = (
            subtitle_y
            + int(
                self.height * 0.07
            )
        )

        cv2.putText(
            frame,
            phase,
            (
                phase_x,
                phase_y,
            ),
            cv2.FONT_HERSHEY_DUPLEX,
            phase_scale,
            self.COLOR_WHITE,
            2,
            cv2.LINE_AA,
        )

    def _draw_checks_panel(
        self,
        frame: np.ndarray,
        checks: list[BootCheck],
    ) -> None:
        panel_width = int(
            self.width * 0.62
        )

        panel_height = int(
            self.height * 0.48
        )

        panel_x = (
            self.width
            - panel_width
        ) // 2

        panel_y = int(
            self.height * 0.34
        )

        panel_bottom = (
            panel_y
            + panel_height
        )

        overlay = frame.copy()

        cv2.rectangle(
            overlay,
            (
                panel_x,
                panel_y,
            ),
            (
                panel_x + panel_width,
                panel_bottom,
            ),
            self.COLOR_PANEL,
            -1,
        )

        cv2.addWeighted(
            overlay,
            0.92,
            frame,
            0.08,
            0,
            frame,
        )

        cv2.rectangle(
            frame,
            (
                panel_x,
                panel_y,
            ),
            (
                panel_x + panel_width,
                panel_bottom,
            ),
            self.COLOR_PANEL_BORDER,
            2,
            cv2.LINE_AA,
        )

        if not checks:
            self._draw_no_checks(
                frame,
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            )
            return

        maximum_rows = 8
        visible_checks = checks[
            :maximum_rows
        ]

        row_height = (
            panel_height
            // maximum_rows
        )

        for index, check in enumerate(
            visible_checks
        ):
            row_y = (
                panel_y
                + row_height * index
            )

            self._draw_check_row(
                frame,
                check,
                panel_x,
                row_y,
                panel_width,
                row_height,
            )

    def _draw_no_checks(
        self,
        frame: np.ndarray,
        panel_x: int,
        panel_y: int,
        panel_width: int,
        panel_height: int,
    ) -> None:
        text = "Preparando comprobaciones..."

        scale = self._scale(
            0.70
        )

        text_size = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            1,
        )[0]

        text_x = (
            panel_x
            + (
                panel_width
                - text_size[0]
            )
            // 2
        )

        text_y = (
            panel_y
            + panel_height // 2
        )

        cv2.putText(
            frame,
            text,
            (
                text_x,
                text_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            self.COLOR_MUTED,
            1,
            cv2.LINE_AA,
        )

    def _draw_check_row(
        self,
        frame: np.ndarray,
        check: BootCheck,
        panel_x: int,
        row_y: int,
        panel_width: int,
        row_height: int,
    ) -> None:
        icon_text, icon_color = (
            self._state_visual(
                check.state
            )
        )

        center_y = (
            row_y
            + row_height // 2
        )

        icon_x = (
            panel_x
            + int(
                panel_width * 0.055
            )
        )

        label_x = (
            panel_x
            + int(
                panel_width * 0.12
            )
        )

        status_x = (
            panel_x
            + int(
                panel_width * 0.73
            )
        )

        icon_scale = self._scale(
            0.68
        )

        label_scale = self._scale(
            0.60
        )

        detail_scale = self._scale(
            0.43
        )

        cv2.putText(
            frame,
            icon_text,
            (
                icon_x,
                center_y + 7,
            ),
            cv2.FONT_HERSHEY_DUPLEX,
            icon_scale,
            icon_color,
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            check.label,
            (
                label_x,
                center_y + 6,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            label_scale,
            self.COLOR_WHITE,
            1,
            cv2.LINE_AA,
        )

        state_text = self._state_text(
            check.state
        )

        cv2.putText(
            frame,
            state_text,
            (
                status_x,
                center_y + 6,
            ),
            cv2.FONT_HERSHEY_DUPLEX,
            label_scale,
            icon_color,
            1,
            cv2.LINE_AA,
        )

        if check.detail:
            detail = self._truncate_text(
                check.detail,
                maximum_characters=42,
            )

            cv2.putText(
                frame,
                detail,
                (
                    label_x,
                    center_y
                    + int(
                        row_height * 0.34
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                detail_scale,
                self.COLOR_MUTED,
                1,
                cv2.LINE_AA,
            )

        if row_y > 0:
            cv2.line(
                frame,
                (
                    panel_x
                    + int(
                        panel_width * 0.04
                    ),
                    row_y,
                ),
                (
                    panel_x
                    + int(
                        panel_width * 0.96
                    ),
                    row_y,
                ),
                (
                    38,
                    48,
                    51,
                ),
                1,
                cv2.LINE_AA,
            )

    def _draw_footer(
        self,
        frame: np.ndarray,
        footer_message: str,
    ) -> None:
        version_text = (
            f"RoadEye v{self._version}"
        )

        system_text = (
            f"IP {self._ip_address}"
        )

        footer_y = int(
            self.height * 0.95
        )

        scale = self._scale(
            0.46
        )

        cv2.putText(
            frame,
            version_text,
            (
                int(
                    self.width * 0.025
                ),
                footer_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            self.COLOR_MUTED,
            1,
            cv2.LINE_AA,
        )

        system_size = cv2.getTextSize(
            system_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            1,
        )[0]

        cv2.putText(
            frame,
            system_text,
            (
                self.width
                - system_size[0]
                - int(
                    self.width * 0.025
                ),
                footer_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            self.COLOR_MUTED,
            1,
            cv2.LINE_AA,
        )

        if footer_message:
            message_size = cv2.getTextSize(
                footer_message,
                cv2.FONT_HERSHEY_SIMPLEX,
                scale,
                1,
            )[0]

            message_x = (
                self.width
                - message_size[0]
            ) // 2

            cv2.putText(
                frame,
                footer_message,
                (
                    message_x,
                    footer_y,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                scale,
                self.COLOR_WHITE,
                1,
                cv2.LINE_AA,
            )

    # ---------------------------------------------------------
    # Estados visuales
    # ---------------------------------------------------------

    def _state_visual(
        self,
        state: BootCheckState,
    ) -> tuple[str, tuple[int, int, int]]:
        if state == BootCheckState.OK:
            return "OK", self.COLOR_GREEN

        if state == BootCheckState.WARNING:
            return "!", self.COLOR_YELLOW

        if state == BootCheckState.ERROR:
            return "X", self.COLOR_RED

        if state == BootCheckState.RUNNING:
            return ">", self.COLOR_BLUE

        return "-", self.COLOR_MUTED

    @staticmethod
    def _state_text(
        state: BootCheckState,
    ) -> str:
        labels = {
            BootCheckState.PENDING: "ESPERA",
            BootCheckState.RUNNING: "INICIANDO",
            BootCheckState.OK: "OK",
            BootCheckState.WARNING: "AVISO",
            BootCheckState.ERROR: "ERROR",
        }

        return labels[
            state
        ]

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _scale(
        self,
        base_scale: float,
    ) -> float:
        width_factor = (
            self.width / 1280
        )

        height_factor = (
            self.height / 720
        )

        return max(
            0.35,
            base_scale
            * min(
                width_factor,
                height_factor,
            ),
        )

    @staticmethod
    def _truncate_text(
        text: str,
        maximum_characters: int,
    ) -> str:
        cleaned = " ".join(
            str(text).split()
        )

        if len(cleaned) <= maximum_characters:
            return cleaned

        return (
            cleaned[
                : maximum_characters - 3
            ]
            + "..."
        )

    @staticmethod
    def _read_version() -> str:
        if not VERSION_FILE.exists():
            return "desconocida"

        version = VERSION_FILE.read_text(
            encoding="utf-8"
        ).strip()

        return (
            version
            if version
            else "desconocida"
        )

    @staticmethod
    def _detect_ip_address() -> str:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            sock.connect(
                (
                    "8.8.8.8",
                    80,
                )
            )

            return str(
                sock.getsockname()[0]
            )

        except OSError:
            return "sin red"

        finally:
            sock.close()
