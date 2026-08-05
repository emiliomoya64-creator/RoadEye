#!/usr/bin/env python3

from __future__ import annotations

import json
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"


def write_file(
    relative_path: str,
    content: str,
) -> None:
    path = PROJECT_DIR / relative_path

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if path.exists():
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup = path.with_name(
            f"{path.name}.backup_{timestamp}"
        )

        shutil.copy2(
            path,
            backup,
        )

        print(
            f"  Copia: {backup.relative_to(PROJECT_DIR)}"
        )

    path.write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )

    print(
        f"  Creado: {path.relative_to(PROJECT_DIR)}"
    )


def make_executable(
    relative_path: str,
) -> None:
    path = PROJECT_DIR / relative_path

    path.chmod(
        path.stat().st_mode | 0o111
    )


VERIFY_PROJECT = r'''
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
'''


DOCTOR = r'''
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
'''


INSTALL_MENU = r'''
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
'''


ARCHITECTURE = r'''
# RoadEye Architecture

## Objetivo

RoadEye es una plataforma modular de dashcam, registro de viajes,
gestión multimedia y asistencia a la conducción para Raspberry Pi.

## Módulos principales

### Recorder

Ubicación:

- `recorder/`

Responsabilidad:

- Captura de cámara.
- Grabación por segmentos.
- Metadatos.
- Miniaturas.
- Protección de grabaciones.

### Trip Manager

Ubicación:

- `trip/`

Responsabilidad:

- Agrupar segmentos en viajes.
- Guardar rutas GPS.
- Guardar eventos y fotografías.
- Estadísticas del trayecto.

### Storage Manager

Ubicación:

- `core/storage_manager.py`

Responsabilidad:

- Vigilar el SSD.
- Borrar grabaciones normales antiguas.
- Respetar grabaciones protegidas.
- Limpiar archivos huérfanos.
- Actualizar viajes afectados.

### Web API

Ubicación:

- `web/api.py`
- `web/server.py`

Responsabilidad:

- Estado del sistema.
- Control de grabación.
- Explorador multimedia.
- Viajes.
- Fotografías.
- Configuración.
- Gestión del almacenamiento.

### Frontend principal

Ubicación:

- `templates/index.html`
- `static/js/`
- `static/css/`

Responsabilidad:

- HUD.
- Explorador de vídeos.
- Explorador de viajes.
- Multimedia Center.

### Control Center

Ubicación prevista:

- `static/control-center/`

Responsabilidad:

- Ajustes de grabación.
- Gestión del almacenamiento.
- Modo Parking.
- Pantalla y sistema.

### Developer Kit

Ubicación:

- `scripts/`

Responsabilidad:

- Verificación.
- Diagnóstico.
- Instalación de módulos.
- Copias de seguridad.
- Checkpoints.

## Principios

1. Cada módulo debe tener una responsabilidad clara.
2. Los archivos protegidos nunca se eliminan automáticamente.
3. Las escrituras importantes deben ser atómicas.
4. Cada gran fase debe terminar con una verificación y un checkpoint.
5. Los instaladores deben poder repetirse sin romper la instalación.
'''


def verify_created_files() -> None:
    required = [
        "scripts/verify_project.py",
        "scripts/doctor.py",
        "scripts/install.py",
        "ARCHITECTURE.md",
    ]

    missing = [
        name
        for name in required
        if not (
            PROJECT_DIR / name
        ).exists()
    ]

    if missing:
        raise RuntimeError(
            "Faltan archivos: "
            + ", ".join(missing)
        )

    for name in (
        "scripts/verify_project.py",
        "scripts/doctor.py",
        "scripts/install.py",
    ):
        py_compile.compile(
            str(
                PROJECT_DIR / name
            ),
            doraise=True,
        )


def main() -> int:
    print()
    print("=" * 58)
    print("      Instalación RoadEye Development Kit")
    print("=" * 58)
    print()

    write_file(
        "scripts/verify_project.py",
        VERIFY_PROJECT,
    )

    write_file(
        "scripts/doctor.py",
        DOCTOR,
    )

    write_file(
        "scripts/install.py",
        INSTALL_MENU,
    )

    write_file(
        "ARCHITECTURE.md",
        ARCHITECTURE,
    )

    for script in (
        "scripts/bootstrap_devkit.py",
        "scripts/verify_project.py",
        "scripts/doctor.py",
        "scripts/install.py",
    ):
        make_executable(
            script
        )

    verify_created_files()

    print()
    print("Verificación final correcta.")
    print()
    print(
        "Ejecuta ahora:"
    )
    print(
        "  python3 scripts/verify_project.py"
    )
    print(
        "  python3 scripts/doctor.py"
    )
    print(
        "  python3 scripts/install.py"
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except Exception as exc:
        print()
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        raise SystemExit(1)
