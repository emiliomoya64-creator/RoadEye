#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONTROL_DIR = PROJECT_DIR / "static" / "control-center"
MODULES_DIR = CONTROL_DIR / "modules"
APP_JS = PROJECT_DIR / "static" / "js" / "app.js"
API_FILE = PROJECT_DIR / "web" / "api.py"
CONFIG_FILE = PROJECT_DIR / "config" / "config.json"


FILES = {
    "index.html": r'''
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>RoadEye Control Center</title>

    <link
        rel="stylesheet"
        href="/static/control-center/control-center.css"
    >
</head>

<body>
    <div class="control-shell">
        <aside class="control-sidebar">
            <div class="control-brand">
                <span class="control-logo">R</span>

                <span>
                    <strong>RoadEye</strong>
                    <small>Control Center</small>
                </span>
            </div>

            <nav class="control-navigation">
                <button
                    class="nav-button active"
                    data-section="overview"
                    type="button"
                >
                    <span>⌂</span>
                    Resumen
                </button>

                <button
                    class="nav-button"
                    data-section="storage"
                    type="button"
                >
                    <span>▰</span>
                    Almacenamiento
                </button>

                <button
                    class="nav-button"
                    data-section="recording"
                    type="button"
                >
                    <span>●</span>
                    Grabación
                </button>

                <button
                    class="nav-button"
                    data-section="parking"
                    type="button"
                >
                    <span>P</span>
                    Modo Parking
                </button>
            </nav>

            <div class="connection-card">
                <span
                    id="connectionDot"
                    class="connection-dot"
                ></span>

                <span>
                    <strong id="connectionText">
                        Conectando…
                    </strong>

                    <small>RoadEye API</small>
                </span>
            </div>
        </aside>

        <main class="control-main">
            <header class="control-header">
                <div>
                    <span class="eyebrow">
                        Configuración del dispositivo
                    </span>

                    <h1 id="sectionTitle">
                        Resumen
                    </h1>
                </div>

                <span
                    id="loadStatus"
                    class="load-status"
                >
                    Cargando…
                </span>
            </header>

            <div
                id="message"
                class="message hidden"
            ></div>

            <section
                id="controlContent"
                class="control-content"
            >
                <div class="loading-card">
                    Cargando RoadEye Control Center…
                </div>
            </section>
        </main>
    </div>

    <script
        type="module"
        src="/static/control-center/control-center.js"
    ></script>
</body>
</html>
''',

    "control-center.css": r'''
:root {
    color-scheme: dark;

    --background: #070a0c;
    --sidebar: #0b1013;
    --panel: #11181c;
    --panel-light: #172126;
    --border: rgba(255, 255, 255, 0.08);
    --text: #edf3f5;
    --muted: #81929a;
    --accent: #35c878;
    --accent-soft: rgba(53, 200, 120, 0.12);
    --danger: #e05c5c;
}

* {
    box-sizing: border-box;
}

html,
body {
    min-height: 100%;
}

body {
    margin: 0;

    color: var(--text);
    font-family:
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background:
        radial-gradient(
            circle at 85% 5%,
            rgba(45, 106, 137, 0.14),
            transparent 30%
        ),
        var(--background);
}

button,
input,
select {
    font: inherit;
}

.control-shell {
    display: grid;
    grid-template-columns: 238px minmax(0, 1fr);

    min-height: 100vh;
}

.control-sidebar {
    position: sticky;
    top: 0;

    display: flex;
    flex-direction: column;

    height: 100vh;
    padding: 20px 15px;

    border-right: 1px solid var(--border);

    background:
        linear-gradient(
            180deg,
            rgba(15, 22, 26, 0.98),
            rgba(7, 11, 13, 0.99)
        );
}

.control-brand {
    display: flex;
    align-items: center;
    gap: 12px;

    padding: 4px 8px 22px;
}

.control-logo {
    display: grid;
    place-items: center;

    width: 42px;
    height: 42px;

    color: #07110c;
    font-size: 1.2rem;
    font-weight: 900;

    border-radius: 13px;
    background: var(--accent);

    box-shadow:
        0 0 0 6px rgba(53, 200, 120, 0.09);
}

.control-brand strong,
.control-brand small,
.connection-card strong,
.connection-card small {
    display: block;
}

.control-brand small,
.connection-card small {
    margin-top: 3px;
    color: var(--muted);
    font-size: 0.66rem;
}

.control-navigation {
    display: grid;
    gap: 6px;
}

.nav-button {
    display: grid;
    grid-template-columns: 28px minmax(0, 1fr);
    align-items: center;
    gap: 9px;

    min-height: 47px;
    padding: 0 12px;

    color: #a6b4ba;
    text-align: left;

    border: 1px solid transparent;
    border-radius: 11px;

    background: transparent;
    cursor: pointer;
}

.nav-button > span {
    color: #6f858e;
    font-weight: 850;
    text-align: center;
}

.nav-button:hover {
    color: white;
    background: rgba(255, 255, 255, 0.035);
}

.nav-button.active {
    color: #f0f8f4;

    border-color: rgba(53, 200, 120, 0.17);
    background: var(--accent-soft);
}

.nav-button.active > span {
    color: var(--accent);
}

.connection-card {
    display: flex;
    align-items: center;
    gap: 10px;

    margin-top: auto;
    padding: 13px;

    border: 1px solid var(--border);
    border-radius: 12px;

    background: rgba(255, 255, 255, 0.025);
}

.connection-dot {
    width: 9px;
    height: 9px;

    flex: 0 0 auto;

    border-radius: 50%;
    background: #65747a;
}

.connection-dot.online {
    background: var(--accent);

    box-shadow:
        0 0 0 5px rgba(53, 200, 120, 0.11);
}

.control-main {
    min-width: 0;
    padding: 24px;
}

.control-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;

    max-width: 1180px;
    margin: 0 auto 21px;
}

.control-header h1 {
    margin: 6px 0 0;
    font-size: clamp(1.45rem, 3vw, 2rem);
}

.eyebrow {
    color: var(--accent);
    font-size: 0.66rem;
    font-weight: 850;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.load-status {
    color: var(--muted);
    font-size: 0.7rem;
}

.control-content {
    max-width: 1180px;
    margin: 0 auto;
}

.hero-card,
.metric-card,
.settings-card,
.information-card,
.loading-card {
    border: 1px solid var(--border);
    border-radius: 17px;

    background:
        linear-gradient(
            145deg,
            rgba(22, 31, 36, 0.97),
            rgba(12, 18, 21, 0.98)
        );

    box-shadow:
        0 16px 42px rgba(0, 0, 0, 0.24),
        inset 0 1px 0 rgba(255, 255, 255, 0.025);
}

.hero-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 30px;

    min-height: 178px;
    padding: 28px;
}

.hero-card h2 {
    margin: 6px 0 0;
}

.hero-card p,
.information-card p,
.settings-card p {
    margin: 10px 0 0;

    color: var(--muted);
    line-height: 1.6;
}

.hero-check {
    display: grid;
    place-items: center;

    width: 76px;
    height: 76px;

    flex: 0 0 auto;

    color: var(--accent);
    font-size: 2rem;

    border: 1px solid rgba(53, 200, 120, 0.2);
    border-radius: 50%;

    background: var(--accent-soft);
}

.metric-grid,
.settings-grid {
    display: grid;
    grid-template-columns:
        repeat(
            2,
            minmax(0, 1fr)
        );

    gap: 13px;
    margin-top: 13px;
}

.metric-grid {
    grid-template-columns:
        repeat(
            4,
            minmax(0, 1fr)
        );
}

.metric-card,
.settings-card,
.information-card {
    padding: 20px;
}

.metric-card span,
.metric-card strong,
.metric-card small {
    display: block;
}

.metric-card span {
    color: var(--muted);
    font-size: 0.68rem;
    text-transform: uppercase;
}

.metric-card strong {
    margin-top: 12px;
    font-size: 1.35rem;
}

.metric-card small {
    margin-top: 7px;
    color: #687c84;
}

.settings-card h2,
.settings-card h3,
.information-card h3 {
    margin: 0;
}

.data-list {
    display: grid;
    gap: 10px;
    margin-top: 17px;
}

.data-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;

    min-height: 52px;
    padding: 10px 0;

    border-top: 1px solid var(--border);
}

.data-row:first-child {
    border-top: 0;
}

.data-row span {
    color: var(--muted);
}

.data-row strong {
    text-align: right;
}

.message {
    max-width: 1180px;
    margin: 0 auto 15px;
    padding: 13px 15px;

    color: #ffaaaa;

    border: 1px solid rgba(224, 92, 92, 0.25);
    border-radius: 11px;

    background: rgba(224, 92, 92, 0.10);
}

.loading-card {
    padding: 30px;
    color: var(--muted);
    text-align: center;
}

.hidden {
    display: none !important;
}

@media (max-width: 900px) {
    .control-shell {
        grid-template-columns: 1fr;
    }

    .control-sidebar {
        position: relative;
        height: auto;
    }

    .control-navigation {
        grid-template-columns:
            repeat(
                2,
                minmax(0, 1fr)
            );
    }

    .connection-card {
        margin-top: 14px;
    }

    .metric-grid {
        grid-template-columns:
            repeat(
                2,
                minmax(0, 1fr)
            );
    }
}

@media (max-width: 650px) {
    .control-main {
        padding: 15px;
    }

    .settings-grid,
    .metric-grid {
        grid-template-columns: 1fr;
    }

    .hero-check {
        display: none;
    }
}
''',

    "control-center.js": r'''
"use strict";

import {
    fetchSettings,
    fetchStorageStatus
} from "./modules/api.js";

import {
    setConnection,
    showError
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
    activeSection: "overview"
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

        setConnection(true);
        renderActiveSection();

        document.getElementById(
            "loadStatus"
        ).textContent = "Configuración cargada";

    } catch (error) {
        setConnection(false);
        showError(error.message);
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

        return;
    }

    if (state.activeSection === "recording") {
        renderRecording(
            state.settings.recording || {}
        );

        return;
    }

    if (state.activeSection === "parking") {
        renderParking(
            state.settings.parking || {}
        );

        return;
    }

    renderOverview(
        state.settings,
        state.storage
    );
}
''',

    "modules/api.js": r'''
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

    const data = await response.json();

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
''',

    "modules/ui.js": r'''
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


export function showError(
    message
) {
    const element = document.getElementById(
        "message"
    );

    element.textContent = message;
    element.classList.remove(
        "hidden"
    );

    document.getElementById(
        "loadStatus"
    ).textContent = "Error";
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
''',

    "modules/overview.js": r'''
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
''',

    "modules/storage.js": r'''
"use strict";

import {
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

                        <strong>
                            ${storage.folder || "--"}
                        </strong>
                    </div>
                </div>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Configuración
                </span>

                <h2>Límites automáticos</h2>

                <div class="data-list">
                    <div class="data-row">
                        <span>Gestión automática</span>

                        <strong>
                            ${
                                settings.enabled
                                ? "Activada"
                                : "Desactivada"
                            }
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Uso máximo</span>

                        <strong>
                            ${
                                settings
                                .max_usage_percent ?? "--"
                            } %
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Reserva mínima</span>

                        <strong>
                            ${
                                settings
                                .minimum_free_gb ?? "--"
                            } GB
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Intervalo</span>

                        <strong>
                            ${
                                settings
                                .check_interval_seconds ?? "--"
                            } s
                        </strong>
                    </div>
                </div>
            </article>
        </div>
    `);
}
''',

    "modules/recording.js": r'''
"use strict";

import {
    setContent
} from "./ui.js";


export function renderRecording(
    recording
) {
    setContent(`
        <article class="settings-card">
            <span class="eyebrow">
                Cámara principal
            </span>

            <h2>Grabación</h2>

            <div class="data-list">
                <div class="data-row">
                    <span>Grabar al iniciar</span>

                    <strong>
                        ${
                            recording.enabled
                            ? "Sí"
                            : "No"
                        }
                    </strong>
                </div>

                <div class="data-row">
                    <span>Duración por segmento</span>

                    <strong>
                        ${
                            recording
                            .segment_seconds ?? "--"
                        } segundos
                    </strong>
                </div>

                <div class="data-row">
                    <span>Imágenes por segundo</span>

                    <strong>
                        ${
                            recording.fps ?? "--"
                        } FPS
                    </strong>
                </div>
            </div>
        </article>
    `);
}
''',

    "modules/parking.js": r'''
"use strict";

import {
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

                <h2>Modo Parking</h2>

                <div class="data-list">
                    <div class="data-row">
                        <span>Estado</span>

                        <strong>
                            ${
                                parking.enabled
                                ? "Activado"
                                : "Desactivado"
                            }
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Detección</span>

                        <strong>
                            ${
                                parking.trigger
                                || "motion_or_impact"
                            }
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Sensibilidad</span>

                        <strong>
                            ${
                                parking
                                .motion_sensitivity ?? "--"
                            }
                        </strong>
                    </div>
                </div>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Tiempos configurables
                </span>

                <h2>Grabación del evento</h2>

                <div class="data-list">
                    <div class="data-row">
                        <span>Segundos anteriores</span>

                        <strong>
                            ${
                                parking
                                .pre_event_seconds ?? "--"
                            } s
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Duración inicial</span>

                        <strong>
                            ${
                                parking
                                .record_seconds ?? "--"
                            } s
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Extensión</span>

                        <strong>
                            ${
                                parking
                                .extend_seconds ?? "--"
                            } s
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Duración máxima</span>

                        <strong>
                            ${
                                parking
                                .max_event_seconds ?? "--"
                            } s
                        </strong>
                    </div>

                    <div class="data-row">
                        <span>Espera entre eventos</span>

                        <strong>
                            ${
                                parking
                                .cooldown_seconds ?? "--"
                            } s
                        </strong>
                    </div>
                </div>
            </article>
        </div>
    `);
}
'''
}


def backup(path: Path) -> None:
    if not path.exists():
        return

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    target = path.with_name(
        f"{path.name}.backup_{stamp}"
    )

    shutil.copy2(
        path,
        target,
    )

    print(
        f"  Copia: {target.relative_to(PROJECT_DIR)}"
    )


def write_files() -> None:
    CONTROL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MODULES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for relative_name, content in FILES.items():
        path = CONTROL_DIR / relative_name

        backup(path)

        path.write_text(
            content.strip() + "\n",
            encoding="utf-8",
        )

        print(
            f"  Creado: {path.relative_to(PROJECT_DIR)}"
        )


def verify_backend() -> None:
    if not API_FILE.exists():
        raise RuntimeError(
            "No existe web/api.py"
        )

    api_text = API_FILE.read_text(
        encoding="utf-8"
    )

    for marker in (
        '"/api/settings"',
        '"/api/storage/status"',
    ):
        if marker not in api_text:
            raise RuntimeError(
                f"Falta la API {marker}"
            )

    data = json.loads(
        CONFIG_FILE.read_text(
            encoding="utf-8"
        )
    )

    for section in (
        "recording",
        "storage",
        "parking",
    ):
        if not isinstance(
            data.get(section),
            dict,
        ):
            raise RuntimeError(
                f"Falta config.{section}"
            )

    print("  Backend: correcto")


def patch_app_js() -> None:
    text = APP_JS.read_text(
        encoding="utf-8"
    )

    original = text

    text = text.replace(
        'src="/settings"',
        (
            'src="/static/control-center/'
            'index.html"'
        ),
        1,
    )

    text = text.replace(
        'title: "Configuración de RoadEye",',
        'title: "RoadEye Control Center",',
        1,
    )

    text = text.replace(
        'title="Configuración del HUD"',
        'title="RoadEye Control Center"',
        1,
    )

    if (
        "/static/control-center/index.html"
        not in text
    ):
        raise RuntimeError(
            "No se pudo conectar el iframe."
        )

    if text != original:
        backup(APP_JS)

        APP_JS.write_text(
            text,
            encoding="utf-8",
        )

        print("  app.js actualizado")
    else:
        print("  app.js ya estaba actualizado")


def verify_installation() -> None:
    required = [
        CONTROL_DIR / "index.html",
        CONTROL_DIR / "control-center.css",
        CONTROL_DIR / "control-center.js",
        MODULES_DIR / "api.js",
        MODULES_DIR / "ui.js",
        MODULES_DIR / "overview.js",
        MODULES_DIR / "storage.js",
        MODULES_DIR / "recording.js",
        MODULES_DIR / "parking.js",
    ]

    missing = [
        str(path.relative_to(PROJECT_DIR))
        for path in required
        if not path.is_file()
        or path.stat().st_size == 0
    ]

    if missing:
        raise RuntimeError(
            "Faltan archivos: "
            + ", ".join(missing)
        )

    print("  Verificación visual: correcta")


def main() -> int:
    print()
    print("=" * 60)
    print("   Instalación RoadEye Control Center modular")
    print("=" * 60)
    print()

    verify_backend()
    write_files()
    patch_app_js()
    verify_installation()

    Path(__file__).chmod(
        Path(__file__).stat().st_mode
        | 0o111
    )

    print()
    print(
        "Control Center modular instalado correctamente."
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
