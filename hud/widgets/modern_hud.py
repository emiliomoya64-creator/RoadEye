from __future__ import annotations

import datetime
import time
import cv2

from hud.hud_engine import hud
from hud.icon_manager import icons
from hud.layout import Layout


class ModernHUDWidget:
    """
    HUD RoadEye moderno.

    Inspirado en interfaces dashcam:
    - vídeo prácticamente completo
    - información flotante
    - velocidad abajo izquierda
    - acciones laterales
    - cápsula central inferior
    """

    GREEN = (70, 220, 110)
    ORANGE = (0, 165, 255)
    RED = (40, 40, 240)

    def __init__(self):
        self.recording_started_at = None
        self._recording_previous = False
        self._recording_counter = "00:00:00"
        self._recording_blink_on = False

    def draw(
        self,
        frame,
        *,
        recording=False,
        parking_enabled=False,
        parking_motion=False,
        gps_fix=False,
        satellites=0,
        speed=0,
        speed_limit=0,
        road="---",
        visible=None,
    ):
        visible = visible or {}

        self._draw_recording(
            frame,
            recording,
        )

        self._draw_road(
            frame,
            road,
        )

        self._draw_speed_limit(
            frame,
            speed_limit,
        )

        self._draw_left_controls(
            frame,
            gps_fix,
            satellites,
        )

        # Cámara y Parking se muestran ahora únicamente
        # en la barra inferior.

        # Velocidad actual oculta en el HUD.
        # Se conserva _draw_speed() por si se desea
        # recuperar más adelante.

        self._draw_bottom_capsule(
            frame,
            recording,
            parking_enabled,
            parking_motion,
        )

        self._draw_clock(
            frame,
        )

    # --------------------------------------------------

    def _panel(
        self,
        frame,
        x,
        y,
        w,
        h,
        alpha=0.55,
    ):
        hud.rounded_rect(
            frame,
            x=x,
            y=y,
            w=w,
            h=h,
            radius=min(
                hud.scale(18),
                h // 2,
            ),
            color=(8, 11, 14),
            alpha=alpha,
        )

    def _modern_icon_scale(
        self,
        base_size,
    ):
        return max(
            1,
            int(
                hud.icon_scale(
                    base_size
                )
                * 1.45
            ),
        )


    def _circle_button(
        self,
        frame,
        center,
        *,
        icon_name,
        icon_color=(255, 255, 255),
        radius=28,
        alpha=0.70,
    ):
        radius_px = hud.scale(radius)

        overlay = frame.copy()

        cv2.circle(
            overlay,
            center,
            radius_px,
            (8, 11, 14),
            -1,
            cv2.LINE_AA,
        )

        cv2.addWeighted(
            overlay,
            alpha,
            frame,
            1.0 - alpha,
            0,
            frame,
        )

        icons.draw_centered(
            frame,
            icon_name,
            center,
            self._modern_icon_scale(42),
            tint=icon_color,
        )


    # --------------------------------------------------

    def _draw_recording(
        self,
        frame,
        recording,
    ):
        recording = bool(recording)

        if (
            recording
            and not self._recording_previous
        ):
            self.recording_started_at = (
                time.monotonic()
            )

        elif (
            not recording
            and self._recording_previous
        ):
            self.recording_started_at = None

        self._recording_previous = recording

        if not recording:
            self._recording_counter = "00:00:00"
            self._recording_blink_on = False
            return

        if self.recording_started_at is None:
            self.recording_started_at = (
                time.monotonic()
            )

        elapsed_seconds = max(
            0,
            int(
                time.monotonic()
                - self.recording_started_at
            ),
        )

        hours, remainder = divmod(
            elapsed_seconds,
            3600,
        )

        minutes, seconds = divmod(
            remainder,
            60,
        )

        self._recording_counter = (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

        self._recording_blink_on = (
            int(
                time.monotonic() * 2
            )
            % 2
            == 0
        )

    # --------------------------------------------------

    def _draw_road(
        self,
        frame,
        road,
    ):
        text = str(
            road or "---"
        )

        if len(text) > 38:
            text = text[:35] + "..."

        font = hud.font_face()

        scale = (
            0.58
            * Layout.S
            * hud.text_factor()
        )

        thickness = max(
            1,
            hud.scale(1),
        )

        text_size = cv2.getTextSize(
            text,
            font,
            scale,
            thickness,
        )[0]

        icon_size = self._modern_icon_scale(25)

        gap = hud.scale(12)

        total_width = (
            icon_size
            + gap
            + text_size[0]
        )

        start_x = (
            Layout.W // 2
            - total_width // 2
        )

        center_y = hud.scale(72)

        icons.draw_centered(
            frame,
            "road",
            (
                start_x
                + icon_size // 2,
                center_y,
            ),
            icon_size,
            tint=hud.primary_color(),
        )

        hud.shadow_text(
            frame,
            text,
            (
                start_x
                + icon_size
                + gap,
                center_y
                + text_size[1] // 2,
            ),
            scale=0.58,
            color=(255, 255, 255),
            thickness=1,
        )

    # --------------------------------------------------

    def _draw_speed_limit(
        self,
        frame,
        speed_limit,
    ):
        try:
            value = int(
                round(
                    float(speed_limit or 0)
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            value = 0

        center = (
            Layout.W - hud.scale(115),
            hud.scale(72),
        )

        radius = self._modern_icon_scale(20)

        cv2.circle(
            frame,
            center,
            radius,
            (245, 245, 245),
            -1,
            cv2.LINE_AA,
        )

        cv2.circle(
            frame,
            center,
            radius,
            (0, 0, 230),
            max(
                2,
                hud.scale(3),
            ),
            cv2.LINE_AA,
        )

        text = (
            str(value)
            if value > 0
            else "—"
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
                center[0] - size[0] // 2,
                center[1] + size[1] // 2,
            ),
            font,
            scale,
            (20, 20, 20),
            thickness,
            cv2.LINE_AA,
        )

    # --------------------------------------------------

    def _draw_left_controls(
        self,
        frame,
        gps_fix,
        satellites,
    ):
        satellites = max(
            0,
            self._safe_int(
                satellites
            ),
        )

        x = hud.scale(30)
        y = hud.scale(28)

        width = hud.scale(220)
        height = hud.scale(105)

        self._panel(
            frame,
            x,
            y,
            width,
            height,
            alpha=0.68,
        )

        gps_color = (
            self.GREEN
            if gps_fix
            else hud.muted_color()
        )

        icon_center = (
            x + hud.scale(52),
            y + height // 2,
        )

        icons.draw_centered(
            frame,
            "satellite",
            icon_center,
            self._modern_icon_scale(26),
            tint=gps_color,
        )

        # Cuatro barras de señal.
        #
        # 0-2 satélites  -> 0 barras
        # 3-5            -> 1
        # 6-8            -> 2
        # 9-11           -> 3
        # 12+            -> 4

        active_bars = min(
            4,
            satellites // 3,
        )

        bar_x = (
            x + hud.scale(120)
        )

        base_y = (
            y + hud.scale(72)
        )

        bar_width = max(
            2,
            hud.scale(5),
        )

        gap = max(
            2,
            hud.scale(4),
        )

        heights = [
            hud.scale(9),
            hud.scale(15),
            hud.scale(21),
            hud.scale(27),
        ]

        for index, bar_height in enumerate(
            heights
        ):
            color = (
                gps_color
                if index < active_bars
                else (80, 84, 88)
            )

            bx = (
                bar_x
                + index
                * (
                    bar_width
                    + gap
                )
            )

            cv2.rectangle(
                frame,
                (
                    bx,
                    base_y - bar_height,
                ),
                (
                    bx + bar_width,
                    base_y,
                ),
                color,
                -1,
                cv2.LINE_AA,
            )

        hud.shadow_text(
            frame,
            str(satellites),
            (
                x + hud.scale(182),
                y + hud.scale(66),
            ),
            scale=0.48,
            color=gps_color,
            thickness=2,
        )

    # --------------------------------------------------

    def _draw_right_controls(
        self,
        frame,
        parking_enabled,
        parking_motion,
    ):
        x = (
            Layout.W
            - hud.scale(85)
        )

        camera_y = hud.scale(175)
        parking_y = hud.scale(300)

        self._circle_button(
            frame,
            (
                x,
                camera_y,
            ),
            icon_name="camera",
            icon_color=hud.primary_color(),
            radius=54,
        )

        parking_color = (
            self.ORANGE
            if parking_motion
            else (
                self.GREEN
                if parking_enabled
                else hud.muted_color()
            )
        )

        self._circle_button(
            frame,
            (
                x,
                parking_y,
            ),
            icon_name="parking",
            icon_color=parking_color,
            radius=54,
        )

        if parking_enabled:
            text = (
                "MOVIMIENTO"
                if parking_motion
                else "VIGILANDO"
            )

            font = hud.font_face()

            scale = (
                0.34
                * Layout.S
                * hud.text_factor()
            )

            size = cv2.getTextSize(
                text,
                font,
                scale,
                1,
            )[0]

            text_x = (
                x
                - hud.scale(36)
                - size[0]
            )

            hud.shadow_text(
                frame,
                text,
                (
                    text_x,
                    parking_y + hud.scale(5),
                ),
                scale=0.34,
                color=parking_color,
                thickness=1,
            )

    # --------------------------------------------------

    def _draw_speed(
        self,
        frame,
        speed,
    ):
        value = max(
            0,
            self._safe_int(
                speed
            ),
        )

        x = hud.scale(25)

        baseline = (
            Layout.H
            - hud.scale(30)
        )

        speed_text = str(value)

        hud.shadow_text(
            frame,
            speed_text,
            (
                x,
                baseline,
            ),
            scale=1.45,
            color=(255, 255, 255),
            thickness=3,
        )

        font = hud.font_face()

        speed_scale = (
            1.45
            * Layout.S
            * hud.text_factor()
        )

        speed_thickness = max(
            1,
            hud.scale(3),
        )

        speed_size = cv2.getTextSize(
            speed_text,
            font,
            speed_scale,
            speed_thickness,
        )[0]

        unit_x = (
            x
            + speed_size[0]
            + hud.scale(12)
        )

        hud.shadow_text(
            frame,
            "KM/H",
            (
                unit_x,
                baseline,
            ),
            scale=0.42,
            color=(255, 255, 255),
            thickness=1,
        )

    # --------------------------------------------------

    def _draw_bottom_capsule(
        self,
        frame,
        recording,
        parking_enabled,
        parking_motion,
    ):
        """
        Barra inferior definitiva RoadEye.

        Ajustes | Galería | Cámara | Parking | REC

        Al grabar, la barra se prolonga hacia
        la derecha para alojar el contador.
        """

        # Anchura fija para los 5 botones.
        base_width = hud.scale(640)

        # Espacio adicional SOLO cuando está grabando.
        counter_extra = (
            hud.scale(200)
            if recording
            else 0
        )

        total_width = (
            base_width
            + counter_extra
        )

        height = hud.scale(105)

        # La parte de botones permanece siempre
        # en el mismo sitio.
        x = (
            Layout.W // 2
            - base_width // 2
        )

        y = (
            Layout.H
            - height
            - hud.scale(16)
        )

        # Fondo completo.
        # Cuando REC está activo se alarga
        # automáticamente para cubrir el contador.
        hud.rounded_rect(
            frame,
            x=x,
            y=y,
            w=total_width,
            h=height,
            radius=height // 2,
            color=(8, 11, 14),
            alpha=0.80,
        )

        # ----------------------------------------------------
        # Posiciones de los cinco botones.
        # Mucho más separados que antes.
        # ----------------------------------------------------

        centers = [
            x + base_width * 1 // 10,
            x + base_width * 3 // 10,
            x + base_width * 5 // 10,
            x + base_width * 7 // 10,
            x + base_width * 9 // 10,
        ]

        # ----------------------------------------------------
        # Separadores
        # ----------------------------------------------------

        for index in range(1, 5):
            separator_x = (
                x
                + base_width * index // 5
            )

            cv2.line(
                frame,
                (
                    separator_x,
                    y + hud.scale(18),
                ),
                (
                    separator_x,
                    y + height - hud.scale(18),
                ),
                (75, 80, 85),
                max(
                    1,
                    hud.scale(1),
                ),
                cv2.LINE_AA,
            )

        # ----------------------------------------------------
        # Colores Parking
        # ----------------------------------------------------

        parking_color = (
            self.ORANGE
            if parking_motion
            else (
                self.GREEN
                if parking_enabled
                else hud.muted_color()
            )
        )

        # ----------------------------------------------------
        # Cuatro primeros botones
        # ----------------------------------------------------

        controls = [
            (
                "settings",
                hud.primary_color(),
            ),
            (
                "gallery",
                hud.primary_color(),
            ),
            (
                "camera",
                hud.primary_color(),
            ),
            (
                "parking",
                parking_color,
            ),
        ]

        for center_x, (
            icon_name,
            color,
        ) in zip(
            centers[:4],
            controls,
        ):
            icons.draw_centered(
                frame,
                icon_name,
                (
                    center_x,
                    y + height // 2,
                ),
                self._modern_icon_scale(30),
                tint=color,
            )

        # ----------------------------------------------------
        # REC
        # ----------------------------------------------------

        rec_x = centers[4]
        rec_y = (
            y
            + height // 2
        )

        if recording:
            # Conserva el parpadeo que ya teníamos.
            rec_color = (
                self.RED
                if self._recording_blink_on
                else (70, 70, 150)
            )
        else:
            rec_color = (
                hud.primary_color()
            )

        icons.draw_centered(
            frame,
            "rec",
            (
                rec_x,
                rec_y,
            ),
            self._modern_icon_scale(30),
            tint=rec_color,
        )

        # ----------------------------------------------------
        # Contador
        # ----------------------------------------------------

        if recording:
            hud.shadow_text(
                frame,
                self._recording_counter,
                (
                    rec_x
                    + hud.scale(55),
                    rec_y
                    + hud.scale(8),
                ),
                scale=0.48,
                color=(255, 255, 255),
                thickness=1,
            )

    # --------------------------------------------------

    def _draw_clock(
        self,
        frame,
    ):
        now = datetime.datetime.now()

        text = now.strftime(
            "%H:%M | %d/%m/%Y"
        )

        font = hud.font_face()

        scale = (
            0.48
            * Layout.S
            * hud.text_factor()
        )

        thickness = max(
            1,
            hud.scale(1),
        )

        size = cv2.getTextSize(
            text,
            font,
            scale,
            thickness,
        )[0]

        x = (
            Layout.W
            - size[0]
            - hud.scale(25)
        )

        y = (
            Layout.H
            - hud.scale(25)
        )

        hud.shadow_text(
            frame,
            text,
            (
                x,
                y,
            ),
            scale=0.48,
            color=(255, 255, 255),
            thickness=1,
        )

    # --------------------------------------------------

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


modern_hud_widget = ModernHUDWidget()
