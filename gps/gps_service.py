from threading import Thread
import time

import serial
import pynmea2

from core.system_state import system_state


class GPSService:

    PORT = "/dev/serial0"
    BAUDRATE = 9600

    def __init__(self):

        self.running = False
        self.serial = None

    def start(self):

        if self.running:
            return

        try:

            self.serial = serial.Serial(
                self.PORT,
                self.BAUDRATE,
                timeout=1
            )

            print(f"🛰 GPS conectado ({self.PORT})")

        except Exception as e:

            print(f"❌ Error abriendo GPS: {e}")
            return

        self.running = True

        Thread(
            target=self.loop,
            daemon=True
        ).start()

    def loop(self):

        print("🛰 Esperando datos GPS...")

        while self.running:

            try:

                line = self.serial.readline().decode(
                    "ascii",
                    errors="ignore"
                ).strip()

                if not line.startswith("$"):
                    continue

                msg = pynmea2.parse(line)

                # -----------------------------
                # RMC
                # -----------------------------

                if isinstance(msg, pynmea2.types.talker.RMC):

                    if msg.status == "A":

                        system_state.set("gps_fix", True)

                        system_state.set(
                            "latitude",
                            float(msg.latitude or 0)
                        )

                        system_state.set(
                            "longitude",
                            float(msg.longitude or 0)
                        )

                        velocidad = (
                            float(msg.spd_over_grnd or 0)
                            * 1.852
                        )

                        system_state.set(
                            "speed",
                            velocidad
                        )

                        rumbo = float(msg.true_course or 0)

                        dirs = [
                            "N",
                            "NE",
                            "E",
                            "SE",
                            "S",
                            "SW",
                            "W",
                            "NW"
                        ]

                        idx = int((rumbo + 22.5) / 45) % 8

                        system_state.set(
                            "heading",
                            dirs[idx]
                        )

                    else:

                        system_state.set("gps_fix", False)
                        system_state.set("speed", 0)

                # -----------------------------
                # GGA
                # -----------------------------

                elif isinstance(msg, pynmea2.types.talker.GGA):

                    system_state.set(
                        "satellites",
                        int(msg.num_sats or 0)
                    )

                    if msg.altitude:

                        system_state.set(
                            "altitude",
                            float(msg.altitude)
                        )

            except Exception:
                pass

            time.sleep(0.01)