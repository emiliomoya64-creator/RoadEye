#!/usr/bin/env bash

set -Eeuo pipefail


# ============================================================
# RoadEye - Configuración de identidad Git
# ============================================================


SCRIPT_NAME="$(basename "$0")"

TARGET_USER="${SUDO_USER:-emilio}"

GIT_USER_NAME="${ROAD_EYE_GIT_NAME:-Emilio Moya}"
GIT_USER_EMAIL="${ROAD_EYE_GIT_EMAIL:-emiliomoya64@gmail.com}"


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
        fatal "Ejecuta este script mediante sudo."
    fi
}


check_user() {
    if ! id "$TARGET_USER" >/dev/null 2>&1; then
        fatal "No existe el usuario ${TARGET_USER}."
    fi

    success "Usuario Git detectado: ${TARGET_USER}"
}


check_git() {
    if ! command -v git >/dev/null 2>&1; then
        fatal "Git no está instalado."
    fi

    success "Git disponible: $(git --version)"
}


configure_identity() {
    log "Configurando identidad Git..."

    sudo \
        --user "$TARGET_USER" \
        -- \
        git config \
        --global \
        user.name \
        "$GIT_USER_NAME"

    sudo \
        --user "$TARGET_USER" \
        -- \
        git config \
        --global \
        user.email \
        "$GIT_USER_EMAIL"

    success "Nombre Git configurado: ${GIT_USER_NAME}"
    success "Correo Git configurado: ${GIT_USER_EMAIL}"
}


configure_defaults() {
    sudo \
        --user "$TARGET_USER" \
        -- \
        git config \
        --global \
        init.defaultBranch \
        main

    sudo \
        --user "$TARGET_USER" \
        -- \
        git config \
        --global \
        pull.ff \
        only

    success "Preferencias básicas de Git configuradas."
}


verify_configuration() {
    local configured_name
    local configured_email

    configured_name="$(
        sudo \
            --user "$TARGET_USER" \
            -- \
            git config \
            --global \
            --get \
            user.name
    )"

    configured_email="$(
        sudo \
            --user "$TARGET_USER" \
            -- \
            git config \
            --global \
            --get \
            user.email
    )"

    if [[ "$configured_name" != "$GIT_USER_NAME" ]]; then
        fatal "El nombre Git no se ha guardado correctamente."
    fi

    if [[ "$configured_email" != "$GIT_USER_EMAIL" ]]; then
        fatal "El correo Git no se ha guardado correctamente."
    fi

    success "Identidad Git verificada."
}


print_summary() {
    printf '\n'
    printf '============================================================\n'
    printf ' ROAD EYE - GIT CONFIGURADO\n'
    printf '============================================================\n'
    printf '\n'
    printf 'Usuario Linux:\n'
    printf '  %s\n' "$TARGET_USER"
    printf '\n'
    printf 'Nombre Git:\n'
    printf '  %s\n' "$GIT_USER_NAME"
    printf '\n'
    printf 'Correo Git:\n'
    printf '  %s\n' "$GIT_USER_EMAIL"
    printf '\n'
    printf 'Nota:\n'
    printf '  Las credenciales o tokens de GitHub no se guardan.\n'
    printf '\n'
}


main() {
    require_root
    check_user
    check_git
    configure_identity
    configure_defaults
    verify_configuration
    print_summary
}


main "$@"
