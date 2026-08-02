from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Any, Optional, Protocol


logger = logging.getLogger(__name__)


class ServiceState(str, Enum):
    """
    Estados posibles de un servicio de RoadEye.
    """

    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"


class ServiceProtocol(Protocol):
    """
    Contrato mínimo que debe cumplir un servicio RoadEye.
    """

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...


@dataclass
class ServiceStatus:
    """
    Estado público de un servicio registrado.
    """

    name: str
    state: ServiceState
    enabled: bool
    critical: bool
    description: str
    started_at: Optional[float]
    stopped_at: Optional[float]
    restart_count: int
    last_error: Optional[str]

    @property
    def uptime_seconds(self) -> float:
        """
        Tiempo que lleva activo el servicio.
        """

        if (
            self.state != ServiceState.RUNNING
            or self.started_at is None
        ):
            return 0.0

        return max(
            0.0,
            time.monotonic() - self.started_at,
        )

    def as_dict(self) -> dict[str, Any]:
        """
        Convierte el estado en un diccionario serializable.
        """

        return {
            "name": self.name,
            "state": self.state.value,
            "enabled": self.enabled,
            "critical": self.critical,
            "description": self.description,
            "uptime_seconds": round(
                self.uptime_seconds,
                2,
            ),
            "restart_count": self.restart_count,
            "last_error": self.last_error,
        }


class ManagedService:
    """
    Adaptador que permite al ServiceManager controlar cualquier
    objeto que implemente start() y stop().

    No obliga a modificar inmediatamente los servicios existentes.
    """

    def __init__(
        self,
        name: str,
        service: ServiceProtocol,
        *,
        description: str = "",
        enabled: bool = True,
        critical: bool = False,
        start_order: int = 100,
        stop_order: Optional[int] = None,
    ) -> None:
        cleaned_name = str(name).strip()

        if not cleaned_name:
            raise ValueError(
                "El nombre del servicio no puede estar vacío"
            )

        if not hasattr(service, "start"):
            raise TypeError(
                f"El servicio '{cleaned_name}' no tiene start()"
            )

        if not hasattr(service, "stop"):
            raise TypeError(
                f"El servicio '{cleaned_name}' no tiene stop()"
            )

        self.name = cleaned_name
        self.service = service
        self.description = str(description).strip()
        self.enabled = bool(enabled)
        self.critical = bool(critical)
        self.start_order = int(start_order)

        self.stop_order = (
            int(stop_order)
            if stop_order is not None
            else -self.start_order
        )

        self._state = (
            ServiceState.REGISTERED
            if self.enabled
            else ServiceState.DISABLED
        )

        self._started_at: Optional[float] = None
        self._stopped_at: Optional[float] = None
        self._restart_count = 0
        self._last_error: Optional[str] = None
        self._lock = RLock()

    # ---------------------------------------------------------
    # Estado
    # ---------------------------------------------------------

    @property
    def state(self) -> ServiceState:
        with self._lock:
            return self._state

    @property
    def running(self) -> bool:
        """
        Intenta consultar el estado real del servicio.

        Si el servicio dispone de una propiedad running, se usa.
        Si no existe, se utiliza el estado controlado internamente.
        """

        with self._lock:
            external_running = getattr(
                self.service,
                "running",
                None,
            )

            if isinstance(external_running, bool):
                return external_running

            return self._state == ServiceState.RUNNING

    def status(self) -> ServiceStatus:
        """
        Devuelve una instantánea del estado.
        """

        with self._lock:
            state = self._state

            if (
                state == ServiceState.RUNNING
                and not self.running
            ):
                state = ServiceState.STOPPED

            return ServiceStatus(
                name=self.name,
                state=state,
                enabled=self.enabled,
                critical=self.critical,
                description=self.description,
                started_at=self._started_at,
                stopped_at=self._stopped_at,
                restart_count=self._restart_count,
                last_error=self._last_error,
            )

    # ---------------------------------------------------------
    # Control
    # ---------------------------------------------------------

    def start(self) -> bool:
        """
        Inicia el servicio.

        Devuelve True si queda funcionando o ya estaba activo.
        """

        with self._lock:
            if not self.enabled:
                self._state = ServiceState.DISABLED
                return False

            if self.running:
                self._state = ServiceState.RUNNING
                return True

            self._state = ServiceState.STARTING
            self._last_error = None

        try:
            logger.info(
                "Iniciando servicio '%s'",
                self.name,
            )

            self.service.start()

            with self._lock:
                self._state = ServiceState.RUNNING
                self._started_at = time.monotonic()
                self._stopped_at = None

            logger.info(
                "Servicio '%s' iniciado",
                self.name,
            )

            return True

        except Exception as exc:
            with self._lock:
                self._state = ServiceState.ERROR
                self._last_error = (
                    f"{type(exc).__name__}: {exc}"
                )

            logger.exception(
                "Error iniciando servicio '%s'",
                self.name,
            )

            return False

    def stop(self) -> bool:
        """
        Detiene el servicio.

        Devuelve True si queda detenido.
        """

        with self._lock:
            if self._state in {
                ServiceState.STOPPED,
                ServiceState.REGISTERED,
                ServiceState.DISABLED,
            }:
                return True

            self._state = ServiceState.STOPPING

        try:
            logger.info(
                "Deteniendo servicio '%s'",
                self.name,
            )

            self.service.stop()

            with self._lock:
                self._state = ServiceState.STOPPED
                self._stopped_at = time.monotonic()

            logger.info(
                "Servicio '%s' detenido",
                self.name,
            )

            return True

        except Exception as exc:
            with self._lock:
                self._state = ServiceState.ERROR
                self._last_error = (
                    f"{type(exc).__name__}: {exc}"
                )

            logger.exception(
                "Error deteniendo servicio '%s'",
                self.name,
            )

            return False

    def restart(self) -> bool:
        """
        Reinicia el servicio.
        """

        with self._lock:
            self._restart_count += 1

        stopped = self.stop()

        if not stopped:
            return False

        return self.start()

    def enable(self) -> None:
        """
        Habilita el servicio para futuros arranques.
        """

        with self._lock:
            self.enabled = True

            if self._state == ServiceState.DISABLED:
                self._state = ServiceState.REGISTERED

    def disable(
        self,
        stop_if_running: bool = True,
    ) -> bool:
        """
        Deshabilita el servicio.

        Opcionalmente lo detiene si está funcionando.
        """

        if stop_if_running and self.running:
            if not self.stop():
                return False

        with self._lock:
            self.enabled = False
            self._state = ServiceState.DISABLED

        return True
