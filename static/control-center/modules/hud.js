"use strict";

import {
    setContent
} from "./ui.js";


export function renderHud(
    hud
) {
    const iconPercent = Math.round(
        (hud.icon_scale ?? 1.0) * 100
    );

    const textPercent = Math.round(
        (hud.text_scale ?? 1.0) * 100
    );

    setContent(`
        <div class="settings-grid">
            <article class="settings-card">
                <span class="eyebrow">
                    Pantalla
                </span>

                <h2>HUD</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Tamaño de iconos
                        </strong>

                        <small>
                            Ajusta los iconos de la barra
                            superior de RoadEye.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            id="hudIconScale"
                            type="range"
                            min="80"
                            max="200"
                            step="5"
                            value="${iconPercent}"
                        >

                        <b id="hudIconScaleValue">
                            ${iconPercent}%
                        </b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Tamaño de texto
                        </strong>

                        <small>
                            Ajusta el tamaño de las letras
                            del HUD.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            id="hudTextScale"
                            type="range"
                            min="80"
                            max="200"
                            step="5"
                            value="${textPercent}"
                        >

                        <b id="hudTextScaleValue">
                            ${textPercent}%
                        </b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Fuente
                        </strong>
                        <small>
                            Tipografía del HUD.
                        </small>
                    </span>

                    <select id="hudFont">
                        <option value="simplex"
                            ${hud.font === "simplex" ? "selected" : ""}>
                            Simple
                        </option>
                        <option value="duplex"
                            ${(hud.font ?? "duplex") === "duplex" ? "selected" : ""}>
                            RoadEye
                        </option>
                        <option value="triplex"
                            ${hud.font === "triplex" ? "selected" : ""}>
                            Triplex
                        </option>
                        <option value="complex"
                            ${hud.font === "complex" ? "selected" : ""}>
                            Técnica
                        </option>
                    
                        <option value="plain"
                            ${hud.font === "plain" ? "selected" : ""}>
                            Plain
                        </option>

                        <option value="complex_small"
                            ${hud.font === "complex_small" ? "selected" : ""}>
                            Compacta
                        </option>

                        <option value="script"
                            ${hud.font === "script" ? "selected" : ""}>
                            Script
                        </option>

                        <option value="script_complex"
                            ${hud.font === "script_complex" ? "selected" : ""}>
                            Script Complex
                        </option>
</select>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Color del HUD
                        </strong>
                        <small>
                            Color principal de iconos
                            y texto.
                        </small>
                    </span>

                    <select id="hudColor">
                        <option value="white"
                            ${(hud.color ?? "white") === "white" ? "selected" : ""}>
                            Blanco
                        </option>
                        <option value="green"
                            ${hud.color === "green" ? "selected" : ""}>
                            Verde
                        </option>
                        <option value="amber"
                            ${hud.color === "amber" ? "selected" : ""}>
                            Ámbar
                        </option>
                        <option value="ice_blue"
                            ${hud.color === "ice_blue" ? "selected" : ""}>
                            Azul hielo
                        </option>
                        <option value="red"
                            ${hud.color === "red" ? "selected" : ""}>
                            Rojo
                        </option>
                    </select>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Modo de pantalla
                        </strong>
                        <small>
                            Automático atenúa el HUD
                            durante la noche.
                        </small>
                    </span>

                    <select id="hudMode">
                        <option value="auto"
                            ${(hud.mode ?? "auto") === "auto" ? "selected" : ""}>
                            Automático
                        </option>
                        <option value="day"
                            ${hud.mode === "day" ? "selected" : ""}>
                            Día
                        </option>
                        <option value="night"
                            ${hud.mode === "night" ? "selected" : ""}>
                            Noche
                        </option>
                    </select>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Perfil
                        </strong>

                        <small>
                            Apariencia general del HUD.
                        </small>
                    </span>

                    <select id="hudProfile">
                        <option
                            value="minimal"
                            ${
                                hud.profile === "minimal"
                                ? "selected"
                                : ""
                            }
                        >
                            Minimalista
                        </option>

                        <option
                            value="normal"
                            ${
                                hud.profile === "normal"
                                ? "selected"
                                : ""
                            }
                        >
                            Normal
                        </option>

                        <option
                            value="professional"
                            ${
                                hud.profile === "professional"
                                ? "selected"
                                : ""
                            }
                        >
                            Profesional
                        </option>
                    </select>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Posición de información
                        </strong>

                        <small>
                            Sitúa la barra informativa
                            arriba o abajo.
                        </small>
                    </span>

                    <select id="hudInfoPosition">
                        <option
                            value="top"
                            ${
                                hud.info_position === "top"
                                ? "selected"
                                : ""
                            }
                        >
                            Superior
                        </option>

                        <option
                            value="bottom"
                            ${
                                hud.info_position === "bottom"
                                ? "selected"
                                : ""
                            }
                        >
                            Inferior
                        </option>
                    </select>
                </label>
            </article>

                    <label class="form-row">
                    <span>
                        <strong>
                            Color de las franjas
                        </strong>
                        <small>
                            Fondo superior e inferior.
                        </small>
                    </span>

                    <select id="hudBarColor">
                        <option value="black"
                            ${(hud.bar_color ?? "black") === "black" ? "selected" : ""}>
                            Negro
                        </option>

                        <option value="white"
                            ${hud.bar_color === "white" ? "selected" : ""}>
                            Blanco
                        </option>
                    </select>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Tamaño franja superior
                        </strong>
                        <small>
                            Altura de la barra superior.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            id="hudTopBarScale"
                            type="range"
                            min="70"
                            max="160"
                            step="5"
                            value="${Math.round((hud.top_bar_scale ?? 1.0) * 100)}"
                        >

                        <b id="hudTopBarScaleValue">
                            ${Math.round((hud.top_bar_scale ?? 1.0) * 100)}%
                        </b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Tamaño franja inferior
                        </strong>
                        <small>
                            Altura de la barra inferior.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            id="hudInfoBarScale"
                            type="range"
                            min="70"
                            max="160"
                            step="5"
                            value="${Math.round((hud.info_bar_scale ?? 1.0) * 100)}"
                        >

                        <b id="hudInfoBarScaleValue">
                            ${Math.round((hud.info_bar_scale ?? 1.0) * 100)}%
                        </b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Transparencia superior
                        </strong>
                        <small>
                            Opacidad de la franja superior.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            id="hudTopOpacity"
                            type="range"
                            min="0"
                            max="100"
                            step="5"
                            value="${Math.round((hud.top_opacity ?? 0.65) * 100)}"
                        >

                        <b id="hudTopOpacityValue">
                            ${Math.round((hud.top_opacity ?? 0.65) * 100)}%
                        </b>
                    </span>
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Transparencia inferior
                        </strong>
                        <small>
                            Opacidad de la franja inferior.
                        </small>
                    </span>

                    <span class="input-unit">
                        <input
                            id="hudInfoOpacity"
                            type="range"
                            min="0"
                            max="100"
                            step="5"
                            value="${Math.round((hud.info_opacity ?? 0.50) * 100)}"
                        >

                        <b id="hudInfoOpacityValue">
                            ${Math.round((hud.info_opacity ?? 0.50) * 100)}%
                        </b>
                    </span>
                </label>

                <div class="form-row hud-visibility">
                    <span>
                        <strong>
                            Elementos visibles
                        </strong>
                        <small>
                            Elige qué aparece en el HUD.
                        </small>
                    </span>

                    <div class="hud-visibility-grid">
                        ${[
                            ["recording", "REC"],
                            ["parking", "Parking"],
                            ["gps", "GPS"],
                            ["speed", "Velocidad"],
                            ["snapshot", "Cámara"],
                            ["gallery", "Galería"],
                            ["speed_limit", "Límite"],
                            ["road", "Carretera"],
                            ["coordinates", "Coordenadas"],
                            ["date", "Fecha"],
                            ["time", "Hora"],
                            ["settings", "Ajustes"]
                        ].map(([name, label]) => `
                            <label>
                                <input
                                    type="checkbox"
                                    data-hud-visible="${name}"
                                    ${(hud.show?.[name] ?? true) ? "checked" : ""}
                                >
                                ${label}
                            </label>
                        `).join("")}
                    </div>
                </div>

        <article class="information-card hud-preview-card">
                <span class="eyebrow">
                    Vista previa
                </span>

                <h2>RoadEye HUD</h2>

                <div
                    id="hudPreview"
                    class="hud-preview hud-preview-final"
                >
                    <svg
                        class="roadeye-preview-svg"
                        viewBox="0 0 1280 720"
                        role="img"
                        aria-label="Vista previa RoadEye HUD"
                    >

                        <defs>
                            <linearGradient
                                id="roadeyeSky"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="0%"
                                    stop-color="#7794a1"
                                />
                                <stop
                                    offset="48%"
                                    stop-color="#526a74"
                                />
                                <stop
                                    offset="49%"
                                    stop-color="#405044"
                                />
                                <stop
                                    offset="100%"
                                    stop-color="#1b2922"
                                />
                            </linearGradient>

                            <linearGradient
                                id="roadeyeRoad"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="0%"
                                    stop-color="#4d5354"
                                />
                                <stop
                                    offset="100%"
                                    stop-color="#25292a"
                                />
                            </linearGradient>
                        </defs>


                        <!-- FONDO -->

                        <rect
                            x="0"
                            y="0"
                            width="1280"
                            height="720"
                            fill="url(#roadeyeSky)"
                        />

                        <!-- Horizonte -->

                        <path
                            d="
                                M0 360
                                L115 328
                                L205 342
                                L320 300
                                L405 337
                                L520 310
                                L635 345
                                L760 308
                                L870 334
                                L995 302
                                L1100 337
                                L1280 310
                                L1280 420
                                L0 420
                                Z
                            "
                            fill="#25352f"
                            opacity=".75"
                        />


                        <!-- CARRETERA -->

                        <path
                            d="
                                M500 720
                                L598 370
                                L682 370
                                L790 720
                                Z
                            "
                            fill="url(#roadeyeRoad)"
                        />

                        <!-- Bordes carretera -->

                        <path
                            d="M500 720 L598 370"
                            stroke="#c7ced0"
                            stroke-width="7"
                            opacity=".65"
                        />

                        <path
                            d="M790 720 L682 370"
                            stroke="#c7ced0"
                            stroke-width="7"
                            opacity=".65"
                        />

                        <!-- Línea central -->

                        <path
                            d="M640 680 L640 610"
                            stroke="#ffffff"
                            stroke-width="8"
                            opacity=".72"
                        />

                        <path
                            d="M640 570 L640 520"
                            stroke="#ffffff"
                            stroke-width="7"
                            opacity=".64"
                        />

                        <path
                            d="M640 485 L640 450"
                            stroke="#ffffff"
                            stroke-width="6"
                            opacity=".58"
                        />

                        <path
                            d="M640 420 L640 397"
                            stroke="#ffffff"
                            stroke-width="5"
                            opacity=".5"
                        />


                        <!-- =====================================
                             FRANJA SUPERIOR
                             ===================================== -->

                        <rect
                            x="0"
                            y="0"
                            width="1280"
                            height="132"
                            rx="0"
                            class="preview-hud-bar"
                        />


                        <!-- REC -->

                        <g
                            class="preview-rec-block"
                        >
                            <circle
                                cx="52"
                                cy="66"
                                r="11"
                                fill="#35e65b"
                            />

                            <text
                                x="86"
                                y="75"
                                class="preview-main-text preview-rec"
                            >
                                REC
                            </text>

                            <text
                                x="165"
                                y="75"
                                class="preview-secondary-text"
                            >
                                LISTO
                            </text>
                        </g>


                        <!-- PARKING -->

                        <g
                            class="preview-scalable-icon"
                            transform="translate(355 66)"
                        >
                            <circle
                                cx="0"
                                cy="0"
                                r="34"
                                fill="none"
                                class="preview-line"
                                stroke-width="5"
                            />

                            <text
                                x="0"
                                y="13"
                                text-anchor="middle"
                                class="preview-main-text preview-parking-p"
                            >
                                P
                            </text>
                        </g>


                        <!-- SATÉLITE -->

                        <g
                            class="preview-scalable-icon"
                            transform="translate(500 66)"
                        >
                            <rect
                                x="-16"
                                y="-15"
                                width="32"
                                height="30"
                                rx="5"
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <path
                                d="
                                    M-17 -11
                                    L-34 -27
                                    L-52 -9
                                    L-36 7
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <path
                                d="
                                    M17 11
                                    L34 27
                                    L52 9
                                    L36 -7
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <path
                                d="
                                    M15 -15
                                    Q37 -15 39 -38
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <path
                                d="
                                    M21 -21
                                    Q48 -20 49 -49
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="3"
                            />
                        </g>

                        <text
                            x="565"
                            y="76"
                            class="preview-main-text preview-satellite-number"
                        >
                            12
                        </text>


                        <!-- CALIDAD GNSS -->

                        <g
                            class="preview-scalable-icon"
                            transform="translate(660 92)"
                        >
                            <rect
                                x="-34"
                                y="-18"
                                width="11"
                                height="18"
                                rx="3"
                                class="preview-fill"
                            />

                            <rect
                                x="-14"
                                y="-31"
                                width="11"
                                height="31"
                                rx="3"
                                class="preview-fill"
                            />

                            <rect
                                x="6"
                                y="-47"
                                width="11"
                                height="47"
                                rx="3"
                                class="preview-fill"
                            />

                            <rect
                                x="26"
                                y="-66"
                                width="11"
                                height="66"
                                rx="3"
                                class="preview-fill"
                            />
                        </g>


                        <!-- CÁMARA -->

                        <g
                            class="preview-scalable-icon"
                            transform="translate(810 66)"
                        >
                            <rect
                                x="-39"
                                y="-27"
                                width="78"
                                height="54"
                                rx="9"
                                fill="none"
                                class="preview-line"
                                stroke-width="5"
                            />

                            <circle
                                cx="0"
                                cy="0"
                                r="17"
                                fill="none"
                                class="preview-line"
                                stroke-width="5"
                            />

                            <path
                                d="
                                    M-23 -27
                                    L-14 -40
                                    L14 -40
                                    L23 -27
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="5"
                            />
                        </g>


                        <!-- GALERÍA -->

                        <g
                            class="preview-scalable-icon"
                            transform="translate(940 66)"
                        >
                            <rect
                                x="-34"
                                y="-25"
                                width="66"
                                height="50"
                                rx="7"
                                fill="none"
                                class="preview-line"
                                stroke-width="5"
                            />

                            <rect
                                x="-23"
                                y="-35"
                                width="66"
                                height="50"
                                rx="7"
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                                opacity=".55"
                            />

                            <path
                                d="
                                    M-25 15
                                    L-9 -3
                                    L4 9
                                    L14 -2
                                    L28 15
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />
                        </g>


                        <!-- LÍMITE -->

                        <g
                            class="preview-scalable-icon"
                            transform="translate(1100 66)"
                        >
                            <circle
                                cx="0"
                                cy="0"
                                r="41"
                                fill="#ffffff"
                                stroke="#e52626"
                                stroke-width="8"
                            />

                            <text
                                x="0"
                                y="12"
                                text-anchor="middle"
                                fill="#111111"
                                class="preview-limit-number"
                            >
                                50
                            </text>
                        </g>


                        <!-- =====================================
                             FRANJA INFERIOR
                             ===================================== -->

                        <rect
                            x="0"
                            y="612"
                            width="1280"
                            height="108"
                            class="preview-hud-bar"
                        />


                        <!-- ROAD -->

                        <g
                            class="preview-bottom-icon"
                            transform="translate(38 666)"
                        >
                            <path
                                d="
                                    M-14 23
                                    L-5 -23
                                    M14 23
                                    L5 -23
                                    M0 17
                                    L0 7
                                    M0 0
                                    L0 -10
                                    M0 -16
                                    L0 -23
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="5"
                                stroke-linecap="round"
                            />
                        </g>

                        <text
                            x="76"
                            y="675"
                            class="preview-info-text"
                        >
                            Avinguda de Joan XXIII
                        </text>


                        <!-- COORDENADAS -->

                        <g
                            class="preview-bottom-icon"
                            transform="translate(488 665)"
                        >
                            <path
                                d="
                                    M0 24
                                    C-22 2 -28 -8 -28 -21
                                    A28 28 0 1 1 28 -21
                                    C28 -8 22 2 0 24
                                    Z
                                "
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <circle
                                cx="0"
                                cy="-20"
                                r="8"
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />
                        </g>

                        <text
                            x="526"
                            y="675"
                            class="preview-info-text"
                        >
                            39.4699 -0.3763
                        </text>


                        <!-- CALENDARIO -->

                        <g
                            class="preview-bottom-icon"
                            transform="translate(790 665)"
                        >
                            <rect
                                x="-25"
                                y="-23"
                                width="50"
                                height="48"
                                rx="6"
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <path
                                d="M-25 -9 L25 -9"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <path
                                d="
                                    M-13 -30 L-13 -17
                                    M13 -30 L13 -17
                                "
                                class="preview-line"
                                stroke-width="4"
                                stroke-linecap="round"
                            />
                        </g>

                        <text
                            x="828"
                            y="675"
                            class="preview-info-text"
                        >
                            07/08/2026
                        </text>


                        <!-- RELOJ -->

                        <g
                            class="preview-bottom-icon"
                            transform="translate(1034 665)"
                        >
                            <circle
                                cx="0"
                                cy="0"
                                r="25"
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <path
                                d="
                                    M0 0
                                    L0 -14
                                    M0 0
                                    L12 7
                                "
                                class="preview-line"
                                stroke-width="4"
                                stroke-linecap="round"
                            />
                        </g>

                        <text
                            x="1071"
                            y="675"
                            class="preview-info-text"
                        >
                            18:42
                        </text>


                        <!-- AJUSTES -->

                        <g
                            class="preview-bottom-icon"
                            transform="translate(1218 665)"
                        >
                            <circle
                                cx="0"
                                cy="0"
                                r="11"
                                fill="none"
                                class="preview-line"
                                stroke-width="4"
                            />

                            <circle
                                cx="0"
                                cy="0"
                                r="24"
                                fill="none"
                                class="preview-line"
                                stroke-width="5"
                                stroke-dasharray="8 6"
                            />
                        </g>

                    </svg>
                </div>
            </article>
        </div>
    `);
}
