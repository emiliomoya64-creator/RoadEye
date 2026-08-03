from hud.overlay import overlay


def render(frame):
    """
    Aplica el HUD central de RoadEye sobre el frame.

    Las franjas, widgets y transparencias se dibujan únicamente
    desde HUDOverlay. De esta forma no existen fondos duplicados.
    """

    return overlay.draw(frame)
