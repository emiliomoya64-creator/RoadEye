from core.logger import info


class CameraManager:

    def __init__(self):

        self.cameras = {}


    def add_camera(self, camera):

        self.cameras[camera.name] = camera

        info(f"Cámara registrada: {camera.name}")


    def start_all(self):

        for camera in self.cameras.values():

            info(f"Iniciando {camera.name}")

            camera.start()


    def stop_all(self):

        for camera in self.cameras.values():

            camera.stop()


    def get(self, name):

        return self.cameras.get(name)


    def get_frame(self, name):

        camera = self.get(name)

        if camera:

            return camera.get_frame()

        return None


    def list(self):

        return list(self.cameras.keys())

