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
