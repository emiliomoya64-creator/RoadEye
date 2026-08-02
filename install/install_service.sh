#!/usr/bin/env bash

set -Eeuo pipefail

# ============================================================
# RoadEye - Instalación del servicio systemd
# ============================================================

SCRIPT_NAME="$(basename "$0")"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SERVICE_SOURCE="${PROJECT_DIR}/install/roadeye.service"
SERVICE_DEST="/etc/systemd/system/roadeye.service"


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

trap 'fatal "Error en línea $LINENO."' ERR


require_root() {

    [[ "$EUID" -eq 0 ]] || fatal "Ejecuta con sudo."

}


check_files() {

    [[ -f "$SERVICE_SOURCE" ]] || fatal "No existe ${SERVICE_SOURCE}"

}


install_service() {

    log "Instalando roadeye.service..."

    install \
        -m 644 \
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

    success "Servicio habilitado."

}


restart_service() {

    log "Reiniciando RoadEye..."

    systemctl restart roadeye.service

    sleep 5

    success "Servicio reiniciado."

}


verify_service() {

    log "Verificando servicio..."

    if systemctl is-active --quiet roadeye.service
    then

        success "RoadEye está funcionando."

    else

        systemctl status roadeye.service --no-pager

        fatal "RoadEye no ha arrancado."

    fi

}


summary() {

cat <<EOF

============================================================
 RoadEye instalado como servicio del sistema
============================================================

Para consultar el estado:

    systemctl status roadeye.service

Para ver el log:

    journalctl -u roadeye.service -f

EOF

}


main() {

    require_root

    check_files

    install_service

    reload_systemd

    enable_service

    restart_service

    verify_service

    summary

}

main "$@"
