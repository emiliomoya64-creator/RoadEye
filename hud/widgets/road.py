import cv2

from config import COLOR_GREEN, COLOR_WHITE
from hud.layout import layout


class RoadWidget:

    def draw(self, frame, road, road_type, lanes):

        if not road:
            road = "---"

        if not road_type:
            road_type = "---"

        if not lanes:
            lanes = "?"

        cv2.putText(
            frame,
            road,
            layout.ROAD,
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            COLOR_GREEN,
            2
        )

        cv2.putText(
            frame,
            f"{road_type}   |   {lanes} carriles",
            layout.ROAD_INFO,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            COLOR_WHITE,
            1
        )


road_widget = RoadWidget()