class Layout:
    """
    Distribución adaptativa del HUD RoadEye 0.6.

    Diseño actual:

        Parte superior:
            REC, Parking, GPS, velocidad, foto,
            vídeos y límite de velocidad.

        Parte inferior:
            Calle, coordenadas, fecha, hora
            y configuración.

    En fases posteriores, estas posiciones se leerán desde
    ConfigManager para permitir personalizar el HUD.
    """

    def update(
        self,
        frame,
        info_position="bottom",
        top_bar_scale=1.0,
        info_bar_scale=1.0,
    ):
        h, w = frame.shape[:2]

        self.W = w
        self.H = h

        # Escala respecto a Full HD.
        self.S = min(
            w / 1920.0,
            h / 1080.0,
        )

        # =====================================================
        # Barra superior: acciones y estados
        # =====================================================

        top_bar_scale = max(
            0.70,
            min(
                1.60,
                float(top_bar_scale),
            ),
        )

        self.TOP_ROW_HEIGHT = max(
            38,
            int(
                82
                * self.S
                * top_bar_scale
            ),
        )

        self.TOP_ROW_Y = 0
        self.TOP_BAR = self.TOP_ROW_HEIGHT

        # =====================================================
        # Barra inferior: ubicación e información
        # =====================================================

        info_bar_scale = max(
            0.70,
            min(
                1.60,
                float(info_bar_scale),
            ),
        )

        self.INFO_ROW_HEIGHT = max(
            34,
            int(
                68
                * self.S
                * info_bar_scale
            ),
        )

        if str(info_position).lower() == "top":
            self.INFO_ROW_Y = self.TOP_ROW_HEIGHT
        else:
            self.INFO_ROW_Y = (
                self.H
                - self.INFO_ROW_HEIGHT
            )

        self.BOTTOM_BAR = self.INFO_ROW_HEIGHT

        # =====================================================
        # Márgenes generales
        # =====================================================

        self.HORIZONTAL_MARGIN = max(
            12,
            int(24 * self.S),
        )

        self.ROW_PADDING = max(
            8,
            int(14 * self.S),
        )

        # =====================================================
        # Posiciones compatibles con widgets existentes
        # =====================================================

        # REC original:
        # punto, texto REC y estado LISTO/contador.
        self.REC = (
            self.HORIZONTAL_MARGIN
            + int(12 * self.S),
            self.TOP_ROW_Y
            + self.TOP_ROW_HEIGHT // 2,
        )

        # GPS antiguo, conservado para compatibilidad.
        self.GPS = (
            int(self.W * 0.27),
            self.TOP_ROW_Y
            + self.TOP_ROW_HEIGHT // 2,
        )

        # Velocidad antigua, conservada para compatibilidad.
        self.SPEED = (
            self.W // 2,
            self.TOP_ROW_Y
            + int(self.TOP_ROW_HEIGHT * 0.66),
        )

        self.SPEED_SIGN = (
            self.W
            - self.HORIZONTAL_MARGIN
            - int(38 * self.S),
            self.TOP_ROW_Y
            + self.TOP_ROW_HEIGHT // 2,
        )

        # =====================================================
        # Barra inferior
        # =====================================================

        self.DATE = (
            self.HORIZONTAL_MARGIN,
            self.INFO_ROW_Y
            + self.INFO_ROW_HEIGHT // 2,
        )

        self.ROAD_ICON = (
            self.HORIZONTAL_MARGIN
            + int(18 * self.S),
            self.INFO_ROW_Y
            + self.INFO_ROW_HEIGHT // 2,
        )

        self.ROAD = (
            self.HORIZONTAL_MARGIN
            + int(52 * self.S),
            self.INFO_ROW_Y
            + int(self.INFO_ROW_HEIGHT * 0.47),
        )

        self.ROAD_INFO = (
            self.ROAD[0],
            self.INFO_ROW_Y
            + int(self.INFO_ROW_HEIGHT * 0.78),
        )

        self.SYSTEM = (
            self.W - int(430 * self.S),
            self.INFO_ROW_Y
            + int(self.INFO_ROW_HEIGHT * 0.72),
        )


Layout = Layout()
