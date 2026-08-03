"use strict";


window.RoadEyeMedia = window.RoadEyeMedia || {};


window.RoadEyeMedia.tripSegments = (() => {
    function build(
        trip,
        {
            escapeHtml,
            formatSeconds
        }
    ) {
        const segments = (
            Array.isArray(trip.segments)
            ? trip.segments
            : []
        );

        if (!segments.length) {
            return `
                <div class="trip-segments-empty">
                    Este viaje no contiene vídeos.
                </div>
            `;
        }

        return segments
            .map((segment, index) => {
                return buildCard(
                    segment,
                    index,
                    segments.length,
                    {
                        escapeHtml,
                        formatSeconds
                    }
                );
            })
            .join("");
    }


    function buildCard(
        segment,
        index,
        total,
        {
            escapeHtml,
            formatSeconds
        }
    ) {
        const filename = String(
            segment.filename || ""
        );

        const thumbnailUrl = filename
            ? (
                "/api/videos/thumbnail/"
                + encodeURIComponent(
                    filename
                )
            )
            : null;

        const protectedState = Boolean(
            segment.protected
        );

        const reasons = normalizeReasons(
            segment.protection_reasons
        );

        const reasonVisual = protectionVisual(
            reasons
        );

        const created = parseSegmentDate(
            segment.created
        );

        const timeText = created
            ? created.toLocaleTimeString(
                "es-ES",
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                }
            )
            : filenameTime(
                filename
            );

        const durationText = formatSeconds(
            segment.duration || 0
        );

        const maximumSpeed = Number(
            segment.speed?.max || 0
        );

        const averageSpeed = Number(
            segment.speed?.average || 0
        );

        const thumbnail = thumbnailUrl
            ? `
                <img
                    class="trip-segment-thumbnail"
                    src="${escapeHtml(thumbnailUrl)}"
                    alt=""
                    loading="lazy"
                >

                <span class="trip-segment-fallback hidden">
                    ▶
                </span>
            `
            : `
                <span class="trip-segment-fallback">
                    ▶
                </span>
            `;

        return `
            <button
                class="
                    trip-segment
                    trip-segment-premium
                    ${
                        protectedState
                        ? "is-protected"
                        : ""
                    }
                    segment-reason-${reasonVisual.state}
                "
                type="button"
                data-segment="${escapeHtml(filename)}"
                title="Abrir este vídeo"
            >
                <span class="trip-segment-media">
                    ${thumbnail}

                    <span class="trip-segment-number">
                        ${index + 1}
                        /
                        ${total}
                    </span>

                    <span class="trip-segment-duration">
                        ${escapeHtml(durationText)}
                    </span>

                    ${
                        protectedState
                        ? `
                            <span class="trip-segment-shield">
                                🛡
                            </span>
                        `
                        : ""
                    }
                </span>

                <span class="trip-segment-content">
                    <span class="trip-segment-heading">
                        <span>
                            <small>
                                Segmento ${index + 1}
                            </small>

                            <strong>
                                ${escapeHtml(timeText)}
                            </strong>
                        </span>

                        <span class="trip-segment-play">
                            ▶
                        </span>
                    </span>

                    <span class="trip-segment-stats">
                        <span>
                            <small>Máxima</small>

                            <strong>
                                ${maximumSpeed.toFixed(1)}
                                km/h
                            </strong>
                        </span>

                        <span>
                            <small>Media</small>

                            <strong>
                                ${averageSpeed.toFixed(1)}
                                km/h
                            </strong>
                        </span>
                    </span>

                    ${
                        protectedState
                        ? `
                            <span
                                class="
                                    trip-segment-protection
                                    protection-${reasonVisual.state}
                                "
                            >
                                <span>
                                    ${reasonVisual.icon}
                                </span>

                                <span>
                                    <small>Protegido por</small>

                                    <strong>
                                        ${escapeHtml(
                                            reasonVisual.label
                                        )}
                                    </strong>
                                </span>
                            </span>
                        `
                        : `
                            <span class="trip-segment-normal">
                                Grabación normal
                            </span>
                        `
                    }

                    <span class="trip-segment-filename">
                        ${escapeHtml(filename)}
                    </span>
                </span>
            </button>
        `;
    }


    function bind(
        root,
        {
            openSegment
        }
    ) {
        if (!root) {
            return;
        }

        root.querySelectorAll(
            ".trip-segment-premium"
        ).forEach((button) => {
            const image = button.querySelector(
                ".trip-segment-thumbnail"
            );

            if (image) {
                image.addEventListener(
                    "error",
                    () => {
                        image.classList.add(
                            "hidden"
                        );

                        const fallback = button.querySelector(
                            ".trip-segment-fallback"
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

            button.addEventListener(
                "click",
                () => {
                    openSegment(
                        button.dataset.segment
                    );
                }
            );
        });
    }


    function normalizeReasons(
        value
    ) {
        if (!Array.isArray(value)) {
            return [];
        }

        return value
            .map(
                item => String(
                    item || ""
                ).trim().toLowerCase()
            )
            .filter(Boolean);
    }


    function protectionVisual(
        reasons
    ) {
        if (reasons.includes("impact")) {
            return {
                state: "impact",
                label: "Impacto",
                icon: "!"
            };
        }

        if (reasons.includes("parking")) {
            return {
                state: "parking",
                label: "Parking",
                icon: "P"
            };
        }

        if (reasons.includes("braking")) {
            return {
                state: "warning",
                label: "Frenazo",
                icon: "⚠"
            };
        }

        if (reasons.includes("overspeed")) {
            return {
                state: "warning",
                label: "Exceso de velocidad",
                icon: "↑"
            };
        }

        if (reasons.includes("adas")) {
            return {
                state: "warning",
                label: "Aviso ADAS",
                icon: "A"
            };
        }

        if (reasons.includes("manual")) {
            return {
                state: "manual",
                label: "Protección manual",
                icon: "●"
            };
        }

        if (reasons.length) {
            return {
                state: "event",
                label: reasons.join(", "),
                icon: "●"
            };
        }

        return {
            state: "protected",
            label: "Evento protegido",
            icon: "🛡"
        };
    }


    function parseSegmentDate(
        value
    ) {
        if (!value) {
            return null;
        }

        const date = new Date(
            value
        );

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return null;
        }

        return date;
    }


    function filenameTime(
        filename
    ) {
        const match = String(
            filename
        ).match(
            /_(\d{2})(\d{2})(\d{2})/
        );

        if (!match) {
            return "--:--:--";
        }

        return (
            `${match[1]}:`
            + `${match[2]}:`
            + `${match[3]}`
        );
    }


    return {
        build,
        bind,
        protectionVisual
    };
})();
