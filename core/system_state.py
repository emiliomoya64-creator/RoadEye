from threading import Lock


class SystemState:

    def __init__(self):

        self.lock = Lock()

        self.recording = False

        self.gps_fix = False

        self.speed = 0.0

        self.satellites = 0

        self.cpu = 0

        self.temp = 0

        self.storage = 0

        self.front_camera = True

        self.rear_camera = False

        self.left_camera = False

        self.right_camera = False

        self.lane_departure = False

        self.forward_collision = False

    def set(self, key, value):

        with self.lock:

            setattr(self, key, value)

    def get(self, key):

        with self.lock:

            return getattr(self, key)


system_state = SystemState()