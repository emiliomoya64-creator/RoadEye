"use strict";


window.RoadEyeMedia = window.RoadEyeMedia || {};


window.RoadEyeMedia.tripCards = (() => {
    function render(
        trips,
        {
            escapeHtml,
            formatDistance,
            selectTrip
        }
    ) {
        const list = document.getElementById(
            "tripList"
        );

        if (!list) {
            return;
        }

        if (!Array.isArray(trips) || !trips.length) {
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

            const visual = visualState(
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

            const media = thumbnailUrl
                ? `
                    <img
                        class="trip-card-thumbnail"
                        src="${escapeHtml(thumbnailUrl)}"
                        alt=""
                        loading="lazy"
                    >

                    <span class="trip-card-fallback hidden">
                        ${visual.icon}
                    </span>
                `
                : `
                    <span class="trip-card-fallback">
                        ${visual.icon}
                    </span>
                `;

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
                        ${escapeHtml(trip.duration || "00:00")}
                    </span>
                </span>

                <span class="trip-card-content">
                    <span class="trip-card-heading">
                        <span>
                            <strong>
                                ${escapeHtml(
                                    premiumDate(
                                        trip.started,
                                        trip.date
                                    )
                                )}
                            </strong>

                            <small>
                                ${escapeHtml(
                                    trip.time || "--:--:--"
                                )}
                            </small>
                        </span>

                        <span class="trip-card-arrow">
                            →
                        </span>
                    </span>

                    <span class="trip-card-primary-stats">
                        <span>
                            <small>Distancia</small>
                            <strong>
                                ${escapeHtml(distance)}
                            </strong>
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

            const thumbnail = card.querySelector(
                ".trip-card-thumbnail"
            );

            if (thumbnail) {
                thumbnail.addEventListener(
                    "error",
                    () => {
                        thumbnail.classList.add(
                            "hidden"
                        );

                        const fallback = card.querySelector(
                            ".trip-card-fallback"
                        );

                        if (fallback) {
                            fallback.classList.remove(
                                "hidden"
                            );
                        }
                    },
                    {
                        once: true
                    }
                );
            }

            card.addEventListener(
                "click",
                () => {
                    selectTrip(
                        trip,
                        card
                    );
                }
            );

            list.appendChild(
                card
            );
        }
    }


    function visualState(
        trip
    ) {
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


    function premiumDate(
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
            return (
                fallback
                || "Fecha desconocida"
            );
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


    return {
        render,
        visualState,
        premiumDate
    };
})();
