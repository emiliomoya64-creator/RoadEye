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

    let data = {};

    try {
        data = await response.json();

    } catch {
        throw new Error(
            `Respuesta no válida de ${url}`
        );
    }

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


export function fetchParkingStatus() {
    return requestJson(
        "/api/parking/status"
    );
}


export function fetchParkingHistory(
    limit = 20
) {
    return requestJson(
        `/api/parking/history?limit=${limit}`
    );
}


export function simulateParkingEvent() {
    return requestJson(
        "/api/parking/simulate",
        {
            method: "POST"
        }
    );
}


export function saveSettings(
    settings
) {
    return requestJson(
        "/api/settings",
        {
            method: "PUT",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                settings
            )
        }
    );
}


export function runStorageCleanup(
    options
) {
    return requestJson(
        "/api/storage/cleanup",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                options || {}
            )
        }
    );
}



export function fetchHudSettings() {
    return requestJson(
        "/api/hud/settings"
    );
}


export function saveHudSettings(
    settings
) {
    return requestJson(
        "/api/hud/settings",
        {
            method: "PUT",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                settings
            )
        }
    );
}


export function fetchSystemStatus() {
    return requestJson(
        "/api/system/status"
    );
}
