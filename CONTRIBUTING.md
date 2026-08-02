# Contribuir a RoadEye

Gracias por tu interés en colaborar con RoadEye.

RoadEye es una plataforma modular para Dashcam y ADAS basada en Raspberry Pi. Su principal objetivo es mantener una arquitectura limpia, estable y fácilmente ampliable.

Antes de realizar cualquier contribución, lee este documento y el archivo `README.md`.

---

# Principios del proyecto

Toda contribución debe respetar los principios fundamentales de RoadEye:

- Arquitectura modular.
- Una única responsabilidad por servicio.
- Configuración centralizada mediante `ConfigManager`.
- Gestión centralizada mediante `ServiceManager`.
- Un único render del HUD.
- Instalación completamente reproducible.
- Código claro y mantenible.
- Documentación actualizada.

---

# Reglas de desarrollo

## Configuración

Toda configuración persistente debe almacenarse mediante `ConfigManager`.

No deben añadirse constantes de configuración repartidas por distintos archivos.

---

## Servicios

Todo servicio nuevo debe registrarse en `ServiceManager`.

Cada servicio debe implementar, como mínimo:

```python
start()

stop()
```

Siempre que sea posible también deberá exponer su estado de funcionamiento.

---

## Procesamiento de imágenes

El flujo principal de vídeo debe mantenerse:

```text
CameraService
      ↓
FrameBuffer
      ↓
RenderService
      ↓
DisplayBuffer
      ↓
Web / HDMI / Grabación
```

El HUD solo debe renderizarse una vez.

No deben duplicarse imágenes ni realizarse renderizados innecesarios.

---

## Instalación

Si una nueva funcionalidad requiere dependencias adicionales deberán actualizarse:

```text
requirements.txt

install/install_dependencies.sh

install/install_python.sh

install/configure_pi.sh

install/install.sh
```

Una funcionalidad no se considera terminada hasta que pueda instalarse correctamente desde una Raspberry Pi completamente nueva.

---

## RoadEye Doctor

Toda funcionalidad importante deberá añadir, cuando corresponda, una comprobación en RoadEye Doctor.

El objetivo es que cualquier problema pueda diagnosticarse automáticamente.

---

# Calidad del código

Se recomienda:

- utilizar nombres descriptivos;
- evitar código duplicado;
- mantener funciones pequeñas;
- separar responsabilidades;
- documentar el código importante;
- gestionar correctamente las excepciones.

No deben utilizarse bloques como:

```python
except Exception:
    pass
```

salvo que exista una justificación técnica clara.

---

# Documentación

Toda modificación importante deberá reflejarse en:

- README.md
- CHANGELOG.md
- documentación correspondiente

La documentación forma parte del proyecto y debe mantenerse actualizada.

---

# Commits

Los mensajes de commit deben ser claros.

Ejemplos:

```text
RoadEye: añadir RecorderService

RoadEye: mejorar RoadEye Doctor

RoadEye v0.6.0: grabación circular
```

Evitar mensajes como:

```text
cambios

arreglo

prueba
```

---

# Versiones

RoadEye utiliza versionado semántico:

```text
MAJOR.MINOR.PATCH
```

Ejemplos:

```text
0.5.0

0.5.1

0.6.0

1.0.0
```

Cada versión estable debe incluir:

- código funcional;
- documentación actualizada;
- instalador actualizado;
- RoadEye Doctor actualizado;
- entrada correspondiente en CHANGELOG;
- etiqueta Git.

---

# Pruebas recomendadas

Antes de enviar un cambio se recomienda comprobar:

```bash
roadeye doctor
```

```bash
sudo systemctl restart roadeye.service
```

y verificar:

- Streaming Web.
- Salida HDMI.
- GPS.
- Grabación.
- Estado de los servicios.

---

# Licencia

Al contribuir a RoadEye aceptas que tu código pase a formar parte del proyecto bajo la licencia GPL v3.

Consulta el archivo `LICENSE` para obtener más información.
