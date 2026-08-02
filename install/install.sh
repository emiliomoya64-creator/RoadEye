#!/usr/bin/env bash

set -Eeuo pipefail


# ============================================================
# RoadEye v0.5.0 - Instalador maestro
# ============================================================
#
# Instalación soportada actualmente:
#
#   Usuario:   emilio
#   Proyecto:  /home/emilio/PiDash
#   Sistema:   Debian 12 Bookworm arm64
#
# Este instalador:
#
#   1. Comprueba el proyecto y el usuario.
#   2. Instala dependencias APT.
#   3. Configura cámara, HDMI, KMS, UART y permisos.
#   4. Crea y prepara el entorno virtual Python.
#   5. Instala roadeye.service.
#   6. Instala el comando global "roadeye".
#   7. Ejecuta comprobaciones finales.
#
# Debe ejecutarse con:
#
#   sudo ./install/install.sh
#
# ============================================================


SCRIPT_NAME="$(basename "$0")"

PROJECT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.."
    pwd
)"

INSTALL_DIR="${PROJECT_DIR}/install"

EXPECTED_PROJECT_DIR="/home/emilio/PiDash"
TARGET_USER="${SUDO_USER:-emilio}"
TARGET_GROUP="${TARGET_USER}"

DEPENDENCIES_SCRIPT="${INSTALL_DIR}/install_dependencies.sh"
GIT_CONFIG_SCRIPT="${INSTALL_DIR}/configure_git.sh"
CONFIGURE_SCRIPT="${INSTALL_DIR}/configure_pi.sh"
PYTHON_SCRIPT="${INSTALL_DIR}/install_python.sh"
SERVICE_SCRIPT="${INSTALL_DIR}/install_service.sh"
DOCTOR_SCRIPT="${INSTALL_DIR}/doctor.py"
ROAD_EYE_COMMAND="${INSTALL_DIR}/roadeye"

GLOBAL_COMMAND="/usr/local/bin/roadeye"

REBOOT_REQUIRED_FILE="${PROJECT_DIR}/.roadeye-reboot-required"


log() {
    printf '[RoadEye] %s\n' "$*"
}


step() {
    printf '\n'
    printf '============================================================\n'
    printf ' %s\n' "$*"
    printf '============================================================\n'
    printf '\n'
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

    printf '[RoadEye] La instalación no ha terminado.\n' >&2

    exit "$exit_code"
}


trap 'on_error $LINENO' ERR


require_root() {
    if [[ "$EUID" -ne 0 ]]; then
        fatal "Ejecuta el instalador con sudo."
    fi
}


check_target_user() {
    if ! id "$TARGET_USER" >/dev/null 2>&1; then
        fatal "No existe el usuario ${TARGET_USER}."
    fi

    TARGET_GROUP="$(
        id -gn "$TARGET_USER"
    )"

    success \
        "Usuario de instalación: ${TARGET_USER}:${TARGET_GROUP}"
}


check_project_location() {
    if [[ "$PROJECT_DIR" != "$EXPECTED_PROJECT_DIR" ]]; then
        fatal \
            "RoadEye v0.5.0 debe estar en ${EXPECTED_PROJECT_DIR}. " \
            "Ruta actual: ${PROJECT_DIR}"
    fi

    if [[ ! -f "${PROJECT_DIR}/app.py" ]]; then
        fatal "No se encuentra app.py."
    fi

    if [[ ! -f "${PROJECT_DIR}/VERSION" ]]; then
        fatal "No se encuentra VERSION."
    fi

    if [[ ! -d "${PROJECT_DIR}/.git" ]]; then
        warning \
            "La carpeta no parece un repositorio Git."
    fi

    success \
        "Proyecto RoadEye detectado: ${PROJECT_DIR}"
}


check_installation_scripts() {
    local required_scripts=(
        "$DEPENDENCIES_SCRIPT"
        "$GIT_CONFIG_SCRIPT"
        "$CONFIGURE_SCRIPT"
        "$PYTHON_SCRIPT"
        "$SERVICE_SCRIPT"
    )

    local script_path

    for script_path in "${required_scripts[@]}"; do
        if [[ ! -f "$script_path" ]]; then
            fatal \
                "No se encuentra el script: ${script_path}"
        fi

        chmod +x "$script_path"

        success \
            "Script disponible: $(basename "$script_path")"
    done

    if [[ ! -f "$DOCTOR_SCRIPT" ]]; then
        fatal \
            "No se encuentra RoadEye Doctor: ${DOCTOR_SCRIPT}"
    fi

    if [[ ! -f "$ROAD_EYE_COMMAND" ]]; then
        fatal \
            "No se encuentra el lanzador: ${ROAD_EYE_COMMAND}"
    fi

    chmod +x \
        "$DOCTOR_SCRIPT" \
        "$ROAD_EYE_COMMAND"

    success "RoadEye Doctor disponible."
}


show_version() {
    local version

    version="$(
        tr -d '[:space:]' \
            < "${PROJECT_DIR}/VERSION"
    )"

    if [[ -z "$version" ]]; then
        fatal "El archivo VERSION está vacío."
    fi

    log "Versión que se instalará: ${version}"
}


prepare_project_permissions() {
    log \
        "Ajustando permisos del proyecto para ${TARGET_USER}..."

    chown -R \
        "${TARGET_USER}:${TARGET_GROUP}" \
        "$PROJECT_DIR"

    success "Permisos del proyecto preparados."
}


current_boot_id() {
    cat /proc/sys/kernel/random/boot_id
}


mark_reboot_required() {
    current_boot_id > "$REBOOT_REQUIRED_FILE"

    chown \
        "${TARGET_USER}:${TARGET_GROUP}" \
        "$REBOOT_REQUIRED_FILE"

    success \
        "Primer reinicio marcado como obligatorio."
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

install_system_dependencies() {
    step "1/6 - DEPENDENCIAS DEL SISTEMA"

    "$DEPENDENCIES_SCRIPT"
}


configure_git_identity() {
    step "CONFIGURACIÓN DE GIT"

    SUDO_USER="$TARGET_USER" \
        "$GIT_CONFIG_SCRIPT"

    success \
        "Identidad Git configurada."
}


configure_raspberry_pi() {
    step "2/6 - CONFIGURACIÓN DE RASPBERRY PI"

    SUDO_USER="$TARGET_USER" \
        "$CONFIGURE_SCRIPT"

    mark_reboot_required

    success \
        "Configuración de arranque preparada."
}

install_python_environment() {
    step "3/6 - ENTORNO PYTHON"

    # install_python.sh nunca debe ejecutarse como root.
    sudo \
        --preserve-env=PATH \
        --user "$TARGET_USER" \
        -- \
        "$PYTHON_SCRIPT"

    success \
        "Entorno Python preparado."
}


install_global_command() {
    step "4/6 - COMANDO GLOBAL ROAD EYE"

    ln -sfn \
        "$ROAD_EYE_COMMAND" \
        "$GLOBAL_COMMAND"

    chmod +x \
        "$ROAD_EYE_COMMAND"

    success \
        "Comando instalado: ${GLOBAL_COMMAND}"

    local resolved_path

    resolved_path="$(
        readlink -f "$GLOBAL_COMMAND"
    )"

    if [[ "$resolved_path" != "$ROAD_EYE_COMMAND" ]]; then
        fatal \
            "El enlace global no apunta al lanzador correcto."
    fi

    success \
        "Enlace verificado: ${resolved_path}"
}


install_system_service() {
    step "5/6 - SERVICIO SYSTEMD"

    "$SERVICE_SCRIPT"

    success \
        "roadeye.service instalado."
}


run_final_checks() {
    step "6/6 - COMPROBACIONES FINALES"

    if ! systemctl is-enabled \
        --quiet \
        roadeye.service
    then
        fatal \
            "roadeye.service no está habilitado."
    fi

    success \
        "roadeye.service habilitado al arrancar."

    if [[ -x "${PROJECT_DIR}/.venv/bin/python" ]]; then
        success \
            "Python virtual disponible."
    else
        fatal \
            "No se encuentra el Python virtual."
    fi

    if command -v roadeye >/dev/null 2>&1; then
        success \
            "Comando global roadeye disponible."
    else
        fatal \
            "El comando roadeye no está disponible."
    fi

    if reboot_is_pending; then
        warning \
            "El primer reinicio está pendiente."

        success \
            "Instalación preparada correctamente para reiniciar."

        printf '\n'
        printf 'RoadEye se comprobará después del reinicio.\n'
        printf '\n'

        return
    fi

    if ! systemctl is-active \
        --quiet \
        roadeye.service
    then
        systemctl status \
            roadeye.service \
            --no-pager \
            -l || true

        fatal \
            "roadeye.service no está activo."
    fi

    success \
        "roadeye.service está activo."

    if ! curl \
        --silent \
        --fail \
        --max-time 5 \
        http://127.0.0.1:8000/api/status \
        >/dev/null
    then
        fatal \
            "La API web no responde en el puerto 8000."
    fi

    success \
        "API web disponible en el puerto 8000."
}

run_doctor() {
    step "ROAD EYE DOCTOR"

    # El Doctor puede devolver 1 por advertencias o 2 por errores.
    # Mostramos el resultado sin abortar el instalador porque algunas
    # comprobaciones de hardware requieren un reinicio.
    sudo \
        --user "$TARGET_USER" \
        -- \
        "${PROJECT_DIR}/.venv/bin/python" \
        "$DOCTOR_SCRIPT" \
        || true
}


print_summary() {
    local version

    version="$(
        tr -d '[:space:]' \
            < "${PROJECT_DIR}/VERSION"
    )"

    printf '\n'
    printf '============================================================\n'
    printf ' ROAD EYE %s - INSTALACIÓN COMPLETADA\n' "$version"
    printf '============================================================\n'
    printf '\n'
    printf 'Proyecto:\n'
    printf '  %s\n' "$PROJECT_DIR"
    printf '\n'
    printf 'Usuario:\n'
    printf '  %s\n' "$TARGET_USER"
    printf '\n'
    printf 'Servicio:\n'
    printf '  roadeye.service\n'
    printf '\n'
    printf 'Web:\n'
    printf '  http://IP-DE-LA-RASPBERRY:8000\n'
    printf '\n'
    printf 'Comandos:\n'
    printf '  roadeye doctor\n'
    printf '  roadeye status\n'
    printf '  roadeye logs\n'
    printf '  roadeye restart\n'
    printf '\n'

    if [[ -f "$REBOOT_REQUIRED_FILE" ]]; then
        printf 'IMPORTANTE:\n'
        printf '\n'
        printf '  Debes reiniciar para aplicar completamente:\n'
        printf '  - Cámara IMX219\n'
        printf '  - HDMI/KMS\n'
        printf '  - UART GPS\n'
        printf '  - Grupos del usuario\n'
        printf '\n'
        printf 'Ejecuta:\n'
        printf '\n'
        printf '  sudo reboot\n'
        printf '\n'
    fi
}


main() {
    require_root
    check_target_user
    check_project_location
    check_installation_scripts
    show_version
    prepare_project_permissions
    install_system_dependencies
    configure_git_identity
    configure_raspberry_pi
    install_python_environment
    install_global_command
    install_system_service
    run_final_checks
    run_doctor
    print_summary
}


main "$@"
