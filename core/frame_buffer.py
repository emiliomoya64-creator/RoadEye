from threading import Lock


class FrameBuffer:

    def __init__(self):

        self.lock = Lock()

        self.frame = None

        self.frame_number = 0

    def set_frame(self, frame):

        with self.lock:

            self.frame = frame.copy()

            self.frame_number += 1

    def get_frame(self):

        with self.lock:

            if self.frame is None:
                return None

            return self.frame.copy()

    def get_frame_number(self):

        with self.lock:

            return self.frame_number


frame_buffer = FrameBuffer()