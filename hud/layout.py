class Layout:

    def update(self, frame):

        h, w = frame.shape[:2]

        self.W = w
        self.H = h

        # Escala respecto a Full HD
        self.S = min(
            w / 1920.0,
            h / 1080.0
        )

        # ==========================
        # Barra superior
        # ==========================

        self.TOP_BAR = int(145 * self.S)

        self.DATE = (
            int(35 * self.S),
            int(52 * self.S)
        )

        self.REC = (
            int(45 * self.S),
            int(110 * self.S)
        )

        self.GPS = (
            int(470 * self.S),
            int(115 * self.S)
        )

        self.SPEED = (
            w // 2 - int(45 * self.S),
            int(105 * self.S)
        )

        self.SPEED_SIGN = (
            w - int(85 * self.S),
            int(85 * self.S)
        )

        # ==========================
        # Barra inferior
        # ==========================

        self.BOTTOM_BAR = int(78 * self.S)

        self.ROAD_ICON = (
            int(55 * self.S),
            h - int(45 * self.S)
        )

        self.ROAD = (
            int(95 * self.S),
            h - int(48 * self.S)
        )

        self.ROAD_INFO = (
            int(95 * self.S),
            h - int(18 * self.S)
        )

        self.SYSTEM = (
            w - int(430 * self.S),
            h - int(18 * self.S)
        )


Layout = Layout()