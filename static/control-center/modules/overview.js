"use strict";

import {
    formatBytes,
    setContent
} from "./ui.js";


export function renderOverview(
    settings,
    storage
) {
    const disk = storage.disk || {};
    const recording = settings.recording || {};
    const parking = settings.parking || {};
    const storageConfig = settings.storage || {};

    setContent(`
        <article class="hero-card">
            <div>
                <span class="eyebrow">
                    Estado general
                </span>

                <h2>RoadEye operativo</h2>

                <p>
                    El Control Center está conectado con
                    la configuración y el Storage Manager.
                </p>
            </div>

            <span class="hero-check">✓</span>
        </article>

        <div class="metric-grid">
            <article class="metric-card">
                <span>Uso del SSD</span>

                <strong>
                    ${Number(
                        disk.used_percent || 0
                    ).toFixed(1)} %
                </strong>

                <small>
                    ${formatBytes(
                        disk.free_bytes || 0
                    )} libres
                </small>
            </article>

            <article class="metric-card">
                <span>Límite del SSD</span>

                <strong>
                    ${
                        storageConfig
                        .max_usage_percent ?? "--"
                    } %
                </strong>

                <small>
                    Limpieza automática
                </small>
            </article>

            <article class="metric-card">
                <span>Segmentos</span>

                <strong>
                    ${
                        recording
                        .segment_seconds ?? "--"
                    } s
                </strong>

                <small>
                    ${
                        recording.fps ?? "--"
                    } FPS
                </small>
            </article>

            <article class="metric-card">
                <span>Modo Parking</span>

                <strong>
                    ${
                        parking.enabled
                        ? "Activado"
                        : "Desactivado"
                    }
                </strong>

                <small>
                    ${
                        parking
                        .record_seconds ?? "--"
                    } segundos iniciales
                </small>
            </article>
        </div>

        <article class="information-card">
            <h3>Estado del módulo</h3>

            <p>
                Esta primera versión modular es de lectura.
                El siguiente bloque añadirá edición,
                validación y guardado seguro.
            </p>
        </article>
    `);
}
