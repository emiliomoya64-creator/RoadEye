from __future__ import annotations

import json
import logging
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from core.config_manager import PROJECT_DIR
from startup.boot_screen import (
    BootCheck,
    BootCheckState,
)


logger = logging.getLogger(__name__)


@dataclass
class BootCheckDefinition:
    """
    Define una comprobación rápida del arranque.

    key:
        Identificador interno.

    label:
        Texto mostrado en pantalla.

    critical:
        Si es True, un fallo impide considerar RoadEye preparado.

    checker:
        Función que ejecuta la comprobación.
    """

    key: str
    label: str
    critical: bool
    checker: Callable[[], tuple[BootCheckState, str]]


class BootChecks:
    """
    Conjunto de comprobaciones rápidas del arranque de RoadEye.

    Estas pruebas deben ser:

    - rápidas;
    - no destructivas;
    - sin modificar el sistema;
    - adecuadas para ejecutarse en cada arranque.

    RoadEye Doctor seguirá siendo el diagnóstico completo.
    """

    CONFIG_PATH = PROJECT_DIR / "config" / "config.json"
    VERSION_PATH = PROJECT_DIR / "VERSION"

    CAMERA_DEVICE_CANDIDATES = (
        Path("/dev/video0"),
        Path("/dev/media0"),
        Path("/dev/media1"),
        Path("/dev/media2"),
    )

    GPS_DEVICE = Path("/dev/serial0")

    DRM_CONNECTORS = Path("/sys/class/drm")

    MINIMUM_FREE_GB = 2.0
    WARNING_FREE_GB = 10.0

    def __init__(self) -> None:
        self._definitions: list[
            BootCheckDefinition
        ] = [
            BootCheckDefinition(
                key="config",
                label="Configuración",
                critical=True,
                checker=self._check_configuration,
            ),
            BootCheckDefinition(
                key="storage",
                label="Almacenamiento",
                critical=True,
                checker=self._check_storage,
            ),
            BootCheckDefinition(
                key="camera",
                label="Cámara IMX219",
                critical=True,
                checker=self._check_camera,
            ),
            BootCheckDefinition(
                key="gps",
                label="Receptor GPS",
                critical=False,
                checker=self._check_gps,
            ),
            BootCheckDefinition(
                key="hdmi",
                label="Pantalla HDMI",
                critical=False,
                checker=self._check_hdmi,
            ),
            BootCheckDefinition(
                key="network",
                label="Red",
                critical=False,
                checker=self._check_network,
            ),
            BootCheckDefinition(
                key="version",
                label="Versión RoadEye",
                critical=True,
                checker=self._check_version,
            ),
        ]

    # ---------------------------------------------------------
    # Información pública
    # ---------------------------------------------------------

    def definitions(
        self,
    ) -> list[BootCheckDefinition]:
        """
        Devuelve las definiciones registradas.
        """

        return list(
            self._definitions
        )

    def initial_checks(
        self,
    ) -> list[BootCheck]:
        """
        Genera la lista inicial para BootScreen.
        """

        return [
            BootCheck(
                key=definition.key,
                label=definition.label,
                state=BootCheckState.PENDING,
                detail="",
            )
            for definition in self._definitions
        ]

    def run(
        self,
        key: str,
    ) -> tuple[
        BootCheckState,
        str,
        bool,
    ]:
        """
        Ejecuta una comprobación concreta.

        Devuelve:

            estado,
            detalle,
            es_critica
        """

        definition = self._find_definition(
            key
        )

        if definition is None:
            return (
                BootCheckState.ERROR,
                f"Comprobación desconocida: {key}",
                True,
            )

        try:
            state, detail = (
                definition.checker()
            )

            return (
                state,
                detail,
                definition.critical,
            )

        except Exception as exc:
            logger.exception(
                "Error ejecutando comprobación '%s'",
                key,
            )

            return (
                BootCheckState.ERROR,
                f"{type(exc).__name__}: {exc}",
                definition.critical,
            )

    def run_all(
        self,
    ) -> list[
        tuple[
            BootCheck,
            bool,
        ]
    ]:
        """
        Ejecuta todas las comprobaciones.

        Devuelve pares:

            BootCheck,
            critical
        """

        results: list[
            tuple[
                BootCheck,
                bool,
            ]
        ] = []

        for definition in self._definitions:
            state, detail, critical = (
                self.run(
                    definition.key
                )
            )

            results.append(
                (
                    BootCheck(
                        key=definition.key,
                        label=definition.label,
                        state=state,
                        detail=detail,
                    ),
                    critical,
                )
            )

        return results

    # ---------------------------------------------------------
    # Comprobaciones
    # ---------------------------------------------------------

    def _check_configuration(
        self,
    ) -> tuple[
        BootCheckState,
        str,
    ]:
        if not self.CONFIG_PATH.exists():
            return (
                BootCheckState.ERROR,
                "No existe config/config.json",
            )

        try:
            content = self.CONFIG_PATH.read_text(
                encoding="utf-8"
            )

            data = json.loads(
                content
            )

        except json.JSONDecodeError as exc:
            return (
                BootCheckState.ERROR,
                (
                    "JSON inválido "
                    f"línea {exc.lineno}"
                ),
            )

        except OSError as exc:
            return (
                BootCheckState.ERROR,
                str(exc),
            )

        if not isinstance(
            data,
            dict,
        ):
            return (
                BootCheckState.ERROR,
                "La raíz del JSON no es un objeto",
            )

        required_sections = (
            "project",
            "camera",
            "display",
            "web",
            "gps",
            "recording",
        )

        missing = [
            section
            for section in required_sections
            if section not in data
        ]

        if missing:
            return (
                BootCheckState.ERROR,
                "Faltan: "
                + ", ".join(
                    missing
                ),
            )

        return (
            BootCheckState.OK,
            "config.json válido",
        )

    def _check_storage(
        self,
    ) -> tuple[
        BootCheckState,
        str,
    ]:
        usage = shutil.disk_usage(
            PROJECT_DIR
        )

        free_gb = (
            usage.free
            / 1024
            / 1024
            / 1024
        )

        if free_gb < self.MINIMUM_FREE_GB:
            return (
                BootCheckState.ERROR,
                f"Solo {free_gb:.1f} GB libres",
            )

        if free_gb < self.WARNING_FREE_GB:
            return (
                BootCheckState.WARNING,
                f"{free_gb:.1f} GB libres",
            )

        return (
            BootCheckState.OK,
            f"{free_gb:.1f} GB libres",
        )

    def _check_camera(
        self,
    ) -> tuple[
        BootCheckState,
        str,
    ]:
        model_files = list(
            Path(
                "/sys/bus/i2c/devices"
            ).glob(
                "*/name"
            )
        )

        for model_file in model_files:
            try:
                name = model_file.read_text(
                    encoding="utf-8"
                ).strip()

            except OSError:
                continue

            if "imx219" in name.lower():
                return (
                    BootCheckState.OK,
                    "Sensor IMX219 detectado",
                )

        existing_devices = [
            str(path)
            for path in self.CAMERA_DEVICE_CANDIDATES
            if path.exists()
        ]

        if existing_devices:
            return (
                BootCheckState.WARNING,
                "Dispositivo de cámara presente",
            )

        return (
            BootCheckState.ERROR,
            "No se detecta la cámara",
        )

    def _check_gps(
        self,
    ) -> tuple[
        BootCheckState,
        str,
    ]:
        if not self.GPS_DEVICE.exists():
            return (
                BootCheckState.WARNING,
                "/dev/serial0 no existe",
            )

        try:
            resolved = self.GPS_DEVICE.resolve()

            return (
                BootCheckState.OK,
                f"{self.GPS_DEVICE} → {resolved}",
            )

        except OSError:
            return (
                BootCheckState.OK,
                str(
                    self.GPS_DEVICE
                ),
            )

    def _check_hdmi(
        self,
    ) -> tuple[
        BootCheckState,
        str,
    ]:
        if not self.DRM_CONNECTORS.exists():
            return (
                BootCheckState.WARNING,
                "DRM no disponible",
            )

        connectors = sorted(
            self.DRM_CONNECTORS.glob(
                "card*-HDMI-A-*"
            )
        )

        if not connectors:
            return (
                BootCheckState.WARNING,
                "No se encuentra HDMI",
            )

        for connector in connectors:
            status_file = (
                connector / "status"
            )

            modes_file = (
                connector / "modes"
            )

            try:
                status = status_file.read_text(
                    encoding="utf-8"
                ).strip()

            except OSError:
                continue

            if status != "connected":
                continue

            mode = "conectado"

            try:
                modes = [
                    line.strip()
                    for line in modes_file.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if line.strip()
                ]

                if modes:
                    mode = modes[0]

            except OSError:
                pass

            return (
                BootCheckState.OK,
                f"{connector.name} · {mode}",
            )

        return (
            BootCheckState.WARNING,
            "Monitor HDMI no conectado",
        )

    def _check_network(
        self,
    ) -> tuple[
        BootCheckState,
        str,
    ]:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.settimeout(
            1.0
        )

        try:
            sock.connect(
                (
                    "8.8.8.8",
                    80,
                )
            )

            ip_address = (
                sock.getsockname()[0]
            )

            return (
                BootCheckState.OK,
                ip_address,
            )

        except OSError:
            return (
                BootCheckState.WARNING,
                "Sin conexión de red",
            )

        finally:
            sock.close()

    def _check_version(
        self,
    ) -> tuple[
        BootCheckState,
        str,
    ]:
        if not self.VERSION_PATH.exists():
            return (
                BootCheckState.ERROR,
                "No existe VERSION",
            )

        try:
            version = (
                self.VERSION_PATH.read_text(
                    encoding="utf-8"
                ).strip()
            )

        except OSError as exc:
            return (
                BootCheckState.ERROR,
                str(exc),
            )

        if not version:
            return (
                BootCheckState.ERROR,
                "VERSION está vacío",
            )

        return (
            BootCheckState.OK,
            f"v{version}",
        )

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _find_definition(
        self,
        key: str,
    ) -> Optional[
        BootCheckDefinition
    ]:
        normalized = str(
            key
        ).strip().lower()

        for definition in self._definitions:
            if definition.key == normalized:
                return definition

        return None
