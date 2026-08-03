import uvicorn

from hud.icon_manager import icons


from web.server import app

if __name__ == "__main__":

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=8000

    )
