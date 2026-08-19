"use strict";

import {
    setContent
} from "./ui.js";


function formatBytes(bytes) {
    const value = Number(bytes || 0);

    if (value >= 1024 ** 3) {
        return (
            value / (1024 ** 3)
        ).toFixed(1) + " GB";
    }

    if (value >= 1024 ** 2) {
        return (
            value / (1024 ** 2)
        ).toFixed(1) + " MB";
    }

    return value + " B";
}


function formatUptime(seconds) {
    let remaining = Math.max(
        0,
        Math.floor(Number(seconds || 0))
    );

    const days = Math.floor(
        remaining / 86400
    );

    remaining %= 86400;

    const hours = Math.floor(
        remaining / 3600
    );

    remaining %= 3600;

    const minutes = Math.floor(
        remaining / 60
    );

    if (days > 0) {
        return `${days} d ${hours} h ${minutes} min`;
    }

    if (hours > 0) {
        return `${hours} h ${minutes} min`;
    }

    return `${minutes} min`;
}


function badge(
    text,
    type = "ok"
) {
    return `
        <span class="system-badge system-${type}">
            <span class="system-dot"></span>
            ${text}
        </span>
    `;
}


function temperatureBadge(value) {
    const temp = Number(value || 0);

    if (temp >= 80) {
        return badge(
            `${temp.toFixed(1)} °C`,
            "danger"
        );
    }

    if (temp >= 70) {
        return badge(
            `${temp.toFixed(1)} °C`,
            "warning"
        );
    }

    return badge(
        `${temp.toFixed(1)} °C`,
        "ok"
    );
}


function cpuBadge(value) {
    const cpu = Number(value || 0);

    if (cpu >= 90) {
        return badge(
            `${cpu.toFixed(1)} %`,
            "danger"
        );
    }

    if (cpu >= 70) {
        return badge(
            `${cpu.toFixed(1)} %`,
            "warning"
        );
    }

    return badge(
        `${cpu.toFixed(1)} %`,
        "ok"
    );
}


function diskBadge(value) {
    const used = Number(value || 0);

    if (used >= 95) {
        return badge(
            `${used.toFixed(1)} %`,
            "danger"
        );
    }

    if (used >= 85) {
        return badge(
            `${used.toFixed(1)} %`,
            "warning"
        );
    }

    return badge(
        `${used.toFixed(1)} %`,
        "ok"
    );
}


function serviceRows(services) {
    return Object.values(
        services || {}
    ).map((service) => {

        const state =
            service.state || "unknown";

        let type = "warning";

        if (state === "running") {
            type = "ok";
        }

        if (
            state === "failed"
            || service.last_error
        ) {
            type = "danger";
        }

        /*
         * Startup es una pantalla temporal.
         * Es normal que quede stopped
         * después de terminar el arranque.
         */
        if (
            service.name === "startup"
            && state === "stopped"
            && !service.last_error
        ) {
            type = "ok";
        }

        const visibleState =
            service.name === "startup"
            && state === "stopped"
                ? "Finalizado"
                : state;

        return `
            <div class="form-row">
                <span>
                    <strong>
                        ${
                            service.description
                            || service.name
                        }
                    </strong>

                    <small>
                        ${service.name}
                    </small>
                </span>

                ${
                    badge(
                        visibleState,
                        type
                    )
                }
            </div>

            ${
                service.last_error
                    ? `
                        <div class="system-error">
                            ${service.last_error}
                        </div>
                    `
                    : ""
            }
        `;
    }).join("");
}


export function renderSystem(system) {

    const raspberry =
        system.raspberry || {};

    const storage =
        system.storage || {};

    const camera =
        system.camera || {};

    const gps =
        system.gps || {};

    const recording =
        system.recording || {};

    const parking =
        system.parking || {};

    setContent(`
        <div class="system-live-header">
            <div>
                <span class="eyebrow">
                    Diagnóstico en directo
                </span>

                <h2>Estado de RoadEye</h2>
            </div>

            ${
                badge(
                    "Actualización automática",
                    "ok"
                )
            }
        </div>


        <div class="settings-grid">

            <article class="settings-card">
                <span class="eyebrow">
                    Raspberry Pi
                </span>

                <h2>Sistema</h2>

                <div class="form-row">
                    <span>
                        <strong>CPU</strong>
                        <small>Carga actual</small>
                    </span>

                    ${cpuBadge(
                        raspberry.cpu_percent
                    )}
                </div>

                <div class="form-row">
                    <span>
                        <strong>Temperatura</strong>
                        <small>Procesador</small>
                    </span>

                    ${temperatureBadge(
                        raspberry.temperature_c
                    )}
                </div>

                <div class="form-row">
                    <span>
                        <strong>
                            Tiempo encendido
                        </strong>
                        <small>
                            Desde el último arranque
                        </small>
                    </span>

                    <strong>
                        ${formatUptime(
                            raspberry.uptime_seconds
                        )}
                    </strong>
                </div>
            </article>


            <article class="settings-card">
                <span class="eyebrow">
                    Almacenamiento
                </span>

                <h2>SSD</h2>

                <div class="form-row">
                    <span>
                        <strong>Utilizado</strong>
                        <small>
                            ${formatBytes(
                                storage.used_bytes
                            )}
                            de
                            ${formatBytes(
                                storage.total_bytes
                            )}
                        </small>
                    </span>

                    ${diskBadge(
                        storage.used_percent
                    )}
                </div>

                <div class="form-row">
                    <span>
                        <strong>Libre</strong>
                    </span>

                    <strong>
                        ${formatBytes(
                            storage.free_bytes
                        )}
                    </strong>
                </div>
            </article>


            <article class="settings-card">
                <span class="eyebrow">
                    Hardware
                </span>

                <h2>Dispositivos</h2>

                <div class="form-row">
                    <span>
                        <strong>
                            Cámara frontal
                        </strong>
                    </span>

                    ${
                        camera.front_camera
                            ? badge(
                                "Disponible",
                                "ok"
                            )
                            : badge(
                                "No disponible",
                                "danger"
                            )
                    }
                </div>

                <div class="form-row">
                    <span>
                        <strong>GPS</strong>

                        <small>
                            ${gps.satellites ?? 0}
                            satélites
                        </small>
                    </span>

                    ${
                        gps.fix
                            ? badge(
                                "Fix GPS",
                                "ok"
                            )
                            : badge(
                                "Sin fix",
                                "warning"
                            )
                    }
                </div>
            </article>


            <article class="settings-card">
                <span class="eyebrow">
                    RoadEye
                </span>

                <h2>Grabación</h2>

                <div class="form-row">
                    <span>
                        <strong>Grabador</strong>
                    </span>

                    ${
                        !recording.service_running
                            ? badge(
                                "Detenido",
                                "danger"
                            )
                            : recording.recording
                                ? badge(
                                    "Grabando",
                                    "warning"
                                )
                                : badge(
                                    "Preparado",
                                    "ok"
                                )
                    }
                </div>

                <div class="form-row">
                    <span>
                        <strong>
                            Modo Parking
                        </strong>
                    </span>

                    ${
                        parking.enabled
                            ? badge(
                                parking.motion
                                    ? "Movimiento"
                                    : "Vigilando",
                                parking.motion
                                    ? "warning"
                                    : "ok"
                            )
                            : badge(
                                "Desactivado",
                                "neutral"
                            )
                    }
                </div>

                <div class="form-row">
                    <span>
                        <strong>
                            Sentinel
                        </strong>
                    </span>

                    <strong>
                        ${
                            parking.state
                            || "desconocido"
                        }
                    </strong>
                </div>
            </article>


            <article class=
                "settings-card system-services-card"
            >
                <span class="eyebrow">
                    Diagnóstico
                </span>

                <h2>Servicios RoadEye</h2>

                ${serviceRows(
                    system.services
                )}
            </article>

        </div>
    `);
}
