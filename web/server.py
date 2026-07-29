import time

import cv2
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cameras.camera_service import CameraService
from recorder.recorder_service import RecorderService
from gps.gps_service import GPSService
from gps.map_service import MapService
from core.frame_buffer import frame_buffer
from hud.render import render

import web.api as api

app = FastAPI(title="RoadEye")

app.include_router(api.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Cámara

camera = CameraService()
camera.start()

# GPS

gps = GPSService()
gps.start()

# Mapas

maps = MapService()
maps.start()

# Grabador

recorder = RecorderService()
api.recorder = recorder

last_time = time.time()


@app.get("/")
async def index(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


def generate():

    global last_time

    while True:

        frame = frame_buffer.get_frame()

        if frame is None:
            time.sleep(0.01)
            continue

        now = time.time()

        elapsed = now - last_time

        fps = 0 if elapsed <= 0 else 1 / elapsed

        last_time = now

        frame = render(frame)

        ok, jpeg = cv2.imencode(".jpg", frame)

        if not ok:
            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + jpeg.tobytes() +
            b'\r\n'
        )

        time.sleep(0.03)


@app.get("/video")
def video():

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )