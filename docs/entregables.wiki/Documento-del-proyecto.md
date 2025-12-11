# Documento del pixel-hub-1

## Indicadores del proyecto

(_debe dejar enlaces a evidencias que permitan de una forma sencilla analizar estos indicadores, con gráficas y/o con enlaces_)

La razón por la que a algunos miembros del equipo se le han asociado dos WI es porque hemos trabajado haciendo pairprogramming.

| Miembro del equipo                                                   | Horas | Commits | LoC | Test | Issues | Work Item                                                                          | Dificultad     |
| -------------------------------------------------------------------- | ----- | ------- | --- | ---- | ------ | ---------------------------------------------------------------------------------- | -------------- |
| [Campos Díez, Lucía](https://github.com/LWH9900)                     | HH    | XX      | YY  | ZZ   | II     | Two-factor authentication (2FA) (H) \#89 & Embeddable badge \#102 (M)              | M & H          |
| [Mayoral Ansias, Aaron](https://github.com/aaronma300604)            | HH    | XX      | YY  | ZZ   | II     | newdataset - Evolving uvlhub into a "datatypehub" \#104                            | H              |
| [Oviedo Govantes, Claudia](https://github.com/ClaudiaOviedoGovantes) | HH    | XX      | YY  | ZZ   | II     | Trending datasets \#100 (M) & Two-factor authentication (2FA) (H)                  | M & H          |
| [Peñaloza Friqui, Nora](https://github.com/norapfr)                  | HH    | XX      | YY  | ZZ   | II     | Trending datasets \#100 (M) & Automatic dataset recommendations \#98 (H)           | M & H          |
| [Sánchez Quirós, Jesús](https://github.com/JesusSQ)                  | HH    | XX      | YY  | ZZ   | II     | Add download counter for datasets (L) & Automatic dataset recommendations \#98 (H) | L & H          |
| **TOTAL**                                                            | tHH   | tXX     | tYY | tZZ  | tII    | Descripción breve                                                                  | H(2)/M(2)/L(1) |

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

## Visión global del proceso de desarrollo (1.500 palabras aproximadamente)

Debe dar una visión general del proceso que ha seguido enlazándolo con las herramientas que ha utilizado. Ponga un ejemplo de un cambio que se proponga al sistema y cómo abordaría todo el ciclo hasta tener ese cambio en producción. Los detalles de cómo hacer el cambio vendrán en el apartado correspondiente.

### Entorno de desarrollo (800 palabras aproximadamente)

Debe explicar cuál es el entorno de desarrollo que ha usado, cuáles son las versiones usadas y qué pasos hay que seguir para instalar tanto su sistema como los subsistemas relacionados para hacer funcionar el sistema al completo. Si se han usado distintos entornos de desarrollo por parte de distintos miembros del grupo, también debe referenciarlo aquí.

### Ejercicio de propuesta de cambio

Se presentará un ejercicio con una propuesta concreta de cambio en la que a partir de un cambio que se requiera, se expliquen paso por paso (incluyendo comandos y uso de herramientas) lo que hay que hacer para realizar dicho cambio. Debe ser un ejercicio ilustrativo de todo el proceso de evolución y gestión de la configuración del proyecto.

### Conclusiones y trabajo futuro

Se enunciarán algunas conclusiones y se presentará un apartado sobre las mejoras que se proponen para el futuro (curso siguiente) y que no han sido desarrolladas en el sistema que se entrega

```

```
