#!/usr/bin/env bash

set -Eeuo pipefail


# ============================================================
# RoadEye - Configuración de Raspberry Pi
# ============================================================
#
# Configura:
#
# - Cámara frontal IMX219.
# - Controlador gráfico DRM/KMS.
# - Salida HDMI 1280x720 a 60 Hz.
# - UART para GPS.
# - Desactivación de consola serie.
# - USB en modo host.
# - Permisos de usuario.
#
# Antes de modificar archivos de arranque crea copias de seguridad.
#
# El script puede ejecutarse varias veces.
# ============================================================


SCRIPT_NAME="$(basename "$0")"

BOOT_CONFIG="/boot/firmware/config.txt"
CMDLINE_FILE="/boot/firmware/cmdline.txt"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

TARGET_USER="${SUDO_USER:-emilio}"


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
    if [[ "$EUID" -ne 0 ]]; then
        fatal "Ejecuta este script con sudo."
    fi
}


check_files() {
    if [[ ! -f "$BOOT_CONFIG" ]]; then
        fatal "No existe ${BOOT_CONFIG}"
    fi

    if [[ ! -f "$CMDLINE_FILE" ]]; then
        fatal "No existe ${CMDLINE_FILE}"
    fi

    success "Archivos de arranque detectados."
}


check_user() {
    if ! id "$TARGET_USER" >/dev/null 2>&1; then
        fatal "No existe el usuario ${TARGET_USER}"
    fi

    success "Usuario detectado: ${TARGET_USER}"
}


backup_boot_files() {
    local config_backup
    local cmdline_backup

    config_backup="${BOOT_CONFIG}.roadeye-${TIMESTAMP}.backup"
    cmdline_backup="${CMDLINE_FILE}.roadeye-${TIMESTAMP}.backup"

    cp --preserve=all \
        "$BOOT_CONFIG" \
        "$config_backup"

    cp --preserve=all \
        "$CMDLINE_FILE" \
        "$cmdline_backup"

    success "Copia creada: ${config_backup}"
    success "Copia creada: ${cmdline_backup}"
}


set_config_value() {
    local key="$1"
    local value="$2"
    local desired_line="${key}=${value}"

    if grep -Eq "^[[:space:]]*${key}=" "$BOOT_CONFIG"; then
        sed -i \
            -E \
            "s|^[[:space:]]*${key}=.*$|${desired_line}|" \
            "$BOOT_CONFIG"
    else
        printf '\n%s\n' "$desired_line" >> "$BOOT_CONFIG"
    fi

    success "${desired_line}"
}


ensure_exact_config_line() {
    local desired_line="$1"

    if grep -Fxq "$desired_line" "$BOOT_CONFIG"; then
        success "${desired_line}"
        return
    fi

    printf '%s\n' "$desired_line" >> "$BOOT_CONFIG"

    success "${desired_line}"
}


remove_config_line() {
    local pattern="$1"

    sed -i \
        -E \
        "/${pattern}/d" \
        "$BOOT_CONFIG"
}


configure_camera() {
    log "Configurando cámara IMX219..."

    set_config_value \
        "camera_auto_detect" \
        "0"

    # Eliminar posibles overlays automáticos de otros sensores
    # que pudieran entrar en conflicto con la IMX219.
    remove_config_line \
        '^[[:space:]]*dtoverlay=imx708([[:space:]]|$)'

    ensure_exact_config_line \
        "dtoverlay=imx219"

    success "Cámara IMX219 configurada."
}


configure_kms() {
    log "Configurando DRM/KMS..."

    # Sustituir el antiguo controlador FKMS si existiera.
    sed -i \
        -E \
        's|^[[:space:]]*dtoverlay=vc4-fkms-v3d.*$|dtoverlay=vc4-kms-v3d|' \
        "$BOOT_CONFIG"

    ensure_exact_config_line \
        "dtoverlay=vc4-kms-v3d"

    set_config_value \
        "display_auto_detect" \
        "1"

    set_config_value \
        "max_framebuffers" \
        "2"

    success "DRM/KMS configurado."
}


configure_uart() {
    log "Configurando UART para GPS..."

    set_config_value \
        "enable_uart" \
        "1"

    systemctl disable \
        serial-getty@ttyAMA0.service \
        >/dev/null 2>&1 || true

    systemctl disable \
        serial-getty@serial0.service \
        >/dev/null 2>&1 || true

    systemctl stop \
        serial-getty@ttyAMA0.service \
        >/dev/null 2>&1 || true

    systemctl stop \
        serial-getty@serial0.service \
        >/dev/null 2>&1 || true

    success "UART habilitado y consola serie desactivada."
}


configure_usb_host() {
    log "Configurando USB en modo host..."

    if grep -Eq \
        '^[[:space:]]*dtoverlay=dwc2([,[:space:]]|$)' \
        "$BOOT_CONFIG"
    then
        sed -i \
            -E \
            's|^[[:space:]]*dtoverlay=dwc2.*$|dtoverlay=dwc2,dr_mode=host|' \
            "$BOOT_CONFIG"
    else
        printf '%s\n' \
            "dtoverlay=dwc2,dr_mode=host" \
            >> "$BOOT_CONFIG"
    fi

    success "USB host configurado."
}


configure_hdmi_cmdline() {
    log "Configurando HDMI 1280x720 a 60 Hz..."

    local current_line
    local cleaned_line
    local new_line

    current_line="$(
        tr '\n' ' ' < "$CMDLINE_FILE"
    )"

    cleaned_line="$(
        printf '%s\n' "$current_line" \
            | sed -E \
                's/(^|[[:space:]])video=HDMI-A-[^[:space:]]+//g' \
            | sed -E \
                's/[[:space:]]+/ /g' \
            | sed -E \
                's/^[[:space:]]+|[[:space:]]+$//g'
    )"

    new_line="${cleaned_line} video=HDMI-A-1:1280x720M@60"

    printf '%s\n' "$new_line" > "$CMDLINE_FILE"

    success "HDMI-A-1 configurado a 1280x720M@60."
}


remove_serial_console_from_cmdline() {
    log "Eliminando consola serie del arranque..."

    local current_line
    local cleaned_line

    current_line="$(
        tr '\n' ' ' < "$CMDLINE_FILE"
    )"

    cleaned_line="$(
        printf '%s\n' "$current_line" \
            | sed -E \
                's/(^|[[:space:]])console=(serial0|ttyAMA0|ttyS0),[0-9]+//g' \
            | sed -E \
                's/[[:space:]]+/ /g' \
            | sed -E \
                's/^[[:space:]]+|[[:space:]]+$//g'
    )"

    printf '%s\n' "$cleaned_line" > "$CMDLINE_FILE"

    success "Consola serie eliminada de cmdline.txt."
}


configure_user_groups() {
    log "Configurando permisos del usuario ${TARGET_USER}..."

    local groups=(
        video
        render
        dialout
        gpio
        i2c
        spi
    )

    local group_name

    for group_name in "${groups[@]}"; do
        if getent group "$group_name" >/dev/null 2>&1; then
            usermod \
                -aG "$group_name" \
                "$TARGET_USER"

            success \
                "Usuario añadido al grupo ${group_name}."
        else
            warning \
                "El grupo ${group_name} no existe."
        fi
    done
}


verify_boot_config() {
    log "Comprobando config.txt..."

    local required_lines=(
        "camera_auto_detect=0"
        "dtoverlay=imx219"
        "display_auto_detect=1"
        "dtoverlay=vc4-kms-v3d"
        "max_framebuffers=2"
        "enable_uart=1"
        "dtoverlay=dwc2,dr_mode=host"
    )

    local required_line

    for required_line in "${required_lines[@]}"; do
        if grep -Fxq \
            "$required_line" \
            "$BOOT_CONFIG"
        then
            success "$required_line"
        else
            fatal \
                "No se encuentra en config.txt: ${required_line}"
        fi
    done
}


verify_cmdline() {
    log "Comprobando cmdline.txt..."

    if grep -q \
        'video=HDMI-A-1:1280x720M@60' \
        "$CMDLINE_FILE"
    then
        success \
            "Resolución HDMI configurada."
    else
        fatal \
            "No aparece la configuración HDMI esperada."
    fi

    if grep -Eq \
        'console=(serial0|ttyAMA0|ttyS0),' \
        "$CMDLINE_FILE"
    then
        fatal \
            "Todavía existe una consola serie en cmdline.txt."
    fi

    success \
        "El puerto serie queda disponible para el GPS."
}


verify_user_groups() {
    log "Comprobando grupos del usuario..."

    local user_groups

    user_groups="$(
        id -nG "$TARGET_USER"
    )"

    printf '[RoadEye] Grupos: %s\n' \
        "$user_groups"

    for required_group in video render dialout; do
        if grep -qw \
            "$required_group" \
            <<< "$user_groups"
        then
            success \
                "Grupo disponible: ${required_group}"
        else
            fatal \
                "El usuario no pertenece a ${required_group}"
        fi
    done
}


print_summary() {
    printf '\n'
    printf '============================================================\n'
    printf ' ROAD EYE - RASPBERRY PI CONFIGURADA\n'
    printf '============================================================\n'
    printf '\n'
    printf '✓ Cámara IMX219\n'
    printf '✓ DRM/KMS\n'
    printf '✓ HDMI 1280x720 a 60 Hz\n'
    printf '✓ UART para GPS\n'
    printf '✓ Consola serie desactivada\n'
    printf '✓ USB host\n'
    printf '✓ Permisos video, render y dialout\n'
    printf '\n'
    printf 'Es necesario reiniciar la Raspberry para aplicar todos\n'
    printf 'los cambios de arranque y los nuevos grupos del usuario.\n'
    printf '\n'
}


main() {
    require_root
    check_files
    check_user
    backup_boot_files
    configure_camera
    configure_kms
    configure_uart
    configure_usb_host
    remove_serial_console_from_cmdline
    configure_hdmi_cmdline
    configure_user_groups
    verify_boot_config
    verify_cmdline
    verify_user_groups
    print_summary
}


main "$@"
