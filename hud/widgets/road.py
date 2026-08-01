import cv2

from hud.hud_engine import hud
from hud.layout import Layout


class RoadWidget:
    """
    Widget de información de la vía.

    Muestra:
    - Icono de carretera.
    - Nombre de la calle o carretera.
    - Tipo de vía.
    - Número de carriles.
    """

    COLOR_PRIMARY = (245, 245, 245)
    COLOR_SECONDARY = (205, 205, 205)
    COLOR_ICON = (235, 235, 235)

    def draw(self, frame, road, road_type, lanes):
        road = self._safe_text(road, "---")
        road_type = self._safe_text(road_type, "---")
        lanes_text = self._format_lanes(lanes)

        self._draw_road_icon(
            frame,
            Layout.ROAD_ICON,
        )

        hud.shadow_text(
            frame,
            road,
            Layout.ROAD,
            scale=0.75,
            thickness=2,
            color=self.COLOR_PRIMARY,
        )

        hud.shadow_text(
            frame,
            f"{road_type}  ·  {lanes_text}",
            Layout.ROAD_INFO,
            scale=0.55,
            thickness=1,
            color=self.COLOR_SECONDARY,
        )

    # -------------------------------------------------
    # Icono de carretera
    # -------------------------------------------------

    def _draw_road_icon(self, frame, center):
        x, y = center

        line_color = self.COLOR_ICON
        side_thickness = max(1, hud.scale(4))
        center_thickness = max(1, hud.scale(2))

        top_y = y - hud.scale(26)
        bottom_y = y + hud.scale(26)

        left_top = x - hud.scale(8)
        left_bottom = x - hud.scale(22)

        right_top = x + hud.scale(8)
        right_bottom = x + hud.scale(22)

        cv2.line(
            frame,
            (left_top, top_y),
            (left_bottom, bottom_y),
            line_color,
            side_thickness,
            cv2.LINE_AA,
        )

        cv2.line(
            frame,
            (right_top, top_y),
            (right_bottom, bottom_y),
            line_color,
            side_thickness,
            cv2.LINE_AA,
        )

        # Línea discontinua central.
        dash_height = hud.scale(8)
        dash_gap = hud.scale(7)

        current_y = top_y

        while current_y < bottom_y:
            cv2.line(
                frame,
                (x, current_y),
                (
                    x,
                    min(current_y + dash_height, bottom_y),
                ),
                line_color,
                center_thickness,
                cv2.LINE_AA,
            )

            current_y += dash_height + dash_gap

    # -------------------------------------------------
    # Formato de datos
    # -------------------------------------------------

    @staticmethod
    def _safe_text(value, default):
        if value is None:
            return default

        text = str(value).strip()

        if not text:
            return default

        return text

    @staticmethod
    def _format_lanes(lanes):
        try:
            lane_count = int(lanes)

            if lane_count == 1:
                return "1 carril"

            return f"{lane_count} carriles"

        except (TypeError, ValueError):
            text = str(lanes).strip()

            if not text or text == "?":
                return "? carriles"

            return f"{text} carriles"


road_widget = RoadWidget()