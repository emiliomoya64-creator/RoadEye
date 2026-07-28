from threading import Thread
import time

import requests

from core.system_state import system_state


class MapService:

    def __init__(self):

        self.running = False

        self.last_lat = None
        self.last_lon = None

    def start(self):

        if self.running:
            return

        self.running = True

        Thread(
            target=self.loop,
            daemon=True
        ).start()

        print("🗺 Map Service iniciado")

    # -------------------------------------------------

    def reverse_geocode(self, lat, lon):

        try:

            r = requests.get(

                "https://nominatim.openstreetmap.org/reverse",

                params={
                    "format": "jsonv2",
                    "lat": lat,
                    "lon": lon,
                    "zoom": 18,
                    "addressdetails": 1
                },

                headers={
                    "User-Agent": "RoadEye"
                },

                timeout=5

            )

            if r.status_code != 200:
                return

            data = r.json()

            address = data.get("address", {})

            road = (
                address.get("road")
                or address.get("pedestrian")
                or address.get("residential")
                or address.get("suburb")
                or "---"
            )

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or ""
            )

            system_state.set("road", road)
            system_state.set("city", city)

            print(f"🛣 {road}")

        except Exception:

            pass

    # -------------------------------------------------

    def get_road_info(self, lat, lon):

        try:

            query = f"""
[out:json][timeout:10];

way(around:20,{lat},{lon})["highway"];

out tags;
"""

            r = requests.post(

                "https://overpass-api.de/api/interpreter",

                data=query,

                headers={
                    "User-Agent": "RoadEye"
                },

                timeout=10

            )

            if r.status_code != 200:
                return

            data = r.json()

            if len(data["elements"]) == 0:
                return

            tags = data["elements"][0]["tags"]

            speed = tags.get("maxspeed", "0")
            lanes = tags.get("lanes", "?")
            highway = tags.get("highway", "?")
            oneway = tags.get("oneway", "no")

            try:
                speed = int(speed.split()[0])
            except:
                speed = 0

            system_state.set("speed_limit", speed)
            system_state.set("lanes", lanes)
            system_state.set("highway", highway)
            system_state.set("oneway", oneway)

            print(
                f"🚦 {speed} km/h | "
                f"{highway} | "
                f"{lanes} carriles"
            )

        except Exception:

            pass

    # -------------------------------------------------

    def loop(self):

        while self.running:

            if not system_state.get("gps_fix"):

                time.sleep(2)
                continue

            lat = system_state.get("latitude")
            lon = system_state.get("longitude")

            if lat == 0 or lon == 0:

                time.sleep(2)
                continue

            if self.last_lat is not None:

                if (
                    abs(lat - self.last_lat) < 0.0002
                    and
                    abs(lon - self.last_lon) < 0.0002
                ):

                    time.sleep(5)
                    continue

            self.last_lat = lat
            self.last_lon = lon

            self.reverse_geocode(lat, lon)

            self.get_road_info(lat, lon)

            time.sleep(5)