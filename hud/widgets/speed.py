import cv2

from hud.layout import layout


class SpeedWidget:

    def draw(self, frame, speed, limit, blink):

        color = (0, 255, 0)

        if limit > 0:

            if speed >= limit:

                color = (0, 0, 255) if blink else (255, 255, 255)

            elif speed >= limit - 5:

                color = (0, 255, 255)

        x, y = layout.SPEED

        cv2.putText(
            frame,
            f"{int(speed)} km/h",
            (x, y),
            cv2.FONT_HERSHEY_DUPLEX,
            1.0,
            color,
            2
        )

        if limit > 0:

            cx, cy = layout.SPEED_SIGN

            cv2.circle(frame, (cx, cy), 28, (0, 0, 255), -1)
            cv2.circle(frame, (cx, cy), 23, (255, 255, 255), -1)

            cv2.putText(
                frame,
                str(limit),
                (cx - 12, cy + 8),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                (0, 0, 0),
                2
            )


speed_widget = SpeedWidget()