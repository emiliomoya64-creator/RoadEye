# RoadEye - Historial de versiones

Este documento recoge todos los cambios importantes realizados en el proyecto RoadEye.

---

# 0.5.0-dev
Estado: En desarrollo

## Arquitectura

- Nuevo ConfigManager centralizado.
- Configuración almacenada en `config/config.json`.
- Archivo `VERSION` incorporado al proyecto.
- CameraService migrado al ConfigManager.
- Nuevo sistema de escritura atómica de configuración.
- Copias automáticas de seguridad (`config.json.backup`).

## Infraestructura

- RoadEye Doctor.
- Auditoría automática del sistema.
- Primeros scripts de instalación.

## Render

- RenderService.
- DisplayBuffer.
- Salida HDMI compartida.
- Streaming Web compartido.

## HUD

- HUD modular mediante widgets.
- Widget REC.
- Widget GPS.
- Widget Speed.
- Widget Road.
- Widget System.

## Hardware

- Raspberry Pi 4.
- Raspberry Pi Camera IMX219.
- HDMI funcionando.
- GPS funcionando.

---

# 0.4.0

## Render

- Primer RenderService.
- Primer DisplayBuffer.
- Salida simultánea Web + HDMI.

---

# 0.3.0

## HUD

- Primer HUD modular.

---

# 0.2.0

## Streaming

- FastAPI.
- Streaming MJPEG.

---

# 0.1.0

## Inicio del proyecto

- Captura de cámara.
- Picamera2.
- Primer HUD.
