from threading import Thread
import shutil
import subprocess
import time

import psutil

from core.frame_buffer import frame_buffer
from core.system_state import system_state


class HealthMonitor:

    def __init__(self):

        self.running = False

    def start(self):

        if self.running:
            return

        self.running = True

        Thread(
            target=self.loop,
            daemon=True
        ).start()

        print("❤️ Health Monitor iniciado")

    def cpu_temp(self):

        try:

            temp = subprocess.check_output(
                ["vcgencmd", "measure_temp"]
            ).decode()

            return float(
                temp.split("=")[1].replace("'C\n", "")
            )

        except Exception:

            return 0

    def loop(self):

        while self.running:

            cpu = psutil.cpu_percent()

            ram = psutil.virtual_memory().percent

            temp = self.cpu_temp()

            total, used, free = shutil.disk_usage("/")

            disk = round((used / total) * 100)

            system_state.set("cpu", cpu)
            system_state.set("ram", ram)
            system_state.set("temp", temp)
            system_state.set("disk", disk)

            if frame_buffer.get_frame() is None:

                print("⚠ Cámara sin imágenes")

            if temp >= 75:

                print(f"🔥 Temperatura alta {temp:.1f}°C")

            if ram >= 90:

                print(f"⚠ RAM {ram:.0f}%")

            if disk >= 90:

                print(f"⚠ Disco {disk}%")

            time.sleep(5)