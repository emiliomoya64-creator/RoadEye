from __future__ import annotations

import datetime

import cv2

from hud.hud_engine import hud
from hud.icon_manager import icons
from hud.layout import Layout


class InfoBarWidget:

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
        center_y = row_y + row_h // 2

        now = datetime.datetime.now()

        road_text = self._safe_text(
            road,
            "---",
        )

        coordinates = self._coordinates_text(
            latitude,
            longitude,
            gps_fix,
        )

        date_text = now.strftime(
            "%d/%m/%Y"
        )

        time_text = now.strftime(
            "%H:%M"
        )

        # Segmentos de la barra inferior.
        sections = {
            # La carretera recibe casi la mitad
            # de toda la barra inferior.
            "road": (
                0.02,
                0.48,
            ),

            # Bloque derecho más compacto.
            "coordinates": (
                0.49,
                0.68,
            ),
            "date": (
                0.69,
                0.82,
            ),
            "time": (
                0.83,
                0.93,
            ),
            "settings": (
                0.94,
                0.995,
            ),
        }

        if is_visible("road"):
            self._draw_item(
                frame,
                sections["road"],
                center_y,
                "road",
                road_text,
                max_chars=40,
                text_scale=0.58,
                text_thickness=2,
            )

        if is_visible("coordinates"):
            self._draw_item(
                frame,
                sections["coordinates"],
                center_y,
                "coordinates",
                coordinates,
                max_chars=24,
                muted=True,
            )

        if is_visible("date"):
            self._draw_item(
                frame,
                sections["date"],
                center_y,
                "calendar",
                date_text,
                max_chars=10,
            )

        if is_visible("time"):
            self._draw_item(
                frame,
                sections["time"],
                center_y,
                "clock",
                time_text,
                max_chars=5,
            )

        if is_visible("settings"):
            left = int(
                Layout.W
                * sections["settings"][0]
            )

            right = int(
                Layout.W
                * sections["settings"][1]
            )

            icons.draw_centered(
                frame,
                "settings",
                (
                    (left + right) // 2,
                    center_y,
                ),
                hud.icon_scale(32),
                tint=hud.primary_color(),
            )

    # -----------------------------------------------------

    def _draw_item(
        self,
        frame,
        section,
        center_y,
        icon_name,
        text,
        *,
        max_chars,
        muted=False,
        text_scale=0.47,
        text_thickness=1,
    ):

        left = int(
            Layout.W
            * section[0]
        )

        right = int(
            Layout.W
            * section[1]
        )

        icon_size = hud.icon_scale(32)

        icon_x = (
            left
            + icon_size // 2
        )

        color = (
            hud.muted_color()
            if muted
            else hud.primary_color()
        )

        icons.draw_centered(
            frame,
            icon_name,
            (
                icon_x,
                center_y,
            ),
            icon_size,
            tint=color,
        )

        safe_text = str(text)

        if len(safe_text) > max_chars:
            safe_text = (
                safe_text[
                    :max(
                        1,
                        max_chars - 3,
                    )
                ]
                + "..."
            )

        text_x = (
            left
            + icon_size
            + hud.scale(8)
        )

        available = max(
            20,
            right
            - text_x
            - hud.scale(4),
        )

        fitted = self._fit_text(
            safe_text,
            available,
            base_scale=text_scale,
        )

        hud.shadow_text(
            frame,
            fitted,
            (
                text_x,
                center_y
                + hud.scale(6),
            ),
            scale=text_scale,
            color=color,
            thickness=text_thickness,
        )

    # -----------------------------------------------------

    def _fit_text(
        self,
        text,
        maximum_width,
        *,
        base_scale,
    ):

        cleaned = str(text)

        font = hud.font_face()

        scale = (
            base_scale
            * Layout.S
            * hud.text_factor()
        )

        while cleaned:

            size = cv2.getTextSize(
                cleaned,
                font,
                scale,
                1,
            )[0]

            if size[0] <= maximum_width:
                return cleaned

            if len(cleaned) <= 4:
                return "..."

            cleaned = (
                cleaned[:-4]
                .rstrip()
                + "..."
            )

        return "---"

    # -----------------------------------------------------

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
                f"{float(latitude):.5f} "
                f"{float(longitude):.5f}"
            )
        except (
            TypeError,
            ValueError,
        ):
            return "---"

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
