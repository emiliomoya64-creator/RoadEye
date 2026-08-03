from __future__ import annotations

import datetime

import cv2

from hud.hud_engine import hud
from hud.icon_manager import icons
from hud.layout import Layout


class InfoBarWidget:
    """
    Segunda fila superior del HUD RoadEye 0.6.

    Muestra:

    - Calle o carretera.
    - Coordenadas GPS.
    - Fecha.
    - Hora.
    - Acceso visual a configuración.
    """

    COLOR_WHITE = (242, 245, 245)
    COLOR_MUTED = (175, 185, 188)
    COLOR_SEPARATOR = (85, 92, 95)

    def draw(
        self,
        frame,
        *,
        road,
        latitude,
        longitude,
        gps_fix,
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

        row_y = Layout.INFO_ROW_Y
        row_h = Layout.INFO_ROW_HEIGHT

        margin = Layout.HORIZONTAL_MARGIN
        center_y = row_y + row_h // 2

        now = datetime.datetime.now()

        road_text = self._safe_text(
            road,
            "---",
        )

        coordinates_text = self._coordinates_text(
            latitude,
            longitude,
            gps_fix,
        )

        date_text = now.strftime(
            "%d/%m/%Y"
        )

        time_text = now.strftime(
            "%H:%M:%S"
        )

        settings_width = max(
            62,
            int(92 * Layout.S),
        )

        right_edge = (
            Layout.W
            - margin
            - settings_width
        )

        time_width = max(
            88,
            int(145 * Layout.S),
        )

        date_width = max(
            98,
            int(170 * Layout.S),
        )

        coordinates_width = max(
            180,
            int(310 * Layout.S),
        )

        time_x = right_edge - time_width
        date_x = time_x - date_width
        coordinates_x = date_x - coordinates_width

        road_x = margin
        road_available = max(
            100,
            coordinates_x - road_x - hud.scale(15),
        )

        road_text = self._fit_text(
            road_text,
            road_available,
            scale=0.60,
            thickness=1,
        )

        if is_visible("road"):
            road_icon_size = hud.scale(30)

            icons.draw_centered(
                frame,
                "road",
                (
                    road_x
                    + road_icon_size // 2,
                    center_y,
                ),
                road_icon_size,
                tint=self.COLOR_WHITE,
            )

            hud.shadow_text(
                frame,
                road_text,
                (
                    road_x
                    + road_icon_size
                    + hud.scale(10),
                    center_y + hud.scale(7),
                ),
                scale=0.60,
                color=self.COLOR_WHITE,
                thickness=1,
            )

        if is_visible("coordinates"):
            hud.shadow_text(
                frame,
                coordinates_text,
                (
                    coordinates_x + hud.scale(14),
                    center_y + hud.scale(6),
                ),
                scale=0.48,
                color=self.COLOR_MUTED,
                thickness=1,
            )

        if is_visible("date"):
            hud.shadow_text(
                frame,
                date_text,
                (
                    date_x + hud.scale(14),
                    center_y + hud.scale(6),
                ),
                scale=0.50,
                color=self.COLOR_WHITE,
                thickness=1,
            )

        if is_visible("time"):
            hud.shadow_text(
                frame,
                time_text,
                (
                    time_x + hud.scale(14),
                    center_y + hud.scale(6),
                ),
                scale=0.56,
                color=self.COLOR_WHITE,
                thickness=1,
            )

        if is_visible("settings"):
            self._draw_settings_icon(
                frame,
                (
                    right_edge
                    + settings_width // 2,
                    center_y,
                ),
            )

    # ---------------------------------------------------------
    # Configuración
    # ---------------------------------------------------------

    def _draw_settings_icon(
        self,
        frame,
        center,
    ):
        x, y = center

        outer_radius = hud.scale(17)
        inner_radius = hud.scale(6)

        cv2.circle(
            frame,
            center,
            outer_radius,
            self.COLOR_WHITE,
            max(1, hud.scale(2)),
            cv2.LINE_AA,
        )

        cv2.circle(
            frame,
            center,
            inner_radius,
            self.COLOR_WHITE,
            max(1, hud.scale(2)),
            cv2.LINE_AA,
        )

        for angle in range(0, 360, 45):
            import math

            radians = math.radians(angle)

            x1 = int(
                x + math.cos(radians) * outer_radius
            )
            y1 = int(
                y + math.sin(radians) * outer_radius
            )

            x2 = int(
                x + math.cos(radians)
                * (outer_radius + hud.scale(7))
            )
            y2 = int(
                y + math.sin(radians)
                * (outer_radius + hud.scale(7))
            )

            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                self.COLOR_WHITE,
                max(1, hud.scale(3)),
                cv2.LINE_AA,
            )

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _draw_separator(
        self,
        frame,
        x,
        row_y,
        row_h,
    ):
        cv2.line(
            frame,
            (
                x,
                row_y + hud.scale(10),
            ),
            (
                x,
                row_y + row_h - hud.scale(10),
            ),
            self.COLOR_SEPARATOR,
            max(1, hud.scale(1)),
            cv2.LINE_AA,
        )

    def _fit_text(
        self,
        text,
        maximum_width,
        *,
        scale,
        thickness,
    ):
        cleaned = self._safe_text(
            text,
            "---",
        )

        font_scale = max(
            0.35,
            scale * Layout.S,
        )

        while cleaned:
            width = cv2.getTextSize(
                cleaned,
                cv2.FONT_HERSHEY_DUPLEX,
                font_scale,
                max(1, hud.scale(thickness)),
            )[0][0]

            if width <= maximum_width:
                return cleaned

            if len(cleaned) <= 4:
                return "---"

            cleaned = (
                cleaned[:-4].rstrip()
                + "..."
            )

        return "---"

    @staticmethod
    def _coordinates_text(
        latitude,
        longitude,
        gps_fix,
    ):
        if not gps_fix:
            return "GPS sin posición"

        try:
            return (
                f"{float(latitude):.5f}, "
                f"{float(longitude):.5f}"
            )
        except (TypeError, ValueError):
            return "Coordenadas no disponibles"

    @staticmethod
    def _safe_text(
        value,
        default,
    ):
        if value is None:
            return default

        text = str(value).strip()

        return text or default


info_bar_widget = InfoBarWidget()
