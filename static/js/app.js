"use strict";


class PopupManager {
    constructor() {
        this.backdrop = document.getElementById(
            "popupBackdrop"
        );

        this.window = document.getElementById(
            "popupWindow"
        );

        this.title = document.getElementById(
            "popupTitle"
        );

        this.eyebrow = document.getElementById(
            "popupEyebrow"
        );

        this.content = document.getElementById(
            "popupContent"
        );

        this.closeButton = document.getElementById(
            "popupClose"
        );

        this.activePopup = null;

        this._bindEvents();
    }

    _bindEvents() {
        this.closeButton.addEventListener(
            "click",
            () => this.close()
        );

        this.backdrop.addEventListener(
            "click",
            (event) => {
                if (event.target === this.backdrop) {
                    this.close();
                }
            }
        );

        document.addEventListener(
            "keydown",
            (event) => {
                if (event.key === "Escape") {
                    this.close();
                }
            }
        );

        document.querySelectorAll(
            "[data-popup]"
        ).forEach((button) => {
            button.addEventListener(
                "click",
                () => {
                    this.open(
                        button.dataset.popup
                    );
                }
            );
        });
    }

    open(name) {
        const popup = this._popupDefinition(
            name
        );

        if (!popup) {
            return;
        }

        this.activePopup = name;

        this.eyebrow.textContent = (
            popup.eyebrow
        );

        this.title.textContent = (
            popup.title
        );

        this.content.innerHTML = (
            popup.content
        );

        this.backdrop.classList.add(
            "visible"
        );

        this.backdrop.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "popup-open"
        );

        if (
            typeof popup.onOpen
            === "function"
        ) {
            popup.onOpen();
        }
    }

    close() {
        this.backdrop.classList.remove(
            "visible"
        );

        this.backdrop.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "popup-open"
        );

        this.content.innerHTML = "";
        this.activePopup = null;
    }

    _popupDefinition(name) {
        if (name === "settings") {
            return {
                eyebrow: "Personalización",
                title: "Configuración de RoadEye",
                content: `
                    <iframe
                        class="popup-frame"
                        src="/settings"
                        title="Configuración del HUD"
                    ></iframe>
                `
            };
        }

        if (name === "photo") {
            const event = pendingPhotoEvent;

            if (!event) {
                return null;
            }

            const photo = (
                event.data
                && event.data.photo
                ? event.data.photo
                : {}
            );

            return {
                eyebrow: "Fotografía del viaje",
                title: event.label || "Fotografía",
                content: `
                    <div class="photo-viewer">
                        <div class="photo-viewer-image">
                            <img
                                src="${escapeHtml(
                                    photo.url || ""
                                )}"
                                alt="Fotografía de RoadEye"
                            >
                        </div>

                        <div class="photo-viewer-info">
                            <div class="photo-metadata-grid">
                                <div>
                                    <span>Momento del viaje</span>
                                    <strong>
                                        ${formatTrackTime(
                                            event.trip_time
                                        )}
                                    </strong>
                                </div>

                                <div>
                                    <span>Velocidad</span>
                                    <strong>
                                        ${Number(
                                            event.speed || 0
                                        ).toFixed(1)} km/h
                                    </strong>
                                </div>

                                <div>
                                    <span>GPS</span>
                                    <strong>
                                        ${
                                            Array.isArray(event.gps)
                                            ? escapeHtml(
                                                `${event.gps[0]}, ${event.gps[1]}`
                                            )
                                            : "Sin posición GPS"
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>Resolución</span>
                                    <strong>
                                        ${photo.width || "--"}
                                        ×
                                        ${photo.height || "--"}
                                    </strong>
                                </div>
                            </div>

                            <div class="photo-viewer-actions">
                                <a
                                    class="browser-button"
                                    href="${escapeHtml(
                                        photo.url || "#"
                                    )}?download=1"
                                    download
                                >
                                    Descargar foto
                                </a>

                                <button
                                    id="photoOpenVideo"
                                    class="browser-button"
                                    type="button"
                                >
                                    Ver vídeo en este instante
                                </button>
                            </div>
                        </div>
                    </div>
                `,
                onOpen: () => {
                    const openVideoButton = (
                        document.getElementById(
                            "photoOpenVideo"
                        )
                    );

                    if (openVideoButton) {
                        openVideoButton.onclick = () => {
                            openTripEvent(
                                event.segment,
                                event.segment_time
                            );
                        };
                    }
                }
            };
        }

        if (name === "trips") {
            return {
                eyebrow: "Trayectos",
                title: "Viajes de RoadEye",
                content: `
                    <div class="trips-browser">
                        <div class="video-browser-toolbar">
                            <div>
                                <strong id="tripCount">
                                    Cargando viajes…
                                </strong>

                                <span id="tripFolder"></span>
                            </div>

                            <button
                                id="refreshTrips"
                                class="browser-button"
                                type="button"
                            >
                                Actualizar
                            </button>
                        </div>

                        <div class="trips-layout">
                            <section
                                id="tripList"
                                class="trip-list"
                            >
                                <div class="browser-loading">
                                    Buscando viajes…
                                </div>
                            </section>

                            <section
                                id="tripDetails"
                                class="trip-details"
                            >
                                <div class="player-empty">
                                    <div class="empty-icon">⌁</div>

                                    <strong>
                                        Selecciona un viaje
                                    </strong>

                                    <span>
                                        Aquí aparecerán su ruta,
                                        estadísticas y segmentos.
                                    </span>
                                </div>
                            </section>
                        </div>
                    </div>
                `,
                onOpen: () => {
                    initializeTripsBrowser();
                }
            };
        }

        if (name === "videos") {
            return {
                eyebrow: "Grabaciones",
                title: "Explorador de vídeos",
                content: `
                    <div class="video-browser">
                        <div class="video-browser-toolbar">
                            <div>
                                <strong id="videoCount">
                                    Cargando vídeos…
                                </strong>

                                <span id="videoFolder"></span>
                            </div>

                            <button
                                id="refreshVideos"
                                class="browser-button"
                                type="button"
                            >
                                Actualizar
                            </button>
                        </div>

                        <div class="video-browser-layout">
                            <section
                                id="videoList"
                                class="video-list"
                            >
                                <div class="browser-loading">
                                    Buscando grabaciones…
                                </div>
                            </section>

                            <section class="video-player-panel">
                                <div
                                    id="videoPlayerEmpty"
                                    class="player-empty"
                                >
                                    <div class="empty-icon">▶</div>

                                    <strong>
                                        Selecciona un vídeo
                                    </strong>

                                    <span>
                                        La reproducción aparecerá aquí.
                                    </span>
                                </div>

                                <div
                                    id="videoPlayerContent"
                                    class="player-content hidden"
                                >
                                    <div class="media-tabs">
                                        <button
                                            id="videoTabButton"
                                            class="media-tab active"
                                            type="button"
                                        >
                                            Vídeo
                                        </button>

                                        <button
                                            id="mapTabButton"
                                            class="media-tab"
                                            type="button"
                                        >
                                            Mapa y ruta
                                        </button>
                                    </div>

                                    <div
                                        id="videoTabPanel"
                                        class="media-tab-panel"
                                    >
                                        <video
                                            id="videoPlayer"
                                            controls
                                            preload="metadata"
                                        ></video>
                                    </div>

                                    <div
                                        id="mapTabPanel"
                                        class="media-tab-panel hidden"
                                    >
                                        <div class="route-map-wrap">
                                            <div id="routeMap"></div>

                                            <div
                                                id="routeSyncStatus"
                                                class="route-sync-status hidden"
                                            >
                                                <span class="route-sync-dot"></span>

                                                <span>
                                                    <strong id="routeSyncTime">
                                                        00:00
                                                    </strong>

                                                    <small id="routeSyncSpeed">
                                                        0 km/h
                                                    </small>
                                                </span>
                                            </div>
                                        </div>

                                        <div
                                            id="routeEmpty"
                                            class="route-empty hidden"
                                        >
                                            Esta grabación no contiene
                                            recorrido GPS.
                                        </div>
                                    </div>

                                    <div class="player-metadata">
                                        <strong id="videoPlayerName"></strong>

                                        <span id="videoPlayerDetails"></span>
                                    </div>

                                    <div class="player-actions">
                                        <a
                                            id="videoDownload"
                                            class="browser-button"
                                            href="#"
                                            download
                                        >
                                            Descargar
                                        </a>

                                        <button
                                            id="videoProtection"
                                            class="browser-button"
                                            type="button"
                                        >
                                            Proteger
                                        </button>

                                        <button
                                            id="videoDelete"
                                            class="browser-button danger"
                                            type="button"
                                        >
                                            Borrar
                                        </button>
                                    </div>
                                </div>
                            </section>
                        </div>
                    </div>
                `,
                onOpen: () => {
                    initializeVideoBrowser();
                }
            };
        }

        return null;
    }
}


const popupManager = new PopupManager();


const recordingState = document.getElementById(
    "recordingState"
);

const gpsState = document.getElementById(
    "gpsState"
);

const speedState = document.getElementById(
    "speedState"
);

const systemState = document.getElementById(
    "systemState"
);

const systemDetails = document.getElementById(
    "systemDetails"
);

const diskState = document.getElementById(
    "diskState"
);

const videosState = document.getElementById(
    "videosState"
);

const connectionStatus = document.getElementById(
    "connectionStatus"
);

const startButton = document.getElementById(
    "start"
);

const stopButton = document.getElementById(
    "stop"
);


async function updateStatus() {
    try {
        const response = await fetch(
            "/api/status",
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error(
                "RoadEye no responde"
            );
        }

        const data = await response.json();

        connectionStatus.textContent = (
            "En línea"
        );

        connectionStatus.classList.add(
            "online"
        );

        recordingState.textContent = (
            data.recording
            ? "GRABANDO"
            : "LISTO"
        );

        recordingState.classList.toggle(
            "recording",
            Boolean(data.recording)
        );

        startButton.disabled = Boolean(
            data.recording
        );

        stopButton.disabled = !data.recording;

        gpsState.textContent = (
            data.gps_fix
            ? "GPS conectado"
            : "Sin señal GPS"
        );

        speedState.textContent = (
            `${Math.round(Number(data.speed) || 0)} km/h`
        );

        systemState.textContent = (
            "RoadEye operativo"
        );

        systemDetails.textContent = (
            `CPU ${data.cpu ?? 0}% · `
            + `${data.temp ?? 0} °C`
        );

        diskState.textContent = (
            `${data.disk ?? 0}% usado`
        );

        videosState.textContent = (
            `${data.videos ?? 0} vídeos`
        );
    } catch (error) {
        connectionStatus.textContent = (
            "Sin conexión"
        );

        connectionStatus.classList.remove(
            "online"
        );

        systemState.textContent = (
            "No disponible"
        );
    }
}


async function setRecording(action) {
    startButton.disabled = true;
    stopButton.disabled = true;

    try {
        const response = await fetch(
            `/api/record/${action}`
        );

        if (!response.ok) {
            throw new Error(
                "No se pudo cambiar la grabación"
            );
        }

        await updateStatus();
    } catch (error) {
        console.error(
            error
        );

        await updateStatus();
    }
}


startButton.addEventListener(
    "click",
    () => setRecording("start")
);

stopButton.addEventListener(
    "click",
    () => setRecording("stop")
);


setInterval(
    updateStatus,
    1000
);

updateStatus();


// ============================================================
// Explorador de vídeos
// ============================================================

let selectedVideo = null;


async function initializeVideoBrowser() {
    const refreshButton = document.getElementById(
        "refreshVideos"
    );

    if (refreshButton) {
        refreshButton.addEventListener(
            "click",
            loadVideos
        );
    }

    await loadVideos();
}


async function loadVideos() {
    const list = document.getElementById(
        "videoList"
    );

    const count = document.getElementById(
        "videoCount"
    );

    const folder = document.getElementById(
        "videoFolder"
    );

    if (!list) {
        return;
    }

    list.innerHTML = `
        <div class="browser-loading">
            Buscando grabaciones…
        </div>
    `;

    try {
        const response = await fetch(
            "/api/videos",
            {
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || "No se pudieron cargar los vídeos."
            );
        }

        count.textContent = (
            `${data.count} `
            + (
                data.count === 1
                ? "vídeo"
                : "vídeos"
            )
        );

        folder.textContent = (
            data.folder
        );

        renderVideoList(
            data.videos
        );
    } catch (error) {
        list.innerHTML = `
            <div class="browser-error">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


function renderVideoList(videos) {
    const list = document.getElementById(
        "videoList"
    );

    if (!videos.length) {
        list.innerHTML = `
            <div class="browser-empty">
                <div class="empty-icon">▣</div>

                <strong>
                    No hay grabaciones
                </strong>

                <span>
                    Los nuevos vídeos aparecerán aquí.
                </span>
            </div>
        `;

        clearVideoPlayer();
        return;
    }

    list.innerHTML = "";

    let lastDate = null;

    for (const video of videos) {
        if (video.date !== lastDate) {
            const dateHeading = (
                document.createElement(
                    "div"
                )
            );

            dateHeading.className = (
                "video-date-heading"
            );

            dateHeading.textContent = (
                dateSectionLabel(
                    video.date
                )
            );

            list.appendChild(
                dateHeading
            );

            lastDate = video.date;
        }

        const button = document.createElement(
            "button"
        );

        button.className = "video-list-item";
        button.type = "button";

        button.dataset.videoName = (
            video.name
        );

        const kind = videoKindLabel(
            video.kind
        );

        const thumbnail = (
            video.thumbnail_url
            ? `
                <img
                    class="video-thumbnail"
                    src="${escapeHtml(video.thumbnail_url)}"
                    alt=""
                    loading="lazy"
                >
            `
            : `
                <span class="video-list-icon">
                    ▶
                </span>
            `
        );

        const protectedBadge = (
            video.protected
            ? `
                <span
                    class="video-protected"
                    title="Grabación protegida"
                >
                    ★
                </span>
            `
            : ""
        );

        const speedText = (
            Number(video.speed.max) > 0
            ? ` · Máx. ${video.speed.max} km/h`
            : ""
        );

        button.innerHTML = `
            <span class="video-thumbnail-wrap">
                ${thumbnail}

                <span class="video-duration">
                    ${escapeHtml(video.duration)}
                </span>
            </span>

            <span class="video-list-main">
                <strong>
                    ${escapeHtml(video.time)}
                    ${protectedBadge}
                </strong>

                <span>
                    ${escapeHtml(video.size)}
                    ${escapeHtml(speedText)}
                </span>

                <span class="video-file-name">
                    ${escapeHtml(video.name)}
                </span>
            </span>

            <span class="video-kind ${video.kind}">
                ${kind}
            </span>
        `;

        button.addEventListener(
            "click",
            () => selectVideo(
                video,
                button
            )
        );

        list.appendChild(
            button
        );
    }
}


function dateSectionLabel(dateText) {
    const today = new Date();

    const todayText = [
        String(
            today.getDate()
        ).padStart(2, "0"),

        String(
            today.getMonth() + 1
        ).padStart(2, "0"),

        today.getFullYear()
    ].join("/");

    const yesterday = new Date(
        today
    );

    yesterday.setDate(
        yesterday.getDate() - 1
    );

    const yesterdayText = [
        String(
            yesterday.getDate()
        ).padStart(2, "0"),

        String(
            yesterday.getMonth() + 1
        ).padStart(2, "0"),

        yesterday.getFullYear()
    ].join("/");

    if (dateText === todayText) {
        return "Hoy";
    }

    if (dateText === yesterdayText) {
        return "Ayer";
    }

    return dateText;
}


function selectVideo(
    video,
    button
) {
    selectedVideo = video;

    document.querySelectorAll(
        ".video-list-item"
    ).forEach((item) => {
        item.classList.remove(
            "selected"
        );
    });

    button.classList.add(
        "selected"
    );

    const empty = document.getElementById(
        "videoPlayerEmpty"
    );

    const content = document.getElementById(
        "videoPlayerContent"
    );

    const player = document.getElementById(
        "videoPlayer"
    );

    empty.classList.add(
        "hidden"
    );

    content.classList.remove(
        "hidden"
    );

    initializeMediaTabs();
    showMediaTab("video");

    player.src = video.stream_url;

    initializeVideoMapSynchronization(
        player
    );

    document.getElementById(
        "videoPlayerName"
    ).textContent = video.name;

    const startGps = (
        video.gps.start_text
        || "Sin posición GPS"
    );

    const endGps = (
        video.gps.end_text
        || "Sin posición GPS"
    );

    document.getElementById(
        "videoPlayerDetails"
    ).innerHTML = `
        <div class="metadata-grid">
            <div>
                <span>Fecha</span>
                <strong>
                    ${escapeHtml(video.date)}
                    ·
                    ${escapeHtml(video.time)}
                </strong>
            </div>

            <div>
                <span>Duración</span>
                <strong>
                    ${escapeHtml(video.duration)}
                </strong>
            </div>

            <div>
                <span>Tipo</span>
                <strong>
                    ${escapeHtml(
                        videoKindLabel(video.kind)
                    )}
                </strong>
            </div>

            <div>
                <span>Tamaño</span>
                <strong>
                    ${escapeHtml(video.size)}
                </strong>
            </div>

            <div>
                <span>Velocidad máxima</span>
                <strong>
                    ${escapeHtml(video.speed.max)}
                    km/h
                </strong>
            </div>

            <div>
                <span>Velocidad media</span>
                <strong>
                    ${escapeHtml(video.speed.average)}
                    km/h
                </strong>
            </div>

            <div>
                <span>GPS inicial</span>
                <strong>
                    ${escapeHtml(startGps)}
                </strong>
            </div>

            <div>
                <span>GPS final</span>
                <strong>
                    ${escapeHtml(endGps)}
                </strong>
            </div>

            <div>
                <span>Protección</span>
                <strong>
                    ${video.protected ? "Protegido" : "Normal"}
                </strong>
            </div>

            <div>
                <span>Metadatos</span>
                <strong>
                    ${video.has_metadata ? "Completos" : "Vídeo antiguo"}
                </strong>
            </div>
        </div>
    `;

    const download = document.getElementById(
        "videoDownload"
    );

    download.href = video.download_url;

    download.setAttribute(
        "download",
        video.name
    );

    const protectionButton = document.getElementById(
        "videoProtection"
    );

    protectionButton.textContent = (
        video.protected
        ? "Quitar protección"
        : "Proteger"
    );

    protectionButton.classList.toggle(
        "protected",
        Boolean(video.protected)
    );

    protectionButton.onclick = (
        () => toggleSelectedVideoProtection()
    );

    const deleteButton = document.getElementById(
        "videoDelete"
    );

    deleteButton.onclick = (
        () => deleteSelectedVideo()
    );

    player.load();
}


async function deleteSelectedVideo() {
    if (!selectedVideo) {
        return;
    }

    const confirmed = window.confirm(
        `¿Borrar definitivamente ${selectedVideo.name}?`
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `/api/videos/${
                encodeURIComponent(
                    selectedVideo.name
                )
            }`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || "No se pudo borrar el vídeo."
            );
        }

        clearVideoPlayer();
        await loadVideos();
    } catch (error) {
        window.alert(
            error.message
        );
    }
}


function clearVideoPlayer() {
    selectedVideo = null;

    const player = document.getElementById(
        "videoPlayer"
    );

    if (player) {
        player.pause();
        player.removeAttribute(
            "src"
        );
        player.load();
    }

    const empty = document.getElementById(
        "videoPlayerEmpty"
    );

    const content = document.getElementById(
        "videoPlayerContent"
    );

    if (empty) {
        empty.classList.remove(
            "hidden"
        );
    }

    if (content) {
        content.classList.add(
            "hidden"
        );
    }
}


function videoKindLabel(kind) {
    if (kind === "parking") {
        return "Parking";
    }

    if (kind === "event") {
        return "Evento";
    }

    return "Normal";
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ============================================================
// Mapa y recorrido GPS
// ============================================================

let routeMap = null;
let routeLayer = null;
let routeProgressLayer = null;
let routeStartMarker = null;
let routeEndMarker = null;
let routeVehicleMarker = null;
let routeSyncTrack = [];


function initializeMediaTabs() {
    const videoButton = document.getElementById(
        "videoTabButton"
    );

    const mapButton = document.getElementById(
        "mapTabButton"
    );

    if (!videoButton || !mapButton) {
        return;
    }

    videoButton.onclick = (
        () => showMediaTab("video")
    );

    mapButton.onclick = (
        () => showMediaTab("map")
    );
}


function showMediaTab(name) {
    const videoButton = document.getElementById(
        "videoTabButton"
    );

    const mapButton = document.getElementById(
        "mapTabButton"
    );

    const videoPanel = document.getElementById(
        "videoTabPanel"
    );

    const mapPanel = document.getElementById(
        "mapTabPanel"
    );

    const showMap = (
        name === "map"
    );

    videoButton.classList.toggle(
        "active",
        !showMap
    );

    mapButton.classList.toggle(
        "active",
        showMap
    );

    videoPanel.classList.toggle(
        "hidden",
        showMap
    );

    mapPanel.classList.toggle(
        "hidden",
        !showMap
    );

    if (showMap) {
        window.setTimeout(
            () => {
                renderSelectedVideoRoute();

                if (routeMap) {
                    routeMap.invalidateSize();
                }

                const player = document.getElementById(
                    "videoPlayer"
                );

                updateVideoMapPosition(
                    player
                    ? Number(player.currentTime) || 0
                    : 0
                );
            },
            80
        );
    }
}


function renderSelectedVideoRoute() {
    const mapElement = document.getElementById(
        "routeMap"
    );

    const emptyElement = document.getElementById(
        "routeEmpty"
    );

    const syncStatus = document.getElementById(
        "routeSyncStatus"
    );

    if (!mapElement || !emptyElement) {
        return;
    }

    const track = (
        selectedVideo
        && Array.isArray(selectedVideo.track)
        ? selectedVideo.track
        : []
    ).filter((point) => {
        return (
            Number.isFinite(Number(point.lat))
            && Number.isFinite(Number(point.lon))
            && Number.isFinite(Number(point.time))
        );
    }).sort((first, second) => {
        return (
            Number(first.time)
            - Number(second.time)
        );
    });

    routeSyncTrack = track;

    if (!track.length) {
        mapElement.classList.add(
            "hidden"
        );

        emptyElement.classList.remove(
            "hidden"
        );

        if (syncStatus) {
            syncStatus.classList.add(
                "hidden"
            );
        }

        return;
    }

    if (typeof L === "undefined") {
        mapElement.classList.add(
            "hidden"
        );

        emptyElement.textContent = (
            "No se pudo cargar el sistema de mapas."
        );

        emptyElement.classList.remove(
            "hidden"
        );

        return;
    }

    mapElement.classList.remove(
        "hidden"
    );

    emptyElement.classList.add(
        "hidden"
    );

    if (syncStatus) {
        syncStatus.classList.remove(
            "hidden"
        );
    }

    if (!routeMap) {
        routeMap = L.map(
            mapElement,
            {
                zoomControl: true,
                attributionControl: true
            }
        );

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution:
                    "&copy; OpenStreetMap contributors"
            }
        ).addTo(
            routeMap
        );
    }

    for (
        const layer
        of [
            routeLayer,
            routeProgressLayer,
            routeStartMarker,
            routeEndMarker,
            routeVehicleMarker
        ]
    ) {
        if (layer) {
            routeMap.removeLayer(
                layer
            );
        }
    }

    routeLayer = null;
    routeProgressLayer = null;
    routeStartMarker = null;
    routeEndMarker = null;
    routeVehicleMarker = null;

    const coordinates = track.map(
        (point) => [
            Number(point.lat),
            Number(point.lon)
        ]
    );

    routeLayer = L.polyline(
        coordinates,
        {
            weight: 6,
            opacity: 0.45,
            lineCap: "round",
            lineJoin: "round"
        }
    ).addTo(
        routeMap
    );

    routeProgressLayer = L.polyline(
        [
            coordinates[0]
        ],
        {
            weight: 6,
            opacity: 0.95,
            lineCap: "round",
            lineJoin: "round"
        }
    ).addTo(
        routeMap
    );

    const first = track[0];
    const last = track[
        track.length - 1
    ];

    routeStartMarker = L.marker(
        [
            Number(first.lat),
            Number(first.lon)
        ]
    )
        .addTo(routeMap)
        .bindPopup(
            `Inicio · ${formatTrackTime(first.time)}`
        );

    routeEndMarker = L.marker(
        [
            Number(last.lat),
            Number(last.lon)
        ]
    )
        .addTo(routeMap)
        .bindPopup(
            `Final · ${formatTrackTime(last.time)}`
        );

    const vehicleIcon = L.divIcon(
        {
            className: "roadeye-vehicle-marker-wrap",
            html: `
                <span class="roadeye-vehicle-marker">
                    ●
                </span>
            `,
            iconSize: [
                32,
                32
            ],
            iconAnchor: [
                16,
                16
            ],
            tooltipAnchor: [
                0,
                -18
            ]
        }
    );

    routeVehicleMarker = L.marker(
        coordinates[0],
        {
            icon: vehicleIcon,
            zIndexOffset: 1000
        }
    ).addTo(
        routeMap
    );

    routeVehicleMarker.bindTooltip(
        "Posición actual",
        {
            direction: "top",
            offset: [0, -18]
        }
    );

    if (coordinates.length === 1) {
        routeMap.setView(
            coordinates[0],
            17
        );
    } else {
        routeMap.fitBounds(
            routeLayer.getBounds(),
            {
                padding: [30, 30]
            }
        );
    }

    const player = document.getElementById(
        "videoPlayer"
    );

    updateVideoMapPosition(
        player
        ? Number(player.currentTime) || 0
        : 0
    );
}


function formatTrackTime(seconds) {
    const total = Math.max(
        0,
        Math.round(
            Number(seconds) || 0
        )
    );

    const minutes = Math.floor(
        total / 60
    );

    const remainingSeconds = (
        total % 60
    );

    return (
        String(minutes).padStart(2, "0")
        + ":"
        + String(remainingSeconds).padStart(2, "0")
    );
}


// ============================================================
// Explorador de viajes
// ============================================================

let selectedTrip = null;
let tripMap = null;
let tripRouteLayer = null;


async function initializeTripsBrowser() {
    const refreshButton = document.getElementById(
        "refreshTrips"
    );

    if (refreshButton) {
        refreshButton.onclick = loadTrips;
    }

    await loadTrips();
}


async function loadTrips() {
    const list = document.getElementById(
        "tripList"
    );

    if (!list) {
        return;
    }

    list.innerHTML = `
        <div class="browser-loading">
            Buscando viajes…
        </div>
    `;

    try {
        const response = await fetch(
            "/api/trips",
            {
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || "No se pudieron cargar los viajes."
            );
        }

        document.getElementById(
            "tripCount"
        ).textContent = (
            `${data.count} `
            + (
                data.count === 1
                ? "viaje"
                : "viajes"
            )
        );

        document.getElementById(
            "tripFolder"
        ).textContent = data.folder;

        renderTripsList(
            data.trips
        );

    } catch (error) {
        list.innerHTML = `
            <div class="browser-error">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


function renderTripsList(trips) {
    const list = document.getElementById(
        "tripList"
    );

    if (!list) {
        return;
    }

    if (!trips.length) {
        list.innerHTML = `
            <div class="browser-empty premium-empty">
                <div class="empty-icon">⌁</div>

                <strong>
                    No hay viajes
                </strong>

                <span>
                    Los nuevos trayectos aparecerán aquí.
                </span>
            </div>
        `;

        return;
    }

    list.innerHTML = "";

    for (const trip of trips) {
        const card = document.createElement(
            "button"
        );

        card.className = (
            "trip-list-item trip-premium-card"
        );

        card.type = "button";

        const visual = tripVisualState(
            trip
        );

        card.classList.add(
            `trip-state-${visual.state}`
        );

        const segments = (
            Array.isArray(trip.segments)
            ? trip.segments
            : []
        );

        const events = (
            Array.isArray(trip.events)
            ? trip.events
            : []
        );

        const firstSegment = (
            segments.length
            ? segments[0]
            : null
        );

        const thumbnailUrl = (
            firstSegment
            && firstSegment.filename
            ? (
                "/api/videos/thumbnail/"
                + encodeURIComponent(
                    firstSegment.filename
                )
            )
            : null
        );

        const photoCount = events.filter(
            event => event.type === "photo"
        ).length;

        const protectedCount = segments.filter(
            segment => Boolean(
                segment.protected
            )
        ).length;

        const isProtected = (
            protectedCount > 0
            || events.some(
                event => Boolean(
                    event.protected
                )
            )
        );

        const distance = (
            trip.distance
            && Number.isFinite(
                Number(
                    trip.distance.kilometers
                )
            )
            ? formatDistance(
                trip.distance.kilometers
            )
            : "Sin distancia"
        );

        const media = (
            thumbnailUrl
            ? `
                <img
                    class="trip-card-thumbnail"
                    src="${escapeHtml(thumbnailUrl)}"
                    alt=""
                    loading="lazy"
                    onerror="
                        this.classList.add('hidden');
                        this.nextElementSibling.classList.remove('hidden');
                    "
                >

                <span class="trip-card-fallback hidden">
                    ${visual.icon}
                </span>
            `
            : `
                <span class="trip-card-fallback">
                    ${visual.icon}
                </span>
            `
        );

        card.innerHTML = `
            <span class="trip-card-media">
                ${media}

                <span
                    class="
                        trip-card-status
                        status-${visual.state}
                    "
                >
                    <span>${visual.icon}</span>
                    ${escapeHtml(visual.label)}
                </span>

                ${
                    isProtected
                    ? `
                        <span
                            class="trip-card-protected"
                            title="Contiene vídeos protegidos"
                        >
                            🛡 Protegido
                        </span>
                    `
                    : ""
                }

                <span class="trip-card-duration">
                    ${escapeHtml(trip.duration)}
                </span>
            </span>

            <span class="trip-card-content">
                <span class="trip-card-heading">
                    <span>
                        <strong>
                            ${escapeHtml(
                                premiumTripDate(
                                    trip.started,
                                    trip.date
                                )
                            )}
                        </strong>

                        <small>
                            ${escapeHtml(trip.time)}
                        </small>
                    </span>

                    <span class="trip-card-arrow">
                        →
                    </span>
                </span>

                <span class="trip-card-primary-stats">
                    <span>
                        <small>Distancia</small>
                        <strong>${escapeHtml(distance)}</strong>
                    </span>

                    <span>
                        <small>Velocidad máxima</small>
                        <strong>
                            ${Number(
                                trip.speed?.max || 0
                            ).toFixed(1)}
                            km/h
                        </strong>
                    </span>
                </span>

                <span class="trip-card-chips">
                    <span>
                        🎥
                        ${Number(
                            trip.segment_count || 0
                        )}
                        segmentos
                    </span>

                    <span>
                        📷
                        ${photoCount}
                        fotos
                    </span>

                    <span>
                        ⚠
                        ${Number(
                            trip.event_count
                            || events.length
                            || 0
                        )}
                        eventos
                    </span>

                    ${
                        protectedCount > 0
                        ? `
                            <span class="protected-chip">
                                🛡
                                ${protectedCount}
                                protegidos
                            </span>
                        `
                        : ""
                    }
                </span>
            </span>
        `;

        card.onclick = (
            () => selectTrip(
                trip,
                card
            )
        );

        list.appendChild(
            card
        );
    }
}


function tripVisualState(trip) {
    const events = (
        Array.isArray(trip.events)
        ? trip.events
        : []
    );

    if (
        trip.type === "parking"
        || events.some(
            event => event.type === "parking"
        )
    ) {
        return {
            state: "parking",
            label: "Parking",
            icon: "P"
        };
    }

    if (
        events.some(
            event => event.type === "impact"
        )
    ) {
        return {
            state: "impact",
            label: "Impacto",
            icon: "!"
        };
    }

    if (
        events.some(
            event => [
                "braking",
                "overspeed",
                "adas"
            ].includes(
                event.type
            )
        )
    ) {
        return {
            state: "warning",
            label: "Advertencia",
            icon: "⚠"
        };
    }

    if (events.length > 0) {
        return {
            state: "event",
            label: "Con eventos",
            icon: "●"
        };
    }

    return {
        state: "normal",
        label: "Viaje",
        icon: "⌁"
    };
}


function premiumTripDate(
    started,
    fallback
) {
    const date = new Date(
        started
    );

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return fallback || "Fecha desconocida";
    }

    return new Intl.DateTimeFormat(
        "es-ES",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    ).format(
        date
    );
}


async function selectTrip(
    tripSummary,
    button
) {
    document.querySelectorAll(
        ".trip-list-item"
    ).forEach((item) => {
        item.classList.remove(
            "selected"
        );
    });

    button.classList.add(
        "selected"
    );

    const details = document.getElementById(
        "tripDetails"
    );

    details.innerHTML = `
        <div class="browser-loading">
            Cargando viaje…
        </div>
    `;

    try {
        const response = await fetch(
            `/api/trips/${
                encodeURIComponent(
                    tripSummary.filename
                )
            }`,
            {
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || "No se pudo cargar el viaje."
            );
        }

        selectedTrip = data.trip;

        renderTripDetails(
            selectedTrip
        );

    } catch (error) {
        details.innerHTML = `
            <div class="browser-error">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


function renderTripDetails(trip) {
    const details = document.getElementById(
        "tripDetails"
    );

    const segments = trip.segments
        .map((segment, index) => {
            return `
                <button
                    class="trip-segment"
                    type="button"
                    data-segment="${escapeHtml(segment.filename)}"
                >
                    <span>
                        ${index + 1}
                    </span>

                    <strong>
                        ${escapeHtml(segment.filename)}
                    </strong>

                    <small>
                        ${formatSeconds(segment.duration)}
                    </small>
                </button>
            `;
        })
        .join("");

    const events = (
        Array.isArray(trip.events)
        ? trip.events
        : []
    );

    const eventsHtml = (
        events.length
        ? events.map((event) => `
            <button
                class="trip-event ${escapeHtml(event.severity)}"
                type="button"
                data-event-type="${escapeHtml(
                    event.type || "manual"
                )}"
                data-event-id="${escapeHtml(
                    event.event_id || ""
                )}"
                data-event-segment="${escapeHtml(
                    event.segment || ""
                )}"
                data-event-time="${Number(
                    event.segment_time || 0
                )}"
                data-event-latitude="${
                    Array.isArray(event.gps)
                    ? Number(event.gps[0])
                    : ""
                }"
                data-event-longitude="${
                    Array.isArray(event.gps)
                    ? Number(event.gps[1])
                    : ""
                }"
                title="Abrir el vídeo en este momento"
            >
                <span class="trip-event-icon">
                    ${eventIcon(event.type)}
                </span>

                <span class="trip-event-main">
                    <strong>
                        ${escapeHtml(event.label)}
                    </strong>

                    <small>
                        ${formatTrackTime(event.trip_time)}
                        ·
                        ${escapeHtml(event.type)}
                        ·
                        ${Number(event.speed || 0).toFixed(1)} km/h
                    </small>

                    ${
                        event.type === "photo"
                        && event.data
                        && event.data.photo
                        && event.data.photo.thumbnail_url
                        ? `
                            <img
                                class="trip-event-photo"
                                src="${escapeHtml(
                                    event.data.photo.thumbnail_url
                                )}"
                                alt=""
                                loading="lazy"
                            >
                        `
                        : ""
                    }
                </span>

                <span class="trip-event-status">
                    ${
                        event.protected
                        ? "Protegido"
                        : "Abrir ▶"
                    }
                </span>
            </button>
        `).join("")
        : `
            <div class="trip-events-empty">
                Este viaje no contiene eventos.
            </div>
        `
    );

    const timelineHtml = buildTripTimeline(
        trip,
        events
    );

    details.innerHTML = `
        <div class="trip-details-content">
            <div class="trip-summary-grid">
                <div>
                    <span>Inicio</span>
                    <strong>
                        ${escapeHtml(trip.date)}
                        ·
                        ${escapeHtml(trip.time)}
                    </strong>
                </div>

                <div>
                    <span>Duración</span>
                    <strong>${escapeHtml(trip.duration)}</strong>
                </div>

                <div>
                    <span>Segmentos</span>
                    <strong>${trip.segment_count}</strong>
                </div>

                <div>
                    <span>Velocidad máxima</span>
                    <strong>${trip.speed.max} km/h</strong>
                </div>

                <div>
                    <span>Velocidad media</span>
                    <strong>${trip.speed.average} km/h</strong>
                </div>

                <div>
                    <span>Distancia</span>
                    <strong>
                        ${formatDistance(
                            trip.distance.kilometers
                        )}
                    </strong>
                </div>

                <div>
                    <span>Tiempo en movimiento</span>
                    <strong>
                        ${formatLongDuration(
                            trip.motion.moving_seconds
                        )}
                    </strong>
                </div>

                <div>
                    <span>Tiempo parado</span>
                    <strong>
                        ${formatLongDuration(
                            trip.motion.stopped_seconds
                        )}
                    </strong>
                </div>

                <div>
                    <span>Media en movimiento</span>
                    <strong>
                        ${trip.speed.average_moving} km/h
                    </strong>
                </div>

                <div>
                    <span>Porcentaje en marcha</span>
                    <strong>
                        ${trip.motion.moving_percent} %
                    </strong>
                </div>

                <div>
                    <span>Puntos GPS</span>
                    <strong>${trip.route_points}</strong>
                </div>
            </div>

            <h3>Línea temporal del viaje</h3>

            ${timelineHtml}

            <h3>Ruta completa</h3>

            <div id="tripMap"></div>

            <div
                id="tripRouteEmpty"
                class="route-empty hidden"
            >
                Este viaje no contiene una ruta GPS.
            </div>

            <h3>
                Eventos del viaje
                <span class="section-count">
                    ${trip.event_count || events.length}
                </span>
            </h3>

            <div class="trip-events">
                ${eventsHtml}
            </div>

            <h3>Vídeos del viaje</h3>

            <div class="trip-segments">
                ${segments}
            </div>
        </div>
    `;

    document.querySelectorAll(
        ".timeline-event"
    ).forEach((button) => {
        button.onclick = () => {
            const eventId = (
                button.dataset.eventId
            );

            const event = (
                Array.isArray(selectedTrip.events)
                ? selectedTrip.events.find(
                    item => (
                        item.event_id === eventId
                    )
                )
                : null
            );

            if (event) {
                openTimelineEvent(
                    event
                );
            }
        };
    });

    document.querySelectorAll(
        ".trip-event"
    ).forEach((button) => {
        button.onclick = () => {
            const event = (
                Array.isArray(selectedTrip.events)
                ? selectedTrip.events.find(
                    item => (
                        item.event_id
                        === button.dataset.eventId
                    )
                )
                : null
            );

            if (
                button.dataset.eventType === "photo"
                && event
                && event.data
                && event.data.photo
            ) {
                pendingPhotoEvent = event;
                popupManager.open("photo");
                return;
            }

            openTripEvent(
                button.dataset.eventSegment,
                Number(
                    button.dataset.eventTime
                    || 0
                )
            );
        };
    });

    document.querySelectorAll(
        ".trip-segment"
    ).forEach((button) => {
        button.onclick = () => {
            popupManager.close();

            window.setTimeout(
                () => {
                    popupManager.open("videos");

                    window.setTimeout(
                        async () => {
                            await loadVideos();

                            const target = Array.from(
                                document.querySelectorAll(
                                    ".video-list-item"
                                )
                            ).find(
                                item => (
                                    item.dataset.videoName
                                    === button.dataset.segment
                                )
                            );

                            if (target) {
                                target.click();
                            }
                        },
                        250
                    );
                },
                100
            );
        };
    });

    window.setTimeout(
        renderTripMap,
        80
    );
}


function renderTripMap() {
    const mapElement = document.getElementById(
        "tripMap"
    );

    const emptyElement = document.getElementById(
        "tripRouteEmpty"
    );

    if (!mapElement || !selectedTrip) {
        return;
    }

    const route = Array.isArray(
        selectedTrip.route
    )
        ? selectedTrip.route
        : [];

    if (!route.length) {
        mapElement.classList.add(
            "hidden"
        );

        emptyElement.classList.remove(
            "hidden"
        );

        return;
    }

    if (typeof L === "undefined") {
        mapElement.classList.add(
            "hidden"
        );

        emptyElement.textContent = (
            "No se pudo cargar el sistema de mapas."
        );

        emptyElement.classList.remove(
            "hidden"
        );

        return;
    }

    if (tripMap) {
        tripMap.remove();
        tripMap = null;
        tripRouteLayer = null;
    }

    tripMap = L.map(
        mapElement
    );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution:
                "&copy; OpenStreetMap contributors"
        }
    ).addTo(
        tripMap
    );

    const coordinates = route.map(
        point => [
            Number(point.lat),
            Number(point.lon)
        ]
    );

    tripRouteLayer = L.polyline(
        coordinates,
        {
            weight: 5,
            opacity: 0.9
        }
    ).addTo(
        tripMap
    );

    L.marker(
        coordinates[0]
    )
        .addTo(tripMap)
        .bindPopup("Inicio");

    L.marker(
        coordinates[
            coordinates.length - 1
        ]
    )
        .addTo(tripMap)
        .bindPopup("Final");

    if (coordinates.length === 1) {
        tripMap.setView(
            coordinates[0],
            17
        );
    } else {
        tripMap.fitBounds(
            tripRouteLayer.getBounds(),
            {
                padding: [30, 30]
            }
        );
    }

    tripMap.invalidateSize();
}


function formatSeconds(value) {
    const seconds = Math.max(
        0,
        Math.round(
            Number(value) || 0
        )
    );

    const minutes = Math.floor(
        seconds / 60
    );

    return (
        String(minutes).padStart(2, "0")
        + ":"
        + String(seconds % 60).padStart(2, "0")
    );
}


function formatDistance(kilometers) {
    const value = Math.max(
        0,
        Number(kilometers) || 0
    );

    if (value < 1) {
        return (
            Math.round(value * 1000)
            + " m"
        );
    }

    return (
        value.toFixed(2)
        + " km"
    );
}


function formatLongDuration(value) {
    const totalSeconds = Math.max(
        0,
        Math.round(
            Number(value) || 0
        )
    );

    const hours = Math.floor(
        totalSeconds / 3600
    );

    const minutes = Math.floor(
        (
            totalSeconds % 3600
        ) / 60
    );

    const seconds = (
        totalSeconds % 60
    );

    if (hours > 0) {
        return (
            `${hours} h `
            + `${minutes} min`
        );
    }

    if (minutes > 0) {
        return (
            `${minutes} min `
            + `${seconds} s`
        );
    }

    return `${seconds} s`;
}


// ============================================================
// Marcador manual de eventos
// ============================================================

const markEventButton = document.getElementById(
    "markEvent"
);


async function markManualEvent() {
    if (!markEventButton) {
        return;
    }

    markEventButton.disabled = true;

    try {
        const response = await fetch(
            "/api/events",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(
                    {
                        type: "manual",
                        source: "web",
                        label: "Evento marcado manualmente"
                    }
                )
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || "No se pudo guardar el evento."
            );
        }

        const originalText = (
            markEventButton.textContent
        );

        markEventButton.textContent = (
            "Evento guardado"
        );

        markEventButton.classList.add(
            "event-saved"
        );

        window.setTimeout(
            () => {
                markEventButton.textContent = (
                    originalText
                );

                markEventButton.classList.remove(
                    "event-saved"
                );
            },
            1600
        );

    } catch (error) {
        window.alert(
            error.message
        );

    } finally {
        markEventButton.disabled = false;
    }
}


if (markEventButton) {
    markEventButton.addEventListener(
        "click",
        markManualEvent
    );
}


function eventIcon(type) {
    const icons = {
        manual: "●",
        photo: "📷",
        braking: "!",
        impact: "⚠",
        overspeed: "↑",
        parking: "P",
        adas: "A"
    };

    return icons[type] || "●";
}


// ============================================================
// Navegación desde evento hasta vídeo
// ============================================================

async function openTripEvent(
    segmentName,
    segmentTime
) {
    if (!segmentName) {
        window.alert(
            "Este evento no tiene un segmento de vídeo asociado."
        );

        return;
    }

    const safeTime = Math.max(
        0,
        Number(segmentTime) || 0
    );

    popupManager.close();

    window.setTimeout(
        () => {
            popupManager.open(
                "videos"
            );

            waitForVideoListAndOpenEvent(
                segmentName,
                safeTime,
                0
            );
        },
        120
    );
}


function waitForVideoListAndOpenEvent(
    segmentName,
    segmentTime,
    attempt
) {
    const maximumAttempts = 30;

    const target = Array.from(
        document.querySelectorAll(
            ".video-list-item"
        )
    ).find((item) => {
        return (
            item.dataset.videoName
            === segmentName
        );
    });

    if (target) {
        target.click();

        window.setTimeout(
            () => {
                seekVideoToEvent(
                    segmentTime
                );
            },
            120
        );

        return;
    }

    if (attempt >= maximumAttempts) {
        window.alert(
            "No se encontró el vídeo asociado al evento."
        );

        return;
    }

    window.setTimeout(
        () => {
            waitForVideoListAndOpenEvent(
                segmentName,
                segmentTime,
                attempt + 1
            );
        },
        120
    );
}


function seekVideoToEvent(
    segmentTime
) {
    const player = document.getElementById(
        "videoPlayer"
    );

    if (!player) {
        return;
    }

    const seek = () => {
        const duration = Number(
            player.duration
        );

        let targetTime = Math.max(
            0,
            Number(segmentTime) || 0
        );

        if (
            Number.isFinite(duration)
            && duration > 0
        ) {
            targetTime = Math.min(
                targetTime,
                Math.max(
                    0,
                    duration - 0.05
                )
            );
        }

        try {
            player.currentTime = targetTime;

            const playPromise = player.play();

            if (
                playPromise
                && typeof playPromise.catch
                === "function"
            ) {
                playPromise.catch(
                    () => {
                        // Algunos navegadores bloquean
                        // la reproducción automática.
                    }
                );
            }

        } catch (error) {
            console.error(
                "No se pudo abrir el evento:",
                error
            );
        }
    };

    if (player.readyState >= 1) {
        seek();
    } else {
        player.addEventListener(
            "loadedmetadata",
            seek,
            {
                once: true
            }
        );
    }
}


// ============================================================
// Fotografía inteligente
// ============================================================

let pendingPhotoEvent = null;

const capturePhotoButton = document.getElementById(
    "capturePhoto"
);


async function captureRoadEyePhoto() {
    if (!capturePhotoButton) {
        return;
    }

    capturePhotoButton.disabled = true;

    const originalHtml = (
        capturePhotoButton.innerHTML
    );

    capturePhotoButton.innerHTML = `
        <span class="button-icon">◌</span>
        <span>Guardando…</span>
    `;

    try {
        const response = await fetch(
            "/api/photos/capture",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || "No se pudo guardar la fotografía."
            );
        }

        capturePhotoButton.innerHTML = `
            <span class="button-icon">✓</span>
            <span>Guardada</span>
        `;

        window.setTimeout(
            () => {
                capturePhotoButton.innerHTML = (
                    originalHtml
                );
            },
            1500
        );

    } catch (error) {
        window.alert(
            error.message
        );

        capturePhotoButton.innerHTML = (
            originalHtml
        );

    } finally {
        capturePhotoButton.disabled = false;
    }
}


if (capturePhotoButton) {
    capturePhotoButton.addEventListener(
        "click",
        captureRoadEyePhoto
    );
}


async function toggleSelectedVideoProtection() {
    if (!selectedVideo) {
        return;
    }

    const newProtectedState = (
        !Boolean(
            selectedVideo.protected
        )
    );

    try {
        const response = await fetch(
            `/api/videos/${
                encodeURIComponent(
                    selectedVideo.name
                )
            }/protection`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(
                    {
                        protected: newProtectedState
                    }
                )
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail
                || "No se pudo cambiar la protección."
            );
        }

        selectedVideo.protected = (
            data.protected
        );

        await loadVideos();

    } catch (error) {
        window.alert(
            error.message
        );
    }
}


// ============================================================
// Línea temporal del viaje
// ============================================================

function buildTripTimeline(
    trip,
    events
) {
    const duration = Math.max(
        0.01,
        Number(
            trip.duration_seconds
            || trip.duration
            || 0
        )
    );

    const normalizedEvents = (
        Array.isArray(events)
        ? events
        : []
    );

    const markers = normalizedEvents
        .map((event) => {
            const tripTime = Math.max(
                0,
                Number(
                    event.trip_time
                    || 0
                )
            );

            const percentage = Math.max(
                0,
                Math.min(
                    100,
                    (
                        tripTime
                        / duration
                    ) * 100
                )
            );

            const eventType = escapeHtml(
                event.type || "manual"
            );

            const severity = escapeHtml(
                event.severity || "info"
            );

            const label = escapeHtml(
                event.label || "Evento"
            );

            const speed = Number(
                event.speed || 0
            ).toFixed(1);

            const protectedLabel = (
                event.protected
                ? " · Protegido"
                : ""
            );

            const title = escapeHtml(
                `${event.label || "Evento"} · `
                + `${formatTrackTime(tripTime)} · `
                + `${speed} km/h`
                + protectedLabel
            );

            return `
                <button
                    class="
                        timeline-event
                        timeline-${eventType}
                        severity-${severity}
                        ${
                            event.protected
                            ? "protected"
                            : ""
                        }
                    "
                    type="button"
                    data-event-id="${escapeHtml(
                        event.event_id || ""
                    )}"
                    style="left: ${percentage.toFixed(3)}%;"
                    title="${title}"
                    aria-label="${title}"
                >
                    <span class="timeline-event-symbol">
                        ${eventIcon(event.type)}
                    </span>

                    <span class="timeline-event-tooltip">
                        <strong>${label}</strong>

                        <small>
                            ${formatTrackTime(tripTime)}
                            ·
                            ${speed} km/h
                        </small>
                    </span>
                </button>
            `;
        })
        .join("");

    const quarter = duration / 4;

    return `
        <section class="trip-timeline">
            <div class="timeline-summary">
                <span>
                    Inicio
                    <strong>00:00</strong>
                </span>

                <span>
                    ${normalizedEvents.length}
                    ${
                        normalizedEvents.length === 1
                        ? "evento"
                        : "eventos"
                    }
                </span>

                <span>
                    Final
                    <strong>
                        ${formatTimelineDuration(duration)}
                    </strong>
                </span>
            </div>

            <div class="timeline-track-wrap">
                <div class="timeline-track">
                    <span
                        class="timeline-progress"
                        aria-hidden="true"
                    ></span>

                    ${markers}
                </div>

                <div class="timeline-scale">
                    <span>00:00</span>
                    <span>
                        ${formatTimelineDuration(quarter)}
                    </span>
                    <span>
                        ${formatTimelineDuration(quarter * 2)}
                    </span>
                    <span>
                        ${formatTimelineDuration(quarter * 3)}
                    </span>
                    <span>
                        ${formatTimelineDuration(duration)}
                    </span>
                </div>
            </div>

            ${
                normalizedEvents.length
                ? `
                    <p class="timeline-help">
                        Pulsa cualquier marcador para abrir
                        el vídeo o la fotografía correspondiente.
                    </p>
                `
                : `
                    <div class="timeline-empty">
                        Este viaje no contiene eventos.
                    </div>
                `
            }
        </section>
    `;
}


function openTimelineEvent(event) {
    if (
        event.type === "photo"
        && event.data
        && event.data.photo
    ) {
        pendingPhotoEvent = event;
        popupManager.open(
            "photo"
        );

        return;
    }

    openTripEvent(
        event.segment,
        Number(
            event.segment_time || 0
        )
    );
}


function formatTimelineDuration(value) {
    const totalSeconds = Math.max(
        0,
        Math.round(
            Number(value) || 0
        )
    );

    const hours = Math.floor(
        totalSeconds / 3600
    );

    const minutes = Math.floor(
        (
            totalSeconds % 3600
        ) / 60
    );

    const seconds = (
        totalSeconds % 60
    );

    if (hours > 0) {
        return (
            String(hours).padStart(2, "0")
            + ":"
            + String(minutes).padStart(2, "0")
            + ":"
            + String(seconds).padStart(2, "0")
        );
    }

    return (
        String(minutes).padStart(2, "0")
        + ":"
        + String(seconds).padStart(2, "0")
    );
}


// ============================================================
// Sincronización vídeo y mapa
// ============================================================

function initializeVideoMapSynchronization(
    player
) {
    if (!player) {
        return;
    }

    if (
        player._roadEyeMapSyncHandler
    ) {
        player.removeEventListener(
            "timeupdate",
            player._roadEyeMapSyncHandler
        );

        player.removeEventListener(
            "seeked",
            player._roadEyeMapSyncHandler
        );
    }

    const handler = () => {
        updateVideoMapPosition(
            Number(
                player.currentTime
            ) || 0
        );
    };

    player._roadEyeMapSyncHandler = (
        handler
    );

    player.addEventListener(
        "timeupdate",
        handler
    );

    player.addEventListener(
        "seeked",
        handler
    );

    player.addEventListener(
        "loadedmetadata",
        handler
    );
}


function updateVideoMapPosition(
    videoTime
) {
    if (
        !routeMap
        || !routeVehicleMarker
        || !routeProgressLayer
        || !routeSyncTrack.length
    ) {
        return;
    }

    const currentTime = Math.max(
        0,
        Number(videoTime) || 0
    );

    const position = interpolateTrackPosition(
        routeSyncTrack,
        currentTime
    );

    if (!position) {
        return;
    }

    const coordinate = [
        position.lat,
        position.lon
    ];

    routeVehicleMarker.setLatLng(
        coordinate
    );

    routeVehicleMarker.setTooltipContent(
        `${formatTrackTime(currentTime)}`
        + ` · ${position.speed.toFixed(1)} km/h`
    );

    const progressCoordinates = (
        routeSyncTrack
        .filter((point) => {
            return (
                Number(point.time)
                <= currentTime
            );
        })
        .map((point) => [
            Number(point.lat),
            Number(point.lon)
        ])
    );

    if (!progressCoordinates.length) {
        progressCoordinates.push(
            coordinate
        );
    } else {
        progressCoordinates.push(
            coordinate
        );
    }

    routeProgressLayer.setLatLngs(
        progressCoordinates
    );

    const timeElement = document.getElementById(
        "routeSyncTime"
    );

    const speedElement = document.getElementById(
        "routeSyncSpeed"
    );

    if (timeElement) {
        timeElement.textContent = (
            formatTrackTime(
                currentTime
            )
        );
    }

    if (speedElement) {
        speedElement.textContent = (
            `${position.speed.toFixed(1)} km/h`
        );
    }
}


function interpolateTrackPosition(
    track,
    currentTime
) {
    if (!track.length) {
        return null;
    }

    if (
        currentTime
        <= Number(track[0].time)
    ) {
        return normalizedTrackPoint(
            track[0]
        );
    }

    const last = track[
        track.length - 1
    ];

    if (
        currentTime
        >= Number(last.time)
    ) {
        return normalizedTrackPoint(
            last
        );
    }

    let low = 0;
    let high = track.length - 1;

    while (
        low <= high
    ) {
        const middle = Math.floor(
            (low + high) / 2
        );

        const middleTime = Number(
            track[middle].time
        );

        if (middleTime < currentTime) {
            low = middle + 1;
        } else {
            high = middle - 1;
        }
    }

    const nextIndex = Math.min(
        track.length - 1,
        low
    );

    const previousIndex = Math.max(
        0,
        nextIndex - 1
    );

    const previous = normalizedTrackPoint(
        track[previousIndex]
    );

    const next = normalizedTrackPoint(
        track[nextIndex]
    );

    const interval = Math.max(
        0.001,
        next.time - previous.time
    );

    const progress = Math.max(
        0,
        Math.min(
            1,
            (
                currentTime
                - previous.time
            ) / interval
        )
    );

    return {
        time: currentTime,
        lat: (
            previous.lat
            + (
                next.lat
                - previous.lat
            ) * progress
        ),
        lon: (
            previous.lon
            + (
                next.lon
                - previous.lon
            ) * progress
        ),
        speed: (
            previous.speed
            + (
                next.speed
                - previous.speed
            ) * progress
        )
    };
}


function normalizedTrackPoint(
    point
) {
    return {
        time: Number(
            point.time
        ) || 0,

        lat: Number(
            point.lat
        ),

        lon: Number(
            point.lon
        ),

        speed: Math.max(
            0,
            Number(
                point.speed
            ) || 0
        )
    };
}
