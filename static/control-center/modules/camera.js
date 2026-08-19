"use strict";

import {
    checked,
    setContent
} from "./ui.js";


export function renderCamera(
    camera
) {
    const front = camera.front || {};

    setContent(`
        <div class="settings-grid">
            <article class="settings-card">
                <span class="eyebrow">
                    Cámara principal
                </span>

                <h2>Orientación</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Voltear horizontal
                        </strong>

                        <small>
                            Invierte izquierda y derecha.
                        </small>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "camera.front.flip_horizontal"
                        ${checked(
                            front.flip_horizontal
                        )}
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Voltear vertical
                        </strong>

                        <small>
                            Invierte arriba y abajo.
                        </small>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "camera.front.flip_vertical"
                        ${checked(
                            front.flip_vertical
                        )}
                    >
                </label>
            </article>

            <article class="information-card">
                <h3>
                    Combinación
                </h3>

                <p>
                    Si activas horizontal y vertical
                    al mismo tiempo, la imagen gira 180°.
                </p>
            </article>
        </div>
    `);
}
