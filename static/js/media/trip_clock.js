"use strict";


window.RoadEyeMedia = window.RoadEyeMedia || {};


window.RoadEyeMedia.tripClock = (() => {
    const state = {
        segments: [],
        offsets: [],
        totalDuration: 0,
        currentIndex: 0,
        currentSegmentTime: 0,
        player: null,
        playerHandler: null,
        subscribers: new Set()
    };


    function configure(segments) {
        state.segments = (
            Array.isArray(segments)
            ? segments
            : []
        ).map((segment) => ({
            ...segment,
            duration: Math.max(
                0,
                Number(segment?.duration || 0)
            )
        }));

        state.offsets = [];

        let accumulated = 0;

        for (const segment of state.segments) {
            state.offsets.push(accumulated);
            accumulated += segment.duration;
        }

        state.totalDuration = accumulated;
        state.currentIndex = 0;
        state.currentSegmentTime = 0;

        notify();

        return snapshot();
    }


    function setSegment(index) {
        const safeIndex = Math.max(
            0,
            Math.min(
                Number(index) || 0,
                Math.max(0, state.segments.length - 1)
            )
        );

        state.currentIndex = safeIndex;
        state.currentSegmentTime = 0;

        notify();
    }


    function setSegmentTime(seconds) {
        const segment = state.segments[
            state.currentIndex
        ];

        const maximum = Math.max(
            0,
            Number(segment?.duration || 0)
        );

        let safeTime = Math.max(
            0,
            Number(seconds) || 0
        );

        if (maximum > 0) {
            safeTime = Math.min(
                safeTime,
                maximum
            );
        }

        state.currentSegmentTime = safeTime;

        notify();
    }


    function seekGlobal(globalTime) {
        const target = Math.max(
            0,
            Math.min(
                Number(globalTime) || 0,
                state.totalDuration
            )
        );

        let index = 0;

        for (
            let current = 0;
            current < state.offsets.length;
            current += 1
        ) {
            const offset = state.offsets[current];
            const duration = Number(
                state.segments[current]?.duration || 0
            );

            if (
                target >= offset
                && target <= offset + duration
            ) {
                index = current;
                break;
            }

            if (target > offset) {
                index = current;
            }
        }

        const segmentTime = Math.max(
            0,
            target - Number(state.offsets[index] || 0)
        );

        return {
            index,
            segmentTime,
            globalTime: target
        };
    }


    function bindPlayer(player) {
        unbindPlayer();

        if (!player) {
            return;
        }

        const handler = () => {
            setSegmentTime(
                player.currentTime
            );
        };

        state.player = player;
        state.playerHandler = handler;

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

        handler();
    }


    function unbindPlayer() {
        if (
            state.player
            && state.playerHandler
        ) {
            state.player.removeEventListener(
                "timeupdate",
                state.playerHandler
            );

            state.player.removeEventListener(
                "seeked",
                state.playerHandler
            );

            state.player.removeEventListener(
                "loadedmetadata",
                state.playerHandler
            );
        }

        state.player = null;
        state.playerHandler = null;
    }


    function currentTime() {
        return Math.max(
            0,
            Number(
                state.offsets[state.currentIndex] || 0
            )
            + state.currentSegmentTime
        );
    }


    function totalDuration() {
        return Math.max(
            0,
            state.totalDuration
        );
    }


    function progress() {
        const total = totalDuration();

        if (total <= 0) {
            return 0;
        }

        return Math.max(
            0,
            Math.min(
                1,
                currentTime() / total
            )
        );
    }


    function snapshot() {
        return {
            currentTime: currentTime(),
            totalDuration: totalDuration(),
            progress: progress(),
            currentIndex: state.currentIndex,
            currentSegmentTime:
                state.currentSegmentTime,
            segmentOffset: Number(
                state.offsets[state.currentIndex] || 0
            ),
            segmentCount:
                state.segments.length
        };
    }


    function subscribe(callback) {
        if (typeof callback !== "function") {
            return () => {};
        }

        state.subscribers.add(callback);
        callback(snapshot());

        return () => {
            state.subscribers.delete(callback);
        };
    }


    function notify() {
        const data = snapshot();

        for (const callback of state.subscribers) {
            try {
                callback(data);

            } catch (error) {
                console.error(
                    "Error en Trip Clock:",
                    error
                );
            }
        }
    }


    function reset() {
        unbindPlayer();

        state.segments = [];
        state.offsets = [];
        state.totalDuration = 0;
        state.currentIndex = 0;
        state.currentSegmentTime = 0;

        notify();
    }


    return {
        configure,
        setSegment,
        setSegmentTime,
        seekGlobal,
        bindPlayer,
        unbindPlayer,
        currentTime,
        totalDuration,
        progress,
        snapshot,
        subscribe,
        reset
    };
})();
