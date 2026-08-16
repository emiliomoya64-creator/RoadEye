from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2

from core.config_manager import PROJECT_DIR, config
from core.frame_buffer import frame_buffer
from core.motion_detector import MotionDetector
from core.system_state import system_state
from trip.trip_manager import trip_manager


logger = logging.getLogger(__name__)


class ParkingService:
    """
    RoadEye Sentinel.

    Detecta movimiento desde FrameBuffer y utiliza el RecorderService
    existente para grabar y proteger el contexto del evento.
    """

    def __init__(
        self,
        recorder,
    ) -> None:
        self.recorder = recorder

        self._thread: Optional[
            threading.Thread
        ] = None

        self._stop_event = (
            threading.Event()
        )

        self._lock = (
            threading.RLock()
        )

        self._detector = MotionDetector(
            self._sensitivity()
        )

        self._state = "inactive"
        self._last_motion_ratio = 0.0
        self._last_motion_at = None
        self._last_event_at = None
        self._event_started_at = None
        self._event_deadline = None
        self._maximum_deadline = None
        self._started_recording = False
        self._event_count = 0
        self._simulated_count = 0

        # Estado real de Parking en tiempo de ejecución.
        # Arranca según la configuración, pero puede
        # activarse/desactivarse desde HUD/web/app.
        self._enabled = bool(
            config.get(
                "parking.enabled",
                False,
            )
        )

    @property
    def running(self) -> bool:
        return bool(
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )

    @property
    def enabled(self) -> bool:
        return bool(
            self._enabled
        )

    def start(self) -> None:
        if self.running:
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._loop,
            name="roadeye-parking",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "ParkingService iniciado"
        )

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=4.0
            )

        self._thread = None

        with self._lock:
            if self._event_started_at is not None:
                self._finish_event_locked()

            self._state = "inactive"

        logger.info(
            "ParkingService detenido"
        )

    def activate(self) -> dict:
        with self._lock:
            self._enabled = True
            system_state.set(
                "parking_enabled",
                True,
            )
            self._state = "watching"
            self._detector.reset()

        return self.status()

    def deactivate(self) -> dict:
        with self._lock:
            self._enabled = False
            system_state.set(
                "parking_enabled",
                False,
            )
            system_state.set(
                "parking_motion",
                False,
            )

            if self._event_started_at is not None:
                self._finish_event_locked()

            self._state = "inactive"
            self._detector.reset()

        return self.status()

    def simulate_event(self) -> dict:
        with self._lock:
            self._simulated_count += 1

            if self._state == "inactive":
                self._state = "watching"

            self._start_event_locked(
                source="simulation",
                motion_ratio=1.0,
            )

            return self.status()

    def status(self) -> dict:
        with self._lock:
            remaining = 0.0

            if self._event_deadline is not None:
                remaining = max(
                    0.0,
                    self._event_deadline
                    - time.monotonic(),
                )

            elapsed = 0.0

            if self._event_started_at is not None:
                elapsed = max(
                    0.0,
                    time.monotonic()
                    - self._event_started_at,
                )

            return {
                "running": self.running,
                "enabled": self.enabled,
                "state": self._state,
                "watching": (
                    self._state == "watching"
                ),
                "event_active": (
                    self._state == "event"
                ),
                "event_elapsed": round(
                    elapsed,
                    2,
                ),
                "event_remaining": round(
                    remaining,
                    2,
                ),
                "last_motion_ratio":
                    self._last_motion_ratio,
                "last_motion_at":
                    self._last_motion_at,
                "last_event_at":
                    self._last_event_at,
                "event_count":
                    self._event_count,
                "simulated_count":
                    self._simulated_count,
                "settings": {
                    "record_seconds":
                        self._record_seconds(),
                    "extend_seconds":
                        self._extend_seconds(),
                    "max_event_seconds":
                        self._maximum_seconds(),
                    "cooldown_seconds":
                        self._cooldown_seconds(),
                    "motion_sensitivity":
                        self._sensitivity(),
                    "protect_recording":
                        self._protect_enabled(),
                    "capture_photo":
                        self._photo_enabled(),
                },
            }

    def _loop(self) -> None:
        last_frame_number = -1

        while not self._stop_event.is_set():
            if not self.enabled:
                with self._lock:
                    if self._event_started_at is not None:
                        self._finish_event_locked()

                    self._state = "inactive"

                self._stop_event.wait(
                    0.5
                )

                continue

            with self._lock:
                if self._state == "inactive":
                    self._state = "watching"
                    self._detector.reset()

            frame_number = (
                frame_buffer.get_frame_number()
            )

            if frame_number == last_frame_number:
                self._check_event_deadline()

                self._stop_event.wait(
                    0.08
                )

                continue

            last_frame_number = frame_number

            frame = frame_buffer.get_frame()

            result = self._detector.detect(
                frame
            )

            motion = bool(
                result["motion"]
            )

            ratio = float(
                result["ratio"]
            )

            with self._lock:
                self._last_motion_ratio = ratio

                if motion:
                    self._last_motion_at = (
                        datetime.now().isoformat()
                    )

                    if self._event_started_at is None:
                        if self._cooldown_finished_locked():
                            self._start_event_locked(
                                source="motion",
                                motion_ratio=ratio,
                            )

                    else:
                        self._extend_event_locked()

                self._check_event_deadline_locked()

            # Aproximadamente 5 comprobaciones por segundo.
            self._stop_event.wait(
                0.20
            )

    def _check_event_deadline(self) -> None:
        with self._lock:
            self._check_event_deadline_locked()

    def _check_event_deadline_locked(self) -> None:
        if (
            self._event_started_at is None
            or self._event_deadline is None
        ):
            return

        if time.monotonic() >= self._event_deadline:
            self._finish_event_locked()

    def _start_event_locked(
        self,
        *,
        source: str,
        motion_ratio: float,
    ) -> None:
        now = time.monotonic()

        self._state = "event"
        self._event_started_at = now
        self._event_deadline = (
            now + self._record_seconds()
        )
        self._maximum_deadline = (
            now + self._maximum_seconds()
        )

        self._last_event_at = (
            datetime.now().isoformat()
        )

        recorder_status = (
            self.recorder.status()
        )

        already_recording = bool(
            recorder_status.get(
                "recording",
                False,
            )
        )

        self._started_recording = (
            not already_recording
        )

        # El Recorder ya decide que el tipo es parking
        # consultando este atributo.
        setattr(
            system_state,
            "parking_motion",
            True,
        )

        if self._started_recording:
            self.recorder.start_recording(
                trip_type="parking"
            )

        protection = {
            "previous": False,
            "current": False,
            "next_count": 0,
        }

        if self._protect_enabled():
            protection = (
                self.recorder
                .protect_event_context(
                    reason="parking",
                    protect_previous=True,
                    protect_next=1,
                )
            )

        photo = None

        if self._photo_enabled():
            photo = self._capture_photo_locked()

        status = self.recorder.status()

        current_file = status.get(
            "current_file"
        )

        if current_file:
            current_file = Path(
                str(current_file)
            ).name

        trip_manager.add_event(
            event_type="parking",
            label=(
                "Movimiento en aparcamiento"
                if source == "motion"
                else "Simulación de evento Parking"
            ),
            source=source,
            severity="warning",
            protected=self._protect_enabled(),
            segment=current_file,
            segment_time=float(
                status.get(
                    "segment_elapsed",
                    0.0,
                )
                or 0.0
            ),
            latitude=system_state.get(
                "latitude"
            ),
            longitude=system_state.get(
                "longitude"
            ),
            speed=system_state.get(
                "speed"
            ),
            data={
                "motion_ratio":
                    motion_ratio,
                "simulation": (
                    source == "simulation"
                ),
                "photo": photo,
                "protection_context":
                    protection,
                "record_seconds":
                    self._record_seconds(),
                "extend_seconds":
                    self._extend_seconds(),
                "max_event_seconds":
                    self._maximum_seconds(),
            },
        )

        self._event_count += 1

        logger.warning(
            "Sentinel: evento Parking iniciado "
            "source=%s ratio=%.4f",
            source,
            motion_ratio,
        )

    def _extend_event_locked(self) -> None:
        if (
            self._event_deadline is None
            or self._maximum_deadline is None
        ):
            return

        extended = (
            time.monotonic()
            + self._extend_seconds()
        )

        self._event_deadline = min(
            self._maximum_deadline,
            max(
                self._event_deadline,
                extended,
            ),
        )

    def _finish_event_locked(self) -> None:
        started_recording = (
            self._started_recording
        )

        self._event_started_at = None
        self._event_deadline = None
        self._maximum_deadline = None
        self._started_recording = False

        setattr(
            system_state,
            "parking_motion",
            False,
        )

        if started_recording:
            self.recorder.stop_recording()

        self._state = (
            "watching"
            if self.enabled
            else "inactive"
        )

        logger.info(
            "Sentinel: evento Parking finalizado"
        )

    def _capture_photo_locked(self):
        frame = frame_buffer.get_frame()

        if frame is None:
            return None

        directory = Path(
            str(
                config.get(
                    "photos.folder",
                    "photos",
                )
            )
        )

        if not directory.is_absolute():
            directory = (
                PROJECT_DIR
                / directory
            )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        created = datetime.now()

        filename = created.strftime(
            "parking_%Y%m%d_%H%M%S_%f.jpg"
        )

        path = directory / filename

        quality = int(
            config.get(
                "photos.jpeg_quality",
                95,
            )
        )

        saved = cv2.imwrite(
            str(path),
            frame,
            [
                int(
                    cv2.IMWRITE_JPEG_QUALITY
                ),
                max(
                    1,
                    min(
                        100,
                        quality,
                    ),
                ),
            ],
        )

        if not saved:
            return None

        return {
            "filename": filename,
            "url": (
                f"/api/photos/file/{filename}"
            ),
            "size_bytes":
                int(path.stat().st_size),
            "width":
                int(frame.shape[1]),
            "height":
                int(frame.shape[0]),
        }

    def _cooldown_finished_locked(self) -> bool:
        if self._last_event_at is None:
            return True

        try:
            last = datetime.fromisoformat(
                self._last_event_at
            )

            return (
                datetime.now() - last
            ).total_seconds() >= (
                self._cooldown_seconds()
            )

        except ValueError:
            return True

    @staticmethod
    def _number(
        key: str,
        default: float,
        minimum: float,
        maximum: float,
    ) -> float:
        try:
            value = float(
                config.get(
                    key,
                    default,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            value = default

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    def _record_seconds(self) -> float:
        return self._number(
            "parking.record_seconds",
            30,
            5,
            600,
        )

    def _extend_seconds(self) -> float:
        return self._number(
            "parking.extend_seconds",
            15,
            0,
            300,
        )

    def _maximum_seconds(self) -> float:
        return self._number(
            "parking.max_event_seconds",
            120,
            10,
            3600,
        )

    def _cooldown_seconds(self) -> float:
        return self._number(
            "parking.cooldown_seconds",
            5,
            0,
            300,
        )

    def _sensitivity(self) -> float:
        return self._number(
            "parking.motion_sensitivity",
            0.55,
            0.05,
            1.0,
        )

    def _protect_enabled(self) -> bool:
        return bool(
            config.get(
                "parking.protect_recording",
                True,
            )
        )

    def _photo_enabled(self) -> bool:
        return bool(
            config.get(
                "parking.capture_photo",
                False,
            )
        )
