from __future__ import annotations

import cv2

from hud.hud_engine import hud
from hud.icon_manager import icons
from hud.layout import Layout
from hud.widgets.rec import rec_widget


class ActionBarWidget:

    COLOR_GREEN = (70, 220, 110)
    COLOR_MUTED = (120, 130, 135)

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

        # REC ocupa algo más de espacio.
        boundaries = [
            0.00,
            0.18,
            0.29,
            0.47,
            0.64,
            0.75,
            0.86,
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
            self._draw_icon(
                frame,
                cells[4],
                row_y,
                row_h,
                "camera",
            )

        if is_visible("gallery"):
            self._draw_icon(
                frame,
                cells[5],
                row_y,
                row_h,
                "gallery",
            )

        if is_visible("speed_limit"):
            self._draw_speed_limit(
                frame,
                cells[6],
                row_y,
                row_h,
                speed_limit=speed_limit,
            )

    # -----------------------------------------------------

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

        center = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        if motion:
            color = (40, 70, 255)
        elif enabled:
            color = hud.primary_color()
        else:
            color = hud.muted_color()

        icons.draw_centered(
            frame,
            "parking",
            center,
            hud.icon_scale(40),
            tint=color,
        )

    # -----------------------------------------------------

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

        left, right = cell

        center_y = (
            row_y
            + row_h // 2
        )

        color = (
            self.COLOR_GREEN
            if gps_fix
            else hud.muted_color()
        )

        satellite_count = max(
            0,
            self._safe_int(
                satellites
            ),
        )

        # El conjunto GPS se trata visualmente
        # como una sola familia:
        #
        # señal | satélite | número

        group_center = (
            left
            + (right - left) // 2
        )

        signal_x = (
            group_center
            - hud.icon_scale(27)
        )

        satellite_x = (
            group_center
            + hud.icon_scale(6)
        )

        self._draw_signal_bars(
            frame,
            signal_x,
            center_y,
            satellites=satellite_count,
            gps_fix=gps_fix,
            color=color,
        )

        satellite_size = hud.icon_scale(32)

        icons.draw_centered(
            frame,
            "satellite",
            (
                satellite_x,
                center_y,
            ),
            satellite_size,
            tint=color,
        )

        hud.shadow_text(
            frame,
            str(satellite_count),
            (
                satellite_x
                + satellite_size // 2
                + hud.scale(5),
                center_y
                + hud.scale(7),
            ),
            scale=0.55,
            color=color,
            thickness=2,
        )

    # -----------------------------------------------------

    def _draw_signal_bars(
        self,
        frame,
        center_x,
        center_y,
        *,
        satellites,
        gps_fix,
        color,
    ):
        """
        Indicador GNSS de cuatro barras.

        0-2 satélites  -> 0 barras
        3-5            -> 1 barra
        6-8            -> 2 barras
        9-11           -> 3 barras
        12+            -> 4 barras
        """

        if not gps_fix:
            active = 0
        elif satellites >= 12:
            active = 4
        elif satellites >= 9:
            active = 3
        elif satellites >= 6:
            active = 2
        elif satellites >= 3:
            active = 1
        else:
            active = 0

        bar_width = hud.icon_scale(5)
        gap = hud.icon_scale(3)

        heights = [
            hud.icon_scale(10),
            hud.icon_scale(17),
            hud.icon_scale(24),
            hud.icon_scale(31),
        ]

        total_width = (
            bar_width * 4
            + gap * 3
        )

        start_x = (
            center_x
            - total_width // 2
        )

        bottom = (
            center_y
            + hud.icon_scale(15)
        )

        for index, height in enumerate(
            heights
        ):
            x1 = (
                start_x
                + index
                * (bar_width + gap)
            )

            x2 = x1 + bar_width

            bar_color = (
                color
                if index < active
                else hud.muted_color()
            )

            cv2.rectangle(
                frame,
                (
                    x1,
                    bottom - height,
                ),
                (
                    x2,
                    bottom,
                ),
                bar_color,
                -1,
                cv2.LINE_AA,
            )

    # -----------------------------------------------------

    def _draw_speed(
        self,
        frame,
        cell,
        row_y,
        row_h,
        *,
        speed,
    ):

        center_x, center_y = (
            self._cell_center(
                cell,
                row_y,
                row_h,
            )
        )

        value = max(
            0,
            self._safe_int(
                speed
            ),
        )

        number = str(value)

        font = hud.font_face()

        scale = (
            1.02
            * Layout.S
            * hud.text_factor()
        )

        thickness = max(
            1,
            hud.scale(2),
        )

        number_size = cv2.getTextSize(
            number,
            font,
            scale,
            thickness,
        )[0]

        unit_scale = (
            0.58
            * Layout.S
            * hud.text_factor()
        )

        unit_size = cv2.getTextSize(
            "km/h",
            font,
            unit_scale,
            1,
        )[0]

        gap = hud.scale(8)

        total_width = (
            number_size[0]
            + gap
            + unit_size[0]
        )

        start_x = (
            center_x
            - total_width // 2
        )

        cv2.putText(
            frame,
            number,
            (
                start_x,
                center_y
                + number_size[1] // 2,
            ),
            font,
            scale,
            hud.primary_color(),
            thickness,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            "km/h",
            (
                start_x
                + number_size[0]
                + gap,
                center_y
                + unit_size[1] // 2,
            ),
            font,
            unit_scale,
            hud.muted_color(),
            1,
            cv2.LINE_AA,
        )

    # -----------------------------------------------------

    def _draw_icon(
        self,
        frame,
        cell,
        row_y,
        row_h,
        name,
    ):

        center = self._cell_center(
            cell,
            row_y,
            row_h,
        )

        icons.draw_centered(
            frame,
            name,
            center,
            hud.icon_scale(40),
            tint=hud.primary_color(),
        )

    # -----------------------------------------------------

    def _draw_speed_limit(
        self,
        frame,
        cell,
        row_y,
        row_h,
        *,
        speed_limit,
    ):

        center_x, center_y = (
            self._cell_center(
                cell,
                row_y,
                row_h,
            )
        )

        value = max(
            0,
            self._safe_int(
                speed_limit
            ),
        )

        text = (
            str(value)
            if value > 0
            else "—"
        )

        radius = hud.icon_scale(20)

        border = max(
            hud.icon_scale(3),
            3,
        )

        cv2.circle(
            frame,
            (
                center_x,
                center_y,
            ),
            radius,
            (255, 255, 255),
            -1,
            cv2.LINE_AA,
        )

        cv2.circle(
            frame,
            (
                center_x,
                center_y,
            ),
            radius,
            (0, 0, 230),
            border,
            cv2.LINE_AA,
        )

        font = hud.font_face()

        scale = (
            0.62
            * Layout.S
            * hud.text_factor()
        )

        thickness = max(
            1,
            hud.scale(2),
        )

        size = cv2.getTextSize(
            text,
            font,
            scale,
            thickness,
        )[0]

        cv2.putText(
            frame,
            text,
            (
                center_x
                - size[0] // 2,
                center_y
                + size[1] // 2,
            ),
            font,
            scale,
            (15, 15, 15),
            thickness,
            cv2.LINE_AA,
        )

    # -----------------------------------------------------

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
