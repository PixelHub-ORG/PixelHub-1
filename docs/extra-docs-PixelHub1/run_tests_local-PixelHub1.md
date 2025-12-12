# Ejecución de Tests - Proyecto UVLHub

Este documento describe cómo ejecutar los distintos tipos de tests del proyecto UVLHub en los diferentes entornos.

---

## 1. Tests Unitarios

Los **tests unitarios** utilizan **Rosemary Test**.

### Requisitos

- Tener la aplicación corriendo localmente.
- Tener instalado `rosemary`.

### Comando

```bash
rosemary test
```

> Esto ejecutará todos los tests unitarios del proyecto.

---

## 2. Tests de Performance (Locust)

Los **tests de carga** utilizan **Rosemary Locust**.

### Requisitos

- La aplicación debe estar encendida y accesible.
- Tener instalado `rosemary` y `locust`.
- Para pararlo hay q ejecutar rosemary locust:stop

### Comando

```bash
rosemary locust
```

> Esto iniciará las pruebas de carga usando Locust.

---

## 3. Tests Selenium

Los **tests de Selenium** permiten comprobar la interacción de la aplicación en un navegador real.

### Requisitos

- Tener la aplicación corriendo localmente.
- Tener instalado `pytest` y Selenium.
- Establecer el `PYTHONPATH` del proyecto.

### Comandos

1. Configurar el `PYTHONPATH`:

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
```

2. Ejecutar un test Selenium específico:

```bash
pytest --noconftest app/modules/name_modules/tests/test_selenium/test.py
```

> ⚠️ Nota: Se usa `--noconftest` para ignorar cualquier `conftest.py` global y ejecutar el test de manera aislada.  
> Asegúrate de que los drivers de Selenium (por ejemplo, ChromeDriver) estén correctamente instalados y accesibles.

---

## 4. Resumen

| Tipo de Test | Herramienta | Comando | Requisito clave |
|-------------|------------|---------|----------------|
| Unitario | Rosemary Test | `rosemary test` | Aplicación corriendo |
| Carga | Rosemary Locust | `rosemary locust` | Aplicación corriendo |
| Selenium | pytest + Selenium | `export PYTHONPATH=$(pwd):$PYTHONPATH && pytest --noconftest <test_file>` | Aplicación corriendo, drivers instalados |

