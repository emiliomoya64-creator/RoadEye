import os
import shutil

from fastapi import APIRouter

from core.system_state import system_state

router = APIRouter()


@router.get("/api/status")
async def status():

    total, used, free = shutil.disk_usage("/")

    porcentaje = round((used / total) * 100)

    videos = 0

    ruta = "/home/emilio/RoadEye/videos"

    if os.path.exists(ruta):

        videos = len([
            f for f in os.listdir(ruta)
            if f.endswith(".mp4")
        ])

    return {

        "recording": system_state.get("recording"),

        "gps_fix": system_state.get("gps_fix"),

        "speed": system_state.get("speed"),

        "cpu": system_state.get("cpu"),

        "temp": system_state.get("temp"),

        "disk": porcentaje,

        "videos": videos

    }