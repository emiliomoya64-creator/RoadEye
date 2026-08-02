from __future__ import annotations

import logging
from collections import OrderedDict
from threading import RLock
from typing import Any, Optional

from core.service import (
    ManagedService,
    ServiceProtocol,
    ServiceState,
)


logger = logging.getLogger(__name__)


class ServiceManagerError(RuntimeError):
    """
    Error general del gestor de servicios.
    """


class ServiceAlreadyRegisteredError(
    ServiceManagerError
):
    """
    Se intentó registrar dos veces el mismo nombre.
    """


class ServiceNotFoundError(ServiceManagerError):
    """
    El servicio solicitado no está registrado.
    """


class CriticalServiceError(ServiceManagerError):
    """
    Falló un servicio marcado como crítico.
    """


class ServiceManager:
    """
    Director de servicios de RoadEye.

    Responsabilidades:
    - Registrar servicios.
    - Respetar el orden de arranque.
    - Detener en orden inverso.
    - Consultar estados.
    - Reiniciar servicios individualmente.
    - Detectar fallos en servicios críticos.
    """

    def __init__(self) -> None:
        self._services: OrderedDict[
            str,
            ManagedService,
        ] = OrderedDict()

        self._lock = RLock()
        self._started = False

    # ---------------------------------------------------------
    # Registro
    # ---------------------------------------------------------

    def register(
        self,
        name: str,
        service: ServiceProtocol,
        *,
        description: str = "",
        enabled: bool = True,
        critical: bool = False,
        start_order: int = 100,
        stop_order: Optional[int] = None,
    ) -> ManagedService:
        """
        Registra un servicio.

        Ejemplo:

            service_manager.register(
                "camera",
                camera_service,
                critical=True,
                start_order=10,
            )
        """

        normalized_name = self._normalize_name(
            name
        )

        with self._lock:
            if normalized_name in self._services:
                raise ServiceAlreadyRegisteredError(
                    "Ya existe un servicio registrado "
                    f"con el nombre '{normalized_name}'"
                )

            managed = ManagedService(
                name=normalized_name,
                service=service,
                description=description,
                enabled=enabled,
                critical=critical,
                start_order=start_order,
                stop_order=stop_order,
            )

            self._services[
                normalized_name
            ] = managed

        logger.info(
            "Servicio registrado: %s",
            normalized_name,
        )

        return managed

    def unregister(
        self,
        name: str,
        stop_if_running: bool = True,
    ) -> bool:
        """
        Elimina un servicio del gestor.
        """

        normalized_name = self._normalize_name(
            name
        )

        with self._lock:
            managed = self._services.get(
                normalized_name
            )

        if managed is None:
            return False

        if (
            stop_if_running
            and managed.running
            and not managed.stop()
        ):
            return False

        with self._lock:
            self._services.pop(
                normalized_name,
                None,
            )

        logger.info(
            "Servicio eliminado: %s",
            normalized_name,
        )

        return True

    # ---------------------------------------------------------
    # Acceso
    # ---------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> ManagedService:
        normalized_name = self._normalize_name(
            name
        )

        with self._lock:
            managed = self._services.get(
                normalized_name
            )

        if managed is None:
            raise ServiceNotFoundError(
                f"No existe el servicio '{normalized_name}'"
            )

        return managed

    def has(
        self,
        name: str,
    ) -> bool:
        normalized_name = self._normalize_name(
            name
        )

        with self._lock:
            return normalized_name in self._services

    def names(self) -> list[str]:
        with self._lock:
            return list(
                self._services.keys()
            )

    # ---------------------------------------------------------
    # Arranque y parada
    # ---------------------------------------------------------

    def start(
        self,
        name: str,
    ) -> bool:
        """
        Inicia un único servicio.
        """

        managed = self.get(name)
        result = managed.start()

        if not result and managed.critical:
            raise CriticalServiceError(
                f"Falló el servicio crítico '{managed.name}': "
                f"{managed.status().last_error}"
            )

        return result

    def stop(
        self,
        name: str,
    ) -> bool:
        """
        Detiene un único servicio.
        """

        return self.get(name).stop()

    def restart(
        self,
        name: str,
    ) -> bool:
        """
        Reinicia un único servicio.
        """

        managed = self.get(name)
        result = managed.restart()

        if not result and managed.critical:
            raise CriticalServiceError(
                f"Falló el reinicio del servicio crítico "
                f"'{managed.name}': "
                f"{managed.status().last_error}"
            )

        return result

    def start_all(
        self,
        stop_on_critical_error: bool = True,
    ) -> bool:
        """
        Inicia todos los servicios habilitados por orden.

        Si falla un servicio crítico:
        - detiene los ya iniciados;
        - lanza CriticalServiceError.
        """

        services = self._services_for_start()

        started_names: list[str] = []
        all_started = True

        logger.info(
            "Iniciando %d servicios RoadEye",
            len(services),
        )

        for managed in services:
            if not managed.enabled:
                continue

            result = managed.start()

            if result:
                started_names.append(
                    managed.name
                )
                continue

            all_started = False

            if (
                managed.critical
                and stop_on_critical_error
            ):
                logger.error(
                    "Falló el servicio crítico '%s'. "
                    "Deteniendo servicios iniciados.",
                    managed.name,
                )

                self._stop_selected(
                    started_names
                )

                self._started = False

                raise CriticalServiceError(
                    f"Falló el servicio crítico "
                    f"'{managed.name}': "
                    f"{managed.status().last_error}"
                )

        self._started = all_started

        return all_started

    def stop_all(self) -> bool:
        """
        Detiene todos los servicios en orden de parada.
        """

        services = self._services_for_stop()
        all_stopped = True

        logger.info(
            "Deteniendo %d servicios RoadEye",
            len(services),
        )

        for managed in services:
            if not managed.stop():
                all_stopped = False

        self._started = False

        return all_stopped

    # ---------------------------------------------------------
    # Habilitar y deshabilitar
    # ---------------------------------------------------------

    def enable(
        self,
        name: str,
    ) -> None:
        self.get(name).enable()

    def disable(
        self,
        name: str,
        stop_if_running: bool = True,
    ) -> bool:
        return self.get(name).disable(
            stop_if_running=stop_if_running,
        )

    # ---------------------------------------------------------
    # Estado
    # ---------------------------------------------------------

    def status(
        self,
        name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Devuelve el estado de un servicio o de todos.

        service_manager.status("gps")

        service_manager.status()
        """

        if name is not None:
            managed = self.get(name)

            return managed.status().as_dict()

        with self._lock:
            services = list(
                self._services.values()
            )

        return {
            managed.name: managed.status().as_dict()
            for managed in services
        }

    def summary(self) -> dict[str, Any]:
        """
        Devuelve un resumen numérico del sistema.
        """

        statuses = self.status()

        counts = {
            state.value: 0
            for state in ServiceState
        }

        for status in statuses.values():
            state = status["state"]

            counts[state] = (
                counts.get(state, 0) + 1
            )

        return {
            "registered": len(statuses),
            "manager_started": self._started,
            "states": counts,
            "services": statuses,
        }

    # ---------------------------------------------------------
    # Utilidades internas
    # ---------------------------------------------------------

    def _services_for_start(
        self,
    ) -> list[ManagedService]:
        with self._lock:
            return sorted(
                self._services.values(),
                key=lambda item: (
                    item.start_order,
                    item.name,
                ),
            )

    def _services_for_stop(
        self,
    ) -> list[ManagedService]:
        with self._lock:
            return sorted(
                self._services.values(),
                key=lambda item: (
                    item.stop_order,
                    item.name,
                ),
            )

    def _stop_selected(
        self,
        names: list[str],
    ) -> None:
        selected = [
            self.get(name)
            for name in names
        ]

        selected.sort(
            key=lambda item: (
                item.stop_order,
                item.name,
            )
        )

        for managed in selected:
            managed.stop()

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        normalized = str(name).strip().lower()

        if not normalized:
            raise ValueError(
                "El nombre del servicio no puede estar vacío"
            )

        return normalized


service_manager = ServiceManager()
