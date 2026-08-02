from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from core.config_manager import PROJECT_DIR, config
from core.system_state import system_state
from recorder.recorder_service import RecorderService


router = APIRouter()

recorder: Optional[RecorderService] = None


def _videos_directory() -> Path:
    configured_folder = Path(
        str(
            config.get(
                "recording.folder",
                "videos",
            )
        )
    )

    if not configured_folder.is_absolute():
        configured_folder = (
            PROJECT_DIR
            / configured_folder
        )

    return configured_folder.resolve()


@router.get("/api/status")
async def status():
    total, used, free = shutil.disk_usage(
        PROJECT_DIR
    )

    disk_percent = round(
        used / total * 100
    )

    videos_directory = (
        _videos_directory()
    )

    video_count = 0

    if videos_directory.exists():
        video_count = len(
            list(
                videos_directory.glob(
                    "*.mp4"
                )
            )
        )

    recorder_status = (
        recorder.status()
        if recorder is not None
        else {
            "service_running": False,
            "recording": False,
            "current_file": None,
        }
    )

    return {
        "recording": recorder_status[
            "recording"
        ],
        "recorder": recorder_status,
        "gps_fix": system_state.get(
            "gps_fix"
        ),
        "speed": system_state.get(
            "speed"
        ),
        "cpu": system_state.get(
            "cpu"
        ),
        "temp": system_state.get(
            "temp"
        ),
        "disk": disk_percent,
        "videos": video_count,
    }


@router.get("/api/record/start")
async def record_start():
    if recorder is None:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está disponible",
        )

    started = recorder.start_recording()

    if not started:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está iniciado",
        )

    return {
        "ok": True,
        "recording": True,
        "recorder": recorder.status(),
    }


@router.get("/api/record/stop")
async def record_stop():
    if recorder is None:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está disponible",
        )

    recorder.stop_recording()

    return {
        "ok": True,
        "recording": False,
        "recorder": recorder.status(),
    }


@router.get("/api/record/status")
async def record_status():
    if recorder is None:
        raise HTTPException(
            status_code=503,
            detail="RecorderService no está disponible",
        )

    return recorder.status()