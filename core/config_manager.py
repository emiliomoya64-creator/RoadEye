from __future__ import annotations

import copy
import json
import logging
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any, Optional


logger = logging.getLogger(__name__)


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_DIR / "config" / "config.json"


class ConfigError(RuntimeError):
    """
    Error relacionado con la configuración de RoadEye.
    """


class ConfigManager:
    """
    Gestor central de configuración de RoadEye.

    Características:
    - Rutas absolutas independientes del directorio de ejecución.
    - Acceso mediante claves con puntos:
          config.get("camera.front.width")
    - Valores predeterminados.
    - Escritura atómica para evitar archivos JSON incompletos.
    - Copia de seguridad antes de guardar.
    - Acceso seguro desde varios hilos.
    - Recarga desde disco.
    """

    def __init__(
        self,
        filename: Optional[str | Path] = None,
        auto_create: bool = False,
    ) -> None:
        self.path = Path(filename or DEFAULT_CONFIG_PATH).expanduser().resolve()
        self.backup_path = self.path.with_suffix(
            self.path.suffix + ".backup"
        )

        self.auto_create = bool(auto_create)
        self._lock = RLock()
        self._data: dict[str, Any] = {}

        self.load()

    # ---------------------------------------------------------
    # Carga y guardado
    # ---------------------------------------------------------

    def load(self) -> None:
        """
        Carga el JSON desde disco.

        Si el archivo no existe y auto_create=True, crea uno vacío.
        """

        with self._lock:
            if not self.path.exists():
                if self.auto_create:
                    self.path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    self._data = {}
                    self.save(create_backup=False)
                    return

                raise ConfigError(
                    f"No existe el archivo de configuración: {self.path}"
                )

            try:
                raw_data = self.path.read_text(
                    encoding="utf-8"
                )
                loaded = json.loads(raw_data)

            except json.JSONDecodeError as exc:
                raise ConfigError(
                    "El archivo de configuración contiene JSON no válido: "
                    f"{self.path}. Línea {exc.lineno}, columna {exc.colno}."
                ) from exc

            except OSError as exc:
                raise ConfigError(
                    f"No se pudo leer la configuración: {self.path}"
                ) from exc

            if not isinstance(loaded, dict):
                raise ConfigError(
                    "La raíz de config.json debe ser un objeto JSON."
                )

            self._data = loaded

    def reload(self) -> None:
        """
        Recarga la configuración desde disco.
        """

        self.load()

    def save(self, create_backup: bool = True) -> None:
        """
        Guarda la configuración mediante reemplazo atómico.

        Primero escribe un archivo temporal y después sustituye
        config.json. Así no queda un JSON incompleto si el proceso
        se interrumpe durante la escritura.
        """

        with self._lock:
            self.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if create_backup and self.path.exists():
                try:
                    self.backup_path.write_bytes(
                        self.path.read_bytes()
                    )
                except OSError as exc:
                    raise ConfigError(
                        "No se pudo crear la copia de seguridad: "
                        f"{self.backup_path}"
                    ) from exc

            serialized = json.dumps(
                self._data,
                indent=4,
                ensure_ascii=False,
                sort_keys=False,
            ) + "\n"

            temporary_path: Optional[Path] = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self.path.parent,
                    prefix=f".{self.path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temporary_file:
                    temporary_file.write(serialized)
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())

                    temporary_path = Path(
                        temporary_file.name
                    )

                os.replace(
                    temporary_path,
                    self.path,
                )

            except OSError as exc:
                if (
                    temporary_path is not None
                    and temporary_path.exists()
                ):
                    temporary_path.unlink(
                        missing_ok=True
                    )

                raise ConfigError(
                    f"No se pudo guardar la configuración: {self.path}"
                ) from exc

    # ---------------------------------------------------------
    # Lectura
    # ---------------------------------------------------------

    def get(
        self,
        key: str,
        default: Any = None,
        required: bool = False,
    ) -> Any:
        """
        Obtiene un valor usando una ruta separada por puntos.

        Ejemplos:
            config.get("camera.front.width")
            config.get("adas.enabled", False)

        Si required=True y la clave no existe, lanza ConfigError.
        """

        keys = self._split_key(key)

        with self._lock:
            value: Any = self._data

            for part in keys:
                if (
                    not isinstance(value, dict)
                    or part not in value
                ):
                    if required:
                        raise ConfigError(
                            f"Falta la clave obligatoria: {key}"
                        )

                    return copy.deepcopy(default)

                value = value[part]

            return copy.deepcopy(value)

    def require(self, key: str) -> Any:
        """
        Obtiene una clave obligatoria.
        """

        return self.get(
            key,
            required=True,
        )

    def has(self, key: str) -> bool:
        """
        Indica si existe una clave.
        """

        marker = object()

        return self.get(
            key,
            default=marker,
        ) is not marker

    def section(
        self,
        key: str,
        default: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Obtiene una sección completa y valida que sea un diccionario.
        """

        value = self.get(
            key,
            default=default or {},
        )

        if not isinstance(value, dict):
            raise ConfigError(
                f"La sección '{key}' debe ser un objeto JSON."
            )

        return value

    def as_dict(self) -> dict[str, Any]:
        """
        Devuelve una copia completa de la configuración.
        """

        with self._lock:
            return copy.deepcopy(
                self._data
            )

    # ---------------------------------------------------------
    # Escritura
    # ---------------------------------------------------------

    def set(
        self,
        key: str,
        value: Any,
        save: bool = True,
    ) -> None:
        """
        Establece un valor, creando las secciones intermedias.

        Ejemplo:
            config.set("display.hdmi.enabled", True)
        """

        keys = self._split_key(key)

        with self._lock:
            current = self._data

            for part in keys[:-1]:
                existing = current.get(part)

                if existing is None:
                    current[part] = {}
                    existing = current[part]

                if not isinstance(existing, dict):
                    raise ConfigError(
                        "No se puede crear la clave "
                        f"'{key}' porque '{part}' no es una sección."
                    )

                current = existing

            current[keys[-1]] = copy.deepcopy(
                value
            )

            if save:
                self.save()

    def update(
        self,
        values: dict[str, Any],
        save: bool = True,
    ) -> None:
        """
        Fusiona recursivamente valores con la configuración existente.
        """

        if not isinstance(values, dict):
            raise TypeError(
                "ConfigManager.update() requiere un diccionario."
            )

        with self._lock:
            self._deep_merge(
                self._data,
                values,
            )

            if save:
                self.save()

    def delete(
        self,
        key: str,
        save: bool = True,
    ) -> bool:
        """
        Elimina una clave. Devuelve True si existía.
        """

        keys = self._split_key(key)

        with self._lock:
            current: Any = self._data

            for part in keys[:-1]:
                if (
                    not isinstance(current, dict)
                    or part not in current
                ):
                    return False

                current = current[part]

            if (
                not isinstance(current, dict)
                or keys[-1] not in current
            ):
                return False

            del current[keys[-1]]

            if save:
                self.save()

            return True

    # ---------------------------------------------------------
    # Validación básica
    # ---------------------------------------------------------

    def validate_required(
        self,
        required_keys: list[str],
    ) -> list[str]:
        """
        Devuelve las claves obligatorias que faltan.
        """

        return [
            key
            for key in required_keys
            if not self.has(key)
        ]

    # ---------------------------------------------------------
    # Utilidades internas
    # ---------------------------------------------------------

    @staticmethod
    def _split_key(key: str) -> list[str]:
        if not isinstance(key, str):
            raise TypeError(
                "La clave de configuración debe ser texto."
            )

        parts = [
            part.strip()
            for part in key.split(".")
            if part.strip()
        ]

        if not parts:
            raise ValueError(
                "La clave de configuración no puede estar vacía."
            )

        return parts

    @classmethod
    def _deep_merge(
        cls,
        destination: dict[str, Any],
        source: dict[str, Any],
    ) -> None:
        for key, value in source.items():
            if (
                isinstance(value, dict)
                and isinstance(destination.get(key), dict)
            ):
                cls._deep_merge(
                    destination[key],
                    value,
                )
            else:
                destination[key] = copy.deepcopy(
                    value
                )


config = ConfigManager()