#!/usr/bin/env python3

from __future__ import annotations

import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

RECORDER = ROOT / "recorder/recorder_service.py"
PARKING = ROOT / "core/parking_service.py"
API = ROOT / "web/api.py"

CONTROL_APP = (
    ROOT
    / "static/control-center/control-center.js"
)

CONTROL_API = (
    ROOT
    / "static/control-center/modules/api.js"
)

CONTROL_PARKING = (
    ROOT
    / "static/control-center/modules/parking.js"
)


def stamp() -> str:
    return datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


def backup(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(
            f"No existe {path.relative_to(ROOT)}"
        )

    target = path.with_name(
        f"{path.name}.before-sentinel-complete-{stamp()}"
    )

    shutil.copy2(path, target)

    print(
        "  Copia:",
        target.relative_to(ROOT),
    )


def replace_once(
    path: Path,
    old: str,
    new: str,
    description: str,
) -> None:
    text = path.read_text(
        encoding="utf-8"
    )

    if new in text:
        print(
            f"  Ya aplicado: {description}"
        )
        return

    if old not in text:
        raise RuntimeError(
            f"No se encontró el punto para: {description}"
        )

    backup(path)

    path.write_text(
        text.replace(
            old,
            new,
            1,
        ),
        encoding="utf-8",
    )

    print(
        f"  Aplicado: {description}"
    )


def patch_recorder() -> None:
    replace_once(
        RECORDER,

        '''    def start_recording(self) -> bool:
        """
        Comienza la grabación.
        """
''',

        '''    def start_recording(
        self,
        *,
        trip_type: str = "driving",
    ) -> bool:
        """
        Comienza la grabación.

        trip_type permite que servicios especializados,
        como RoadEye Sentinel, creen viajes Parking sin
        alterar la grabación normal.
        """
''',

        "RecorderService acepta trip_type",
    )

    replace_once(
        RECORDER,

        '''        trip_manager.ensure_trip(
            trip_type="driving",
            started_at=datetime.now(),
        )
''',

        '''        normalized_trip_type = str(
            trip_type
        ).strip().lower()

        if normalized_trip_type not in {
            "driving",
            "parking",
            "event",
        }:
            normalized_trip_type = "driving"

        trip_manager.ensure_trip(
            trip_type=normalized_trip_type,
            started_at=datetime.now(),
        )
''',

        "RecorderService crea el viaje solicitado",
    )


def patch_parking() -> None:
    replace_once(
        PARKING,

        '''        if self._started_recording:
            self.recorder.start_recording()
''',

        '''        if self._started_recording:
            self.recorder.start_recording(
                trip_type="parking"
            )
''',

        "Sentinel inicia grabación Parking",
    )

    # El ensure_trip posterior ya no debe intentar corregir el tipo.
    text = PARKING.read_text(
        encoding="utf-8"
    )

    duplicate = '''        trip_manager.ensure_trip(
            trip_type="parking",
            started_at=datetime.now(),
        )

        trip_manager.add_event(
'''

    replacement = '''        trip_manager.add_event(
'''

    if duplicate in text:
        backup(PARKING)

        PARKING.write_text(
            text.replace(
                duplicate,
                replacement,
                1,
            ),
            encoding="utf-8",
        )

        print(
            "  Eliminado ensure_trip Parking duplicado"
        )
    else:
        print(
            "  No hay ensure_trip Parking duplicado"
        )


PARKING_API = r'''

# ============================================================
# RoadEye Sentinel · Historial Parking
# ============================================================

@router.get(
    "/api/parking/history"
)
async def parking_history(
    limit: int = 20,
):
    safe_limit = max(
        1,
        min(
            100,
            int(limit),
        ),
    )

    trips_directory = (
        PROJECT_DIR / "trips"
    )

    history = []

    if trips_directory.exists():
        paths = sorted(
            trips_directory.glob(
                "trip_*.json"
            ),
            key=lambda item: (
                item.stat().st_mtime
            ),
            reverse=True,
        )

        for path in paths:
            try:
                trip = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

            except (
                OSError,
                json.JSONDecodeError,
            ):
                continue

            if not isinstance(
                trip,
                dict,
            ):
                continue

            for event in trip.get(
                "events",
                [],
            ):
                if not isinstance(
                    event,
                    dict,
                ):
                    continue

                if str(
                    event.get(
                        "type",
                        "",
                    )
                ).lower() != "parking":
                    continue

                data = event.get(
                    "data",
                    {},
                )

                if not isinstance(
                    data,
                    dict,
                ):
                    data = {}

                history.append(
                    {
                        "event_id": event.get(
                            "event_id"
                        ),
                        "created": event.get(
                            "created"
                        ),
                        "label": event.get(
                            "label",
                            "Evento Parking",
                        ),
                        "source": event.get(
                            "source"
                        ),
                        "protected": bool(
                            event.get(
                                "protected",
                                False,
                            )
                        ),
                        "segment": event.get(
                            "segment"
                        ),
                        "segment_time": event.get(
                            "segment_time",
                            0,
                        ),
                        "trip_id": trip.get(
                            "trip_id"
                        ),
                        "trip_type": trip.get(
                            "type"
                        ),
                        "motion_ratio": data.get(
                            "motion_ratio"
                        ),
                        "simulation": bool(
                            data.get(
                                "simulation",
                                False,
                            )
                        ),
                        "photo": data.get(
                            "photo"
                        ),
                    }
                )

    history.sort(
        key=lambda item: str(
            item.get(
                "created",
                "",
            )
        ),
        reverse=True,
    )

    return {
        "ok": True,
        "count": min(
            len(history),
            safe_limit,
        ),
        "events": history[
            :safe_limit
        ],
    }
'''


def patch_api() -> None:
    text = API.read_text(
        encoding="utf-8"
    )

    if "/api/parking/history" in text:
        print(
            "  API de historial ya instalada"
        )
        return

    backup(API)

    API.write_text(
        text.rstrip()
        + "\n"
        + PARKING_API.strip()
        + "\n",
        encoding="utf-8",
    )

    print(
        "  API de historial Parking instalada"
    )


CONTROL_API_CODE = r'''
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


export function fetchParkingStatus() {
    return requestJson(
        "/api/parking/status"
    );
}


export function fetchParkingHistory(
    limit = 20
) {
    return requestJson(
        `/api/parking/history?limit=${limit}`
    );
}


export function simulateParkingEvent() {
    return requestJson(
        "/api/parking/simulate",
        {
            method: "POST"
        }
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


PARKING_UI_CODE = r'''
"use strict";

import {
    checked,
    selected,
    setContent
} from "./ui.js";


export function renderParking(
    parking,
    runtime = {},
    history = []
) {
    const stateLabels = {
        inactive: "Inactivo",
        watching: "Vigilando",
        event: "Evento activo"
    };

    const ratio = (
        Number(
            runtime.last_motion_ratio || 0
        ) * 100
    );

    setContent(`
        <article class="hero-card">
            <div>
                <span class="eyebrow">
                    RoadEye Sentinel
                </span>

                <h2 id="sentinelState">
                    ${
                        stateLabels[
                            runtime.state
                        ] || "Consultando…"
                    }
                </h2>

                <p>
                    Vigilancia visual automática,
                    grabación inteligente y protección
                    de eventos.
                </p>
            </div>

            <span class="hero-check">
                ${
                    runtime.event_active
                    ? "!"
                    : "✓"
                }
            </span>
        </article>

        <div class="metric-grid">
            <article class="metric-card">
                <span>Estado</span>

                <strong id="parkingLiveState">
                    ${
                        stateLabels[
                            runtime.state
                        ] || "--"
                    }
                </strong>

                <small>
                    ${
                        runtime.running
                        ? "Servicio activo"
                        : "Servicio detenido"
                    }
                </small>
            </article>

            <article class="metric-card">
                <span>Movimiento</span>

                <strong id="parkingLiveRatio">
                    ${ratio.toFixed(2)} %
                </strong>

                <small>
                    Sensibilidad:
                    ${
                        parking
                        .motion_sensitivity ?? "--"
                    }
                </small>
            </article>

            <article class="metric-card">
                <span>Tiempo restante</span>

                <strong id="parkingLiveRemaining">
                    ${Number(
                        runtime.event_remaining || 0
                    ).toFixed(0)} s
                </strong>

                <small>
                    ${
                        runtime.event_active
                        ? "Grabando evento"
                        : "Sin evento activo"
                    }
                </small>
            </article>

            <article class="metric-card">
                <span>Eventos</span>

                <strong id="parkingLiveCount">
                    ${
                        runtime.event_count ?? 0
                    }
                </strong>

                <small>
                    ${
                        runtime.simulated_count ?? 0
                    } simulados
                </small>
            </article>
        </div>

        <div class="settings-grid">
            <article class="settings-card">
                <span class="eyebrow">
                    Vigilancia
                </span>

                <h2>Activación</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Activar Modo Parking
                        </strong>

                        <small>
                            Detecta movimiento delante
                            del vehículo.
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
                        <strong>Detección</strong>
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
                            Alta sensibilidad detecta
                            movimientos más pequeños.
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
                    Grabación inteligente
                </span>

                <h2>Tiempos</h2>

                ${timeField(
                    "Duración inicial",
                    "parking.record_seconds",
                    parking.record_seconds ?? 30,
                    5,
                    600,
                    5
                )}

                ${timeField(
                    "Extensión con movimiento",
                    "parking.extend_seconds",
                    parking.extend_seconds ?? 15,
                    0,
                    300,
                    5
                )}

                ${timeField(
                    "Duración máxima",
                    "parking.max_event_seconds",
                    parking.max_event_seconds ?? 120,
                    10,
                    3600,
                    10
                )}

                ${timeField(
                    "Espera entre eventos",
                    "parking.cooldown_seconds",
                    parking.cooldown_seconds ?? 5,
                    0,
                    300,
                    1
                )}
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Protección
                </span>

                <h2>Contenido</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Proteger grabación
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "parking.protect_recording"
                        ${
                            checked(
                                parking
                                .protect_recording
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

                <div class="button-row">
                    <button
                        id="simulateParking"
                        class="secondary-button"
                        type="button"
                    >
                        Simular evento
                    </button>
                </div>

                <pre
                    id="parkingSimulationResult"
                    class="result-box hidden"
                ></pre>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Historial
                </span>

                <h2>Eventos recientes</h2>

                <div
                    id="parkingHistory"
                    class="data-list"
                >
                    ${
                        renderHistory(
                            history
                        )
                    }
                </div>
            </article>
        </div>
    `);
}


export function updateParkingRuntime(
    runtime
) {
    const stateLabels = {
        inactive: "Inactivo",
        watching: "Vigilando",
        event: "Evento activo"
    };

    setText(
        "parkingLiveState",
        stateLabels[
            runtime.state
        ] || "--"
    );

    setText(
        "parkingLiveRatio",
        `${
            (
                Number(
                    runtime
                    .last_motion_ratio || 0
                ) * 100
            ).toFixed(2)
        } %`
    );

    setText(
        "parkingLiveRemaining",
        `${
            Number(
                runtime
                .event_remaining || 0
            ).toFixed(0)
        } s`
    );

    setText(
        "parkingLiveCount",
        String(
            runtime.event_count ?? 0
        )
    );

    setText(
        "sentinelState",
        stateLabels[
            runtime.state
        ] || "--"
    );
}


function renderHistory(
    history
) {
    if (!history.length) {
        return `
            <div class="data-row">
                <span>
                    Sin eventos Parking
                </span>

                <strong>—</strong>
            </div>
        `;
    }

    return history
        .slice(0, 10)
        .map((event) => {
            const created = event.created
                ? new Date(
                    event.created
                ).toLocaleString(
                    "es-ES"
                )
                : "--";

            return `
                <div class="data-row">
                    <span>
                        ${created}

                        <small>
                            ${
                                event.simulation
                                ? "Simulación"
                                : "Movimiento"
                            }
                        </small>
                    </span>

                    <strong>
                        ${
                            event.protected
                            ? "Protegido"
                            : "Normal"
                        }
                    </strong>
                </div>
            `;
        })
        .join("");
}


function timeField(
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


function setText(
    id,
    value
) {
    const element = document.getElementById(
        id
    );

    if (element) {
        element.textContent = value;
    }
}
'''


CONTROL_APP_CODE = r'''
"use strict";

import {
    fetchSettings,
    fetchStorageStatus,
    fetchParkingStatus,
    fetchParkingHistory,
    saveSettings,
    runStorageCleanup,
    simulateParkingEvent
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
    renderParking,
    updateParkingRuntime
} from "./modules/parking.js";


const state = {
    settings: {},
    storage: {},
    parkingRuntime: {},
    parkingHistory: [],
    activeSection: "overview",
    dirty: false,
    parkingTimer: null
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

    startParkingPolling();
}


async function reloadData() {
    try {
        const [
            settingsResponse,
            storageResponse,
            parkingResponse,
            historyResponse
        ] = await Promise.all(
            [
                fetchSettings(),
                fetchStorageStatus(),
                fetchParkingStatus(),
                fetchParkingHistory(20)
            ]
        );

        state.settings = (
            settingsResponse.settings || {}
        );

        state.storage = (
            storageResponse.storage || {}
        );

        state.parkingRuntime = (
            parkingResponse.parking || {}
        );

        state.parkingHistory = (
            historyResponse.events || []
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
            state.settings.parking || {},
            state.parkingRuntime,
            state.parkingHistory
        );

    } else {
        renderOverview(
            state.settings,
            state.storage
        );
    }

    bindEditableFields();
    bindStorageActions();
    bindParkingActions();
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


function bindParkingActions() {
    const button = document.getElementById(
        "simulateParking"
    );

    if (!button) {
        return;
    }

    button.addEventListener(
        "click",
        async () => {
            const output = document.getElementById(
                "parkingSimulationResult"
            );

            output.classList.remove(
                "hidden"
            );

            output.textContent = (
                "Simulando evento Parking…"
            );

            try {
                const response = (
                    await simulateParkingEvent()
                );

                state.parkingRuntime = (
                    response.parking || {}
                );

                updateParkingRuntime(
                    state.parkingRuntime
                );

                output.textContent = [
                    "EVENTO SENTINEL INICIADO",
                    "",
                    `Estado: ${
                        state.parkingRuntime.state
                    }`,
                    `Evento activo: ${
                        state.parkingRuntime
                        .event_active
                        ? "Sí"
                        : "No"
                    }`,
                    `Duración: ${
                        state.parkingRuntime
                        .settings
                        ?.record_seconds ?? "--"
                    } s`,
                    "",
                    "La grabación y protección "
                    + "se están ejecutando."
                ].join("\n");

            } catch (error) {
                output.textContent = (
                    `ERROR\n\n${error.message}`
                );
            }
        }
    );
}


function startParkingPolling() {
    if (state.parkingTimer) {
        clearInterval(
            state.parkingTimer
        );
    }

    state.parkingTimer = setInterval(
        refreshParkingRuntime,
        1000
    );
}


async function refreshParkingRuntime() {
    try {
        const response = (
            await fetchParkingStatus()
        );

        state.parkingRuntime = (
            response.parking || {}
        );

        if (
            state.activeSection
            === "parking"
        ) {
            updateParkingRuntime(
                state.parkingRuntime
            );
        }

    } catch {
        // La carga principal mostrará errores.
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
        const [
            section,
            key
        ] = element.dataset.setting.split(
            "."
        );

        if (
            section
            && key
            && result[section]
        ) {
            result[section][key] = (
                readFieldValue(
                    element
                )
            );
        }
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
        const newSettings = (
            collectSectionValues()
        );

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

    } catch (error) {
        state.dirty = true;

        updateSaveState();

        showMessage(
            error.message,
            "error"
        );

    } finally {
        button.textContent = (
            "Guardar cambios"
        );

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
        const response = (
            await runStorageCleanup(
                {
                    force: dryRun,
                    dry_run: dryRun
                }
            )
        );

        output.textContent = JSON.stringify(
            response.result || {},
            null,
            2
        );

    } catch (error) {
        output.textContent = (
            `ERROR\n\n${error.message}`
        );
    }
}
'''


def write_file(
    path: Path,
    content: str,
    description: str,
) -> None:
    backup(path)

    path.write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )

    print(
        f"  Actualizado: {description}"
    )


def patch_control_center() -> None:
    write_file(
        CONTROL_API,
        CONTROL_API_CODE,
        "API JavaScript",
    )

    write_file(
        CONTROL_PARKING,
        PARKING_UI_CODE,
        "panel Sentinel",
    )

    write_file(
        CONTROL_APP,
        CONTROL_APP_CODE,
        "Control Center principal",
    )


def verify() -> None:
    for path in (
        RECORDER,
        PARKING,
        API,
    ):
        py_compile.compile(
            str(path),
            doraise=True,
        )

    recorder_text = RECORDER.read_text(
        encoding="utf-8"
    )

    parking_text = PARKING.read_text(
        encoding="utf-8"
    )

    api_text = API.read_text(
        encoding="utf-8"
    )

    if 'trip_type: str = "driving"' not in recorder_text:
        raise RuntimeError(
            "Recorder no acepta trip_type."
        )

    if 'trip_type="parking"' not in parking_text:
        raise RuntimeError(
            "Sentinel no solicita viaje Parking."
        )

    if "/api/parking/history" not in api_text:
        raise RuntimeError(
            "Falta historial Parking."
        )

    print(
        "  Verificación final correcta"
    )


def main() -> int:
    print()
    print("=" * 64)
    print(
        "      RoadEye Sentinel · Actualización completa"
    )
    print("=" * 64)
    print()

    patch_recorder()
    patch_parking()
    patch_api()
    patch_control_center()
    verify()

    Path(__file__).chmod(
        Path(__file__).stat().st_mode
        | 0o111
    )

    print()
    print(
        "Sentinel completo instalado correctamente."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except Exception as exc:
        print(
            f"\nERROR: {exc}",
            file=sys.stderr,
        )

        raise SystemExit(1)
