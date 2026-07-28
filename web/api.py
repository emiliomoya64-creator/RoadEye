from pathlib import Path
import shutil

from fastapi import APIRouter

from core.system_state import system_state

router = APIRouter()

# Se asignará desde web/server.py
recorder = None

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "videos"


@router.get("/api/status")
async def status():

    total, used, free = shutil.disk_usage(BASE_DIR)

    porcentaje = round((used / total) * 100)

    videos = 0

    if VIDEOS_DIR.exists():
        videos = len(list(VIDEOS_DIR.glob("*.mp4")))

    return {
        "recording": system_state.get("recording"),
        "gps_fix": system_state.get("gps_fix"),
        "speed": system_state.get("speed"),
        "cpu": system_state.get("cpu"),
        "temp": system_state.get("temp"),
        "disk": porcentaje,
        "videos": videos
    }


@router.get("/api/record/start")
async def record_start():

    global recorder

    if recorder is not None:
        recorder.start()
        system_state.set("recording", True)

    return {"ok": True}


@router.get("/api/record/stop")
async def record_stop():

    global recorder

    if recorder is not None:
        recorder.stop()
        system_state.set("recording", False)

    return {"ok": True}