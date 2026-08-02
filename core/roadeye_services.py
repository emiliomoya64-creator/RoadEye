from __future__ import annotations

import logging

from cameras.camera_service import CameraService
from core.config_manager import config
from core.render_service import render_service
from core.service_manager import ServiceManager
from display.hdmi_display_service import (
    hdmi_display_service,
)
from gps.gps_service import GPSService
from gps.map_service import MapService


logger = logging.getLogger(__name__)


class RoadEyeServices:
    """
    Construye y registra los servicios principales de RoadEye.

    Orden de arranque:

        10  Cámara
        20  GPS
        30  Mapas
        40  Render
        50  HDMI

    La parada se realiza automáticamente en orden inverso.
    """

    def __init__(self) -> None:
        self.manager = ServiceManager()

        self.camera = CameraService()
        self.gps = GPSService()
        self.maps = MapService()

        self.render = render_service
        self.hdmi = hdmi_display_service

        self._register_services()

    def _register_services(self) -> None:
        self.manager.register(
            "camera",
            self.camera,
            description="Cámara frontal",
            enabled=bool(
                config.get(
                    "camera.front.enabled",
                    True,
                )
            ),
            critical=True,
            start_order=10,
        )

        self.manager.register(
            "gps",
            self.gps,
            description="Receptor GPS",
            enabled=bool(
                config.get(
                    "gps.enabled",
                    True,
                )
            ),
            critical=False,
            start_order=20,
        )

        self.manager.register(
            "maps",
            self.maps,
            description="Información cartográfica",
            enabled=bool(
                config.get(
                    "gps.map_service",
                    True,
                )
            ),
            critical=False,
            start_order=30,
        )

        self.manager.register(
            "render",
            self.render,
            description="Render central HUD",
            enabled=bool(
                config.get(
                    "render.enabled",
                    True,
                )
            ),
            critical=True,
            start_order=40,
        )

        self.manager.register(
            "hdmi",
            self.hdmi,
            description="Pantalla HDMI",
            enabled=bool(
                config.get(
                    "display.hdmi.enabled",
                    True,
                )
            ),
            critical=False,
            start_order=50,
        )

    def start_all(self) -> bool:
        logger.info(
            "Arrancando servicios principales de RoadEye"
        )

        result = self.manager.start_all(
            stop_on_critical_error=True,
        )

        self._log_status()

        return result

    def stop_all(self) -> bool:
        logger.info(
            "Deteniendo servicios principales de RoadEye"
        )

        result = self.manager.stop_all()

        self._log_status()

        return result

    def status(self) -> dict:
        return self.manager.status()

    def summary(self) -> dict:
        return self.manager.summary()

    def _log_status(self) -> None:
        for name, status in self.status().items():
            logger.info(
                "Servicio %-10s estado=%s error=%s",
                name,
                status["state"],
                status["last_error"],
            )


roadeye_services = RoadEyeServices()
