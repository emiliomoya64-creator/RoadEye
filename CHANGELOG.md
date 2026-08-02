# RoadEye - Historial de versiones

Este documento recoge todos los cambios importantes realizados en el proyecto RoadEye.

# 0.5.1-dev

Estado: En desarrollo  
Fecha de inicio: 2026-08-02

## Arranque

- Nuevo RoadEye BootManager.
- Pantalla de inicio en HDMI.
- Comprobaciones rápidas durante el arranque.
- Estados visuales: espera, iniciando, OK, aviso y error.
- StartupService integrado en ServiceManager.
- HDMI inicia antes que la cámara para mostrar la pantalla inicial.
- Transición automática desde BootManager hasta cámara y HUD.
- Estado del arranque disponible en `/api/services`.

## Comprobaciones de arranque

- Configuración.
- Almacenamiento.
- Cámara IMX219.
- GPS.
- HDMI.
- Red.
- Versión de RoadEye.

---

# 0.5.0

Estado: Estable  
Fecha: 2026-08-02

## Arquitectura

- Nuevo ConfigManager centralizado.
- Configuración almacenada en `config/config.json`.
- Archivo `VERSION` incorporado al proyecto.
- CameraService migrado al ConfigManager.
- GPSService migrado al ConfigManager.
- MapService migrado al ConfigManager.
- RecorderService migrado al ConfigManager.
- Nuevo sistema de escritura atómica de configuración.
- Copias automáticas de seguridad mediante `config.json.backup`.
- Nuevo ServiceManager para controlar los servicios principales.
- Orden centralizado de arranque y parada.
- Gestión diferenciada de servicios críticos y no críticos.
- Endpoint `/api/services` para consultar el estado interno.

## Servicios gestionados

- CameraService.
- GPSService.
- MapService.
- RenderService.
- HDMIDisplayService.
- RecorderService.

## Infraestructura

- RoadEye Doctor.
- Auditoría automática del sistema.
- Archivo limpio de dependencias Python `requirements.txt`.
- Instalación automática de dependencias APT.
- Creación automática del entorno virtual Python.
- Configuración automática de Raspberry Pi.
- Configuración de cámara IMX219.
- Configuración de DRM/KMS.
- Configuración de HDMI.
- Configuración de UART para GPS.
- Configuración de permisos de usuario.
- Instalación automática de `roadeye.service`.
- Comando global `roadeye`.
- Instalador maestro `install/install.sh`.

## Render

- RenderService centralizado.
- DisplayBuffer compartido.
- El HUD se renderiza una sola vez.
- Streaming web y HDMI comparten el mismo frame final.
- Salida HDMI mediante GStreamer nativo.
- Uso de `appsrc` y `kmssink`.
- Reintento automático de la salida HDMI.

## Web

- Streaming MJPEG mediante FastAPI.
- HUD visible simultáneamente en web y HDMI.
- Endpoint `/api/status`.
- Endpoint `/api/services`.
- Control de grabación mediante API.
- Configuración de calidad JPEG desde `config.json`.

## Grabación

- RecorderService integrado en ServiceManager.
- Separación entre servicio activo y grabación activa.
- El servicio del grabador permanece preparado sin grabar.
- Inicio de grabación mediante `/api/record/start`.
- Parada de grabación mediante `/api/record/stop`.
- Consulta mediante `/api/record/status`.
- Grabación segmentada en archivos MP4.
- Carpeta, FPS y duración de segmentos configurables.
- Cierre correcto de los archivos de vídeo.
- Corrección de la creación de segmentos residuales al detener la grabación.
- Estado de grabación compartido con el HUD y la API.

## HUD

- HUD modular mediante widgets.
- Widget REC.
- Contador del tiempo de grabación.
- Estado LISTO cuando no se está grabando.
- Widget GPS.
- Widget Speed.
- Widget Road.
- Widget System.
- HUD compartido entre web y HDMI.

## Hardware

- Raspberry Pi 4.
- Raspberry Pi Camera IMX219.
- Captura mediante Picamera2.
- Monitor HDMI mediante DRM/KMS.
- GPS mediante `/dev/serial0`.
- SSD para sistema y grabaciones.

## Diagnóstico

- Comprobación del sistema operativo.
- Comprobación del modelo Raspberry Pi.
- Comprobación del almacenamiento.
- Comprobación de Git y versión.
- Comprobación del entorno virtual.
- Comprobación de dependencias Python.
- Comprobación de cámara.
- Comprobación de GStreamer.
- Comprobación de HDMI.
- Comprobación de GPS.
- Comprobación de `roadeye.service`.
- Comprobación del servidor web.
- Comprobación de temperatura.
- Comprobación de alimentación y throttling.

---

# 0.4.0

## Render

- Primer RenderService.
- Primer DisplayBuffer.
- Salida simultánea Web + HDMI.
- HUD compartido entre ambos destinos.

---

# 0.3.0

## HUD

- Primer HUD modular.
- Separación del HUD en widgets independientes.

---

# 0.2.0

## Streaming

- FastAPI.
- Streaming MJPEG.
- Primera interfaz web.

---

# 0.1.0

## Inicio del proyecto

- Captura de cámara.
- Picamera2.
- Primer HUD.
- Primera estructura modular.
