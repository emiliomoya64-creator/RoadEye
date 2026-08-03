from core.system_state import system_state
from hud.hud_engine import hud
from hud.layout import Layout
from hud.settings import hud_settings
from hud.widgets.action_bar import action_bar_widget
from hud.widgets.info_bar import info_bar_widget


class HUDOverlay:
    """
    Compositor configurable del HUD RoadEye 0.6.
    """

    TOP_COLOR = (12, 16, 18)
    INFO_COLOR = (18, 23, 25)

    def draw(self, frame):
        settings = hud_settings.snapshot()

        if not settings["enabled"]:
            return frame

        Layout.update(
            frame,
            info_position=settings[
                "info_position"
            ],
        )

        show = settings["show"]

        self._draw_backgrounds(
            frame,
            top_opacity=settings[
                "top_opacity"
            ],
            info_opacity=settings[
                "info_opacity"
            ],
        )

        action_bar_widget.draw(
            frame,
            recording=bool(
                getattr(
                    system_state,
                    "recording",
                    False,
                )
            ),
            parking_enabled=bool(
                getattr(
                    system_state,
                    "parking_enabled",
                    False,
                )
            ),
            parking_motion=bool(
                getattr(
                    system_state,
                    "parking_motion",
                    False,
                )
            ),
            gps_fix=bool(
                getattr(
                    system_state,
                    "gps_fix",
                    False,
                )
            ),
            satellites=getattr(
                system_state,
                "satellites",
                0,
            ),
            speed=getattr(
                system_state,
                "speed",
                0,
            ),
            speed_limit=getattr(
                system_state,
                "speed_limit",
                0,
            ),
            visible=show,
        )

        info_bar_widget.draw(
            frame,
            road=getattr(
                system_state,
                "road",
                "---",
            ),
            latitude=getattr(
                system_state,
                "latitude",
                0.0,
            ),
            longitude=getattr(
                system_state,
                "longitude",
                0.0,
            ),
            gps_fix=bool(
                getattr(
                    system_state,
                    "gps_fix",
                    False,
                )
            ),
            visible=show,
        )

        return frame

    def _draw_backgrounds(
        self,
        frame,
        *,
        top_opacity,
        info_opacity,
    ):
        hud.transparent_rect(
            frame,
            x=0,
            y=Layout.TOP_ROW_Y,
            w=Layout.W,
            h=Layout.TOP_ROW_HEIGHT,
            color=self.TOP_COLOR,
            alpha=top_opacity,
        )

        hud.transparent_rect(
            frame,
            x=0,
            y=Layout.INFO_ROW_Y,
            w=Layout.W,
            h=Layout.INFO_ROW_HEIGHT,
            color=self.INFO_COLOR,
            alpha=info_opacity,
        )


overlay = HUDOverlay()
