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

                <label class="form-row">
                    <span>
                        <strong>
                            Duración de grabación
                        </strong>

                        <small>
                            Tiempo inicial al detectar movimiento.
                        </small>
                    </span>

                    <select
                        data-setting="parking.record_seconds"
                    >
                        <option value="15" ${
                            Number(parking.record_seconds ?? 30) === 15
                                ? "selected"
                                : ""
                        }>
                            15 segundos
                        </option>

                        <option value="20" ${
                            Number(parking.record_seconds ?? 30) === 20
                                ? "selected"
                                : ""
                        }>
                            20 segundos
                        </option>

                        <option value="30" ${
                            Number(parking.record_seconds ?? 30) === 30
                                ? "selected"
                                : ""
                        }>
                            30 segundos
                        </option>
                    </select>
                </label>

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
