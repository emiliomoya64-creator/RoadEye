from core.system_state import system_state
from hud.overlay import overlay
from hud.hud_engine import hud


def render(frame):

    # Barra superior transparente
    hud.transparent_rect(
        frame,
        x=0,
        y=0,
        w=frame.shape[1],
        h=55,
        color=(20, 20, 20),
        alpha=0.45,
    )

    # Dibujar HUD
    overlay.draw(frame)

    return frame