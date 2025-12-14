#### Entorno de desarrollo: tecnologías y herramientas utilizadas

En este apartado se describen las tecnologías y herramientas que han conformado el entorno de desarrollo utilizado por el equipo durante la realización del proyecto. El objetivo principal ha sido trabajar con herramientas comunes, estables y bien soportadas, que faciliten el desarrollo colaborativo y la integración continua del sistema.

##### Sistema operativo

El desarrollo del proyecto se ha realizado en entornos heterogéneos:

- **Ubuntu Linux** ha sido el sistema operativo principal, utilizado por 4 de los 5 miembros del equipo.
- **macOS** ha sido utilizado por 1 miembro del equipo.

Aunque la mayoría del desarrollo se ha llevado a cabo sobre Ubuntu, se ha tenido en cuenta la compatibilidad con macOS. En este caso concreto, fue necesario realizar pequeños ajustes en rutas y scripts para permitir la correcta ejecución del sistema y de los tests en local, manteniendo estos cambios aislados del flujo principal de desarrollo.

##### Lenguajes utilizados

El sistema ha sido desarrollado utilizando los siguientes lenguajes:

- **Python 3.11.7** como lenguaje principal para la implementación de la lógica de la aplicación.
- **SQL** para la gestión y consulta de la base de datos.

Python ha sido el eje central del proyecto, utilizándose tanto para la lógica de negocio como para la integración con la base de datos y otros subsistemas del sistema.

##### Entorno de desarrollo integrado (IDE)

Como entorno de desarrollo integrado se ha utilizado **Visual Studio Code**. Este IDE ha sido elegido por su amplio soporte para Python, su integración con Git y GitHub, y la posibilidad de ampliación mediante extensiones. Su uso ha permitido una experiencia de desarrollo homogénea entre los miembros del equipo, independientemente del sistema operativo utilizado.

##### Control de versiones e integración continua

El control de versiones del proyecto se ha gestionado mediante **Git**, utilizando **GitHub** como repositorio remoto central. GitHub ha permitido coordinar el trabajo del equipo, mantener un historial claro de cambios y facilitar la integración continua del sistema.

Para la automatización de procesos se han utilizado **GitHub Actions**, definiendo distintos _workflows_ en función del tipo de tarea a ejecutar. Entre los aspectos más relevantes se incluyen:

- Ejecución automática de **tests con pytest**, integrados directamente en GitHub Actions.
- Verificación del estilo y calidad del código mediante **linting**, utilizando las herramientas **flake8**, **black** y **rosemary linter**.
- Diferentes _workflows_ en función de la rama, por ejemplo:
  - Ejecución de análisis de calidad (como SonarQube) en _push_ a la rama `main`.
  - Ejecución de linting en cualquier _push_, independientemente de la rama.

Además, se han implementado **hooks de Git** para reforzar estas comprobaciones en local, obligando a cumplir los criterios de linting antes de permitir ciertos commits. Esto ha contribuido a mantener una base de código consistente y alineada con buenas prácticas desde las primeras fases del desarrollo.

##### Base de datos

El sistema utiliza **MariaDB 12.0.2** como sistema de gestión de bases de datos relacional. MariaDB se ha empleado para almacenar de forma persistente la información del sistema, incluyendo usuarios, datasets y registros asociados a descargas y visualizaciones.

El uso de SQL ha permitido estructurar claramente los datos y realizar consultas eficientes, facilitando tanto el desarrollo como el mantenimiento del sistema.

##### Testing y validación

Para garantizar la calidad del software, se han utilizado distintas herramientas de testing, cada una orientada a un tipo concreto de validación:

- **Pytest**, integrado en GitHub Actions, para la ejecución de pruebas unitarias.
- **Tests unitarios**, centrados en validar el correcto funcionamiento de componentes individuales del sistema.
- **Selenium**, utilizado en local para pruebas funcionales y de interfaz, simulando la interacción de usuarios con la aplicación.
- **Locust**, empleado en local para pruebas de carga, permitiendo evaluar el comportamiento del sistema bajo escenarios de uso intensivo.

La combinación de estas herramientas ha permitido validar tanto la lógica interna del sistema como su comportamiento desde el punto de vista del usuario final, contribuyendo a un desarrollo más robusto y fiable.

#### Instalación, ejecución y despliegue

### Despliegue

##### Uso del sistema con Docker

Si prefieres ejecutar **PixelHub** en un entorno aislado sin instalar dependencias manualmente, hemos preparado una configuración lista para producción utilizando Docker.

### Requisitos previos

- Tener instalado [Docker Desktop](https://www.docker.com/products/docker-desktop/) (o Docker Engine + Docker Compose).

### Guía paso a paso

**1. Configuración del entorno**
El sistema necesita ciertas variables de entorno para funcionar (credenciales de base de datos, claves secretas, etc.). Para empezar rápidamente, copia la plantilla de producción proporcionada:

```bash
cp .env.docker.production.example .env
```

**2. Ejecución del sistema**
Descarga la última versión de la imagen oficial y levanta los servicios en segundo plano con un solo comando. Asegúrate de ejecutarlo desde la raíz del proyecto:

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

> **Nota:** La primera vez puede tardar unos minutos mientras se descargan las imágenes de `claovigov/pixelhub`, MariaDB y Nginx.

**3. Acceso a la aplicación**
Una vez que los contenedores estén listos, abre tu navegador y accede a:

**http://localhost**

---

### Comandos útiles

**Verificar el estado de los contenedores:**
Si algo no funciona, puedes consultar los logs en tiempo real:

```bash
docker compose -f docker/docker-compose.prod.yml logs -f
```

**Detener el sistema:**
Para apagar los servicios y liberar recursos:

```bash
docker compose -f docker/docker-compose.prod.yml down
```
