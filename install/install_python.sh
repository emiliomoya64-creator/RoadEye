#!/usr/bin/env bash

set -Eeuo pipefail


# ============================================================
# RoadEye - Instalación del entorno Python
# ============================================================
#
# Este script:
#
# - Comprueba que existe Python 3.
# - Crea el entorno virtual .venv.
# - Permite usar dentro del entorno los paquetes instalados por APT.
# - Actualiza pip, setuptools y wheel.
# - Instala requirements.txt.
# - Comprueba las importaciones principales de RoadEye.
#
# Puede ejecutarse varias veces.
# ============================================================


SCRIPT_NAME="$(basename "$0")"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"
REQUIREMENTS_FILE="${PROJECT_DIR}/requirements.txt"


log() {
    printf '[RoadEye] %s\n' "$*"
}


success() {
    printf '[RoadEye] ✓ %s\n' "$*"
}


warning() {
    printf '[RoadEye] ADVERTENCIA: %s\n' "$*" >&2
}


fatal() {
    printf '[RoadEye] ERROR: %s\n' "$*" >&2
    exit 1
}


on_error() {
    local exit_code=$?
    local line_number="${1:-desconocida}"

    printf '\n' >&2
    printf '[RoadEye] ERROR en %s, línea %s.\n' \
        "$SCRIPT_NAME" \
        "$line_number" >&2

    printf '[RoadEye] Código de salida: %s\n' \
        "$exit_code" >&2

    exit "$exit_code"
}


trap 'on_error $LINENO' ERR


check_project() {
    if [[ ! -f "${PROJECT_DIR}/app.py" ]]; then
        fatal "No se encuentra app.py en ${PROJECT_DIR}"
    fi

    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        fatal "No se encuentra requirements.txt"
    fi

    success "Proyecto RoadEye detectado en ${PROJECT_DIR}"
}


check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        fatal "Python 3 no está instalado."
    fi

    local version

    version="$(python3 --version 2>&1)"

    success "Python disponible: ${version}"
}


create_virtual_environment() {
    if [[ -x "$VENV_PYTHON" ]]; then
        success "El entorno virtual ya existe: ${VENV_DIR}"
        return
    fi

    log "Creando entorno virtual con acceso a paquetes del sistema..."

    python3 -m venv \
        --system-site-packages \
        "$VENV_DIR"

    success "Entorno virtual creado."
}


verify_system_site_packages() {
    local config_file="${VENV_DIR}/pyvenv.cfg"

    if [[ ! -f "$config_file" ]]; then
        fatal "No se encuentra ${config_file}"
    fi

    if grep -Eq \
        '^include-system-site-packages = true$' \
        "$config_file"
    then
        success "El entorno virtual usa paquetes Python de APT."
        return
    fi

    warning \
        "El entorno virtual existente no usa paquetes del sistema."

    log "Corrigiendo pyvenv.cfg..."

    sed -i \
        's/^include-system-site-packages = false$/include-system-site-packages = true/' \
        "$config_file"

    if ! grep -Eq \
        '^include-system-site-packages = true$' \
        "$config_file"
    then
        fatal \
            "No se pudo activar include-system-site-packages."
    fi

    success "Acceso a paquetes del sistema activado."
}


upgrade_installer_tools() {
    log "Actualizando pip, setuptools y wheel..."

    "$VENV_PYTHON" -m pip install \
        --upgrade \
        pip \
        setuptools \
        wheel

    success "Herramientas de instalación actualizadas."
}


install_requirements() {
    log "Instalando dependencias de requirements.txt..."

    "$VENV_PYTHON" -m pip install \
        --requirement \
        "$REQUIREMENTS_FILE"

    success "Dependencias Python instaladas."
}


verify_import() {
    local code="$1"
    local description="$2"

    if "$VENV_PYTHON" -c "$code" >/dev/null 2>&1; then
        success "$description"
    else
        fatal "Falló la importación: ${description}"
    fi
}


verify_python_environment() {
    log "Comprobando el entorno Python de RoadEye..."

    verify_import \
        "import fastapi" \
        "FastAPI"

    verify_import \
        "import uvicorn" \
        "Uvicorn"

    verify_import \
        "import jinja2" \
        "Jinja2"

    verify_import \
        "import multipart" \
        "python-multipart"

    verify_import \
        "import pynmea2" \
        "pynmea2"

    verify_import \
        "import serial" \
        "PySerial"

    verify_import \
        "import requests" \
        "Requests"

    verify_import \
        "import psutil" \
        "psutil"

    verify_import \
        "import numpy" \
        "NumPy desde APT"

    verify_import \
        "import cv2" \
        "OpenCV desde APT"

    verify_import \
        "from picamera2 import Picamera2" \
        "Picamera2 desde APT"

    verify_import \
        "import gi; gi.require_version('Gst', '1.0'); from gi.repository import Gst; Gst.init(None)" \
        "GStreamer para Python"

    success "Entorno Python verificado."
}


print_versions() {
    printf '\n'
    printf '============================================================\n'
    printf ' ROAD EYE - VERSIONES PYTHON\n'
    printf '============================================================\n'
    printf '\n'

    "$VENV_PYTHON" - <<'PY'
import cv2
import fastapi
import jinja2
import numpy
import psutil
import pynmea2
import requests
import serial
import uvicorn

print("Python           : OK")
print("FastAPI          :", fastapi.__version__)
print("Uvicorn          :", uvicorn.__version__)
print("Jinja2           :", jinja2.__version__)
print("pynmea2          :", pynmea2.__version__)
print("PySerial         :", serial.__version__)
print("Requests         :", requests.__version__)
print("psutil           :", psutil.__version__)
print("NumPy            :", numpy.__version__)
print("OpenCV           :", cv2.__version__)
PY

    printf '\n'
}


print_summary() {
    printf '============================================================\n'
    printf ' ROAD EYE - ENTORNO PYTHON PREPARADO\n'
    printf '============================================================\n'
    printf '\n'
    printf 'Entorno virtual:\n'
    printf '  %s\n' "$VENV_DIR"
    printf '\n'
    printf 'Python:\n'
    printf '  %s\n' "$VENV_PYTHON"
    printf '\n'
    printf 'El entorno está preparado para ejecutar RoadEye.\n'
    printf '\n'
}


main() {
    check_project
    check_python
    create_virtual_environment
    verify_system_site_packages
    upgrade_installer_tools
    install_requirements
    verify_python_environment
    print_versions
    print_summary
}


main "$@"
