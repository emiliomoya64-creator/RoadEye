import datetime

from core.system_state import system_state
from hud.hud_engine import hud
from hud.layout import Layout
from hud.widgets.gps import gps_widget
from hud.widgets.rec import rec_widget
from hud.widgets.road import road_widget
from hud.widgets.speed import speed_widget


class HUDOverlay:
    """
    Compone el HUD completo sobre cada frame.

    Widgets independizados:
    - REC.
    - GPS.
    - Velocidad y límite.
    - Información de carretera.
    """

    def draw(self, frame):
        # Adaptar posiciones y tamaños a la resolución.
        Layout.update(frame)

        # Fondos superior e inferior.
        hud.draw_top_bar(frame)
        hud.draw_bottom_bar(frame)

        # Fecha y hora.
        self._draw_datetime(frame)

        # Grabación.
        rec_widget.draw(
            frame,
            recording=bool(
                getattr(
                    system_state,
                    "recording",
                    False,
                )
            ),
        )

        # GPS.
        gps_widget.draw(
            frame,
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
        )

        # Velocidad y límite.
        speed_widget.draw(
            frame,
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
        )

        # Información de carretera.
        road_widget.draw(
            frame,
            road=getattr(
                system_state,
                "road",
                "---",
            ),
            road_type=getattr(
                system_state,
                "road_type",
                "---",
            ),
            lanes=getattr(
                system_state,
                "lanes",
                "?",
            ),
        )

        return frame

    # -------------------------------------------------
    # Fecha y hora
    # -------------------------------------------------

    def _draw_datetime(self, frame):
        now = datetime.datetime.now()

        hud.shadow_text(
            frame,
            now.strftime("%d/%m/%Y   %H:%M:%S"),
            Layout.DATE,
            scale=0.65,
            thickness=2,
        )


overlay = HUDOverlay()