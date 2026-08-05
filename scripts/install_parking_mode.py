#!/usr/bin/env python3

from __future__ import annotations

import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

PARKING_SERVICE = ROOT / "core/parking_service.py"
MOTION_DETECTOR = ROOT / "core/motion_detector.py"
SERVICES_FILE = ROOT / "core/roadeye_services.py"
SERVER_FILE = ROOT / "web/server.py"
API_FILE = ROOT / "web/api.py"
PARKING_UI = (
    ROOT
    / "static"
    / "control-center"
    / "modules"
    / "parking.js"
)


MOTION_CODE = r'''
from __future__ import annotations

import cv2
import numpy as np


class MotionDetector:
    """
    Detector visual ligero para RoadEye Sentinel.

    Reduce la imagen antes de comparar para limitar el consumo de CPU.
    """

    def __init__(
        self,
        sensitivity: float = 0.55,
    ) -> None:
        self._previous = None
        self.set_sensitivity(
            sensitivity
        )

    def set_sensitivity(
        self,
        sensitivity: float,
    ) -> None:
        value = max(
            0.05,
            min(
                1.0,
                float(sensitivity),
            ),
        )

        self.sensitivity = value

        # Sensibilidad alta:
        # menor área necesaria para detectar movimiento.
        self.minimum_ratio = (
            0.075
            - value * 0.065
        )

        self.pixel_threshold = int(
            42 - value * 22
        )

    def reset(self) -> None:
        self._previous = None

    def detect(
        self,
        frame,
    ) -> dict:
        if frame is None:
            return {
                "motion": False,
                "ratio": 0.0,
            }

        small = cv2.resize(
            frame,
            (320, 180),
            interpolation=cv2.INTER_AREA,
        )

        gray = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2GRAY,
        )

        gray = cv2.GaussianBlur(
            gray,
            (9, 9),
            0,
        )

        previous = self._previous
        self._previous = gray

        if previous is None:
            return {
                "motion": False,
                "ratio": 0.0,
            }

        difference = cv2.absdiff(
            previous,
            gray,
        )

        _, threshold = cv2.threshold(
            difference,
            self.pixel_threshold,
            255,
            cv2.THRESH_BINARY,
        )

        threshold = cv2.dilate(
            threshold,
            None,
            iterations=2,
        )

        changed = int(
            cv2.countNonZero(
                threshold
            )
        )

        ratio = (
            changed
            / float(
                threshold.shape[0]
                * threshold.shape[1]
            )
        )

        return {
            "motion": bool(
                ratio >= self.minimum_ratio
            ),
            "ratio": round(
                ratio,
                5,
            ),
        }
'''


PARKING_CODE = r'''
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
            config.get(
                "parking.enabled",
                False,
            )
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
            self._state = "watching"
            self._detector.reset()

        return self.status()

    def deactivate(self) -> dict:
        with self._lock:
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
            self.recorder.start_recording()

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

        trip_manager.ensure_trip(
            trip_type="parking",
            started_at=datetime.now(),
        )

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
'''


API_APPEND = r'''

# ============================================================
# RoadEye Sentinel · Modo Parking
# ============================================================

parking_service = None


@router.get(
    "/api/parking/status"
)
async def parking_status():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "parking": parking_service.status(),
    }


@router.post(
    "/api/parking/activate"
)
async def parking_activate():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "parking": parking_service.activate(),
    }


@router.post(
    "/api/parking/deactivate"
)
async def parking_deactivate():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "parking": parking_service.deactivate(),
    }


@router.post(
    "/api/parking/simulate"
)
async def parking_simulate():
    if parking_service is None:
        raise HTTPException(
            status_code=503,
            detail="ParkingService no está disponible.",
        )

    return {
        "ok": True,
        "message": "Evento Parking simulado.",
        "parking": parking_service.simulate_event(),
    }
'''


PARKING_UI_CODE = r'''
"use strict";

import {
    checked,
    selected,
    setContent
} from "./ui.js";


export function renderParking(
    parking
) {
    setContent(`
        <div class="settings-grid">
            <article class="settings-card">
                <span class="eyebrow">
                    RoadEye Sentinel
                </span>

                <h2>Modo Parking</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Activar vigilancia
                        </strong>

                        <small>
                            Detecta movimiento con el coche parado.
                        </small>
                    </span>

                    <input
                        type="checkbox"
                        data-setting="parking.enabled"
                        ${checked(parking.enabled)}
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>Detectar</strong>
                    </span>

                    <select data-setting="parking.trigger">
                        <option
                            value="motion"
                            ${selected(parking.trigger, "motion")}
                        >
                            Movimiento
                        </option>

                        <option
                            value="impact"
                            ${selected(parking.trigger, "impact")}
                        >
                            Impacto
                        </option>

                        <option
                            value="motion_or_impact"
                            ${
                                selected(
                                    parking.trigger,
                                    "motion_or_impact"
                                )
                            }
                        >
                            Movimiento o impacto
                        </option>
                    </select>
                </label>

                <label class="form-row">
                    <span>
                        <strong>Sensibilidad</strong>
                    </span>

                    <input
                        class="plain-number"
                        type="number"
                        min="0.05"
                        max="1"
                        step="0.05"
                        value="${
                            parking.motion_sensitivity ?? 0.55
                        }"
                        data-setting=
                            "parking.motion_sensitivity"
                    >
                </label>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Grabación inteligente
                </span>

                <h2>Tiempos</h2>

                ${timeField(
                    "Duración inicial",
                    "parking.record_seconds",
                    parking.record_seconds ?? 30,
                    5,
                    600,
                    5
                )}

                ${timeField(
                    "Extensión si continúa",
                    "parking.extend_seconds",
                    parking.extend_seconds ?? 15,
                    0,
                    300,
                    5
                )}

                ${timeField(
                    "Duración máxima",
                    "parking.max_event_seconds",
                    parking.max_event_seconds ?? 120,
                    10,
                    3600,
                    10
                )}

                ${timeField(
                    "Espera entre eventos",
                    "parking.cooldown_seconds",
                    parking.cooldown_seconds ?? 5,
                    0,
                    300,
                    1
                )}
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Protección
                </span>

                <h2>Contenido del evento</h2>

                <label class="form-row">
                    <span>
                        <strong>
                            Proteger grabación
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "parking.protect_recording"
                        ${
                            checked(
                                parking.protect_recording
                            )
                        }
                    >
                </label>

                <label class="form-row">
                    <span>
                        <strong>
                            Capturar fotografía
                        </strong>
                    </span>

                    <input
                        type="checkbox"
                        data-setting=
                            "parking.capture_photo"
                        ${
                            checked(
                                parking.capture_photo
                            )
                        }
                    >
                </label>
            </article>

            <article class="settings-card">
                <span class="eyebrow">
                    Prueba del sistema
                </span>

                <h2>Simulación Sentinel</h2>

                <p>
                    Ejecuta el flujo completo sin mover
                    ni golpear el coche.
                </p>

                <div class="button-row">
                    <button
                        id="simulateParking"
                        class="secondary-button"
                        type="button"
                    >
                        Simular evento Parking
                    </button>
                </div>

                <pre
                    id="parkingSimulationResult"
                    class="result-box hidden"
                ></pre>
            </article>
        </div>
    `);
}


function timeField(
    label,
    path,
    value,
    minimum,
    maximum,
    step
) {
    return `
        <label class="form-row">
            <span>
                <strong>${label}</strong>
            </span>

            <span class="input-unit">
                <input
                    type="number"
                    min="${minimum}"
                    max="${maximum}"
                    step="${step}"
                    value="${value}"
                    data-setting="${path}"
                >

                <b>s</b>
            </span>
        </label>
    `;
}
'''


def stamp() -> str:
    return datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


def backup(
    path: Path,
) -> None:
    if not path.exists():
        return

    target = path.with_name(
        f"{path.name}.sentinel_{stamp()}"
    )

    shutil.copy2(
        path,
        target,
    )

    print(
        "  Copia:",
        target.relative_to(ROOT),
    )


def write(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup(path)

    path.write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )

    print(
        "  Creado:",
        path.relative_to(ROOT),
    )


def patch_services() -> None:
    text = SERVICES_FILE.read_text(
        encoding="utf-8"
    )

    original = text

    import_marker = (
        "from recorder.recorder_service "
        "import RecorderService\n"
    )

    parking_import = (
        "from core.parking_service "
        "import ParkingService\n"
    )

    if parking_import not in text:
        if import_marker not in text:
            raise RuntimeError(
                "No se encontró el import del Recorder."
            )

        text = text.replace(
            import_marker,
            import_marker + parking_import,
            1,
        )

    constructor_marker = (
        "        self.recorder = RecorderService()\n"
    )

    constructor_new = (
        "        self.recorder = RecorderService()\n"
        "        self.parking = ParkingService(\n"
        "            self.recorder\n"
        "        )\n"
    )

    if "self.parking = ParkingService" not in text:
        if constructor_marker not in text:
            raise RuntimeError(
                "No se encontró self.recorder."
            )

        text = text.replace(
            constructor_marker,
            constructor_new,
            1,
        )

    register_marker = '''        self.manager.register(
            "recorder",
            self.recorder,
            description="Grabador Dashcam",
            enabled=True,
            critical=False,
            start_order=70,
        )
'''

    register_new = register_marker + '''
        self.manager.register(
            "parking",
            self.parking,
            description="RoadEye Sentinel",
            enabled=True,
            critical=False,
            start_order=80,
        )
'''

    if '"parking",' not in text:
        if register_marker not in text:
            raise RuntimeError(
                "No se encontró registro Recorder."
            )

        text = text.replace(
            register_marker,
            register_new,
            1,
        )

    summary_marker = '''        summary["recorder"] = (
            self.recorder.status()
        )
'''

    summary_new = summary_marker + '''
        summary["parking"] = (
            self.parking.status()
        )
'''

    if 'summary["parking"]' not in text:
        if summary_marker not in text:
            raise RuntimeError(
                "No se encontró summary recorder."
            )

        text = text.replace(
            summary_marker,
            summary_new,
            1,
        )

    if text != original:
        backup(SERVICES_FILE)

        SERVICES_FILE.write_text(
            text,
            encoding="utf-8",
        )

        print(
            "  Servicios Sentinel registrados"
        )


def patch_server() -> None:
    text = SERVER_FILE.read_text(
        encoding="utf-8"
    )

    marker = (
        "api.storage_manager = storage_manager\n"
    )

    addition = (
        "api.storage_manager = storage_manager\n"
        "api.parking_service = "
        "roadeye_services.parking\n"
    )

    if "api.parking_service" not in text:
        if marker not in text:
            raise RuntimeError(
                "No se encontró api.storage_manager."
            )

        backup(SERVER_FILE)

        SERVER_FILE.write_text(
            text.replace(
                marker,
                addition,
                1,
            ),
            encoding="utf-8",
        )

        print(
            "  ParkingService conectado a API"
        )


def patch_api() -> None:
    text = API_FILE.read_text(
        encoding="utf-8"
    )

    if "/api/parking/status" in text:
        print(
            "  API Sentinel ya instalada"
        )
        return

    backup(API_FILE)

    API_FILE.write_text(
        text.rstrip()
        + "\n"
        + API_APPEND.strip()
        + "\n",
        encoding="utf-8",
    )

    print(
        "  API Sentinel instalada"
    )


def patch_control_center() -> None:
    write(
        PARKING_UI,
        PARKING_UI_CODE,
    )

    app_path = (
        ROOT
        / "static"
        / "control-center"
        / "control-center.js"
    )

    text = app_path.read_text(
        encoding="utf-8"
    )

    if "simulateParking" not in text:
        marker = '''    bindStorageActions();
}
'''

        addition = '''    bindStorageActions();
    bindParkingActions();
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
                const response = await fetch(
                    "/api/parking/simulate",
                    {
                        method: "POST"
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.detail
                        || "No se pudo simular."
                    );
                }

                const parking = data.parking || {};

                output.textContent = [
                    "EVENTO SENTINEL INICIADO",
                    "",
                    `Estado: ${parking.state}`,
                    `Evento activo: ${
                        parking.event_active
                        ? "Sí"
                        : "No"
                    }`,
                    `Duración inicial: ${
                        parking.settings
                        ?.record_seconds ?? "--"
                    } s`,
                    `Protección: ${
                        parking.settings
                        ?.protect_recording
                        ? "Sí"
                        : "No"
                    }`,
                    "",
                    "RoadEye está grabando el evento."
                ].join("\\n");

            } catch (error) {
                output.textContent = (
                    `ERROR\\n\\n${error.message}`
                );
            }
        }
    );
}
'''

        if marker not in text:
            raise RuntimeError(
                "No se encontró bindStorageActions."
            )

        backup(app_path)

        app_path.write_text(
            text.replace(
                marker,
                addition,
                1,
            ),
            encoding="utf-8",
        )

        print(
            "  Simulación conectada al Control Center"
        )


def verify() -> None:
    for path in (
        MOTION_DETECTOR,
        PARKING_SERVICE,
        SERVICES_FILE,
        SERVER_FILE,
        API_FILE,
    ):
        if path.suffix == ".py":
            py_compile.compile(
                str(path),
                doraise=True,
            )

    if "/api/parking/status" not in (
        API_FILE.read_text(
            encoding="utf-8"
        )
    ):
        raise RuntimeError(
            "La API Sentinel no quedó instalada."
        )

    print(
        "  Verificación final correcta"
    )


def main() -> int:
    print()
    print("=" * 62)
    print("       RoadEye Sentinel · Instalación completa")
    print("=" * 62)
    print()

    write(
        MOTION_DETECTOR,
        MOTION_CODE,
    )

    write(
        PARKING_SERVICE,
        PARKING_CODE,
    )

    patch_services()
    patch_server()
    patch_api()
    patch_control_center()
    verify()

    Path(__file__).chmod(
        Path(__file__).stat().st_mode
        | 0o111
    )

    print()
    print(
        "RoadEye Sentinel instalado correctamente."
    )
    print()
    print(
        "Reinicia RoadEye y prueba "
        "/api/parking/status."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except Exception as exc:
        print(
            f"\nERROR: {exc}",
            file=sys.stderr,
        )

        raise SystemExit(1)
