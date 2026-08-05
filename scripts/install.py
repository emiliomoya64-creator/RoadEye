#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"


def run_script(
    name: str,
) -> None:
    path = SCRIPTS_DIR / name

    if not path.exists():
        print()
        print(
            f"El módulo {name} todavía no existe."
        )
        input(
            "\nPulsa Enter para continuar..."
        )
        return

    subprocess.run(
        [
            sys.executable,
            str(path),
        ],
        cwd=PROJECT_DIR,
        check=False,
    )

    input(
        "\nPulsa Enter para continuar..."
    )


def menu() -> None:
    while True:
        print(
            "\033[2J\033[H",
            end="",
        )

        print("=" * 52)
        print("          RoadEye Developer Kit")
        print("=" * 52)
        print()
        print("1) Verificar proyecto")
        print("2) RoadEye Doctor")
        print("3) Instalar Control Center")
        print("4) Instalar Modo Parking")
        print("5) Crear copia de seguridad")
        print("6) Salir")
        print()

        option = input(
            "Selecciona una opción: "
        ).strip()

        if option == "1":
            run_script(
                "verify_project.py"
            )

        elif option == "2":
            run_script(
                "doctor.py"
            )

        elif option == "3":
            run_script(
                "install_control_center.py"
            )

        elif option == "4":
            run_script(
                "install_parking_mode.py"
            )

        elif option == "5":
            run_script(
                "backup_project.py"
            )

        elif option == "6":
            return

        else:
            input(
                "Opción no válida. Pulsa Enter..."
            )


if __name__ == "__main__":
    menu()
