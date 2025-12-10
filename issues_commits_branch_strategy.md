# Organización de Issues, Convenciones de Commits y Estrategia de Ramas - Proyecto UVLHub

Este documento explica cómo se han organizado las **issues** dentro de los equipos, la estructura de **Conventional Commits** utilizada en el proyecto y la estrategia de ramas.

---

## 1. Organización de Issues - Equipo 1

El proyecto se ha organizado de manera que cada equipo tiene **2 issues obligatorias**.  
Dentro del **Equipo 1**, las issues se asignaron de la siguiente manera:

### 1.1 Issues - Equipo 1

| Issue | Título | Prioridad | Asignación | Descripción |
|-------|--------|-----------|------------|-------------|
| #104 | WI-newdataset - Evolving uvlhub into a "[datatype]hub" | MANDATORY 🟦 | Aaron | Reestructura uvlhub para soportar múltiples tipos de datasets, cada uno con su modelo propio y lógica modular. Detalle de modelos, validaciones, flujos de carga/edición y sistema de versionado extendido. |
| #105 | Add download counter for datasets | LOW 🟩 | Jesus | Permite rastrear cuántas veces se ha descargado un dataset. Se añade el campo `download_count`, se incrementa en cada descarga y se muestra en la API y detalle del dataset. Opcional: endpoint `/datasets/{id}/stats`. |
| #100 | Trending datasets | MEDIUM 🟨 | Nora & Claudia | Muestra un ranking de los datasets más vistos o descargados para destacar los populares. Se crean secciones en la home o explorador. |
| #102 | Embeddable badge | MEDIUM 🟨 | Lucía | Badge dinámico estilo shields.io con título, DOI y descargas, para insertar en GitHub o webs. (Se hizo sola por motivos de tiempo) |
| #89  | Two-factor authentication (2FA) | HIGH 🟥 | Claudia & Lucía | Permite a los usuarios habilitar un segundo factor de autenticación para mayor seguridad. |
| #98  | Automatic dataset recommendations | HIGH 🟥 | Jesus & Nora | Muestra datasets relacionados según autor, tags o comunidad, priorizando los más recientes o descargados. |

### 1.2 Prioridades de Issues

- **LOW 🟩**: Funcionalidad opcional o mejoras menores.  
- **MEDIUM 🟨**: Funcionalidad relevante, pero no crítica.  
- **HIGH 🟥**: Funcionalidad importante y necesaria.  
- **MANDATORY 🟦**: Funcionalidad obligatoria para el proyecto.

### 1.3 Organización y Asignación

- La **issue obligatoria** (#104) la realizó **Aaron**.  
- La **issue LOW** (#105) la realizó **Jesus**.  
- Las **issues MEDIUM y HIGH** se asignaron en parejas, salvo excepciones:  
  - Badge (#102) la hizo sola **Lucía**.  
  - Trending (#100) la hicieron **Nora y Claudia**.  
  - Two-factor (#89) la hicieron **Claudia y Lucía**.  
  - Recommendations (#98) la hicieron **Jesus y Nora**.  

Esta organización permite repartir responsabilidades de forma equitativa y mantener un desarrollo eficiente.

---

## 2. Convenciones de Commits

En este proyecto se sigue la convención de **Conventional Commits**, que permite mantener un historial de commits claro, estructurado y fácil de entender.  

### 2.1 Principios principales

- Cada commit comienza con un **tipo** que indica la naturaleza del cambio. Los tipos utilizados son, por ejemplo:
  - `feat` o `feature`: para nuevas funcionalidades.
  - `fix`: para correcciones de errores.
  - `chore`: tareas de mantenimiento sin impacto funcional.
  - `docs`: cambios en documentación.
  - `style`: cambios de formato, estilo o limpieza de código.
  - `refactor`: cambios que reestructuran el código sin cambiar su comportamiento.
  - `test`: para añadir o modificar pruebas.

- Después del tipo, se escribe un **mensaje descriptivo** que explique claramente qué se ha hecho.
- La convención permite incluir información adicional, como el número de la **issue** asociada.

### 2.2 Beneficios

- Mantiene un **historial de commits uniforme**, facilitando la revisión del código.  
- Permite **generar changelogs automáticamente** a partir de los commits.  
- Ayuda a entender rápidamente el **propósito de cada commit** sin necesidad de abrir el código.  
- Reduce errores al forzar mensajes claros mediante herramientas de **pre-commit** que validan el formato.

---

## 3. Estrategia de Ramas

La gestión de ramas en el proyecto se organiza de la siguiente manera:

### 3.1 Ramas principales

- **main**: rama estable que contiene el código listo para producción.  
- **trunk**: rama de desarrollo principal donde se integran las funcionalidades completadas. Cada vez que Aaron lo decida, se realiza un **merge de trunk a main**.

### 3.2 Ramas de funcionalidad

- Para desarrollar una nueva funcionalidad, se crea una **rama nueva** a partir de `trunk`.  
- Al finalizar la implementación de la funcionalidad, esta rama se mergea nuevamente en `trunk`.  
- El flujo recomendado es:
  1. Primero desarrollar la **funcionalidad principal**.  
  2. Luego agregar los **tests unitarios** correspondientes a esa funcionalidad.  

Este flujo asegura que siempre se mantenga la integridad del código en `trunk` y que las pruebas se agreguen de forma ordenada, manteniendo la calidad del proyecto.

---
