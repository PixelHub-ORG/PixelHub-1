# HOOKS_DOCUMENTATION.md

# Documentación de Hooks y Pre-Commit en el Proyecto

Este documento describe las configuraciones implementadas para **control de calidad y estilo de código** en el proyecto, usando Git hooks y `pre-commit`.

---

## 1. Hook `.git/hooks/pre-commit`

Se utiliza un **hook de pre-commit** que se ejecuta automáticamente antes de realizar un `git commit`. Su objetivo es garantizar que el código cumpla con los estándares de calidad, estilo y buenas prácticas definidos en el proyecto.

### Flujo del hook:

1. **Detección de archivos Python en staging**

   El hook comprueba si existen archivos `.py` en el área de staging. Si no hay ninguno, el commit continúa sin ejecutar validaciones adicionales.

2. **Ejecución de Rosemary Linter**

   ```bash
   rosemary linter
   ```

   * Ejecuta el linter personalizado del proyecto.
   * Verifica reglas de estilo y buenas prácticas.
   * Si se detectan errores, el commit se aborta con el mensaje:

     ```
     ❌ Errores detectados por Rosemary. Abortando commit.
     ```

3. **Formateo automático con Black**

   ```bash
   black app rosemary core
   ```

   * Aplica automáticamente el formato estándar de Black a todo el código Python.

4. **Corrección de errores PEP8 con autopep8**

   ```bash
   autopep8 --in-place --aggressive --aggressive --recursive app rosemary core
   ```

   * Corrige automáticamente errores comunes de PEP8.
   * Si `autopep8` no está instalado, el hook lo instala automáticamente.

5. **Ordenación de imports con isort**

   ```bash
   isort app rosemary core
   ```

   * Garantiza un orden consistente de las importaciones.

6. **Verificación final con flake8**

   ```bash
   flake8 app rosemary core
   ```

   * Realiza una validación final del código.
   * Si solo existen errores de indentación `E122`, se intenta una corrección automática usando `yapf`.
   * Si persisten errores no corregibles automáticamente, el commit se aborta.

7. **Añadido automático de cambios al commit**

   * Si el formateo modifica archivos, estos se añaden automáticamente al staging area y se incluyen en el commit actual.

8. **Resultado final**

   * Todos los checks pasan → el commit se permite.
   * Algún error no corregible → el commit se bloquea.

---

## 2. Configuración `pre-commit`

Se utiliza **pre-commit** como capa adicional de validación para ejecutar linters y verificaciones antes de cada commit.

### Hooks implementados:

#### Ruff

* Repo: [astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit)
* Rev: `v0.14.5`
* Args: `--fix`
* Analiza código Python y corrige problemas automáticamente en archivos staged.

#### pre-commit-hooks

* Repo: [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks)
* Rev: `v6.0.0`
* Hooks:

  * `check-merge-conflict`
  * `check-added-large-files` (máx. 5MB)
  * `check-yaml`
  * `check-json`

#### Commitlint

* Repo: [alessandrojcm/commitlint-pre-commit-hook](https://github.com/alessandrojcm/commitlint-pre-commit-hook)
* Rev: `v9.23.0`
* Stage: `commit-msg`
* Valida mensajes de commit siguiendo **Conventional Commits**.

#### Rosemary Linter

* Repo: `local`
* Entry: `rosemary linter`
* Language: `system`
* Ejecuta el linter sobre el proyecto completo.

#### Black

* Repo: [psf/black](https://github.com/psf/black)
* Rev: `24.10.0`
* Formatea automáticamente el código Python.

#### isort

* Repo: [PyCQA/isort](https://github.com/PyCQA/isort)
* Rev: `5.13.2`
* Ordena las importaciones de Python.

---

## 3. Beneficios de esta configuración

* Garantiza **alta calidad de código** antes de cada commit.
* Aplica correcciones automáticas sin intervención manual.
* Evita introducir errores de estilo o formato en el repositorio.
* Mantiene consistencia entre desarrolladores.
* Refuerza buenas prácticas en mensajes de commit.

---

## 4. Uso

1. Instalar los hooks de pre-commit:

```bash
pre-commit install
```

2. Realizar commits normalmente:

```bash
git add .
git commit -m "feat: nueva funcionalidad"
```

* Los formateos se aplican automáticamente.
* Si existen errores no corregibles, el commit se aborta hasta ser solucionados.

---

