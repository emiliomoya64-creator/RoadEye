import threading
import time


class BaseCamera:

    def __init__(self, name):

        self.name = name

        self.frame = None

        self.running = False

        self.thread = None


    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.update,
            daemon=True
        )

        self.thread.start()


    def stop(self):

        self.running = False

        if self.thread:
            self.thread.join(timeout=2)


    def update(self):

        raise NotImplementedError


    def get_frame(self):

        return self.frame
