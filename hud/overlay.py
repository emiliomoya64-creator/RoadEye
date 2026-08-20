from core.system_state import system_state
from hud.layout import Layout
from hud.settings import hud_settings
from hud.widgets.modern_hud import modern_hud_widget


class HUDOverlay:
    """
    Compositor RoadEye HUD moderno.
    """

    def draw(
        self,
        frame,
    ):
        settings = (
            hud_settings.snapshot()
        )

        if not settings["enabled"]:
            return frame

        Layout.update(
            frame,
            info_position=settings[
                "info_position"
            ],
            top_bar_scale=settings.get(
                "top_bar_scale",
                1.0,
            ),
            info_bar_scale=settings.get(
                "info_bar_scale",
                1.0,
            ),
        )

        modern_hud_widget.draw(
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
            road=getattr(
                system_state,
                "road",
                "---",
            ),
            visible=settings[
                "show"
            ],
        )

        return frame


overlay = HUDOverlay()
