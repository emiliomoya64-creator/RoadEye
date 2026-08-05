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
