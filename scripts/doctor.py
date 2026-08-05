#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


def command_output(
    command: list[str],
) -> str:
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    except (
        OSError,
        subprocess.CalledProcessError,
    ):
        return ""


def api_json(
    path: str,
) -> dict:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:8000{path}",
            timeout=3,
        ) as response:
            return json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except (
        OSError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ):
        return {}


def line(
    name: str,
    value: str,
    healthy: bool = True,
) -> None:
    symbol = "OK" if healthy else "!!"

    print(
        f"[{symbol:>2}] {name:<24} {value}"
    )


def main() -> int:
    print()
    print("=" * 55)
    print("              RoadEye Doctor")
    print("=" * 55)
    print()

    service = command_output(
        [
            "systemctl",
            "is-active",
            "roadeye.service",
        ]
    )

    line(
        "Servicio RoadEye",
        service or "desconocido",
        service == "active",
    )

    status = api_json(
        "/api/status"
    )

    line(
        "API",
        "responde" if status else "sin respuesta",
        bool(status),
    )

    storage = api_json(
        "/api/storage/status"
    ).get(
        "storage",
        {}
    )

    disk = storage.get(
        "disk",
        {},
    )

    line(
        "Storage Manager",
        (
            "activo"
            if storage.get("running")
            else "detenido"
        ),
        bool(
            storage.get("running")
        ),
    )

    if disk:
        line(
            "Uso del SSD",
            f"{disk.get('used_percent', 0)} %",
            not bool(
                disk.get(
                    "cleanup_required"
                )
            ),
        )
    else:
        usage = shutil.disk_usage(
            PROJECT_DIR
        )

        percent = (
            usage.used
            / usage.total
            * 100
        )

        line(
            "Uso del SSD",
            f"{percent:.1f} %",
            percent < 90,
        )

    temperature_path = Path(
        "/sys/class/thermal/"
        "thermal_zone0/temp"
    )

    if temperature_path.exists():
        try:
            temperature = (
                float(
                    temperature_path.read_text(
                        encoding="utf-8"
                    ).strip()
                )
                / 1000
            )

            line(
                "Temperatura CPU",
                f"{temperature:.1f} °C",
                temperature < 80,
            )

        except (
            OSError,
            ValueError,
        ):
            pass

    hdmi_states = []

    for path in Path(
        "/sys/class/drm"
    ).glob(
        "card*-HDMI-A-*/status"
    ):
        try:
            hdmi_states.append(
                path.read_text(
                    encoding="utf-8"
                ).strip()
            )
        except OSError:
            pass

    connected = (
        "connected" in hdmi_states
    )

    line(
        "HDMI",
        (
            "conectado"
            if connected
            else "no detectado"
        ),
        connected,
    )

    settings = api_json(
        "/api/settings"
    )

    line(
        "Configuración API",
        (
            "disponible"
            if settings
            else "no disponible"
        ),
        bool(settings),
    )

    print()
    print("=" * 55)

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
