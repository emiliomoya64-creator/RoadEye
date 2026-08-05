#!/usr/bin/env python3

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONTROL_DIR = PROJECT_DIR / "static" / "control-center"
MODULES_DIR = CONTROL_DIR / "modules"

INDEX_FILE = CONTROL_DIR / "index.html"
CSS_FILE = CONTROL_DIR / "control-center.css"
APP_FILE = CONTROL_DIR / "control-center.js"


def backup(path: Path) -> None:
    if not path.exists():
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    target = path.with_name(
        f"{path.name}.backup_{stamp}"
    )

    shutil.copy2(path, target)

    print(
        "  Copia:",
        target.relative_to(PROJECT_DIR),
    )


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup(path)

    path.write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )

    print(
        "  Actualizado:",
        path.relative_to(PROJECT_DIR),
    )


CONTROL_CENTER_JS = r'''
"use strict";

import {
    fetchSettings,
    fetchStorageStatus,
    saveSettings,
    runStorageCleanup
} from "./modules/api.js";

import {
    setConnection,
    showMessage
} from "./modules/ui.js";

import {
    renderOverview
} from "./modules/overview.js";

import {
    renderStorage
} from "./modules/storage.js";

import {
    renderRecording
} from "./modules/recording.js";

import {
    renderParking
} from "./modules/parking.js";


const state = {
    settings: {},
    storage: {},
    activeSection: "overview",
    dirty: false
};


const titles = {
    overview: "Resumen",
    storage: "Almacenamiento",
    recording: "Grabación",
    parking: "Modo Parking"
};


document.addEventListener(
    "DOMContentLoaded",
    initialize
);


async function initialize() {
    bindNavigation();
    bindSaveButton();

    await reloadData();
}


async function reloadData() {
    try {
        const [
            settingsResponse,
            storageResponse
        ] = await Promise.all(
            [
                fetchSettings(),
                fetchStorageStatus()
            ]
        );

        state.settings = (
            settingsResponse.settings || {}
        );

        state.storage = (
            storageResponse.storage || {}
        );

        state.dirty = false;

        setConnection(true);
        updateSaveState();
        renderActiveSection();

    } catch (error) {
        setConnection(false);

        showMessage(
            error.message,
            "error"
        );
    }
}


function bindNavigation() {
    document.querySelectorAll(
        ".nav-button[data-section]"
    ).forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                state.activeSection = (
                    button.dataset.section
                );

                document.querySelectorAll(
                    ".nav-button[data-section]"
                ).forEach((item) => {
                    item.classList.toggle(
                        "active",
                        item === button
                    );
                });

                renderActiveSection();
            }
        );
    });
}


function bindSaveButton() {
    document.getElementById(
        "saveSettings"
    ).addEventListener(
        "click",
        saveCurrentSettings
    );
}


function renderActiveSection() {
    document.getElementById(
        "sectionTitle"
    ).textContent = (
        titles[state.activeSection]
        || "RoadEye"
    );

    if (state.activeSection === "storage") {
        renderStorage(
            state.storage,
            state.settings.storage || {}
        );

    } else if (
        state.activeSection === "recording"
    ) {
        renderRecording(
            state.settings.recording || {}
        );

    } else if (
        state.activeSection === "parking"
    ) {
        renderParking(
            state.settings.parking || {}
        );

    } else {
        renderOverview(
            state.settings,
            state.storage
        );
    }

    bindEditableFields();
    bindStorageActions();
}


function bindEditableFields() {
    document.querySelectorAll(
        "[data-setting]"
    ).forEach((element) => {
        element.addEventListener(
            "change",
            () => {
                state.dirty = true;
                updateSaveState();
            }
        );
    });
}


function bindStorageActions() {
    const simulateButton = document.getElementById(
        "simulateCleanup"
    );

    const cleanupButton = document.getElementById(
        "runCleanup"
    );

    if (simulateButton) {
        simulateButton.addEventListener(
            "click",
            () => executeCleanup(true)
        );
    }

    if (cleanupButton) {
        cleanupButton.addEventListener(
            "click",
            () => executeCleanup(false)
        );
    }
}


function updateSaveState() {
    const status = document.getElementById(
        "saveStatus"
    );

    const button = document.getElementById(
        "saveSettings"
    );

    status.textContent = (
        state.dirty
        ? "Cambios sin guardar"
        : "Configuración cargada"
    );

    button.disabled = !state.dirty;
}


function readFieldValue(
    element
) {
    if (element.type === "checkbox") {
        return element.checked;
    }

    if (element.type === "number") {
        return Number(element.value);
    }

    return element.value;
}


function collectSectionValues() {
    const result = {
        storage: {
            ...(state.settings.storage || {})
        },

        recording: {
            ...(state.settings.recording || {})
        },

        parking: {
            ...(state.settings.parking || {})
        }
    };

    document.querySelectorAll(
        "[data-setting]"
    ).forEach((element) => {
        const path = element.dataset.setting;

        const [
            section,
            key
        ] = path.split(".");

        if (
            !section
            || !key
            || !result[section]
        ) {
            return;
        }

        result[section][key] = (
            readFieldValue(element)
        );
    });

    return result;
}


async function saveCurrentSettings() {
    const button = document.getElementById(
        "saveSettings"
    );

    button.disabled = true;
    button.textContent = "Guardando…";

    try {
        const newSettings = collectSectionValues();

        const response = await saveSettings(
            newSettings
        );

        state.settings = (
            response.settings
            || newSettings
        );

        state.dirty = false;

        updateSaveState();

        showMessage(
            response.message
            || (
                "Configuración guardada. "
                + "Reinicia RoadEye para aplicar "
                + "todos los cambios."
            ),
            "success"
        );

        if (
            state.activeSection === "overview"
        ) {
            renderActiveSection();
        }

    } catch (error) {
        state.dirty = true;
        updateSaveState();

        showMessage(
            error.message,
            "error"
        );

    } finally {
        button.textContent = "Guardar cambios";
        button.disabled = !state.dirty;
    }
}


async function executeCleanup(
    dryRun
) {
    const output = document.getElementById(
        "cleanupResult"
    );

    if (!output) {
        return;
    }

    output.classList.remove(
        "hidden"
    );

    output.textContent = (
        dryRun
        ? "Simulando limpieza…"
        : "Ejecutando limpieza…"
    );

    try {
        const response = await runStorageCleanup(
            {
                force: dryRun,
                dry_run: dryRun
            }
        );

        const result = response.result || {};

        output.textContent = [
            dryRun
                ? "SIMULACIÓN COMPLETADA"
                : "LIMPIEZA COMPLETADA",

            "",

            `Vídeos seleccionados: ${
                (result.deleted || []).length
            }`,

            `Protegidos respetados: ${
                result.skipped_protected || 0
            }`,

            `Espacio: ${
                result.freed || "0 B"
            }`,

            `Viajes actualizados: ${
                (result.trips_updated || []).length
            }`,

            `Viajes eliminados: ${
                (result.trips_removed || []).length
            }`,

            "",

            dryRun
                ? "No se ha eliminado ningún archivo."
                : "Operación finalizada."
        ].join("\n");

        const storageResponse = (
            await fetchStorageStatus()
        );

        state.storage = (
            storageResponse.storage || {}
        );

    } catch (error) {
        output.textContent = (
            `ERROR\n\n${error.message}`
        );
    }
}
'''


API_JS = r'''
"use strict";


async function requestJson(
    url,
    options = {}
) {
    const response = await fetch(
        url,
        {
            cache: "no-store",
            ...options
        }
    );

    let data = {};

    try {
        data = await response.json();

    } catch {
        throw new Error(
            `Respuesta no válida de ${url}`
        );
    }

    if (!response.ok) {
        throw new Error(
            data.detail
            || `Error HTTP ${response.status}`
        );
    }

    return data;
}


export function fetchSettings() {
    return requestJson(
        "/api/settings"
    );
}


export function fetchStorageStatus() {
    return requestJson(
        "/api/storage/status"
    );
}


export function saveSettings(
    settings
) {
    return requestJson(
        "/api/settings",
        {
            method: "PUT",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                settings
            )
        }
    );
}


export function runStorageCleanup(
    options
) {
    return requestJson(
        "/api/storage/cleanup",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                options || {}
            )
        }
    );
}
'''


UI_JS = r'''
"use strict";


export function setConnection(
    connected
) {
    document.getElementById(
        "connectionDot"
    ).classList.toggle(
        "online",
        connected
    );

    document.getElementById(
        "connectionText"
    ).textContent = (
        connected
        ? "RoadEye conectado"
        : "Sin conexión"
    );
}


export function showMessage(
    message,
    kind = ""
) {
    const element = document.getElementById(
        "message"
    );

    element.textContent = message;

    element.className = (
        `message ${kind}`
    );

    window.setTimeout(
        () => {
            element.classList.add(
                "hidden"
            );
        },
        7000
    );
}


export function setContent(
    html
) {
    document.getElementById(
        "controlContent"
    ).innerHTML = html;
}


export function formatBytes(
    value
) {
    let size = Math.max(
        0,
        Number(value) || 0
    );

    const units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ];

    let index = 0;

    while (
        size >= 1024
        && index < units.length - 1
    ) {
        size /= 1024;
        index += 1;
    }

    return (
        `${size.toFixed(
            index === 0 ? 0 : 1
        )} ${units[index]}`
    );
}


export function checked(
    value
) {
    return value ? "checked" : "";
}


export function selected(
    current,
    expected
) {
    return (
        current === expected
        ? "selected"
        : ""
    );
}
'''


STORAGE_JS = r'''
"use strict";

import {
    checked,
    formatBytes,
    setContent
} from "./ui.js";


export function renderStorage(
    storage,
    settings
) {
    const disk = storage.disk || {};

    setContent(`
        <div class="settings-grid">
            <article class="settings-card">
                <span class="eyebrow">
                    Estado real
                </span>

                <h2>SSD principal</h2>

                <div class="data-list">
                    <div class="data-row">
                        <span>Uso actual</span>

                        <strong>
                            ${Number(
                                disk.used_percent || 0
                            ).toFixed(2)} %
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Espacio libre</span>

                        <strong>
                            ${formatBytes(
                                disk.free_bytes || 0
                            )}
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Storage Manager</span>

                        <strong>
                            ${
                                storage.running
                                ? "Activo"
                                : "Detenido"
                            }
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Carpeta</span>

                        <strong class="path-value">
                            ${storage.folder || "--"}
                        </strong>
                    </div>
                </div>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Límites automáticos
                </span>

                <h2>Configuración</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Gestión automática
                        </strong>

                        <small>
                            Vigila y libera espacio.
                        </small>
                    </span>

                    <input
                        type="checkbox"
                        data-setting="storage.enabled"
                        ${checked(settings.enabled)}
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>Uso máximo</strong>

                        <small>
                            Porcentaje que activa la limpieza.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            type="number"
                            min="40"
                            max="98"
                            step="1"
                            value="${
                                settings
                                .max_usage_percent ?? 85
                            }"
                            data-setting=
                                "storage.max_usage_percent"
                        >

                        <b>%</b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Espacio libre mínimo
                        </strong>

                        <small>
                            Reserva mínima del SSD.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            type="number"
                            min="1"
                            max="500"
                            step="1"
                            value="${
                                settings
                                .minimum_free_gb ?? 10
                            }"
                            data-setting=
                                "storage.minimum_free_gb"
                        >

                        <b>GB</b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Intervalo
                        </strong>

                        <small>
                            Frecuencia de comprobación.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            type="number"
                            min="10"
                            max="86400"
                            step="10"
                            value="${
                                settings
                                .check_interval_seconds ?? 60
                            }"
                            data-setting=
                                "storage.check_interval_seconds"
                        >

                        <b>s</b>
                    </span>
                </label>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Política de limpieza
                </span>

                <h2>Protección y mantenimiento</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Limpiar al arrancar
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "storage.clean_on_start"
                        ${
                            checked(
                                settings.clean_on_start
                            )
                        }
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Antes de grabar
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "storage.clean_before_recording"
                        ${
                            checked(
                                settings
                                .clean_before_recording
                            )
                        }
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Limpiar huérfanos
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "storage.clean_video_orphans"
                        ${
                            checked(
                                settings
                                .clean_video_orphans
                            )
                        }
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Eliminar viajes vacíos
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "storage.delete_empty_trips"
                        ${
                            checked(
                                settings
                                .delete_empty_trips
                            )
                        }
                    >
                </label>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Comprobación manual
                </span>

                <h2>Limpieza del SSD</h2>

                <p>
                    La simulación indica qué archivos
                    se borrarían sin eliminarlos.
                </p>

                <div class="button-row">
                    <button
                        id="simulateCleanup"
                        class="secondary-button"
                        type="button"
                    >
                        Simular limpieza
                    </button>

                    <button
                        id="runCleanup"
                        class="danger-button"
                        type="button"
                    >
                        Limpiar ahora
                    </button>
                </div>

                <pre
                    id="cleanupResult"
                    class="result-box hidden"
                ></pre>
            </article>
        </div>
    `);
}
'''


RECORDING_JS = r'''
"use strict";

import {
    checked,
    setContent
} from "./ui.js";


export function renderRecording(
    recording
) {
    setContent(`
        <div class="settings-grid">
            <article class="settings-card">
                <span class="eyebrow">
                    Cámara principal
                </span>

                <h2>Grabación</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Grabar al iniciar
                        </strong>

                        <small>
                            Inicia automáticamente RoadEye.
                        </small>
                    </span>

                    <input
                        type="checkbox"
                        data-setting="recording.enabled"
                        ${checked(recording.enabled)}
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Duración por segmento
                        </strong>

                        <small>
                            Duración de cada archivo.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            type="number"
                            min="10"
                            max="600"
                            step="5"
                            value="${
                                recording
                                .segment_seconds ?? 30
                            }"
                            data-setting=
                                "recording.segment_seconds"
                        >

                        <b>s</b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Imágenes por segundo
                        </strong>

                        <small>
                            Mayor valor consume más CPU.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            type="number"
                            min="5"
                            max="30"
                            step="1"
                            value="${
                                recording.fps ?? 20
                            }"
                            data-setting="recording.fps"
                        >

                        <b>FPS</b>
                    </span>
                </label>
            </article>

            <article class="information-card">
                <h3>
                    Configuración recomendada
                </h3>

                <p>
                    20 FPS y segmentos de 30 segundos
                    ofrecen buen equilibrio entre calidad,
                    consumo de CPU y facilidad de revisión.
                </p>
            </article>
        </div>
    `);
}
'''


PARKING_JS = r'''
"use strict";

import {
    checked,
    selected,
    setContent
} from "./ui.js";


export function renderParking(
    parking
) {
    setContent(`
        <div class="settings-grid">
            <article class="settings-card">
                <span class="eyebrow">
                    Vigilancia estacionado
                </span>

                <h2>Activación</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Activar Modo Parking
                        </strong>

                        <small>
                            El motor se instalará en la
                            siguiente fase.
                        </small>
                    </span>

                    <input
                        type="checkbox"
                        data-setting="parking.enabled"
                        ${checked(parking.enabled)}
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>Detectar</strong>
                    </span>

                    <select
                        data-setting="parking.trigger"
                    >
                        <option
                            value="motion"
                            ${
                                selected(
                                    parking.trigger,
                                    "motion"
                                )
                            }
                        >
                            Movimiento
                        </option>

                        <option
                            value="impact"
                            ${
                                selected(
                                    parking.trigger,
                                    "impact"
                                )
                            }
                        >
                            Impacto
                        </option>

                        <option
                            value="motion_or_impact"
                            ${
                                selected(
                                    parking.trigger,
                                    "motion_or_impact"
                                )
                            }
                        >
                            Movimiento o impacto
                        </option>
                    </select>
                </label>

                <label class="form-row">
                    <span>
                        <strong>Sensibilidad</strong>

                        <small>
                            De 0,05 a 1,00.
                        </small>
                    </span>

                    <input
                        class="plain-number"
                        type="number"
                        min="0.05"
                        max="1"
                        step="0.05"
                        value="${
                            parking
                            .motion_sensitivity ?? 0.55
                        }"
                        data-setting=
                            "parking.motion_sensitivity"
                    >
                </label>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Tiempos configurables
                </span>

                <h2>Grabación del evento</h2>

                ${
                    numberRow(
                        "Segundos anteriores",
                        "parking.pre_event_seconds",
                        parking.pre_event_seconds ?? 10,
                        0,
                        120,
                        5
                    )
                }

                ${
                    numberRow(
                        "Duración inicial",
                        "parking.record_seconds",
                        parking.record_seconds ?? 30,
                        5,
                        600,
                        5
                    )
                }

                ${
                    numberRow(
                        "Extensión por movimiento",
                        "parking.extend_seconds",
                        parking.extend_seconds ?? 15,
                        0,
                        300,
                        5
                    )
                }

                ${
                    numberRow(
                        "Duración máxima",
                        "parking.max_event_seconds",
                        parking.max_event_seconds ?? 120,
                        10,
                        3600,
                        10
                    )
                }

                ${
                    numberRow(
                        "Espera entre eventos",
                        "parking.cooldown_seconds",
                        parking.cooldown_seconds ?? 5,
                        0,
                        300,
                        1
                    )
                }
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Protección
                </span>

                <h2>Contenido del evento</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Proteger grabaciones
                        </strong>

                        <small>
                            No podrán eliminarse
                            automáticamente.
                        </small>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "parking.protect_recording"
                        ${
                            checked(
                                parking.protect_recording
                            )
                        }
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Capturar fotografía
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "parking.capture_photo"
                        ${
                            checked(
                                parking.capture_photo
                            )
                        }
                    >
                </label>
            </article>
        </div>
    `);
}


function numberRow(
    label,
    path,
    value,
    minimum,
    maximum,
    step
) {
    return `
        <label class="form-row">
            <span>
                <strong>${label}</strong>
            </span>

            <span class="input-unit">
                <input
                    type="number"
                    min="${minimum}"
                    max="${maximum}"
                    step="${step}"
                    value="${value}"
                    data-setting="${path}"
                >

                <b>s</b>
            </span>
        </label>
    `;
}
'''


CSS_ADDITION = r'''

/* ==========================================================
   CONTROL CENTER · FORMULARIOS EDITABLES
   ========================================================== */

.header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}

.primary-button,
.secondary-button,
.danger-button {
    min-height: 42px;
    padding: 0 15px;

    color: white;
    font-weight: 760;

    border: 1px solid transparent;
    border-radius: 10px;

    cursor: pointer;
}

.primary-button {
    color: #06110b;
    background: var(--accent);
}

.secondary-button {
    border-color: var(--border);
    background: var(--panel-light);
}

.danger-button {
    color: #ffcaca;

    border-color: rgba(224, 92, 92, 0.25);
    background: rgba(224, 92, 92, 0.12);
}

button:disabled {
    opacity: 0.45;
    cursor: default;
}

.form-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;

    min-height: 68px;
    padding: 12px 0;

    border-top: 1px solid var(--border);
}

.form-row:first-of-type {
    border-top: 0;
}

.form-row strong,
.form-row small {
    display: block;
}

.form-row small {
    margin-top: 5px;

    color: var(--muted);
    font-size: 0.66rem;
}

.form-row input[type="checkbox"] {
    width: 22px;
    height: 22px;

    accent-color: var(--accent);
}

.input-unit {
    display: flex;
    align-items: center;

    min-width: 116px;

    border: 1px solid var(--border);
    border-radius: 9px;

    background: #0b1114;
}

.input-unit input {
    width: 78px;
    height: 40px;
    padding: 0 9px;

    color: var(--text);
    text-align: right;

    border: 0;
    outline: 0;
    background: transparent;
}

.input-unit b {
    padding-right: 9px;

    color: var(--muted);
    font-size: 0.65rem;
}

.plain-number,
select {
    min-width: 150px;
    height: 42px;
    padding: 0 10px;

    color: var(--text);

    border: 1px solid var(--border);
    border-radius: 9px;

    outline: 0;
    background: #0b1114;
}

.button-row {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;

    margin-top: 18px;
}

.result-box {
    margin: 14px 0 0;
    padding: 15px;

    overflow: auto;

    color: #b9c8ce;
    line-height: 1.55;

    border: 1px solid var(--border);
    border-radius: 11px;

    background: #050809;
}

.message.success {
    color: #8ee9b5;

    border-color: rgba(53, 200, 120, 0.25);
    background: rgba(53, 200, 120, 0.10);
}

.message.error {
    color: #ffaaaa;

    border-color: rgba(224, 92, 92, 0.25);
    background: rgba(224, 92, 92, 0.10);
}

.path-value {
    max-width: 65%;
    overflow-wrap: anywhere;
}

@media (max-width: 650px) {
    .control-header {
        align-items: flex-start;
        flex-direction: column;
    }

    .header-actions {
        width: 100%;
        justify-content: space-between;
    }

    .form-row {
        align-items: flex-start;
    }
}
'''


def patch_index() -> None:
    text = INDEX_FILE.read_text(
        encoding="utf-8"
    )

    old = '''                <span
                    id="loadStatus"
                    class="load-status"
                >
                    Cargando…
                </span>
'''

    new = '''                <div class="header-actions">
                    <span
                        id="saveStatus"
                        class="load-status"
                    >
                        Cargando…
                    </span>

                    <button
                        id="saveSettings"
                        class="primary-button"
                        type="button"
                        disabled
                    >
                        Guardar cambios
                    </button>
                </div>
'''

    if old not in text:
        if 'id="saveSettings"' in text:
            print(
                "  Cabecera editable ya instalada"
            )
            return

        raise RuntimeError(
            "No se encontró loadStatus en index.html"
        )

    backup(INDEX_FILE)

    INDEX_FILE.write_text(
        text.replace(
            old,
            new,
            1,
        ),
        encoding="utf-8",
    )

    print(
        "  Cabecera editable instalada"
    )


def patch_css() -> None:
    text = CSS_FILE.read_text(
        encoding="utf-8"
    )

    marker = (
        "CONTROL CENTER · FORMULARIOS EDITABLES"
    )

    if marker in text:
        print(
            "  Estilos editables ya instalados"
        )
        return

    backup(CSS_FILE)

    CSS_FILE.write_text(
        text.rstrip()
        + "\n"
        + CSS_ADDITION.strip()
        + "\n",
        encoding="utf-8",
    )

    print(
        "  Estilos editables instalados"
    )


def verify() -> None:
    required = [
        APP_FILE,
        MODULES_DIR / "api.js",
        MODULES_DIR / "ui.js",
        MODULES_DIR / "storage.js",
        MODULES_DIR / "recording.js",
        MODULES_DIR / "parking.js",
    ]

    for path in required:
        if not path.is_file():
            raise RuntimeError(
                f"Falta {path.relative_to(PROJECT_DIR)}"
            )

    index = INDEX_FILE.read_text(
        encoding="utf-8"
    )

    if 'id="saveSettings"' not in index:
        raise RuntimeError(
            "No se instaló el botón Guardar."
        )

    api_text = (
        MODULES_DIR
        / "api.js"
    ).read_text(
        encoding="utf-8"
    )

    if 'method: "PUT"' not in api_text:
        raise RuntimeError(
            "No se instaló guardado PUT."
        )

    print(
        "  Verificación final: correcta"
    )


def main() -> int:
    print()
    print("=" * 62)
    print(
        "   RoadEye Control Center · Edición y guardado"
    )
    print("=" * 62)
    print()

    if not INDEX_FILE.exists():
        raise RuntimeError(
            "El Control Center modular "
            "no está instalado."
        )

    patch_index()
    patch_css()

    write_file(
        APP_FILE,
        CONTROL_CENTER_JS,
    )

    write_file(
        MODULES_DIR / "api.js",
        API_JS,
    )

    write_file(
        MODULES_DIR / "ui.js",
        UI_JS,
    )

    write_file(
        MODULES_DIR / "storage.js",
        STORAGE_JS,
    )

    write_file(
        MODULES_DIR / "recording.js",
        RECORDING_JS,
    )

    write_file(
        MODULES_DIR / "parking.js",
        PARKING_JS,
    )

    verify()

    Path(__file__).chmod(
        Path(__file__).stat().st_mode
        | 0o111
    )

    print()
    print(
        "Control Center editable instalado."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())

    except Exception as exc:
        print(
            f"\nERROR: {exc}",
            file=sys.stderr,
        )

        raise SystemExit(1)
