#!/usr/bin/env bash

set -u

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_FILE="${PROJECT_DIR}/install/roadeye-system-audit.txt"

section() {
    printf "\n\n============================================================\n"
    printf "%s\n" "$1"
    printf "============================================================\n"
}

run_optional() {
    local command="$1"

    printf "\n$ %s\n" "$command"

    bash -lc "$command" 2>&1 || true
}

{
    echo "ROAD EYE - INVENTARIO DEL SISTEMA FUNCIONAL"
    echo "Generado: $(date --iso-8601=seconds)"
    echo "Equipo: $(hostname)"
    echo "Usuario: $(id -un)"
    echo "Proyecto: ${PROJECT_DIR}"

    section "SISTEMA OPERATIVO"
    run_optional "cat /etc/os-release"
    run_optional "uname -a"
    run_optional "getconf LONG_BIT"
    run_optional "hostnamectl"

    section "HARDWARE RASPBERRY PI"
    run_optional "cat /proc/device-tree/model 2>/dev/null; echo"
    run_optional "vcgencmd get_throttled"
    run_optional "vcgencmd measure_temp"
    run_optional "free -h"
    run_optional "lsblk -o NAME,MODEL,SIZE,FSTYPE,MOUNTPOINTS"

    section "USUARIO Y PERMISOS"
    run_optional "id"
    run_optional "groups"
    run_optional "ls -l /dev/dri 2>/dev/null"
    run_optional "ls -l /dev/serial* 2>/dev/null"

    section "GIT"
    run_optional "git -C '${PROJECT_DIR}' remote -v"
    run_optional "git -C '${PROJECT_DIR}' branch --show-current"
    run_optional "git -C '${PROJECT_DIR}' rev-parse HEAD"
    run_optional "git -C '${PROJECT_DIR}' status --short"
    run_optional "git -C '${PROJECT_DIR}' tag --sort=-version:refname | head -20"

    section "PYTHON"
    run_optional "python3 --version"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' --version"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -c 'import sys; print(sys.executable); print(sys.path)'"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -m pip --version"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -m pip freeze"

    section "IMPORTACIONES CRÍTICAS"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -c 'import cv2; print(\"OpenCV\", cv2.__version__)'"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -c 'import numpy; print(\"NumPy\", numpy.__version__)'"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -c 'from picamera2 import Picamera2; print(\"Picamera2 OK\")'"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -c 'import gi; gi.require_version(\"Gst\", \"1.0\"); from gi.repository import Gst; Gst.init(None); print(Gst.version_string())'"
    run_optional "'${PROJECT_DIR}/.venv/bin/python' -c 'import fastapi, uvicorn, serial, pynmea2; print(\"FastAPI/GPS OK\")'"

    section "PAQUETES APT RELEVANTES"
    run_optional "dpkg-query -W -f='\${binary:Package}\t\${Version}\n' | grep -Ei 'camera|libcamera|picamera|opencv|gstreamer|python3-gi|python3-gst|numpy|drm|kms|ffmpeg|git|uvicorn'"

    section "GSTREAMER"
    run_optional "gst-launch-1.0 --version"
    run_optional "gst-inspect-1.0 kmssink | head -50"
    run_optional "gst-inspect-1.0 appsrc | head -50"

    section "CÁMARA"
    run_optional "rpicam-hello --list-cameras 2>/dev/null"
    run_optional "libcamera-hello --list-cameras 2>/dev/null"
    run_optional "ls -l /dev/video* /dev/media* 2>/dev/null"

    section "DRM Y HDMI"
    run_optional "cat /proc/fb"
    run_optional "ls /sys/class/drm"
    run_optional "for connector in /sys/class/drm/card*-HDMI-A-*; do echo \"--- \$connector\"; cat \"\$connector/status\"; head -10 \"\$connector/modes\"; done"
    run_optional "grep -nE 'vc4|hdmi|max_framebuffers|display_auto_detect' /boot/firmware/config.txt 2>/dev/null"
    run_optional "cat /boot/firmware/cmdline.txt 2>/dev/null"

    section "CONFIGURACIÓN DE CÁMARA, GPS Y USB"
    run_optional "grep -nE 'imx219|imx708|camera|uart|serial|dwc2' /boot/firmware/config.txt 2>/dev/null"
    run_optional "systemctl is-enabled serial-getty@ttyAMA0.service"
    run_optional "systemctl is-enabled serial-getty@serial0.service"

    section "SERVICIO ROAD EYE"
    run_optional "systemctl is-enabled roadeye.service"
    run_optional "systemctl is-active roadeye.service"
    run_optional "systemctl cat roadeye.service"
    run_optional "systemctl show roadeye.service -p User -p Group -p SupplementaryGroups -p WorkingDirectory -p ExecStart -p Environment"
    run_optional "journalctl -u roadeye.service -b --no-pager | tail -100"

    section "RED Y PUERTO WEB"
    run_optional "hostname -I"
    run_optional "ss -ltnp | grep ':8000'"

    section "ARCHIVOS PRINCIPALES DEL PROYECTO"
    run_optional "find '${PROJECT_DIR}' -maxdepth 2 -type f | sort"

    section "FIN DEL INVENTARIO"
    echo "No se han incluido contraseñas WiFi, claves SSH ni otros secretos."

} > "$OUTPUT_FILE"

echo
echo "Inventario creado correctamente:"
echo "$OUTPUT_FILE"
echo
echo "Tamaño:"
du -h "$OUTPUT_FILE"
