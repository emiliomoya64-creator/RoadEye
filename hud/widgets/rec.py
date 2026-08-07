import time

from hud.hud_engine import hud
from hud.layout import Layout


class RecWidget:
    """
    Widget de estado de grabación.

    - Sin grabar: punto verde y texto LISTO.
    - Grabando: punto rojo intermitente y contador HH:MM:SS.
    """

    BLINK_INTERVAL = 0.5

    def __init__(self):
        self.dot_visible = True
        self.last_blink_time = time.monotonic()
        self.was_recording = False
        self.recording_started_at = None

    def draw(self, frame, recording):
        recording = bool(recording)

        self._update_recording_state(recording)
        self._update_blink(recording)

        hud.filled_circle(
            frame,
            Layout.REC,
            radius=8,
            color=self._get_dot_color(recording),
        )

        hud.shadow_text(
            frame,
            "REC",
            (
                Layout.REC[0] + hud.scale(28),
                Layout.REC[1] + hud.scale(6),
            ),
            scale=0.65,
            thickness=2,
        )

        hud.shadow_text(
            frame,
            self._get_status_text(recording),
            (
                Layout.REC[0] + hud.scale(102),
                Layout.REC[1] + hud.scale(6),
            ),
            scale=0.58,
            thickness=2,
            color=(225, 225, 225),
        )

    def _update_recording_state(self, recording):
        if recording and not self.was_recording:
            self.recording_started_at = time.monotonic()
            self.dot_visible = True
            self.last_blink_time = time.monotonic()

        elif not recording and self.was_recording:
            self.recording_started_at = None
            self.dot_visible = True

        self.was_recording = recording

    def _update_blink(self, recording):
        if not recording:
            self.dot_visible = True
            return

        now = time.monotonic()

        if now - self.last_blink_time >= self.BLINK_INTERVAL:
            self.dot_visible = not self.dot_visible
            self.last_blink_time = now

    def _get_dot_color(self, recording):
        if not recording:
            return (0, 210, 0)

        if self.dot_visible:
            return (0, 0, 255)

        return (45, 45, 45)

    def _get_status_text(self, recording):
        if not recording or self.recording_started_at is None:
            return "LISTO"

        elapsed_seconds = max(
            0,
            int(time.monotonic() - self.recording_started_at),
        )

        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


rec_widget = RecWidget()