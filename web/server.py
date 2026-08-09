from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import cv2
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import web.api as api

from core.config_manager import config
from core.display_buffer import display_buffer
from core.roadeye_services import roadeye_services
from core.storage_manager import storage_manager
from web.webrtc import create_answer, close_all


logger = logging.getLogger(__name__)


api.recorder = roadeye_services.recorder
api.storage_manager = storage_manager
api.parking_service = roadeye_services.parking

storage_manager.set_active_file_provider(
    lambda: (
        roadeye_services.recorder
        .status()
        .get("current_file")
    )
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Iniciando RoadEye mediante ServiceManager"
    )

    roadeye_services.start_all()
    storage_manager.start()

    try:
        yield

    finally:
        logger.info(
            "Deteniendo RoadEye mediante ServiceManager"
        )

        await close_all()
        storage_manager.stop()
        roadeye_services.stop_all()


app = FastAPI(
    title=str(
        config.get(
            "project.name",
            "RoadEye",
        )
    ),
    lifespan=lifespan,
)

app.include_router(
    api.router
)

app.mount(
    "/static",
    StaticFiles(
        directory="static"
    ),
    name="static",
)

templates = Jinja2Templates(
    directory="templates"
)


@app.get("/")
async def index(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/settings")
async def settings_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
    )


@app.get("/api/services")
async def services_status():
    return roadeye_services.summary()


class WebRTCOffer(BaseModel):
    sdp: str
    type: str


@app.post("/api/webrtc/offer")
async def webrtc_offer(
    offer: WebRTCOffer,
):
    return await create_answer(
        offer.sdp,
        offer.type,
    )


def generate():
    jpeg_quality = int(
        config.get(
            "web.jpeg_quality",
            85,
        )
    )

    jpeg_quality = max(
        1,
        min(
            100,
            jpeg_quality,
        ),
    )

    last_frame_number = -1

    while True:
        frame_number = (
            display_buffer.get_frame_number()
        )

        if frame_number == last_frame_number:
            time.sleep(
                0.005
            )
            continue

        frame = display_buffer.get_frame()

        if frame is None:
            time.sleep(
                0.01
            )
            continue

        success, jpeg = cv2.imencode(
            ".jpg",
            frame,
            [
                int(
                    cv2.IMWRITE_JPEG_QUALITY
                ),
                jpeg_quality,
            ],
        )

        if not success:
            time.sleep(
                0.005
            )
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
                "no-store, no-cache, "
                "must-revalidate, max-age=0"
            ),
            "Pragma": "no-cache",
        },
    )