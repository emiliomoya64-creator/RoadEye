import logging
import time
from contextlib import asynccontextmanager

import cv2
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cameras.camera_service import CameraService
from core.display_buffer import display_buffer
from core.render_service import render_service
from display.hdmi_display_service import hdmi_display_service
from gps.gps_service import GPSService
from gps.map_service import MapService
from recorder.recorder_service import RecorderService

import web.api as api


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Servicios principales
# ---------------------------------------------------------

camera = CameraService()
gps = GPSService()
maps = MapService()
recorder = RecorderService()

api.recorder = recorder


# ---------------------------------------------------------
# Ciclo de vida de RoadEye
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando servicios de RoadEye")

    camera.start()
    gps.start()
    maps.start()

    # Primero se genera el frame final con HUD.
    render_service.start()

    # Después ese mismo frame se envía al HDMI.
    hdmi_display_service.start()

    try:
        yield

    finally:
        logger.info("Deteniendo servicios de RoadEye")

        hdmi_display_service.stop()
        render_service.stop()

        try:
            camera.stop()
        except Exception:
            logger.exception(
                "No se pudo detener CameraService"
            )


app = FastAPI(
    title="RoadEye",
    lifespan=lifespan,
)

app.include_router(api.router)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

templates = Jinja2Templates(
    directory="templates",
)


# ---------------------------------------------------------
# Página principal
# ---------------------------------------------------------

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


# ---------------------------------------------------------
# Streaming web
# ---------------------------------------------------------

def generate():
    """
    Genera MJPEG desde el mismo display_buffer utilizado por HDMI.
    """

    last_frame_number = -1

    while True:
        frame_number = display_buffer.get_frame_number()

        if frame_number == last_frame_number:
            time.sleep(0.005)
            continue

        frame = display_buffer.get_frame()

        if frame is None:
            time.sleep(0.01)
            continue

        success, jpeg = cv2.imencode(
            ".jpg",
            frame,
            [
                int(cv2.IMWRITE_JPEG_QUALITY),
                85,
            ],
        )

        if not success:
            time.sleep(0.005)
            continue

        last_frame_number = frame_number

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n"
            b"Cache-Control: no-cache\r\n\r\n"
            + jpeg.tobytes()
            + b"\r\n"
        )


@app.get("/video")
def video():
    return StreamingResponse(
        generate(),
        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
        headers={
            "Cache-Control": (
                "no-store, no-cache, must-revalidate, "
                "max-age=0"
            ),
            "Pragma": "no-cache",
        },
    )