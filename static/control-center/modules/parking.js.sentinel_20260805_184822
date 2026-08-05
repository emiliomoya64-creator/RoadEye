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
