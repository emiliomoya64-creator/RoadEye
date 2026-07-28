from threading import Lock


class SystemState:

    def __init__(self):

        self.lock = Lock()

        # -------------------------
        # Grabación
        # -------------------------

        self.recording = False

        # -------------------------
        # GPS
        # -------------------------

        self.gps_fix = False
        self.satellites = 0
        self.speed = 0.0
        self.heading = "---"
        self.latitude = 0.0
        self.longitude = 0.0

        # -------------------------
        # Mapa
        # -------------------------

        self.road = "---"
        self.road_type = "---"
        self.lanes = "?"
        self.speed_limit = 0

        # -------------------------
        # Sistema
        # -------------------------

        self.cpu = 0
        self.temp = 0
        self.storage = 0

        # -------------------------
        # Cámaras
        # -------------------------

        self.front_camera = True
        self.rear_camera = False
        self.left_camera = False
        self.right_camera = False

        # -------------------------
        # ADAS
        # -------------------------

        self.lane_departure = False
        self.forward_collision = False
        self.pedestrian = False
        self.vehicle_detected = False
        self.traffic_sign = None
        self.traffic_light = None

    def set(self, key, value):

        with self.lock:
            setattr(self, key, value)

    def get(self, key):

        with self.lock:
            return getattr(self, key)


system_state = SystemState()