"use strict";


window.RoadEyeMedia = window.RoadEyeMedia || {};


window.RoadEyeMedia.tripHeader = (() => {
    function build(
        trip,
        {
            escapeHtml,
            formatDistance,
            formatLongDuration
        }
    ) {
        const events = (
            Array.isArray(trip.events)
            ? trip.events
            : []
        );

        const segments = (
            Array.isArray(trip.segments)
            ? trip.segments
            : []
        );

        const cardsModule = (
            window.RoadEyeMedia
            && window.RoadEyeMedia.tripCards
        );

        const visual = cardsModule
            ? cardsModule.visualState(trip)
            : {
                state: "normal",
                label: "Viaje",
                icon: "⌁"
            };

        const photoEvents = events.filter(
            event => event.type === "photo"
        );

        const protectedSegments = segments.filter(
            segment => Boolean(
                segment.protected
            )
        );

        const isProtected = (
            protectedSegments.length > 0
            || events.some(
                event => Boolean(
                    event.protected
                )
            )
        );

        const heroThumbnail = (
            segments.length > 0
            && segments[0].filename
            ? (
                "/api/videos/thumbnail/"
                + encodeURIComponent(
                    segments[0].filename
                )
            )
            : null
        );

        const formattedDate = cardsModule
            ? cardsModule.premiumDate(
                trip.started,
                trip.date
            )
            : (
                trip.date
                || "Fecha desconocida"
            );

        return `
            <section
                class="
                    trip-premium-hero
                    trip-hero-${visual.state}
                "
            >
                <div class="trip-hero-media">
                    ${buildMedia(
                        heroThumbnail,
                        visual,
                        escapeHtml
                    )}

                    <div class="trip-hero-overlay"></div>

                    <div class="trip-hero-topline">
                        <span
                            class="
                                trip-hero-type
                                hero-type-${visual.state}
                            "
                        >
                            <span>${visual.icon}</span>
                            ${escapeHtml(visual.label)}
                        </span>

                        ${
                            isProtected
                            ? `
                                <span class="trip-hero-protected">
                                    🛡 Protegido
                                </span>
                            `
                            : ""
                        }
                    </div>

                    <div class="trip-hero-title">
                        <span>
                            Trayecto RoadEye
                        </span>

                        <strong>
                            ${escapeHtml(formattedDate)}
                        </strong>

                        <small>
                            ${escapeHtml(
                                trip.time || "--:--:--"
                            )}
                            ·
                            ${escapeHtml(
                                trip.duration || "00:00"
                            )}
                        </small>
                    </div>
                </div>

                <div class="trip-hero-body">
                    ${buildKpis(
                        trip,
                        {
                            formatDistance,
                            formatLongDuration
                        }
                    )}

                    ${buildCounters(
                        trip,
                        {
                            photoCount: photoEvents.length,
                            eventCount: events.length,
                            protectedCount:
                                protectedSegments.length
                        }
                    )}

                    <div class="trip-playback-actions">
                        <button
                            class="trip-play-all-button"
                            type="button"
                            data-trip-action="play-all"
                        >
                            <span class="trip-play-all-icon">
                                ▶
                            </span>

                            <span>
                                <strong>
                                    Reproducir viaje completo
                                </strong>

                                <small>
                                    Reproducción continua de todos los segmentos
                                </small>
                            </span>

                            <span class="trip-play-all-arrow">
                                →
                            </span>
                        </button>
                    </div>

                    ${buildNavigation()}
                </div>
            </section>
        `;
    }


    function buildMedia(
        thumbnailUrl,
        visual,
        escapeHtml
    ) {
        if (!thumbnailUrl) {
            return `
                <div class="trip-hero-fallback">
                    ${visual.icon}
                </div>
            `;
        }

        return `
            <img
                src="${escapeHtml(thumbnailUrl)}"
                alt=""
                class="trip-hero-image"
            >

            <div class="trip-hero-fallback hidden">
                ${visual.icon}
            </div>
        `;
    }


    function buildKpis(
        trip,
        {
            formatDistance,
            formatLongDuration
        }
    ) {
        const distanceKm = Number(
            trip.distance?.kilometers || 0
        );

        const maximumSpeed = Number(
            trip.speed?.max || 0
        );

        const movingSeconds = Number(
            trip.motion?.moving_seconds || 0
        );

        const stoppedSeconds = Number(
            trip.motion?.stopped_seconds || 0
        );

        return `
            <div class="trip-hero-kpis">
                <div class="hero-kpi primary">
                    <span class="hero-kpi-icon">
                        ⌁
                    </span>

                    <span>
                        <small>Distancia</small>

                        <strong>
                            ${formatDistance(distanceKm)}
                        </strong>
                    </span>
                </div>

                <div class="hero-kpi">
                    <span class="hero-kpi-icon">
                        ↑
                    </span>

                    <span>
                        <small>Velocidad máxima</small>

                        <strong>
                            ${maximumSpeed.toFixed(1)}
                            km/h
                        </strong>
                    </span>
                </div>

                <div class="hero-kpi">
                    <span class="hero-kpi-icon">
                        ▶
                    </span>

                    <span>
                        <small>En movimiento</small>

                        <strong>
                            ${formatLongDuration(
                                movingSeconds
                            )}
                        </strong>
                    </span>
                </div>

                <div class="hero-kpi">
                    <span class="hero-kpi-icon">
                        Ⅱ
                    </span>

                    <span>
                        <small>Tiempo parado</small>

                        <strong>
                            ${formatLongDuration(
                                stoppedSeconds
                            )}
                        </strong>
                    </span>
                </div>
            </div>
        `;
    }


    function buildCounters(
        trip,
        {
            photoCount,
            eventCount,
            protectedCount
        }
    ) {
        return `
            <div class="trip-hero-counters">
                <span>
                    <strong>
                        ${Number(
                            trip.segment_count || 0
                        )}
                    </strong>

                    <small>Vídeos</small>
                </span>

                <span>
                    <strong>
                        ${Number(photoCount || 0)}
                    </strong>

                    <small>Fotografías</small>
                </span>

                <span>
                    <strong>
                        ${Number(
                            trip.event_count
                            || eventCount
                            || 0
                        )}
                    </strong>

                    <small>Eventos</small>
                </span>

                <span>
                    <strong>
                        ${Number(
                            protectedCount || 0
                        )}
                    </strong>

                    <small>Protegidos</small>
                </span>

                <span>
                    <strong>
                        ${Number(
                            trip.route_points || 0
                        )}
                    </strong>

                    <small>Puntos GPS</small>
                </span>
            </div>
        `;
    }


    function buildNavigation() {
        return `
            <nav
                class="trip-hero-navigation"
                aria-label="Secciones del viaje"
            >
                <button
                    class="trip-hero-nav-button"
                    type="button"
                    data-trip-section="tripTimelineSection"
                >
                    <span>⌁</span>
                    Timeline
                </button>

                <button
                    class="trip-hero-nav-button"
                    type="button"
                    data-trip-section="tripMapSection"
                >
                    <span>⌖</span>
                    Mapa
                </button>

                <button
                    class="trip-hero-nav-button"
                    type="button"
                    data-trip-section="tripEventsSection"
                >
                    <span>⚠</span>
                    Eventos
                </button>

                <button
                    class="trip-hero-nav-button"
                    type="button"
                    data-trip-section="tripVideosSection"
                >
                    <span>▶</span>
                    Vídeos
                </button>
            </nav>
        `;
    }


    function bind(
        root = document,
        {
            playTrip = null
        } = {}
    ) {
        const image = root.querySelector(
            ".trip-hero-image"
        );

        if (image) {
            image.addEventListener(
                "error",
                () => {
                    image.classList.add(
                        "hidden"
                    );

                    const fallback = root.querySelector(
                        ".trip-hero-fallback"
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

        const playAllButton = root.querySelector(
            '[data-trip-action="play-all"]'
        );

        if (
            playAllButton
            && typeof playTrip === "function"
        ) {
            playAllButton.addEventListener(
                "click",
                () => {
                    playTrip();
                }
            );
        }

        root.querySelectorAll(
            ".trip-hero-nav-button"
        ).forEach((button) => {
            button.addEventListener(
                "click",
                () => {
                    const targetId = (
                        button.dataset.tripSection
                    );

                    const target = document.getElementById(
                        targetId
                    );

                    if (!target) {
                        return;
                    }

                    target.scrollIntoView(
                        {
                            behavior: "smooth",
                            block: "start"
                        }
                    );

                    target.classList.add(
                        "section-highlight"
                    );

                    window.setTimeout(
                        () => {
                            target.classList.remove(
                                "section-highlight"
                            );
                        },
                        900
                    );
                }
            );
        });
    }


    return {
        build,
        bind
    };
})();
