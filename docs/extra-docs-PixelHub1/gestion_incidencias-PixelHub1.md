# Gestión de Incidencias

Este documento describe el flujo estándar para gestionar incidencias dentro del proyecto, incluyendo su creación, planificación, ejecución y cierre.

---

## 1. Creación de una nueva incidencia (Issue)
1. Acceder al repositorio en GitHub.
2. Ir a la pestaña **Issues**.
3. Hacer clic en **New Issue**.
4. Se mostrarán varios *templates* disponibles:
   - **Bug Report** — Reportar un error.
   - **Feature Request** — Sugerir una nueva funcionalidad.
   - **Report to help us improve** — Mejoras generales.
   - **Blank Issue** — Crear una incidencia desde cero.
5. Para nuestro flujo, seleccionamos **Blank Issue**.
6. Completar los siguientes campos:
   - **Título** claro y conciso.
   - **Descripción** detallada del problema o tarea.
   - **Assignees (Asignados)**: persona(s) responsable(s).
   - **Labels (Etiquetas)** según dificultad, tipo o prioridad.
   - **Tipo de incidencia**: `bug`, `feature`, `task`.
7. Crear la issue haciendo clic en **Submit new issue**.

---

## 2. Organización inicial en Projects
1. Ir a la pestaña **Projects** del repositorio.
2. Localizar la incidencia recién creada.
3. Mover la tarjeta a la columna **Ready**, indicando que está lista para comenzar a trabajar.

---

## 3. Análisis del alcance y división en subtareas
1. Revisar el alcance completo de la incidencia.
2. Dividir la incidencia en **subtareas** cuando sea necesario.
3. Según el alcance, asignar subtareas a una o varias personas.
4. **Cada persona asignada debe crear una nueva issue** para su subtarea siguiendo el mismo procedimiento anterior.
5. Todas las subtareas se deben mover a la columna **Ready** en Projects.

---

## 4. Desarrollo de subtareas
1. Cada desarrollador crea una **rama local** para su subtarea.
2. En Projects, mover la tarjeta de subtarea a la columna **In Progress** para indicar que está en desarrollo.
3. Desarrollar la funcionalidad o corrección correspondiente.
4. Completar y verificar que funciona correctamente a nivel individual.
5. Hacer push de los cambios y preparar la rama para merge.

---

## 5. Integración en la rama general de la incidencia
1. Cada subtarea se mergea en una **rama general** correspondiente a la incidencia principal.
2. Una vez que todas las subtareas estén integradas:
   - Mover la tarjeta general a **In Review**.
   - Verificar funcionamiento completo de la incidencia.
   - Ejecutar los tests.
   - Añadir nuevos tests si fuese necesario.

---

## 6. Integración en trunk y main
1. Tras pasar las pruebas en la rama general, hacer merge a **trunk**.
2. Verificar nuevamente que todo funciona correctamente.
3. Cuando el responsable/jefe lo indique, ejecutar el merge final de **trunk → main**.

---

## 7. Cierre de incidencia
1. Confirmar que la funcionalidad está en producción o lista para entrega.
2. Marcar la issue principal como **Closed**.
3. Cerrar también las issues correspondientes a las subtareas.

---

## Buenas prácticas
- Mantener descripciones claras y detalladas.
- Asegurar que cada issue tenga su responsable.
- Actualizar el estado de las tarjetas conforme avanza el trabajo.
- Mantener ramas cortas y específicas.
- Realizar revisiones antes de cada merge.

---

Fin del documento.

