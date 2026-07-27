from pathlib import Path
import shutil

from fastapi import APIRouter

from core.system_state import system_state

router = APIRouter()

# Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpeta de vídeos
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