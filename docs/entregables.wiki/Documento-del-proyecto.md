El documento del proyecto debe ser un documento que sintetice los aspectos del proyecto elegido para su desarrollo con respecto a los temas vistos en clases.

Debe tener claramente identificados los nombres y apellidos de cada componente, grupo al que pertenecen (1, 2, o 3 mañana o tarde), curso académico, nombre del proyecto (seguir la política de nombres). Use este [[modelo de portada]] para el documento del proyecto y alójelo en su repositorio o en otro sitio accesible y que tenga posibilidad de verse el último momento de edicación. Puede usar el repositorio del proyecto usando para ello el lenguaje de [markdown](https://guides.github.com/features/mastering-markdown/) que ofrece github. En todo caso, debe ser un documento elaborado en formato [wiki].

Será un documento presentado de manera profesional guardando la forma en los estilos y contenidos y con el máximo nivel de rigor académico y profesional.

Tenga en cuenta los siguientes aspectos:

- Siempre diferencie claramente las secciones y subsecciones y para ello use etiquetas de encabezado como las que se disponen en los lenguajes tipo _markdown_

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

## Resumen ejecutivo (800 palabras aproximadamente)

Se sintetizará de un vistazo lo hecho en el trabajo y los datos fundamentales. Se usarán palabras para resumir el proyecto presentado.

---

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

Una característica importante de nuestro flujo de trabajo es que no utilizamos Pull Requests (PR) salvo para las integraciones entre los distintos equipos. Esto ha permitido un proceso de desarrollo más ágil y sin retrasos innecesarios. También se ha justificado la existencia de ramas específicas para compañeros que usan diferentes sistemas operativos, como el caso de una compañera con Mac que necesita modificar rutas y scripts para hacer funcionar los tests en local.

### Buenas Prácticas

A lo largo de este proyecto, hemos ganado una gran disciplina al adherirnos a prácticas recomendadas para el desarrollo de software, lo que no solo mejora la calidad del proyecto, sino que también facilita la colaboración y el seguimiento de los avances. Estas buenas prácticas incluyen el uso de herramientas de integración continua, la organización del código mediante ramas y el compromiso de mantener un código limpio y bien estructurado.

Además, nos hemos centrado en la mejora continua, adaptando nuestros procesos de trabajo a medida que el proyecto avanzaba y aprendíamos de los desafíos que surgían. La implementación de estas buenas prácticas nos ha permitido tener un control más riguroso sobre el desarrollo del proyecto, asegurando que las entregas sean consistentes y de alta calidad.

### Cierre

En resumen, este trabajo ha consistido en un proceso de mejora continua de una plataforma ya existente (UVLHUB), implementando nuevas funcionalidades y mejorando las ya existentes. Gracias al uso de herramientas de desarrollo y pruebas, así como a la adopción de buenas prácticas de integración continua y gestión de ramas, hemos logrado optimizar la plataforma y mejorar la experiencia del usuario.

## Descripción del sistema (1.500 palabras aproximadamente)

Se explicará el sistema desarrollado desde un punto de vista funcional y arquitectónico. Se hará una descripción tanto funcional como técnica de sus componentes y su relación con el resto de subsistemas. Habrá una sección que enumere explícitamente cuáles son los cambios que se han desarrollado para el proyecto.

## Visión global del proceso de desarrollo (1.500 palabras aproximadamente)

Debe dar una visión general del proceso que ha seguido enlazándolo con las herramientas que ha utilizado. Ponga un ejemplo de un cambio que se proponga al sistema y cómo abordaría todo el ciclo hasta tener ese cambio en producción. Los detalles de cómo hacer el cambio vendrán en el apartado correspondiente.

### Entorno de desarrollo (800 palabras aproximadamente)

Debe explicar cuál es el entorno de desarrollo que ha usado, cuáles son las versiones usadas y qué pasos hay que seguir para instalar tanto su sistema como los subsistemas relacionados para hacer funcionar el sistema al completo. Si se han usado distintos entornos de desarrollo por parte de distintos miembros del grupo, también debe referenciarlo aquí.

### Ejercicio de propuesta de cambio

Se presentará un ejercicio con una propuesta concreta de cambio en la que a partir de un cambio que se requiera, se expliquen paso por paso (incluyendo comandos y uso de herramientas) lo que hay que hacer para realizar dicho cambio. Debe ser un ejercicio ilustrativo de todo el proceso de evolución y gestión de la configuración del proyecto.

### Conclusiones y trabajo futuro

Se enunciarán algunas conclusiones y se presentará un apartado sobre las mejoras que se proponen para el futuro (curso siguiente) y que no han sido desarrolladas en el sistema que se entrega
