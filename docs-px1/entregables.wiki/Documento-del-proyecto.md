# Documento del pixel-hub-1

## Indicadores del proyecto

La razón por la que a algunos miembros del equipo se le han asociado dos WI es porque hemos trabajado haciendo pairprogramming.

| Miembro del equipo                                                   | Horas | Commits | LoC | Test                                               | Issues | Work Item                                                                          | Dificultad     |
| -------------------------------------------------------------------- | ----- | ------- | --- | -------------------------------------------------- | ------ | ---------------------------------------------------------------------------------- | -------------- |
| [Campos Díez, Lucía](https://github.com/HHV4884)                     | 55    | XX      | YY  | Unitarios: 37, Locust:8, Selenium: 4 (total: 49)   | 6      | Two-factor authentication (2FA) (H) \#89 & Embeddable badge \#102 (M)              | M & H          |
| [Mayoral Ansias, Aaron](https://github.com/aaronma300604)            | 47    | XX      | YY  | Unitarios: 5, Locust: 1, Selenium: 1 (total: 7)    | 4      | newdataset - Evolving uvlhub into a "datatypehub" \#104                            | H              |
| [Oviedo Govantes, Claudia](https://github.com/ClaudiaOviedoGovantes) | 65    | XX      | YY  | Unitarios: 27, Locust: 20, Selenium: 1 (total: 48) | 13     | Trending datasets \#100 (M) & Two-factor authentication (2FA) (H)                  | M & H          |
| [Peñaloza Friqui, Nora](https://github.com/norapfr)                  | 52    | XX      | YY  | Unitarios: 10, Locust:13, Selenium:1 (total: 24)   | 12     | Trending datasets \#100 (M) & Automatic dataset recommendations \#98 (H)           | M & H          |
| [Sánchez Quirós, Jesús](https://github.com/JesusSQ)                  | 53    | XX      | YY  | Unitarios: 7, Locust: 7, Selenium: 1 (total: 15)   | 7      | Add download counter for datasets (L) & Automatic dataset recommendations \#98 (H) | L & H          |
| **TOTAL**                                                            | 272   | tXX     | tYY | 143                                                | tII    | Descripción breve                                                                  | H(2)/M(2)/L(1) |

Las evidencias de las horas trabajadas se encuentran en la carpeta `clockify`, que contiene los reports de Clockify de todos los miembros del equipo.

Este es nuestro repositorio: [PixelHub-1](https://github.com/PixelHub-ORG/PixelHub-1)

La tabla contiene la información de cada miembro del proyecto y el total de la siguiente forma:

- Horas: número de horas empleadas en el proyecto
- Commits: solo contar los commits hechos por miembros del equipo, no lo commits previos
- LoC (líneas de código): solo contar las líneas producidas por el equipo y no las que ya existían o las que se producen al incluir código de terceros
- Test: solo contar los test realizados por el equipo nuevos
- Issues: solo contar las issues gestionadas dentro del proyecto y que hayan sido gestionadas por el equipo
- Work Item: principal WI del que se ha hecho cargo el miembro del proyecto
- Dificultad: señalar el grado de dificultad en cada caso. Además, en los totales, poner cuántos se han hecho de cada grado de dificultad entre paréntesis.

## Integración con otros equipos

- [Equipo con el que nos integramos - PixelHub-2](https://github.com/PixelHub-ORG/PixelHub-2): Hemos hecho integración con este grupo para tener un alcance más amplio para nuestro proyecto y queremos optar a la nota máxima.
- [Repositorio conjunto - PixelHub-X](https://github.com/PixelHub-ORG/PixelHub-X): Este es el repositorio en el que se muestra el proyecto final una vez realizada la integración.

## Resumen Ejecutivo

El presente trabajo describe el desarrollo y mejoras implementadas en un proyecto orientado a optimizar [UVLHUB](https://github.com/PixelHub-ORG/UVLHub) un repositorio de feature models en formato UVL. A lo largo del proceso, nos hemos centrado en mejorar la funcionalidad, eficiencia y experiencia del usuario, adoptando mejores prácticas en cuanto a organización, herramientas y metodologías para el desarrollo del software.

### Evolución y Cambios en el Proyecto

En el transcurso del proyecto, hemos realizado varias mejoras clave. Nos hemos enfocado en la implementación de funcionalidades nuevas y la corrección de errores críticos. Entre los cambios más relevantes, destacan los siguientes:

1. **Autenticación en dos factores (2FA):** Esta funcionalidad permite una capa adicional de seguridad para los usuarios, mejorando la protección de sus cuentas.
2. **Datos populares y recomendados:** Implementamos un sistema de clasificación de los datasets más populares, basándonos en las descargas, ya sean semanales o mensuales. También añadimos recomendaciones automáticas de datasets relacionados, lo que mejora la experiencia de descubrimiento para los usuarios.
3. **Mejoras en la interfaz de usuario:** Se desarrolló un "badge" embebible para los datasets, lo que permite que los usuarios compartan fácilmente sus datasets en otras plataformas. Además, se añadió un contador de descargas para cada dataset, lo que brinda más información sobre su popularidad.

### Entorno Tecnológico

Nuestro equipo ha utilizado un conjunto de herramientas estándar para facilitar el desarrollo y la colaboración. Entre las más destacadas se encuentran **Visual Studio Code**, **MariaDB**, **Selenium** y **Locust**, que nos han permitido realizar pruebas funcionales y de carga de manera eficiente. El proceso de despliegue se ha realizado en **Render**, donde hemos integrado la aplicación con su base de datos y realizado las migraciones necesarias. Nuestro proyecto también se puede lanzar con Docker y Vagrant.

En cuanto a la integración continua, hemos adoptado una metodología basada en **GitHub Actions**. Esta herramienta nos ha permitido realizar integraciones constantes y asegurar que cada cambio en el código se pruebe antes de ser fusionado con el repositorio principal. De esta manera, garantizamos una revisión constante de las funcionalidades, minimizando los riesgos de introducir errores en el sistema.

### Organización y Metodología de Trabajo

El modelo de ramas utilizado para la gestión de versiones es el **EGC-flow**, basado en el concepto de **feature-tasks**. Esto nos ha permitido trabajar de forma más organizada y con un flujo de trabajo más ágil, utilizando ramas específicas para cada nueva funcionalidad y fusionándolas de manera regular con la rama **trunk**. Esta metodología facilita la integración continua y asegura que los desarrollos se mantengan actualizados con el código principal.

Además, cada vez que se completaba una funcionalidad, se realizaba un merge a la rama **trunk**, que se mantiene como la rama principal de desarrollo. También hemos implementado una rama **main** que se utiliza como referencia para las versiones liberadas del proyecto, la cual no se destruye y se actualiza con cada nueva entrega.

Una característica importante de nuestro flujo de trabajo es que no utilizamos Pull Requests (PR) salvo para las integraciones entre los distintos equipos. Esto ha permitido un proceso de desarrollo más ágil y sin retrasos innecesarios.

### Buenas Prácticas

A lo largo de este proyecto, hemos ganado una gran disciplina al adherirnos a prácticas recomendadas para el desarrollo de software, lo que no solo mejora la calidad del proyecto, sino que también facilita la colaboración y el seguimiento de los avances. Estas buenas prácticas incluyen el uso de herramientas de integración continua, la organización del código mediante ramas y el compromiso de mantener un código limpio y bien estructurado.

Además, nos hemos centrado en la mejora continua, adaptando nuestros procesos de trabajo a medida que el proyecto avanzaba y aprendíamos de los desafíos que surgían. La implementación de estas buenas prácticas nos ha permitido tener un control más riguroso sobre el desarrollo del proyecto, asegurando que las entregas sean consistentes y de alta calidad.

### Cierre

En resumen, este trabajo ha consistido en un proceso de mejora continua de una plataforma ya existente (UVLHUB), implementando nuevas funcionalidades y mejorando las ya existentes. Gracias al uso de herramientas de desarrollo y pruebas, así como a la adopción de buenas prácticas de integración continua y gestión de ramas, hemos logrado optimizar la plataforma y mejorar la experiencia del usuario.

## Descripción del sistema

El sistema desarrollado es una plataforma para la gestión, visualización y distribución de pixdatasets. Su objetivo principal es proporcionar a los usuarios una forma eficiente de descubrir, compartir y promover datasets relacionados con diferentes áreas de investigación y desarrollo. Además, permite a los autores de datasets tener herramientas para promover sus datasets y hacer un seguimiento de su popularidad, facilitando tanto el descubrimiento como la gestión de datos.

La plataforma se basa en un conjunto de subsistemas que interactúan entre sí para proporcionar una experiencia fluida y eficiente para los usuarios. Entre estos subsistemas se incluyen la gestión de usuarios, la visualización y recomendación de datasets, y las herramientas de autenticación y seguridad. Cada subsistema tiene una función específica que contribuye al funcionamiento integral de la plataforma, mejorando la experiencia tanto para usuarios como para administradores.

### **Arquitectura del Sistema**

El sistema está diseñado bajo una arquitectura modular, lo que facilita su mantenimiento, escalabilidad y ampliación en el futuro. Los componentes principales incluyen:

1. **Autenticación y Gestión de Usuarios**

   - Este subsistema se encarga de la autenticación de usuarios, la gestión de sesiones y la seguridad. Permite a los usuarios registrarse, iniciar sesión y gestionar su perfil.
   - **Autenticación en Dos Factores (2FA):** Una de las principales características de seguridad implementadas en el sistema es la autenticación en dos factores (2FA). Esta medida refuerza la seguridad de las cuentas de usuario, exigiendo un segundo factor de autenticación además de la contraseña. Si un usuario tiene 2FA habilitado, se le solicita un código generado por una aplicación de autenticación cada vez que inicie sesión.
   - **Flujo de Autenticación:** Durante el proceso de inicio de sesión, si 2FA está habilitado para el usuario, se solicita un código de verificación generado por una aplicación de autenticación. Una vez verificado, el usuario obtiene acceso a la plataforma.

2. **Gestión y Visualización de Datasets**

   - Este subsistema se encarga de la creación, visualización y gestión de datasets. Los usuarios pueden subir, ver, editar y eliminar datasets, así como ver estadísticas relacionadas con su popularidad y distribución.
   - **Recomendaciones Automáticas de Datasets:** Cuando un usuario visualiza un dataset, el sistema recomienda otros datasets relacionados, facilitando el descubrimiento de contenido similar que podría interesar al usuario. Las recomendaciones se basan en la similitud de los datasets (por ejemplo, por autor, etiquetas o comunidad) y en su popularidad (descargas o vistas).
   - **Contador de Descargas para Datasets:** El sistema realiza un seguimiento de las descargas de cada dataset. Cada vez que un dataset se descarga, el contador de descargas se incrementa, lo que permite a los usuarios y autores ver la popularidad de los datasets.
   - **Sección de Datasets Populares:** Además, el sistema muestra una sección de "Datasets Populares", donde los usuarios pueden ver los datasets más descargados o visualizados en un período determinado (por ejemplo, en la última semana o mes).

3. **Servicios de Almacenamiento y Distribución**
   - Los datasets se almacenan de manera eficiente y se distribuyen a través de diferentes medios, como descargas directas y el sistema de Zenodo. Los datasets se pueden subir a Zenodo para obtener un DOI (Identificador de Objeto Digital), lo que facilita su citación y distribución.
   - **Subida a Zenodo:** Cuando un usuario sube un dataset a la plataforma, el sistema lo deposita automáticamente en Zenodo, asignándole un DOI y publicándolo. Este flujo de trabajo permite que los datasets estén disponibles en un repositorio académico reconocido y se pueda realizar un seguimiento de sus descargas y citas.
   - **Gestión de Archivos:** El sistema admite la subida de archivos en formatos como `.pix` y `.zip`. Los archivos se gestionan y almacenan en carpetas temporales mientras se procesan, y luego se organizan de manera eficiente para su distribución.

### **Flujo de Trabajo de la Plataforma**

El flujo de trabajo en la plataforma se organiza en torno a las actividades principales de los usuarios: la autenticación, la creación y gestión de datasets, y la visualización y descubrimiento de datasets relacionados. El siguiente es un resumen del flujo general:

1. **Registro y Autenticación:**

   - Los usuarios pueden registrarse en la plataforma, proporcionando su correo electrónico y contraseña. Durante el registro, los usuarios pueden habilitar la autenticación en dos factores (2FA) para mejorar la seguridad de sus cuentas.
   - Al iniciar sesión, si 2FA está habilitado, se solicita un código de verificación generado por una aplicación de autenticación. Una vez verificado, el usuario obtiene acceso a la plataforma.

2. **Creación y Gestión de Datasets:**

   - Los usuarios pueden crear nuevos datasets mediante un formulario que incluye campos para el título, descripción, etiquetas y otros metadatos. Además, los usuarios pueden subir archivos (por ejemplo, `.pix` o `.zip`) asociados con el dataset.
   - Una vez creado un dataset, el sistema lo sube a Zenodo, le asigna un DOI y lo hace disponible para otros usuarios.

3. **Visualización y Descubrimiento de Datasets:**

   - Los usuarios pueden explorar datasets mediante una interfaz que les permite filtrar y buscar datasets por etiquetas, autor o comunidad.
   - Cuando visualizan un dataset, el sistema muestra un bloque de "Datasets Relacionados" con recomendaciones de contenido similar. Las recomendaciones se basan en la similitud con el dataset visualizado, lo que permite una navegación más fluida y enriquecedora.

4. **Descarga de Datasets:**
   - Los usuarios pueden descargar datasets, y el sistema lleva un registro de cada descarga para actualizar el contador de descargas y registrar la actividad en la base de datos.
   - Si el usuario no tiene una cookie de descarga, el sistema genera una nueva para identificar la descarga.

### **Cambios Desarrollados en el Proyecto**

A lo largo del desarrollo de la plataforma, se han implementado y mejorado varias funcionalidades clave. Los cambios más relevantes son los siguientes:

1. **Implementación de la Autenticación en Dos Factores (2FA):**

   - Se ha añadido un sistema de 2FA que proporciona una capa adicional de seguridad para las cuentas de usuario. Los usuarios pueden habilitar esta opción durante el registro o en su perfil, y se les solicita un código de verificación durante el inicio de sesión.

2. **Recomendaciones Automáticas de Datasets:**

   - Se ha implementado un sistema de recomendaciones automáticas que sugiere datasets relacionados basados en la similitud de autores, etiquetas y comunidades, y prioriza los datasets más descargados o más recientes.

3. **Contador de Descargas:**

   - El sistema ahora lleva un seguimiento detallado del número de descargas de cada dataset, permitiendo a los autores ver cuántas veces ha sido descargado su contenido.

4. **Datasets Populares:**

   - Se ha añadido una sección de "Datasets Populares" en la página de inicio y en el explorador de datasets. Esta sección muestra los datasets más populares en función de su número de vistas y descargas en el último período (por ejemplo, semana o mes).

5. **Subida Automática a Zenodo:**

   - Los datasets ahora se suben automáticamente a Zenodo cuando se crean en la plataforma, asignándoles un DOI y permitiendo su citación y distribución.

6. **Interfaz de Usuario Mejorada:**
   - Se han realizado mejoras en la interfaz de usuario para hacerla más intuitiva y fácil de usar, permitiendo a los usuarios gestionar y explorar datasets de manera más eficiente.

## Visión global del proceso de desarrollo

El desarrollo de PixelHub se ha llevado a cabo de forma colaborativa y estructurada, combinando buenas prácticas de integración continua, control de versiones y automatización de tareas. El equipo ha utilizado herramientas como GitHub, Docker (con su propia imagen publicada en Docker Hub para producción) y Vagrant para garantizar un entorno reproducible y estable en cualquier sistema. Gracias a ello, el proyecto puede desplegarse fácilmente tanto en entornos de desarrollo como en producción. A lo largo del documento se explica cómo se ha organizado el proceso y se muestra un ejemplo práctico de cómo se gestiona un cambio desde su propuesta hasta su despliegue final.

### Entorno de desarrollo

En este apartado se describen las tecnologías y herramientas que han conformado el entorno de desarrollo utilizado por el equipo durante la realización del proyecto. El objetivo principal ha sido trabajar con herramientas comunes, estables y bien soportadas, que faciliten el desarrollo colaborativo y la integración continua del sistema.

#### Sistema operativo

El desarrollo del proyecto se ha realizado en entornos heterogéneos:

- **Ubuntu Linux** ha sido el sistema operativo principal, utilizado por 4 de los 5 miembros del equipo.
- **macOS** ha sido utilizado por 1 miembro del equipo.

Aunque la mayoría del desarrollo se ha llevado a cabo sobre Ubuntu, se ha tenido en cuenta la compatibilidad con macOS. En este caso concreto, fue necesario realizar pequeños ajustes en rutas y scripts para permitir la correcta ejecución del sistema y de los tests en local, manteniendo estos cambios aislados del flujo principal de desarrollo.

#### Lenguajes utilizados

El sistema ha sido desarrollado utilizando los siguientes lenguajes:

- **Python 3.11.7** como lenguaje principal para la implementación de la lógica de la aplicación.
- **SQL** para la gestión y consulta de la base de datos.

Python ha sido el eje central del proyecto, utilizándose tanto para la lógica de negocio como para la integración con la base de datos y otros subsistemas del sistema.

#### Entorno de desarrollo integrado (IDE)

Como entorno de desarrollo integrado se ha utilizado **Visual Studio Code**. Este IDE ha sido elegido por su amplio soporte para Python, su integración con Git y GitHub, y la posibilidad de ampliación mediante extensiones. Su uso ha permitido una experiencia de desarrollo homogénea entre los miembros del equipo, independientemente del sistema operativo utilizado.

#### Control de versiones e integración continua

El control de versiones del proyecto se ha gestionado mediante **Git**, utilizando **GitHub** como repositorio remoto central. GitHub ha permitido coordinar el trabajo del equipo, mantener un historial claro de cambios y facilitar la integración continua del sistema.

Para la automatización de procesos se han utilizado **GitHub Actions**, definiendo distintos _workflows_ en función del tipo de tarea a ejecutar. Entre los aspectos más relevantes se incluyen:

- Ejecución automática de **tests con pytest**, integrados directamente en GitHub Actions.
- Verificación del estilo y calidad del código mediante **linting**, utilizando las herramientas **flake8**, **black** y **rosemary linter**.
- Diferentes _workflows_ en función de la rama, por ejemplo:
  - Ejecución de análisis de calidad (como SonarQube) en _push_ a la rama `main`.
  - Ejecución de linting en cualquier _push_, independientemente de la rama.

Además, se han implementado **hooks de Git** para reforzar estas comprobaciones en local, obligando a cumplir los criterios de linting antes de permitir ciertos commits. Esto ha contribuido a mantener una base de código consistente y alineada con buenas prácticas desde las primeras fases del desarrollo.

#### Base de datos

El sistema utiliza **MariaDB 12.0.2** como sistema de gestión de bases de datos relacional. MariaDB se ha empleado para almacenar de forma persistente la información del sistema, incluyendo usuarios, datasets y registros asociados a descargas y visualizaciones.

El uso de SQL ha permitido estructurar claramente los datos y realizar consultas eficientes, facilitando tanto el desarrollo como el mantenimiento del sistema.

#### Testing y validación

Para garantizar la calidad del software, se han utilizado distintas herramientas de testing, cada una orientada a un tipo concreto de validación:

- **Pytest**, integrado en GitHub Actions, para la ejecución de pruebas unitarias.
- **Tests unitarios**, centrados en validar el correcto funcionamiento de componentes individuales del sistema.
- **Selenium**, utilizado en local para pruebas funcionales y de interfaz, simulando la interacción de usuarios con la aplicación.
- **Locust**, empleado en local para pruebas de carga, permitiendo evaluar el comportamiento del sistema bajo escenarios de uso intensivo.

La combinación de estas herramientas ha permitido validar tanto la lógica interna del sistema como su comportamiento desde el punto de vista del usuario final, contribuyendo a un desarrollo más robusto y fiable.

## Instalación, ejecución y despliegue

### Instalación paso a paso

Esta sección detalla los pasos para la instalación de forma manual. Asegúrate de sustituir todas los usuarios y contraseñas de ejemplo por opciones seguras.

### 1. Actualización de Dependencias

Actualizamos las dependencias del sistema:

```bash
sudo apt update -y
sudo apt upgrade -y
```

### 2. Clonación del repositorio

Clonamos el repositorio usando git y nos movemos al directorio del proyecto:

```bash
git clone git@github.com:PixelHub-ORG/PixelHub-1
cd PixelHub1
```

### 3. Configuración MariaDB y MySQL

Es imprescindible que contemos con versiones de Python, MariaDB y MySQL instaladas en nuestro sistema para que la instalación funcione.

Configuramos MySQL:

```bash
sudo mysql_secure_installation
```

Una vez en la consola interactiva pulsamos Enter tres veces hasta que nos solicite una nueva contraseña. Escribimos la contraseña que queramos para el usuario root y damos enter hasta que se cierre la consola.a

### 4. Configuración de la Base de Datos

Una vez configuradas las tecnologías podemos crear la base de datos. Abrimos la consola de MySQL como usuario ROOT:

```bash
sudo mysql -u root -p
```

Esta plantilla sirve como ejemplo para configurar la base de datos desde la consola pero se aconseja cambiar los nombres de usuario y las contraseñas.

```sql
CREATE DATABASE pixelhubdb;
CREATE DATABASE pixelhubdb_test;
CREATE USER 'pixelhubdb_user'@'localhost' IDENTIFIED BY 'elegir_contraseña_segura';
GRANT ALL PRIVILEGES ON pixelhubdb.* TO 'pixelhubdb_user'@'localhost';
GRANT ALL PRIVILEGES ON pixelhubdb_test.* TO 'pixelhubdb_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Configuración del archivo .env

Creamos un archivo de configuración .env

```bash
echo "" > .env
echo "webhook" > .moduleignore
code .
```

Esta plantilla incluye todos los campos que debería tener el arvhivo de configuración:

```bash
FLASK_APP_NAME="PIXELHUB.IO(dev)"
FLASK_ENV=development
DOMAIN=localhost:5000
MARIADB_HOSTNAME=localhost
MARIADB_PORT=3306
MARIADB_DATABASE=pixelhubdb
MARIADB_TEST_DATABASE=pixelhubdb_test
MARIADB_USER=pixelhubdb_user
MARIADB_PASSWORD=contraseña_establecida_mariadb
MARIADB_ROOT_PASSWORD=contraseña_establecida_root
WORKING_DIR=""
ORCID_CLIENT_ID="APP-QDXJOGWEQBPHZ3JR"
ORCID_CLIENT_SECRET="3d15b6fc-2d86-46e0-9522-dba049b5d477"
GITHUB_TOKEN = "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"
```

Una vez escrita la configuración guardamos el archivo y cerramos el editor.

### 6. Creación de Entorno Virtual

En esta sección crearemos un entorno virtual que contenga todas las dependencias del proyecto. Ejecutamos estos comandos para completar el proceso de creación y configuración del entorno virtual:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ./
```

Para probar si todo ha salido bien podemos utilizar el comando 'rosemary' y deberían aparecernos todas las instrucciones de rosemary.

### 6. Migraciones y Seeders

Para migrar y poblar la base de datos utilizamos los siguientes comandos

```bash
flask db upgrade
rosemary db:seed
```

### 7. Ejecutar el Proyecto en Local

Para ejecutar el proyecto en local utilizamos este comando:

```bash
flask run --host=0.0.0.0 --reload --debug
```

Una vez ejecutado la aplicación debería estar corriendo en el puerto 5000 de nuestro host local.

En el comando flask run utilizamos reload para que los cambios en el código se reflejen en tiempo real en la aplicación. Utilizamos debug para ejecutar el proyecto en modo desarrollo (eliminar si no se pretende utilizar el sistema con este fin).

## Despliegue con Docker

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
Una vez que los contenedores estén listos, abre tu navegador y accede a: **http://localhost**

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

## Despliegue con Vagrant

Si prefieres ejecutar **PixelHub** en un entorno con Vagrant

Para desplegar el sistema en una máquina virtual haciendo Vagrant deberemos seguir los siguientes pasos:

### Requisitos Previos

Para utilizar los comandos de vagrant deberemos tener instaladas las dependencias que aparecen en el archivo requirements.txt. Para instalar las dependencias usamos

```bash
pip install -r requirements.txt
```

Además deberemos asegurarnos de que cumplimos los siguientes prerequisitos:

1. La opción Secure Boot de nuestro sistema se encuentra desactivada.
2. El kernel de nuestra máquina está preparado para crear máquinas virtuales. En la mayoría de casos podemos solucionar el problema utilizando el comando sudo rmmod kvm\_{intel/amd} donde utilizaremos la opción que se corresponda con nuestro tipo de procesador.

### Despliegue Paso a Paso

Para desplegar con vagrant seguiremos los siguientes pasos:

1. Copiamos el .env de ejemplo de Vagrant en nuestro .env

```bash
cp .env.vagrant.example .env
```

2. Nos movemos al directorio de Vagrant desde la raíz del proyecto:

```bash
cd vagrant/
```

3. Ejecutamos el comando de ejecución de vagrant:

```bash
vagrant up
```

Una vez hecho todo esto nuestro sistema debería estar corriendo en [esta dirección](http://127.0.0.1:5000/).

### Otros comandos

Si queremos eliminar la máquina virtual en la que se encuentra desplegado el sistema utilizamos:

```bash
vagrant destroy
```

## Ejercicio de propuesta de cambio

Se presentará un ejercicio con una propuesta concreta de cambio que ilustra **todo el proceso de evolución y gestión de la configuración del proyecto**. El cambio consiste en **añadir información detallada del equipo en la sección _Teams_ de la página**.

#### 1. Propuesta del cambio

En primer lugar, **Aaron** detecta la necesidad del cambio y crea una **issue de tipo _feature_ en GitHub**, utilizando la plantilla correspondiente
Una vez completados los campos, Aaron pulsa **Submit new issue**.

#### 2. Análisis y división del trabajo

La issue se asigna a **Jesús**, quien analiza el alcance y determina que el trabajo es demasiado grande para una sola tarea. Por ello, la divide en varias _issues_ más pequeñas. Estas nuevas _issues_ se asignan a distintos miembros del equipo y se mueven al estado **Ready** del tablero.

#### 3. Trabajo en local y creación de ramas

Cada miembro trabaja siguiendo un flujo basado en `trunk`.

1. Actualizar la rama local:

   ```bash
   git checkout trunk
   git pull origin trunk
   ```

2. Crea una rama en local y pasa su issue a **In Progress**:
   ```bash
   git checkout -b feature/update-teams
   ```

#### 4. Implementación del cambio

En la rama creada, cada desarrollador modifica el template de la sección **Teams** añadiendo la información del equipo.
Tras comprobar que todo funciona correctamente, se guardan los cambios:

```bash
git add .
git commit -m "feat: Add team information to Teams section"
```

#### 5. Integración en `trunk`

Una vez finalizada la tarea, se integra el trabajo en la rama de integración, se pasa la issue a **In review**:

```bash
git checkout trunk
git merge feature/update-teams
git push origin trunk
```

#### 6. Verificación automática

Al hacer _push_ a `trunk`, se ejecutan los **workflows de GitHub Actions**.

- Si los checks fallan o se encuentra algún bugs, se crea una nueva _issue_ y se repite el proceso (rama, corrección y merge).
- Si todo pasa correctamente, las _issues_ se cierran.

#### 7. Publicación final

Cuando `trunk` es estable y todas las tareas están completadas, se cierran las issues, se integra en producción:

```bash
git checkout main
git merge trunk
git push origin main
```

Este ejercicio muestra cómo se gestiona un cambio desde su propuesta inicial hasta su despliegue final, garantizando **control, trazabilidad y calidad** en la evolución y gestión de la configuración del proyecto.

### Conclusiones y trabajo futuro

El proceso seguido en PixelHub ha permitido trabajar de forma ordenada, colaborativa y con una buena trazabilidad de los cambios. El uso de herramientas de automatización y control de calidad ha reducido errores y facilitado la integración del trabajo en equipo. De cara al futuro, se prevé seguir mejorando el sistema, incorporando nuevas funcionalidades como mejora de la edición del perfil, un foro, o más estadísticas, y optimizando el rendimiento sin perder la estabilidad ni la coherencia del proyecto.
