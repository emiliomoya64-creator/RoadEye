"use strict";

import {
    fetchSettings,
    fetchStorageStatus,
    fetchParkingStatus,
    fetchParkingHistory,
    saveSettings,
    runStorageCleanup,
    simulateParkingEvent,
    fetchHudSettings,
    saveHudSettings
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
    renderCamera
} from "./modules/camera.js";

import {
    renderParking,
    updateParkingRuntime
} from "./modules/parking.js";


import {
    renderHud
} from "./modules/hud.js";

const state = {
    settings: {},
    storage: {},
    parkingRuntime: {},
    parkingHistory: [],
    hud: {},
    activeSection: "overview",
    dirty: false,
    parkingTimer: null
};


const titles = {
    overview: "Resumen",
    storage: "Almacenamiento",
    recording: "Grabación",
    camera: "Cámara",
    parking: "Modo Parking",
    hud: "HUD"
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
            historyResponse,
            hudResponse
        ] = await Promise.all(
            [
                fetchSettings(),
                fetchStorageStatus(),
                fetchParkingStatus(),
                fetchParkingHistory(20),
                fetchHudSettings()
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

        state.hud = (
            hudResponse.hud || {}
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
        state.activeSection === "camera"
    ) {
        renderCamera(
            state.settings.camera || {}
        );

    } else if (
        state.activeSection === "parking"
    ) {
        renderParking(
            state.settings.parking || {},
            state.parkingRuntime,
            state.parkingHistory
        );

    } else if (
        state.activeSection === "hud"
    ) {
        renderHud(
            state.hud
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
    bindHudActions();
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
        },

        camera: {
            ...(state.settings.camera || {})
        }
    };

    document.querySelectorAll(
        "[data-setting]"
    ).forEach((element) => {
        const parts =
            element.dataset.setting.split(
                "."
            );

        if (parts.length < 2) {
            return;
        }

        const section = parts.shift();

        if (!result[section]) {
            return;
        }

        let target = result[section];

        while (parts.length > 1) {
            const key = parts.shift();

            if (
                !target[key]
                || typeof target[key] !== "object"
            ) {
                target[key] = {};
            }

            target = target[key];
        }

        target[parts[0]] = (
            readFieldValue(
                element
            )
        );
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


function bindHudActions() {
    const slider = document.getElementById(
        "hudIconScale"
    );

    const value = document.getElementById(
        "hudIconScaleValue"
    );

    const textSlider = document.getElementById(
        "hudTextScale"
    );

    const textValue = document.getElementById(
        "hudTextScaleValue"
    );

    if (!slider) {
        return;
    }

    slider.addEventListener(
        "input",
        () => {
            if (value) {
                value.textContent =
                    `${slider.value}%`;
            }
        }
    );

    slider.addEventListener(
        "change",
        saveHudSection
    );


    if (textSlider) {
        textSlider.addEventListener(
            "input",
            () => {
                if (textValue) {
                    textValue.textContent =
                        `${textSlider.value}%`;
                }
            }
        );

        textSlider.addEventListener(
            "change",
            saveHudSection
        );
    }

    const font = document.getElementById(
        "hudFont"
    );

    const color = document.getElementById(
        "hudColor"
    );

    const mode = document.getElementById(
        "hudMode"
    );

    const barColor = document.getElementById(
        "hudBarColor"
    );

    const topBarScale = document.getElementById(
        "hudTopBarScale"
    );

    const infoBarScale = document.getElementById(
        "hudInfoBarScale"
    );

    const topOpacity = document.getElementById(
        "hudTopOpacity"
    );

    const infoOpacity = document.getElementById(
        "hudInfoOpacity"
    );


    const profile = document.getElementById(
        "hudProfile"
    );

    const position = document.getElementById(
        "hudInfoPosition"
    );

    if (font) {
        font.addEventListener(
            "change",
            saveHudSection
        );
    }

    if (color) {
        color.addEventListener(
            "change",
            saveHudSection
        );
    }

    if (mode) {
        mode.addEventListener(
            "change",
            saveHudSection
        );
    }

    if (profile) {
        profile.addEventListener(
            "change",
            saveHudSection
        );
    }

    if (position) {
        position.addEventListener(
            "change",
            saveHudSection
        );
    }
}


async function saveHudSection() {
    const slider = document.getElementById(
        "hudIconScale"
    );

    const textSlider = document.getElementById(
        "hudTextScale"
    );

    const font = document.getElementById(
        "hudFont"
    );

    const color = document.getElementById(
        "hudColor"
    );

    const mode = document.getElementById(
        "hudMode"
    );

    const barColor = document.getElementById(
        "hudBarColor"
    );

    const topBarScale = document.getElementById(
        "hudTopBarScale"
    );

    const infoBarScale = document.getElementById(
        "hudInfoBarScale"
    );

    const topOpacity = document.getElementById(
        "hudTopOpacity"
    );

    const infoOpacity = document.getElementById(
        "hudInfoOpacity"
    );


    const profile = document.getElementById(
        "hudProfile"
    );

    const position = document.getElementById(
        "hudInfoPosition"
    );

    try {
        const payload = {
            ...state.hud,

            icon_scale:
                Number(slider.value) / 100,

            text_scale:
                Number(textSlider.value) / 100,

            font:
                font.value,

            color:
                color.value,

            mode:
                mode.value,

            bar_color:
                barColor.value,

            top_bar_scale:
                Number(topBarScale.value) / 100,

            info_bar_scale:
                Number(infoBarScale.value) / 100,

            top_opacity:
                Number(topOpacity.value) / 100,

            info_opacity:
                Number(infoOpacity.value) / 100,

            show:
                Object.fromEntries(
                    Array.from(
                        document.querySelectorAll(
                            "[data-hud-visible]"
                        )
                    ).map(
                        element => [
                            element.dataset.hudVisible,
                            element.checked
                        ]
                    )
                ),


            profile:
                profile.value,

            info_position:
                position.value
        };

        const response =
            await saveHudSettings(
                payload
            );

        state.hud = (
            response.hud || payload
        );

        showMessage(
            "Ajustes del HUD guardados.",
            "success"
        );

    } catch (error) {
        showMessage(
            error.message,
            "error"
        );
    }

    updateHudPreview();
}


function updateHudPreview() {
    const preview = document.getElementById(
        "hudPreview"
    );

    if (!preview) {
        return;
    }

    const iconSlider = document.getElementById(
        "hudIconScale"
    );

    const textSlider = document.getElementById(
        "hudTextScale"
    );

    const font = document.getElementById(
        "hudFont"
    );

    const color = document.getElementById(
        "hudColor"
    );

    const mode = document.getElementById(
        "hudMode"
    );

    const barColor = document.getElementById(
        "hudBarColor"
    );

    const topBarScale = document.getElementById(
        "hudTopBarScale"
    );

    const infoBarScale = document.getElementById(
        "hudInfoBarScale"
    );

    const topOpacity = document.getElementById(
        "hudTopOpacity"
    );

    const infoOpacity = document.getElementById(
        "hudInfoOpacity"
    );


    const iconScale = (
        Number(iconSlider?.value || 100) / 100
    );

    const textScale = (
        Number(textSlider?.value || 100) / 100
    );

    const colors = {
        white: "#ffffff",
        green: "#78ff78",
        amber: "#ffbe00",
        ice_blue: "#a0dcff",
        red: "#ff5a5a"
    };

    const fonts = {
        simplex:
            "Arial, sans-serif",

        duplex:
            "'Trebuchet MS', Arial, sans-serif",

        triplex:
            "Georgia, serif",

        complex:
            "'Courier New', monospace"
    };

    preview.style.setProperty(
        "--preview-icon-scale",
        iconScale
    );

    preview.style.setProperty(
        "--preview-text-scale",
        textScale
    );

    preview.style.setProperty(
        "--preview-color",
        colors[color?.value] || "#ffffff"
    );

    preview.style.setProperty(
        "--preview-font",
        fonts[font?.value]
        || "'Trebuchet MS', Arial, sans-serif"
    );

    let displayMode = (
        mode?.value || "auto"
    );

    if (displayMode === "auto") {
        const hour = new Date().getHours();

        displayMode = (
            hour >= 7 && hour < 20
            ? "day"
            : "night"
        );
    }

    preview.classList.toggle(
        "preview-night",
        displayMode === "night"
    );

    preview.classList.toggle(
        "preview-day",
        displayMode === "day"
    );
}


document.addEventListener(
    "input",
    (event) => {
        if (
            event.target.closest(
                "#hudIconScale, #hudTextScale"
            )
        ) {
            updateHudPreview();
        }
    }
);

document.addEventListener(
    "change",
    (event) => {
        if (
            event.target.closest(
                "#hudFont, #hudColor, #hudMode, "
                + "#hudProfile, #hudInfoPosition"
            )
        ) {
            updateHudPreview();
        }
    }
);


document.addEventListener(
    "input",
    (event) => {
        if (
            event.target.id === "hudTopOpacity"
            || event.target.id === "hudInfoOpacity"
        ) {
            const id = (
                event.target.id === "hudTopOpacity"
                ? "hudTopOpacityValue"
                : "hudInfoOpacityValue"
            );

            const value = document.getElementById(id);

            if (value) {
                value.textContent =
                    `${event.target.value}%`;
            }

            updateHudPreview();
        }
    }
);

document.addEventListener(
    "change",
    (event) => {
        if (
            event.target.id === "hudBarColor"
            || event.target.matches(
                "[data-hud-visible]"
            )
        ) {
            saveHudSection();
            updateHudPreview();
        }
    }
);


document.addEventListener(
    "input",
    (event) => {
        const map = {
            hudTopBarScale:
                "hudTopBarScaleValue",

            hudInfoBarScale:
                "hudInfoBarScaleValue"
        };

        const outputId = map[event.target.id];

        if (!outputId) {
            return;
        }

        const output =
            document.getElementById(
                outputId
            );

        if (output) {
            output.textContent =
                `${event.target.value}%`;
        }

        updateHudPreview();
    }
);

document.addEventListener(
    "change",
    (event) => {
        if (
            event.target.id === "hudTopBarScale"
            || event.target.id === "hudInfoBarScale"
        ) {
            saveHudSection();
        }
    }
);
