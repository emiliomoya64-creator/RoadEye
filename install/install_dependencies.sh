#!/usr/bin/env bash

set -Eeuo pipefail


# ============================================================
# RoadEye - Instalación de dependencias del sistema
# ============================================================
#
# Instala los paquetes APT necesarios para:
#
# - Python y entorno virtual.
# - Raspberry Pi Camera y Picamera2.
# - OpenCV y NumPy.
# - GStreamer y salida HDMI mediante kmssink.
# - Git y herramientas generales.
# - Diagnóstico DRM/KMS.
#
# Este script es idempotente:
# puede ejecutarse varias veces sin reinstalar innecesariamente.
# ============================================================


SCRIPT_NAME="$(basename "$0")"

ROAD_EYE_APT_PACKAGES=(
    # Herramientas generales
    git
    curl
    ca-certificates
    jq

    # Python
    python3
    python3-dev
    python3-pip
    python3-venv
    python3-setuptools
    python3-wheel

    # Cámara Raspberry Pi
    python3-libcamera
    python3-picamera2
    rpicam-apps

    # Procesamiento de imagen
    python3-numpy
    python3-opencv

    # GObject Introspection y GStreamer para Python
    python3-gi
    python3-gst-1.0
    gir1.2-gstreamer-1.0
    gir1.2-gst-plugins-base-1.0

    # GStreamer
    gstreamer1.0-tools
    gstreamer1.0-plugins-base
    gstreamer1.0-plugins-good
    gstreamer1.0-plugins-bad
    gstreamer1.0-gl

    # Vídeo y diagnóstico
    ffmpeg
    kms++-utils
    kmscube

    # Compilación de posibles dependencias Python
    build-essential
    pkg-config
)


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


require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        fatal "Ejecuta este script con sudo."
    fi
}


check_operating_system() {
    if [[ ! -f /etc/os-release ]]; then
        fatal "No se encuentra /etc/os-release."
    fi

    # shellcheck disable=SC1091
    source /etc/os-release

    local system_id="${ID:-desconocido}"
    local version_id="${VERSION_ID:-desconocida}"
    local architecture

    architecture="$(dpkg --print-architecture)"

    log "Sistema detectado: ${PRETTY_NAME:-desconocido}"
    log "Arquitectura detectada: ${architecture}"

    if [[ "$system_id" != "debian" ]]; then
        warning \
            "El instalador ha sido validado en Debian/Raspberry Pi OS."
    fi

    if [[ "$version_id" != "12" ]]; then
        warning \
            "RoadEye v0.5.0 ha sido validado en Debian 12 Bookworm."
    fi

    if [[ "$architecture" != "arm64" ]]; then
        warning \
            "La instalación funcional de referencia utiliza arm64."
    fi
}


check_raspberry_pi() {
    local model_file="/proc/device-tree/model"

    if [[ ! -f "$model_file" ]]; then
        warning \
            "No se ha podido confirmar que el equipo sea una Raspberry Pi."
        return
    fi

    local model

    model="$(
        tr -d '\0' < "$model_file"
    )"

    log "Hardware detectado: ${model}"

    if [[ "$model" != *"Raspberry Pi"* ]]; then
        warning \
            "El hardware no parece una Raspberry Pi."
    fi
}


update_package_index() {
    log "Actualizando el índice de paquetes APT..."

    export DEBIAN_FRONTEND=noninteractive

    apt-get update

    success "Índice de paquetes actualizado."
}


install_packages() {
    log "Instalando dependencias de RoadEye..."

    export DEBIAN_FRONTEND=noninteractive

    apt-get install \
        --yes \
        --no-install-recommends \
        "${ROAD_EYE_APT_PACKAGES[@]}"

    success "Dependencias APT instaladas."
}


verify_command() {
    local command_name="$1"
    local description="$2"

    if command -v "$command_name" >/dev/null 2>&1; then
        success "${description}: $(command -v "$command_name")"
    else
        fatal \
            "No se encuentra ${description} después de la instalación."
    fi
}


verify_python_import() {
    local import_code="$1"
    local description="$2"

    if python3 -c "$import_code" >/dev/null 2>&1; then
        success "$description"
    else
        fatal \
            "Python no puede importar: ${description}"
    fi
}


verify_gstreamer_plugin() {
    local plugin_name="$1"

    if gst-inspect-1.0 "$plugin_name" >/dev/null 2>&1; then
        success "Plugin GStreamer disponible: ${plugin_name}"
    else
        fatal \
            "No se encuentra el plugin GStreamer: ${plugin_name}"
    fi
}


verify_installation() {
    log "Comprobando la instalación..."

    verify_command \
        "git" \
        "Git"

    verify_command \
        "python3" \
        "Python 3"

    verify_command \
        "gst-launch-1.0" \
        "GStreamer"

    verify_command \
        "gst-inspect-1.0" \
        "GStreamer Inspect"

    verify_command \
        "rpicam-hello" \
        "herramientas de cámara Raspberry Pi"

    verify_command \
        "kmsprint" \
        "herramientas KMS"

    verify_python_import \
        "import numpy" \
        "NumPy"

    verify_python_import \
        "import cv2" \
        "OpenCV"

    verify_python_import \
        "from picamera2 import Picamera2" \
        "Picamera2"

    verify_python_import \
        "import gi; gi.require_version('Gst', '1.0'); from gi.repository import Gst; Gst.init(None)" \
        "GStreamer para Python"

    verify_gstreamer_plugin \
        "appsrc"

    verify_gstreamer_plugin \
        "kmssink"

    success "Todas las dependencias principales están disponibles."
}


print_summary() {
    printf '\n'
    printf '============================================================\n'
    printf ' ROAD EYE - DEPENDENCIAS INSTALADAS\n'
    printf '============================================================\n'
    printf '\n'
    printf '✓ Python\n'
    printf '✓ Picamera2\n'
    printf '✓ OpenCV\n'
    printf '✓ NumPy\n'
    printf '✓ GStreamer\n'
    printf '✓ appsrc\n'
    printf '✓ kmssink\n'
    printf '✓ Git\n'
    printf '✓ Herramientas DRM/KMS\n'
    printf '\n'
    printf 'El sistema está preparado para crear el entorno Python.\n'
    printf '\n'
}


main() {
    require_root
    check_operating_system
    check_raspberry_pi
    update_package_index
    install_packages
    verify_installation
    print_summary
}


main "$@"
