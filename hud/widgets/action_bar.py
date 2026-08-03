from __future__ import annotations

import cv2

from hud.hud_engine import hud
from hud.icon_manager import icons
from hud.layout import Layout
from hud.widgets.rec import rec_widget


class ActionBarWidget:
    """
    Barra superior de RoadEye 0.6.

    Orden actual:

    - REC y estado.
    - Vigilancia de aparcamiento.
    - GPS.
    - Velocidad.
    - Fotografía.
    - Explorador de vídeos.
    - Límite de velocidad.

    No se dibujan separadores verticales.
    """

    COLOR_WHITE = (245, 245, 245)
    COLOR_MUTED = (145, 155, 160)
    COLOR_GREEN = (70, 220, 110)
    COLOR_BLUE = (230, 170, 60)
    COLOR_RED = (50, 60, 240)
    COLOR_ORANGE = (0, 190, 255)

    def draw(
        self,
        frame,
        *,
        recording: bool,
        parking_enabled: bool,
        parking_motion: bool,
        gps_fix: bool,
        satellites: int,
        speed: float,
        speed_limit: int,
        visible: dict | None = None,
    ) -> None:
        visible = visible or {}

        def is_visible(name):
            return bool(
                visible.get(
                    name,
                    True,
                )
            )

        row_y = Layout.TOP_ROW_Y
        row_h = Layout.TOP_ROW_HEIGHT

        boundaries = [
            0.00,
            0.18,
            0.30,
            0.42,
            0.58,
            0.70,
            0.83,
            1.00,
        ]

        cells = [
            (
                int(
                    Layout.W
                    * boundaries[index]
                ),
                int(
                    Layout.W
                    * boundaries[index + 1]
                ),
            )
            for index in range(
                len(boundaries) - 1
            )
        ]

        # Conserva LISTO, contador y parpadeo.
        if is_visible("recording"):
            rec_widget.draw(
                frame,
                recording=recording,
            )

        if is_visible("parking"):
            self._draw_parking(
                frame,
                cells[1],
                row_y,
                row_h,
                enabled=parking_enabled,
                motion=parking_motion,
            )

        if is_visible("gps"):
            self._draw_gps(
                frame,
                cells[2],
                row_y,
                row_h,
                gps_fix=gps_fix,
                satellites=satellites,
            )

        if is_visible("speed"):
            self._draw_speed(
                frame,
                cells[3],
                row_y,
                row_h,
                speed=speed,
            )

        if is_visible("snapshot"):
            self._draw_photo(
                frame,
                cells[4],
                row_y,
                row_h,
            )

        if is_visible("gallery"):
            self._draw_gallery(
                frame,
                cells[5],
                row_y,
                row_h,
            )

        if is_visible("speed_limit"):
            self._draw_speed_limit(
                frame,
                cells[6],
                row_y,
                row_h,
                speed_limit=speed_limit,
            )

    # ---------------------------------------------------------
    # Parking
    # ---------------------------------------------------------

    def _draw_parking(
        self,
        frame,
        cell,
        row_y,
        row_h,
        *,
        enabled,
        motion,
    ):
        center_x, center_y = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        if motion:
            color = self.COLOR_RED
            label = "MOVIMIENTO"
        elif enabled:
            color = self.COLOR_BLUE
            label = "PARK ON"
        else:
            color = self.COLOR_MUTED
            label = "PARK OFF"

        icons.draw_centered(
            frame,
            "radar",
            (
                center_x,
                center_y - hud.scale(5),
            ),
            hud.scale(37),
            tint=color,
            opacity=1.0,
        )

        self._draw_label(
            frame,
            label,
            center_x,
            center_y + hud.scale(27),
            color=color,
        )

    # ---------------------------------------------------------
    # GPS
    # ---------------------------------------------------------

    def _draw_gps(
        self,
        frame,
        cell,
        row_y,
        row_h,
        *,
        gps_fix,
        satellites,
    ):
        center_x, center_y = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        color = (
            self.COLOR_GREEN
            if gps_fix
            else self.COLOR_MUTED
        )

        icons.draw_centered(
            frame,
            "gps_satellite",
            (
                center_x,
                center_y - hud.scale(5),
            ),
            hud.scale(37),
            tint=color,
        )

        satellite_count = max(
            0,
            self._safe_int(
                satellites
            ),
        )

        label = (
            f"GPS {satellite_count}"
            if gps_fix
            else "GPS SIN SEÑAL"
        )

        self._draw_label(
            frame,
            label,
            center_x,
            center_y + hud.scale(27),
            color=color,
        )

    # ---------------------------------------------------------
    # Velocidad
    # ---------------------------------------------------------

    def _draw_speed(
        self,
        frame,
        cell,
        row_y,
        row_h,
        *,
        speed,
    ):
        center_x, center_y = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        value = max(
            0,
            self._safe_int(
                speed
            ),
        )

        number = str(
            value
        )

        scale = max(
            0.76,
            1.08 * Layout.S,
        )

        thickness = max(
            1,
            hud.scale(2),
        )

        size = cv2.getTextSize(
            number,
            cv2.FONT_HERSHEY_DUPLEX,
            scale,
            thickness,
        )[0]

        cv2.putText(
            frame,
            number,
            (
                center_x - size[0] // 2,
                center_y + hud.scale(5),
            ),
            cv2.FONT_HERSHEY_DUPLEX,
            scale,
            self.COLOR_WHITE,
            thickness,
            cv2.LINE_AA,
        )

        self._draw_label(
            frame,
            "km/h",
            center_x,
            center_y + hud.scale(28),
            color=self.COLOR_MUTED,
        )

    # ---------------------------------------------------------
    # Foto
    # ---------------------------------------------------------

    def _draw_photo(
        self,
        frame,
        cell,
        row_y,
        row_h,
    ):
        center_x, center_y = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        icons.draw_centered(
            frame,
            "camera",
            (
                center_x,
                center_y - hud.scale(5),
            ),
            hud.scale(38),
            tint=self.COLOR_WHITE,
        )

        self._draw_label(
            frame,
            "FOTO",
            center_x,
            center_y + hud.scale(28),
        )

    # ---------------------------------------------------------
    # Vídeos
    # ---------------------------------------------------------

    def _draw_gallery(
        self,
        frame,
        cell,
        row_y,
        row_h,
    ):
        center_x, center_y = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        width = hud.scale(38)
        height = hud.scale(27)

        x1 = center_x - width // 2
        y1 = (
            center_y
            - height // 2
            - hud.scale(5)
        )

        cv2.rectangle(
            frame,
            (
                x1,
                y1,
            ),
            (
                x1 + width,
                y1 + height,
            ),
            self.COLOR_WHITE,
            max(
                1,
                hud.scale(2),
            ),
            cv2.LINE_AA,
        )

        cv2.circle(
            frame,
            (
                center_x,
                y1 + height // 2,
            ),
            hud.scale(6),
            self.COLOR_WHITE,
            max(
                1,
                hud.scale(2),
            ),
            cv2.LINE_AA,
        )

        self._draw_label(
            frame,
            "VIDEOS",
            center_x,
            center_y + hud.scale(28),
        )

    # ---------------------------------------------------------
    # Límite
    # ---------------------------------------------------------

    def _draw_speed_limit(
        self,
        frame,
        cell,
        row_y,
        row_h,
        *,
        speed_limit,
    ):
        center_x, center_y = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        icons.draw_centered(
            frame,
            "speed_limit",
            (
                center_x,
                center_y - hud.scale(5),
            ),
            hud.scale(43),
        )

        value = max(
            0,
            self._safe_int(
                speed_limit
            ),
        )

        value_text = (
            str(value)
            if value > 0
            else "--"
        )

        scale = max(
            0.36,
            0.52 * Layout.S,
        )

        thickness = max(
            1,
            hud.scale(1),
        )

        size = cv2.getTextSize(
            value_text,
            cv2.FONT_HERSHEY_DUPLEX,
            scale,
            thickness,
        )[0]

        cv2.putText(
            frame,
            value_text,
            (
                center_x - size[0] // 2,
                center_y
                - hud.scale(5)
                + size[1] // 2,
            ),
            cv2.FONT_HERSHEY_DUPLEX,
            scale,
            (20, 20, 20),
            thickness,
            cv2.LINE_AA,
        )

        self._draw_label(
            frame,
            "LIMITE",
            center_x,
            center_y + hud.scale(28),
        )

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _draw_label(
        self,
        frame,
        text,
        center_x,
        baseline_y,
        *,
        color=None,
    ):
        label_color = (
            color
            if color is not None
            else self.COLOR_MUTED
        )

        scale = max(
            0.29,
            0.38 * Layout.S,
        )

        size = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            1,
        )[0]

        cv2.putText(
            frame,
            text,
            (
                center_x - size[0] // 2,
                baseline_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            label_color,
            1,
            cv2.LINE_AA,
        )

    @staticmethod
    def _cell_center(
        cell,
        row_y,
        row_h,
    ):
        left, right = cell

        return (
            (left + right) // 2,
            row_y + row_h // 2,
        )

    @staticmethod
    def _safe_int(
        value,
    ):
        try:
            return int(
                round(
                    float(value)
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0


action_bar_widget = ActionBarWidget()
