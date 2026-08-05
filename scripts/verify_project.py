#!/usr/bin/env python3

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


REQUIRED_DIRECTORIES = [
    "config",
    "core",
    "recorder",
    "static",
    "templates",
    "trip",
    "videos",
    "web",
]


REQUIRED_FILES = [
    "app.py",
    "config/config.json",
    "core/config_manager.py",
    "core/storage_manager.py",
    "recorder/recorder_service.py",
    "templates/index.html",
    "web/api.py",
    "web/server.py",
]


PYTHON_FILES = [
    "app.py",
    "core/config_manager.py",
    "core/storage_manager.py",
    "recorder/recorder_service.py",
    "trip/trip_manager.py",
    "trip/trip_session.py",
    "web/api.py",
    "web/server.py",
]


def ok(message: str) -> None:
    print(f"[ OK ] {message}")


def warning(message: str) -> None:
    print(f"[WARN] {message}")


def error(message: str) -> None:
    print(f"[FAIL] {message}")


def check_directories() -> int:
    failures = 0

    for name in REQUIRED_DIRECTORIES:
        path = PROJECT_DIR / name

        if path.is_dir():
            ok(f"Directorio {name}")
        else:
            error(f"Falta el directorio {name}")
            failures += 1

    return failures


def check_files() -> int:
    failures = 0

    for name in REQUIRED_FILES:
        path = PROJECT_DIR / name

        if path.is_file():
            ok(f"Archivo {name}")
        else:
            error(f"Falta el archivo {name}")
            failures += 1

    return failures


def check_python() -> int:
    failures = 0

    for name in PYTHON_FILES:
        path = PROJECT_DIR / name

        if not path.exists():
            continue

        try:
            py_compile.compile(
                str(path),
                doraise=True,
            )

            ok(f"Sintaxis Python: {name}")

        except py_compile.PyCompileError as exc:
            error(
                f"Error Python en {name}: {exc.msg}"
            )

            failures += 1

    return failures


def check_config() -> int:
    path = PROJECT_DIR / "config/config.json"

    if not path.exists():
        return 1

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        error(
            f"config.json no es válido: {exc}"
        )

        return 1

    if not isinstance(data, dict):
        error(
            "config.json no contiene un objeto JSON."
        )

        return 1

    ok("config.json válido")

    failures = 0

    for section in (
        "recording",
        "storage",
        "parking",
    ):
        if isinstance(
            data.get(section),
            dict,
        ):
            ok(
                f"Configuración: {section}"
            )
        else:
            error(
                f"Falta la sección: {section}"
            )
            failures += 1

    return failures


def check_control_center() -> int:
    required = [
        "static/control-center/index.html",
        "static/control-center/control-center.css",
        "static/control-center/control-center.js",
    ]

    missing = [
        name
        for name in required
        if not (
            PROJECT_DIR / name
        ).is_file()
    ]

    if missing:
        warning(
            "Control Center pendiente: "
            + ", ".join(missing)
        )

        return 0

    ok("RoadEye Control Center instalado")

    return 0


def check_git() -> int:
    try:
        branch = subprocess.run(
            [
                "git",
                "branch",
                "--show-current",
            ],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        status = subprocess.run(
            [
                "git",
                "status",
                "--short",
            ],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    except (
        OSError,
        subprocess.CalledProcessError,
    ):
        warning("No se pudo consultar Git")
        return 0

    ok(
        f"Rama Git: {branch or 'desconocida'}"
    )

    if status:
        warning(
            "Hay cambios pendientes en Git"
        )

        print(status)
    else:
        ok("Árbol de trabajo limpio")

    return 0


def main() -> int:
    print()
    print("=" * 55)
    print("       RoadEye · Verificación del proyecto")
    print("=" * 55)
    print()

    failures = 0

    failures += check_directories()
    failures += check_files()
    failures += check_python()
    failures += check_config()
    failures += check_control_center()
    failures += check_git()

    print()
    print("-" * 55)

    if failures:
        print(
            f"Resultado: {failures} problema(s) crítico(s)."
        )

        return 1

    print("Resultado: proyecto base correcto.")

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
