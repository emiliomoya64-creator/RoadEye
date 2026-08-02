# RoadEye

> **Professional Dashcam & ADAS Platform for Raspberry Pi**

**Modular • Reproducible • Extensible • Open Source**

---

# Versión

**Versión estable:** **v0.5.0**

---

# ¿Qué es RoadEye?

RoadEye es una plataforma modular desarrollada para Raspberry Pi cuyo objetivo es evolucionar desde una dashcam de altas prestaciones hasta un sistema completo de asistencia avanzada a la conducción (ADAS).

No está diseñado como una simple aplicación, sino como una plataforma de software donde cada componente funciona de forma independiente y puede evolucionar sin afectar al resto del sistema.

La captura de vídeo, el renderizado del HUD, la grabación, la salida HDMI, el streaming web, el GPS, la configuración y la gestión de servicios forman parte de una arquitectura modular diseñada para ser robusta, mantenible y fácilmente ampliable.

El proyecto está orientado tanto al aprendizaje como al desarrollo de una dashcam profesional basada en Raspberry Pi.

---

# Objetivos del proyecto

RoadEye se desarrolla siguiendo cinco objetivos fundamentales.

## 🎥 Dashcam profesional

- Grabación de vídeo de alta calidad.
- Grabación segmentada.
- Preparado para grabación circular.
- Preparado para protección de eventos.
- Máxima estabilidad.

---

## 🚗 Plataforma preparada para ADAS

La arquitectura está preparada para incorporar progresivamente:

- Detección de carriles.
- Detección de vehículos.
- Detección de peatones.
- Reconocimiento de señales.
- Avisos inteligentes.
- Integración con sensores del vehículo.

---

## 🧩 Arquitectura modular

Cada componente funciona como un servicio independiente.

Esto facilita:

- mantenimiento;
- depuración;
- ampliación del proyecto;
- reutilización del código.

---

## 🔄 Instalación completamente reproducible

Una Raspberry Pi completamente nueva debe poder quedar preparada ejecutando únicamente:

```bash
git clone https://github.com/emiliomoya64-creator/RoadEye.git PiDash

cd PiDash

sudo ./install/install.sh

sudo reboot
```

Sin necesidad de realizar configuraciones manuales posteriores.

---

## 🛠️ Mantenimiento a largo plazo

RoadEye prioriza:

- código limpio;
- estabilidad;
- documentación;
- facilidad de mantenimiento;
- evolución continua.

La infraestructura tiene prioridad sobre añadir nuevas funcionalidades.

---

# Estado actual del proyecto

| Componente | Estado |
|------------|:------:|
| Cámara IMX219 | ✅ |
| Streaming Web | ✅ |
| Salida HDMI | ✅ |
| GPS | ✅ |
| HUD | ✅ |
| Grabación MP4 | ✅ |
| ConfigManager | ✅ |
| ServiceManager | ✅ |
| RoadEye Doctor | ✅ |
| Instalador automático | ✅ |
| API REST | ✅ |
| ADAS | 🚧 En desarrollo |

---

© RoadEye Project

# Filosofía del proyecto

RoadEye no pretende ser únicamente una aplicación para Raspberry Pi.

Su objetivo es convertirse en una plataforma profesional para el desarrollo de una dashcam y un sistema avanzado de asistencia a la conducción (ADAS).

Todas las decisiones de diseño del proyecto siguen una serie de principios que garantizan la estabilidad, la mantenibilidad y la capacidad de evolución del sistema.

Estos principios tienen prioridad sobre la incorporación de nuevas funcionalidades.

---

# Principios de diseño

## 1. Un único punto de configuración

Toda la configuración del sistema debe almacenarse mediante **ConfigManager**.

No debe existir configuración duplicada en distintos módulos.

---

## 2. Un único gestor de servicios

Todos los servicios deben ser administrados por **ServiceManager**.

Esto garantiza un arranque, parada y supervisión homogéneos para todo el sistema.

---

## 3. Una única responsabilidad por servicio

Cada servicio debe realizar únicamente una función.

Ejemplos:

- CameraService captura imágenes.
- GPSService obtiene la posición.
- RenderService dibuja el HUD.
- HDMIDisplayService muestra la imagen.
- RecorderService graba vídeo.

Nunca deben mezclarse responsabilidades.

---

## 4. Un único render del HUD

El HUD solo debe renderizarse una vez.

La imagen final será compartida por:

- HDMI
- Streaming Web
- Grabación

De esta forma se evita duplicar trabajo y se garantiza que todas las salidas muestran exactamente la misma información.

---

## 5. Un único DisplayBuffer

Todo el sistema trabaja sobre un único DisplayBuffer.

Ningún servicio debe volver a renderizar una imagen ya procesada.

---

## 6. Arquitectura modular

Cada componente debe poder sustituirse sin afectar al resto del sistema.

Por ejemplo:

- cambiar la cámara;
- cambiar el sistema de grabación;
- añadir nuevos sensores;
- incorporar nuevos módulos ADAS.

---

## 7. Instalación reproducible

Una Raspberry Pi completamente nueva debe poder configurarse ejecutando únicamente:

```bash
sudo ./install/install.sh
```

No deben existir pasos manuales ocultos.

Toda la configuración debe formar parte del propio proyecto.

---

## 8. Diagnóstico integrado

Todo componente importante debe poder comprobarse mediante **RoadEye Doctor**.

Cuando se añada una nueva funcionalidad importante, deberá añadirse también su correspondiente comprobación al sistema de diagnóstico.

---

## 9. Versiones recuperables

Cada versión estable debe quedar identificada mediante una etiqueta (Git Tag).

En cualquier momento debe ser posible recuperar exactamente una versión anterior del proyecto.

---

## 10. Código mantenible

La claridad del código tiene prioridad sobre soluciones complejas.

Se prioriza:

- simplicidad;
- legibilidad;
- modularidad;
- documentación.

El objetivo es que cualquier desarrollador pueda comprender el funcionamiento del proyecto incluso años después de haber sido escrito.

---

# Filosofía de desarrollo

RoadEye crecerá de forma incremental.

Antes de añadir nuevas funcionalidades siempre se consolidará la infraestructura existente.

Cada versión estable debe ser:

- funcional;
- documentada;
- instalable desde cero;
- fácilmente recuperable;
- mantenible a largo plazo.

La estabilidad siempre tendrá prioridad sobre la velocidad de desarrollo.

# Arquitectura del sistema

RoadEye está organizado como un conjunto de servicios independientes coordinados por un núcleo común.

Cada servicio tiene una única responsabilidad y se comunica con el resto mediante componentes compartidos cuidadosamente definidos.

La siguiente figura resume la arquitectura general.

```text
                         Raspberry Pi 4
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                           │
          ▼                                           ▼
   IMX219 Camera                               GPS Receiver
          │                                           │
          └─────────────────────┬─────────────────────┘
                                ▼
                        CameraService
                                │
                                ▼
                         FrameBuffer
                                │
                                ▼
                        RenderService
                                │
                                ▼
                        DisplayBuffer
                                │
        ┌───────────────────────┼────────────────────────┐
        ▼                       ▼                        ▼
 HDMIDisplayService      Web Streaming          RecorderService
        │                       │                        │
        ▼                       ▼                        ▼
 Monitor HDMI             Navegador Web           Archivos MP4
```

---

# Núcleo del sistema

El núcleo de RoadEye está formado por dos componentes fundamentales.

## ConfigManager

ConfigManager es la única fuente de configuración del sistema.

Toda la configuración persistente se almacena en:

```text
config/config.json
```

Ningún servicio mantiene su propia configuración independiente.

Esto garantiza que toda la aplicación trabaja siempre con los mismos parámetros.

---

## ServiceManager

ServiceManager es el encargado de gestionar todos los servicios del sistema.

Sus responsabilidades son:

- registrar servicios;
- arrancarlos;
- detenerlos;
- supervisar su estado;
- informar a la API REST;
- reiniciar servicios cuando sea necesario.

Todos los servicios importantes del proyecto pasan por ServiceManager.

---

# Servicios actuales

Actualmente RoadEye dispone de los siguientes servicios.

| Servicio | Función |
|----------|---------|
| CameraService | Captura imágenes desde la cámara IMX219 |
| GPSService | Obtiene la posición GPS |
| MapService | Obtiene información cartográfica |
| RenderService | Genera el HUD |
| HDMIDisplayService | Envía la imagen al monitor HDMI |
| RecorderService | Graba vídeo en formato MP4 |

---

# Flujo interno de imágenes

Uno de los principios fundamentales de RoadEye es evitar duplicar trabajo.

El recorrido que sigue cada imagen es el siguiente.

```text
IMX219

↓

Picamera2

↓

CameraService

↓

FrameBuffer

↓

RenderService

↓

DisplayBuffer

↓

───────────────┬────────────────────┬──────────────────

               ▼                    ▼

      HDMI Display          Streaming Web

                                    ▼

                             RecorderService

                                    ▼

                                Vídeo MP4
```

Gracias a esta arquitectura:

- el HUD se dibuja una sola vez;
- Web, HDMI y Grabación muestran exactamente la misma imagen;
- el consumo de CPU se reduce considerablemente;
- es mucho más sencillo añadir nuevas salidas en el futuro.

---

# Organización del proyecto

La estructura principal del proyecto es la siguiente.

```text
PiDash/
│
├── cameras/        Captura de imágenes
├── config/         Configuración persistente
├── core/           Núcleo del sistema
├── display/        Salida HDMI
├── gps/            GPS y cartografía
├── install/        Instalador y herramientas
├── recorder/       Grabación de vídeo
├── templates/      Plantillas HTML
├── videos/         Grabaciones
├── web/            API REST e interfaz web
│
├── app.py          Punto de entrada
├── VERSION         Versión instalada
├── CHANGELOG.md    Historial del proyecto
├── README.md       Documentación principal
└── requirements.txt
```

# Hardware soportado

RoadEye ha sido desarrollado y probado sobre la siguiente plataforma.

| Componente | Estado |
|------------|:------:|
| Raspberry Pi 4 Model B | ✅ |
| Raspberry Pi OS / Debian 12 Bookworm (64 bits) | ✅ |
| Cámara Raspberry Pi IMX219 | ✅ |
| SSD USB | ✅ |
| Monitor HDMI | ✅ |
| GPS UART (/dev/serial0) | ✅ |

---

## Hardware recomendado

Para obtener el mejor rendimiento se recomienda:

- Raspberry Pi 4 Model B (4 GB u 8 GB).
- Fuente de alimentación oficial Raspberry Pi USB-C.
- SSD USB 3.0 para el sistema y las grabaciones.
- Cámara Raspberry Pi IMX219.
- Receptor GPS compatible con NMEA.
- Disipador o ventilador para mantener una temperatura estable.

---

# Software utilizado

RoadEye utiliza exclusivamente software libre y ampliamente soportado.

| Software | Función |
|----------|---------|
| Python | Lenguaje principal |
| Picamera2 | Captura de vídeo |
| OpenCV | Procesamiento de imagen |
| NumPy | Operaciones matriciales |
| FastAPI | Servidor Web |
| Uvicorn | Servidor ASGI |
| GStreamer | Streaming y HDMI |
| libcamera | Acceso a la cámara |
| systemd | Servicio del sistema |
| Git | Control de versiones |

---

# Instalación

Una Raspberry Pi completamente nueva puede prepararse ejecutando un único comando.

```bash
git clone https://github.com/emiliomoya64-creator/RoadEye.git PiDash

cd PiDash

sudo ./install/install.sh

sudo reboot
```

---

## ¿Qué hace el instalador?

El instalador automático realiza todas las operaciones necesarias para dejar RoadEye completamente operativo.

### 1. Dependencias del sistema

- Instala Python.
- Instala Picamera2.
- Instala OpenCV.
- Instala NumPy.
- Instala GStreamer.
- Instala las herramientas DRM/KMS.
- Instala Git.

---

### 2. Configuración de Raspberry Pi

Configura automáticamente:

- Cámara IMX219.
- DRM/KMS.
- HDMI.
- UART para GPS.
- USB Host.
- Permisos del usuario.
- Configuración del arranque.

---

### 3. Entorno Python

- Crea `.venv`.
- Actualiza `pip`.
- Instala `requirements.txt`.
- Comprueba todas las dependencias.

---

### 4. Servicio del sistema

Instala automáticamente:

- `roadeye.service`

y lo deja habilitado para arrancar con la Raspberry.

---

### 5. RoadEye Doctor

Al finalizar la instalación se ejecuta RoadEye Doctor para verificar que todo el sistema funciona correctamente.

---

# Primer arranque

Después del primer reinicio basta ejecutar:

```bash
roadeye doctor
```

Si todas las comprobaciones son correctas, RoadEye estará preparado para comenzar a funcionar.

---

# Comandos de RoadEye

RoadEye instala automáticamente el comando global `roadeye`, que permite acceder rápidamente a las funciones de administración y diagnóstico.

## Diagnóstico del sistema

```bash
roadeye doctor
```

Realiza una comprobación completa del sistema:

- Sistema operativo.
- Raspberry Pi.
- Espacio disponible.
- Estado de Git.
- Entorno Python.
- Dependencias.
- Cámara.
- GStreamer.
- HDMI.
- GPS.
- Servicio RoadEye.
- Servidor Web.
- Temperatura de la CPU.
- Alimentación y posibles problemas de throttling.

---

## Estado del servicio

```bash
roadeye status
```

Muestra el estado del servicio `roadeye.service`.

---

## Reiniciar RoadEye

```bash
roadeye restart
```

Reinicia completamente RoadEye.

---

## Ver los registros

```bash
roadeye logs
```

Muestra el registro en tiempo real del servicio.

---

# API REST

RoadEye incorpora una API REST para consultar el estado del sistema y controlar distintas funciones.

## Estado general

```http
GET /api/status
```

Devuelve el estado general de RoadEye.

---

## Servicios

```http
GET /api/services
```

Devuelve el estado de todos los servicios gestionados por ServiceManager.

---

## Grabación

### Estado

```http
GET /api/record/status
```

---

### Iniciar grabación

```http
GET /api/record/start
```

---

### Detener grabación

```http
GET /api/record/stop
```

---

# Servicios actuales

Actualmente ServiceManager controla los siguientes servicios.

| Servicio | Descripción |
|----------|-------------|
| CameraService | Captura imágenes de la cámara |
| GPSService | Obtiene la posición GPS |
| MapService | Información cartográfica |
| RenderService | Genera el HUD |
| HDMIDisplayService | Salida HDMI |
| RecorderService | Grabación de vídeo |

---

# RoadEye Doctor

RoadEye Doctor forma parte del propio proyecto y constituye la principal herramienta de diagnóstico.

Su objetivo es detectar automáticamente cualquier problema de configuración o hardware antes de que afecte al funcionamiento del sistema.

Cada nueva funcionalidad importante incorporada a RoadEye deberá añadir también su correspondiente comprobación dentro de RoadEye Doctor.

De esta forma el sistema de diagnóstico evolucionará al mismo ritmo que el proyecto.

---

# Roadmap

RoadEye se desarrolla de forma incremental.

Cada versión debe consolidar la infraestructura existente antes de incorporar nuevas funcionalidades.

---

# Versión 0.5.x

## Infraestructura

Esta versión consolida la base del proyecto.

### Incluye

- ConfigManager.
- ServiceManager.
- RoadEye Doctor.
- Instalador automático.
- Configuración persistente.
- Servicio systemd.
- Salida HDMI.
- Streaming Web.
- Grabación MP4.
- GPS.
- Arquitectura modular.

Esta versión constituye la primera base estable del proyecto.

---

# Versión 0.6.x

## Dashcam profesional

Objetivos principales:

- Grabación circular.
- Protección de vídeos por eventos.
- Gestión automática del espacio en disco.
- Configuración desde la interfaz Web.
- Descarga de grabaciones.
- Visualización de grabaciones.
- Mejoras del HUD.
- Optimización del rendimiento.

---

# Versión 0.7.x

## ADAS

Comenzará el desarrollo de los sistemas avanzados de asistencia a la conducción.

Características previstas:

- Detección de carriles.
- Detección de vehículos.
- Detección de peatones.
- Reconocimiento de señales.
- Avisos visuales.
- Avisos acústicos.

---

# Versión 0.8.x

## Integración con el vehículo

Objetivos:

- OBD-II.
- IMU.
- Sensores.
- Acelerómetro.
- Eventos por impacto.
- Datos del vehículo.

---

# Versión 1.0.0

## Primera versión estable

La versión 1.0 representará la primera versión completa de RoadEye como plataforma modular para Dashcam y ADAS.

Su objetivo será ofrecer:

- alta estabilidad;
- instalación completamente reproducible;
- arquitectura modular;
- documentación completa;
- mantenimiento sencillo;
- capacidad de evolución durante muchos años.

---

# Contribuciones

RoadEye ha sido diseñado para facilitar la incorporación de nuevas funcionalidades sin modificar la arquitectura existente.

Las contribuciones deberán respetar los principios de diseño definidos en este documento.

Antes de añadir un nuevo componente se recomienda comprobar:

- que cumple una única responsabilidad;
- que puede integrarse mediante ServiceManager;
- que utiliza ConfigManager para su configuración;
- que incorpora su comprobación correspondiente en RoadEye Doctor.

---

# Historial de versiones

El historial completo de cambios se encuentra en:

```

CHANGELOG.md

```

---

# Licencia

La licencia del proyecto se añadirá en una versión posterior.

---

# Créditos

RoadEye es un proyecto desarrollado con el objetivo de crear una plataforma profesional, modular y mantenible para Dashcam y ADAS basada en Raspberry Pi.

La prioridad del proyecto es construir una base sólida sobre la que puedan añadirse nuevas capacidades sin comprometer la estabilidad del sistema.

---

# Estado actual

**Versión estable:** **v0.5.0**

✔ Instalación automática

✔ Arquitectura modular

✔ Configuración persistente

✔ Servicio automático

✔ Diagnóstico integrado

✔ Streaming Web

✔ Salida HDMI

✔ Grabación MP4

✔ Preparado para la siguiente etapa de desarrollo.

---

**RoadEye**

*Professional Dashcam & ADAS Platform for Raspberry Pi*


