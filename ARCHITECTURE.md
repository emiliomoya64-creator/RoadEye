# RoadEye Architecture

## Objetivo

RoadEye es una plataforma modular de dashcam, registro de viajes,
gestión multimedia y asistencia a la conducción para Raspberry Pi.

## Módulos principales

### Recorder

Ubicación:

- `recorder/`

Responsabilidad:

- Captura de cámara.
- Grabación por segmentos.
- Metadatos.
- Miniaturas.
- Protección de grabaciones.

### Trip Manager

Ubicación:

- `trip/`

Responsabilidad:

- Agrupar segmentos en viajes.
- Guardar rutas GPS.
- Guardar eventos y fotografías.
- Estadísticas del trayecto.

### Storage Manager

Ubicación:

- `core/storage_manager.py`

Responsabilidad:

- Vigilar el SSD.
- Borrar grabaciones normales antiguas.
- Respetar grabaciones protegidas.
- Limpiar archivos huérfanos.
- Actualizar viajes afectados.

### Web API

Ubicación:

- `web/api.py`
- `web/server.py`

Responsabilidad:

- Estado del sistema.
- Control de grabación.
- Explorador multimedia.
- Viajes.
- Fotografías.
- Configuración.
- Gestión del almacenamiento.

### Frontend principal

Ubicación:

- `templates/index.html`
- `static/js/`
- `static/css/`

Responsabilidad:

- HUD.
- Explorador de vídeos.
- Explorador de viajes.
- Multimedia Center.

### Control Center

Ubicación prevista:

- `static/control-center/`

Responsabilidad:

- Ajustes de grabación.
- Gestión del almacenamiento.
- Modo Parking.
- Pantalla y sistema.

### Developer Kit

Ubicación:

- `scripts/`

Responsabilidad:

- Verificación.
- Diagnóstico.
- Instalación de módulos.
- Copias de seguridad.
- Checkpoints.

## Principios

1. Cada módulo debe tener una responsabilidad clara.
2. Los archivos protegidos nunca se eliminan automáticamente.
3. Las escrituras importantes deben ser atómicas.
4. Cada gran fase debe terminar con una verificación y un checkpoint.
5. Los instaladores deben poder repetirse sin romper la instalación.
