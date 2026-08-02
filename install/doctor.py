#!/usr/bin/env python3

from __future__ import annotations

import importlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


PROJECT_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
CONFIG_FILE = PROJECT_DIR / "config" / "config.json"
VERSION_FILE = PROJECT_DIR / "VERSION"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    solution: Optional[str] = None


class RoadEyeDoctor:
    """
    Diagnóstico general de RoadEye.

    Estados:
    - OK: componente funcionando.
    - WARNING: componente disponible, pero con alguna observación.
    - ERROR: componente ausente o averiado.
    - OPTIONAL: componente no instalado, pero no obligatorio.
    """

    def __init__(self) -> None:
        self.results: list[CheckResult] = []

    # ---------------------------------------------------------
    # Ejecución principal
    # ---------------------------------------------------------

    def run(self) -> int:
        self._print_header()

        checks: list[Callable[[], None]] = [
            self.check_operating_system,
            self.check_raspberry_model,
            self.check_storage,
            self.check_git,
            self.check_python,
            self.check_python_modules,
            self.check_camera,
            self.check_gstreamer,
            self.check_hdmi,
            self.check_gps,
            self.check_service,
            self.check_web,
            self.check_temperature,
            self.check_throttling,
        ]

        for check in checks:
            try:
                check()
            except Exception as exc:
                self.results.append(
                    CheckResult(
                        name=check.__name__,
                        status="ERROR",
                        detail=f"Excepción no controlada: {exc}",
                    )
                )

        self._print_results()
        return self._print_summary()

    # ---------------------------------------------------------
    # Comprobaciones
    # ---------------------------------------------------------

    def check_operating_system(self) -> None:
        os_release = self._read_os_release()

        pretty_name = os_release.get(
            "PRETTY_NAME",
            platform.platform(),
        )

        architecture = platform.machine()

        if architecture not in {"aarch64", "arm64"}:
            self._add_warning(
                "Sistema operativo",
                f"{pretty_name} · arquitectura {architecture}",
                "RoadEye está diseñado principalmente para Raspberry Pi OS/Debian de 64 bits.",
            )
            return

        self._add_ok(
            "Sistema operativo",
            f"{pretty_name} · {architecture}",
        )

    def check_raspberry_model(self) -> None:
        model_path = Path("/proc/device-tree/model")

        if not model_path.exists():
            self._add_error(
                "Raspberry Pi",
                "No se pudo identificar el modelo.",
                "Comprueba que RoadEye se está ejecutando en una Raspberry Pi.",
            )
            return

        model = (
            model_path.read_bytes()
            .replace(b"\x00", b"")
            .decode(errors="replace")
            .strip()
        )

        if "Raspberry Pi" not in model:
            self._add_warning(
                "Raspberry Pi",
                model,
                "El equipo no parece una Raspberry Pi oficialmente reconocida.",
            )
            return

        self._add_ok(
            "Raspberry Pi",
            model,
        )

    def check_storage(self) -> None:
        usage = shutil.disk_usage("/")

        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        used_percent = (
            usage.used / usage.total * 100
            if usage.total
            else 0
        )

        detail = (
            f"{free_gb:.1f} GB libres de {total_gb:.1f} GB "
            f"({used_percent:.1f}% usado)"
        )

        if free_gb < 5:
            self._add_error(
                "Almacenamiento",
                detail,
                "Libera espacio o amplía el SSD. La grabación puede detenerse.",
            )
        elif free_gb < 20:
            self._add_warning(
                "Almacenamiento",
                detail,
                "Conviene liberar espacio antes de grabaciones largas.",
            )
        else:
            self._add_ok(
                "Almacenamiento",
                detail,
            )

    def check_git(self) -> None:
        if not (PROJECT_DIR / ".git").exists():
            self._add_error(
                "Git",
                "La carpeta del proyecto no contiene un repositorio Git.",
                "Clona RoadEye desde GitHub en lugar de copiar archivos manualmente.",
            )
            return

        branch = self._run(
            ["git", "-C", str(PROJECT_DIR), "branch", "--show-current"]
        )

        commit = self._run(
            ["git", "-C", str(PROJECT_DIR), "rev-parse", "--short", "HEAD"]
        )

        status = self._run(
            ["git", "-C", str(PROJECT_DIR), "status", "--porcelain"]
        )

        version = self._detect_version()

        detail = (
            f"versión {version} · rama {branch or 'desconocida'} "
            f"· commit {commit or 'desconocido'}"
        )

        if status:
            self._add_warning(
                "Git",
                f"{detail} · hay cambios sin guardar",
                "Haz commit o guarda los cambios antes de actualizar RoadEye.",
            )
        else:
            self._add_ok(
                "Git",
                f"{detail} · repositorio limpio",
            )

    def check_python(self) -> None:
        if not VENV_PYTHON.exists():
            self._add_error(
                "Entorno virtual",
                f"No existe {VENV_PYTHON}",
                "Ejecuta el instalador de RoadEye para crear .venv.",
            )
            return

        result = self._run(
            [str(VENV_PYTHON), "--version"],
            include_stderr=True,
        )

        self._add_ok(
            "Entorno virtual",
            result or "Python disponible",
        )

    def check_python_modules(self) -> None:
        modules = {
            "cv2": "OpenCV",
            "numpy": "NumPy",
            "fastapi": "FastAPI",
            "uvicorn": "Uvicorn",
            "serial": "PySerial",
            "pynmea2": "pynmea2",
            "gi": "PyGObject",
            "picamera2": "Picamera2",
        }

        missing: list[str] = []

        for module_name, display_name in modules.items():
            command = (
                "import importlib.util; "
                f"raise SystemExit(0 if importlib.util.find_spec('{module_name}') else 1)"
            )

            completed = subprocess.run(
                [str(VENV_PYTHON), "-c", command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

            if completed.returncode != 0:
                missing.append(display_name)

        if missing:
            self._add_error(
                "Dependencias Python",
                "Faltan: " + ", ".join(missing),
                "Ejecuta el instalador o reinstala las dependencias de RoadEye.",
            )
            return

        opencv_version = self._run(
            [
                str(VENV_PYTHON),
                "-c",
                "import cv2; print(cv2.__version__)",
            ]
        )

        self._add_ok(
            "Dependencias Python",
            f"módulos principales disponibles · OpenCV {opencv_version}",
        )

    def check_camera(self) -> None:
        command = shutil.which("rpicam-hello")

        if command is None:
            self._add_error(
                "Cámara",
                "No existe el comando rpicam-hello.",
                "Instala las herramientas de cámara de Raspberry Pi.",
            )
            return

        output = self._run(
            [command, "--list-cameras"],
            include_stderr=True,
        )

        if "imx219" in output.lower():
            self._add_ok(
                "Cámara frontal",
                "IMX219 detectada",
            )
        elif "available cameras" in output.lower():
            self._add_warning(
                "Cámara frontal",
                "Se detecta una cámara, pero no es IMX219.",
                "Comprueba que la configuración de RoadEye coincide con el sensor instalado.",
            )
        else:
            self._add_error(
                "Cámara frontal",
                "No se detecta ninguna cámara.",
                "Comprueba el cable CSI, el conector y dtoverlay=imx219.",
            )

    def check_gstreamer(self) -> None:
        gst_launch = shutil.which("gst-launch-1.0")
        gst_inspect = shutil.which("gst-inspect-1.0")

        if gst_launch is None or gst_inspect is None:
            self._add_error(
                "GStreamer",
                "No se encuentran las herramientas de GStreamer.",
                "Instala gstreamer1.0-tools y los plugins necesarios.",
            )
            return

        kmssink = subprocess.run(
            [gst_inspect, "kmssink"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        appsrc = subprocess.run(
            [gst_inspect, "appsrc"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        missing = []

        if kmssink.returncode != 0:
            missing.append("kmssink")

        if appsrc.returncode != 0:
            missing.append("appsrc")

        if missing:
            self._add_error(
                "GStreamer",
                "Faltan plugins: " + ", ".join(missing),
                "Instala gstreamer1.0-plugins-base y gstreamer1.0-plugins-bad.",
            )
            return

        version = self._run(
            [gst_launch, "--version"]
        ).splitlines()

        self._add_ok(
            "GStreamer",
            version[0] if version else "GStreamer disponible",
        )

    def check_hdmi(self) -> None:
        connectors = sorted(
            Path("/sys/class/drm").glob("card*-HDMI-A-*")
        )

        if not connectors:
            self._add_error(
                "HDMI",
                "No existen conectores HDMI en DRM.",
                "Comprueba dtoverlay=vc4-kms-v3d.",
            )
            return

        connected: list[str] = []

        for connector in connectors:
            status_file = connector / "status"

            if not status_file.exists():
                continue

            status = status_file.read_text().strip()

            if status == "connected":
                modes_file = connector / "modes"
                first_mode = "modo desconocido"

                if modes_file.exists():
                    modes = [
                        line.strip()
                        for line in modes_file.read_text().splitlines()
                        if line.strip()
                    ]

                    if modes:
                        first_mode = modes[0]

                connected.append(
                    f"{connector.name} · {first_mode}"
                )

        if not connected:
            self._add_warning(
                "HDMI",
                "No hay ningún monitor conectado.",
                "Conecta el monitor antes de encender la Raspberry.",
            )
            return

        self._add_ok(
            "HDMI",
            " | ".join(connected),
        )

    def check_gps(self) -> None:
        serial_path = Path("/dev/serial0")

        if not serial_path.exists():
            self._add_error(
                "GPS",
                "No existe /dev/serial0.",
                "Activa UART y comprueba el cableado del GPS.",
            )
            return

        target = serial_path.resolve()

        self._add_ok(
            "GPS",
            f"/dev/serial0 → {target}",
        )

    def check_service(self) -> None:
        if shutil.which("systemctl") is None:
            self._add_error(
                "Servicio RoadEye",
                "systemd no está disponible.",
            )
            return

        enabled = self._run(
            ["systemctl", "is-enabled", "roadeye.service"],
            include_stderr=True,
        )

        active = self._run(
            ["systemctl", "is-active", "roadeye.service"],
            include_stderr=True,
        )

        if active == "active" and enabled == "enabled":
            self._add_ok(
                "Servicio RoadEye",
                "activo y habilitado al arrancar",
            )
        elif active == "active":
            self._add_warning(
                "Servicio RoadEye",
                "activo, pero no habilitado al arrancar",
                "Ejecuta: sudo systemctl enable roadeye.service",
            )
        else:
            self._add_error(
                "Servicio RoadEye",
                f"estado: {active or 'desconocido'}",
                "Consulta: sudo journalctl -u roadeye.service -b",
            )

    def check_web(self) -> None:
        try:
            with socket.create_connection(
                ("127.0.0.1", 8000),
                timeout=2,
            ):
                pass

            self._add_ok(
                "Servidor web",
                "puerto 8000 accesible",
            )

        except OSError:
            self._add_error(
                "Servidor web",
                "el puerto 8000 no responde",
                "Comprueba roadeye.service y los registros de Uvicorn.",
            )

    def check_temperature(self) -> None:
        output = self._run(
            ["vcgencmd", "measure_temp"]
        )

        try:
            temperature = float(
                output.replace("temp=", "")
                .replace("'C", "")
                .strip()
            )
        except ValueError:
            self._add_warning(
                "Temperatura CPU",
                output or "No disponible",
            )
            return

        if temperature >= 80:
            self._add_error(
                "Temperatura CPU",
                f"{temperature:.1f} °C",
                "Revisa inmediatamente la refrigeración de la Raspberry.",
            )
        elif temperature >= 70:
            self._add_warning(
                "Temperatura CPU",
                f"{temperature:.1f} °C",
                "Conviene mejorar ventilación o disipación.",
            )
        else:
            self._add_ok(
                "Temperatura CPU",
                f"{temperature:.1f} °C",
            )

    def check_throttling(self) -> None:
        output = self._run(
            ["vcgencmd", "get_throttled"]
        )

        if not output.startswith("throttled=0x"):
            self._add_warning(
                "Alimentación y throttling",
                output or "No disponible",
            )
            return

        try:
            value = int(
                output.split("0x", 1)[1],
                16,
            )
        except ValueError:
            self._add_warning(
                "Alimentación y throttling",
                output,
            )
            return

        if value == 0:
            self._add_ok(
                "Alimentación y throttling",
                "sin incidencias detectadas",
            )
            return

        messages = []

        flags = {
            0: "tensión baja actualmente",
            1: "frecuencia limitada actualmente",
            2: "throttling activo actualmente",
            3: "temperatura límite actualmente",
            16: "se detectó tensión baja anteriormente",
            17: "se limitó la frecuencia anteriormente",
            18: "hubo throttling anteriormente",
            19: "se alcanzó temperatura límite anteriormente",
        }

        for bit, message in flags.items():
            if value & (1 << bit):
                messages.append(message)

        current_problem = bool(
            value & 0xF
        )

        detail = (
            f"{output} · "
            + ", ".join(messages)
        )

        if current_problem:
            self._add_error(
                "Alimentación y throttling",
                detail,
                "Comprueba la fuente, el cable USB-C y la refrigeración.",
            )
        else:
            self._add_warning(
                "Alimentación y throttling",
                detail,
                "Se detectaron problemas anteriores. Revisa la fuente de alimentación.",
            )

    # ---------------------------------------------------------
    # Salida
    # ---------------------------------------------------------

    def _print_header(self) -> None:
        print()
        print(f"{BOLD}{CYAN}=============================================={RESET}")
        print(f"{BOLD}{CYAN}              ROAD EYE DOCTOR                {RESET}")
        print(f"{BOLD}{CYAN}=============================================={RESET}")
        print(f"Proyecto: {PROJECT_DIR}")
        print()

    def _print_results(self) -> None:
        for result in self.results:
            icon, color = self._status_style(
                result.status
            )

            print(
                f"{icon} "
                f"{result.name:.<30} "
                f"{color}{result.status}{RESET}"
            )

            print(
                f"   {result.detail}"
            )

            if result.solution:
                print(
                    f"   Solución: {result.solution}"
                )

            print()

    def _print_summary(self) -> int:
        errors = sum(
            1
            for result in self.results
            if result.status == "ERROR"
        )

        warnings = sum(
            1
            for result in self.results
            if result.status == "WARNING"
        )

        print(f"{BOLD}Resumen{RESET}")
        print("----------------------------------------------")
        print(f"Errores:      {errors}")
        print(f"Advertencias: {warnings}")
        print()

        if errors:
            print(
                f"{RED}{BOLD}"
                "🔴 ROAD EYE NECESITA ATENCIÓN"
                f"{RESET}"
            )
            return 2

        if warnings:
            print(
                f"{YELLOW}{BOLD}"
                "🟠 ROAD EYE FUNCIONA CON ADVERTENCIAS"
                f"{RESET}"
            )
            return 1

        print(
            f"{GREEN}{BOLD}"
            "🟢 ROAD EYE FUNCIONANDO CORRECTAMENTE"
            f"{RESET}"
        )
        return 0

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _add_ok(
        self,
        name: str,
        detail: str,
    ) -> None:
        self.results.append(
            CheckResult(
                name=name,
                status="OK",
                detail=detail,
            )
        )

    def _add_warning(
        self,
        name: str,
        detail: str,
        solution: Optional[str] = None,
    ) -> None:
        self.results.append(
            CheckResult(
                name=name,
                status="WARNING",
                detail=detail,
                solution=solution,
            )
        )

    def _add_error(
        self,
        name: str,
        detail: str,
        solution: Optional[str] = None,
    ) -> None:
        self.results.append(
            CheckResult(
                name=name,
                status="ERROR",
                detail=detail,
                solution=solution,
            )
        )

    @staticmethod
    def _status_style(
        status: str,
    ) -> tuple[str, str]:
        if status == "OK":
            return "✅", GREEN

        if status == "WARNING":
            return "⚠️ ", YELLOW

        if status == "OPTIONAL":
            return "➖", CYAN

        return "❌", RED

    @staticmethod
    def _run(
        command: list[str],
        include_stderr: bool = False,
    ) -> str:
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=(
                    subprocess.STDOUT
                    if include_stderr
                    else subprocess.DEVNULL
                ),
                text=True,
                timeout=15,
                check=False,
            )

            return completed.stdout.strip()

        except (
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return ""

    @staticmethod
    def _read_os_release() -> dict[str, str]:
        path = Path("/etc/os-release")

        if not path.exists():
            return {}

        values: dict[str, str] = {}

        for line in path.read_text().splitlines():
            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            values[key] = value.strip().strip('"')

        return values

    def _detect_version(self) -> str:
        if VERSION_FILE.exists():
            version = VERSION_FILE.read_text().strip()

            if version:
                return version

        tag = self._run(
            [
                "git",
                "-C",
                str(PROJECT_DIR),
                "describe",
                "--tags",
                "--always",
                "--dirty",
            ]
        )

        return tag or "sin versión"


def main() -> int:
    doctor = RoadEyeDoctor()
    return doctor.run()


if __name__ == "__main__":
    raise SystemExit(main())
