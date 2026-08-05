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


export function showMessage(
    message,
    kind = ""
) {
    const element = document.getElementById(
        "message"
    );

    element.textContent = message;

    element.className = (
        `message ${kind}`
    );

    window.setTimeout(
        () => {
            element.classList.add(
                "hidden"
            );
        },
        7000
    );
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


export function checked(
    value
) {
    return value ? "checked" : "";
}


export function selected(
    current,
    expected
) {
    return (
        current === expected
        ? "selected"
        : ""
    );
}
