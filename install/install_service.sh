#!/usr/bin/env bash

set -Eeuo pipefail


# ============================================================
# RoadEye - Instalación del servicio systemd
# ============================================================


SCRIPT_NAME="$(basename "$0")"

PROJECT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.."
    pwd
)"

SERVICE_SOURCE="${PROJECT_DIR}/install/roadeye.service"
SERVICE_DEST="/etc/systemd/system/roadeye.service"

REBOOT_REQUIRED_FILE="${PROJECT_DIR}/.roadeye-reboot-required"


log() {
    printf '[RoadEye] %s\n' "$*"
}


success() {
    printf '[RoadEye] ✓ %s\n' "$*"
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
    if [[ "$EUID" -ne 0 ]]; then
        fatal "Ejecuta este script con sudo."
    fi
}


check_files() {
    if [[ ! -f "$SERVICE_SOURCE" ]]; then
        fatal "No existe ${SERVICE_SOURCE}"
    fi

    success "Plantilla roadeye.service encontrada."
}


install_service() {
    log "Instalando roadeye.service..."

    install \
        --mode=644 \
        "$SERVICE_SOURCE" \
        "$SERVICE_DEST"

    success "Servicio copiado."
}


reload_systemd() {
    log "Recargando systemd..."

    systemctl daemon-reload

    success "systemd recargado."
}


enable_service() {
    log "Habilitando servicio..."

    systemctl enable roadeye.service

    success "Servicio habilitado para el arranque."
}


current_boot_id() {
    cat /proc/sys/kernel/random/boot_id
}


reboot_is_pending() {
    if [[ ! -f "$REBOOT_REQUIRED_FILE" ]]; then
        return 1
    fi

    local marked_boot_id
    local active_boot_id

    marked_boot_id="$(
        tr -d '[:space:]' \
            < "$REBOOT_REQUIRED_FILE"
    )"

    active_boot_id="$(
        current_boot_id
    )"

    if [[ -z "$marked_boot_id" ]]; then
        return 0
    fi

    if [[ "$marked_boot_id" == "$active_boot_id" ]]; then
        return 0
    fi

    rm -f "$REBOOT_REQUIRED_FILE"

    return 1
}


prepare_for_first_reboot() {
    log "Preparando RoadEye para el primer reinicio..."

    systemctl stop roadeye.service \
        >/dev/null 2>&1 || true

    systemctl reset-failed roadeye.service \
        >/dev/null 2>&1 || true

    success "RoadEye arrancará automáticamente después de reiniciar."
}


restart_service() {
    log "Reiniciando RoadEye..."

    systemctl restart roadeye.service

    sleep 8
}


verify_enabled() {
    log "Comprobando habilitación del servicio..."

    if systemctl is-enabled \
        --quiet \
        roadeye.service
    then
        success "roadeye.service está habilitado."
    else
        fatal "roadeye.service no está habilitado."
    fi
}


verify_active() {
    log "Comprobando funcionamiento de RoadEye..."

    if systemctl is-active \
        --quiet \
        roadeye.service
    then
        success "RoadEye está funcionando."
        return
    fi

    systemctl status \
        roadeye.service \
        --no-pager \
        -l || true

    fatal "RoadEye no ha arrancado."
}


print_reboot_summary() {
    cat <<'SUMMARY_REBOOT'

============================================================
 ROAD EYE - SERVICIO INSTALADO
============================================================

roadeye.service está instalado y habilitado.

La configuración de cámara, HDMI/KMS, UART y permisos
necesita aplicarse mediante el primer reinicio.

Ejecuta:

    sudo reboot

Después del reinicio:

    roadeye doctor
    roadeye status

SUMMARY_REBOOT
}


print_running_summary() {
    cat <<'SUMMARY_RUNNING'

============================================================
 ROAD EYE - SERVICIO EN FUNCIONAMIENTO
============================================================

Estado:

    roadeye status

Diagnóstico:

    roadeye doctor

Registros:

    roadeye logs

SUMMARY_RUNNING
}


main() {
    require_root
    check_files
    install_service
    reload_systemd
    enable_service
    verify_enabled

    if reboot_is_pending; then
        prepare_for_first_reboot
        print_reboot_summary
        exit 0
    fi

    restart_service
    verify_active
    print_running_summary
}


main "$@"
