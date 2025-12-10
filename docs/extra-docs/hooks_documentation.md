# HOOKS_DOCUMENTATION.md

# Documentación de Hooks y Pre-Commit en el Proyecto

Este documento describe las configuraciones implementadas para **control de calidad y estilo de código** en el proyecto, usando Git hooks y `pre-commit`.

---

## 1. Hook `.git/hooks/pre-push`

Se creó un **hook de pre-push** que se ejecuta automáticamente antes de realizar un `git push`. Su función es garantizar que el código cumpla con los linters y formateadores definidos.

### Flujo del hook:

1. **Ejecuta Rosemary Linter**

   ```bash
   rosemary linter
   ```

   * Verifica errores de estilo y buenas prácticas en Python.
   * Si falla, el push se aborta con el mensaje:

     ```
     ❌ Errores detectados por Rosemary. Abortando push.
     ```

2. **Ejecuta Black**

   ```bash
   black app
   ```

   * Formatea el código según el estilo definido por Black automáticamente.

3. **Ejecuta isort**

   ```bash
   isort app
   ```

   * Ordena las importaciones de Python automáticamente.

4. **Verifica cambios post-formateo**

   ```bash
   git status --porcelain
   ```

   * Si Black o isort modifican archivos, se notifica y se **hace commit automático**:

     ```bash
     git add .
     git commit -m "chore: formateo automático de código"
     ```
   * Si no hay cambios, indica:

     ```
     ✅ No hay cambios adicionales.
     ```

5. **Resultado final**

   * Todo correcto → el push se permite:

     ```
     ✅ Todo listo. Push permitido.
     ```
   * Algún fallo de Rosemary → push abortado.

**Nota:** Esto asegura que cualquier cambio de formato se aplique automáticamente y se suba al remoto, mientras que los errores de linter bloquean el push.

---

## 2. Configuración `pre-commit`

Se utiliza **pre-commit** para ejecutar linters y verificaciones antes de cada commit.

### Hooks implementados:

#### Ruff

* Repo: [astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit)
* Rev: `v0.14.5`
* Args: `--fix`
* Verifica Python y corrige problemas automáticamente en los archivos staged.

#### pre-commit-hooks

* Repo: [pre-commit/pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks)
* Rev: `v6.0.0`
* Hooks:

  * `check-merge-conflict` → evita conflictos sin resolver en commits.
  * `check-added-large-files` → evita subir archivos mayores a 5MB.
  * `check-yaml` → valida archivos YAML.
  * `check-json` → valida archivos JSON.

#### Commitlint

* Repo: [alessandrojcm/commitlint-pre-commit-hook](https://github.com/alessandrojcm/commitlint-pre-commit-hook)
* Rev: `v9.23.0`
* Stages: `commit-msg`
* Verifica que los mensajes de commit sigan la convención de [Conventional Commits](https://www.conventionalcommits.org/)
* Reglas personalizadas:

```js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', ['feature', 'feat', 'fix', 'chore', 'docs', 'style', 'refactor', 'test']],
    'subject-case': [0, 'never', []]
  }
};
```

#### Rosemary Linter

* Repo: `local`
* Entry: `rosemary`
* Lenguaje: `system`
* Tipo: `python`
* Revisa la carpeta app completa, no solo archivos individuales.

#### Black

* Repo: [psf/black](https://github.com/psf/black)
* Rev: `24.10.0`
* Formatea archivos Python staged automáticamente.

#### isort

* Repo: [PyCQA/isort](https://github.com/PyCQA/isort)
* Rev: `5.13.2`
* Ordena importaciones de archivos staged automáticamente.

---

## 3. Beneficios de esta configuración

* Garantiza **calidad de código** antes de cada commit y push.
* Aplica automáticamente los cambios de formato para Python y orden de importaciones.
* Evita enviar código con errores de estilo o importaciones desordenadas.
* Mantiene el **flujo de trabajo consistente** en el equipo.
* Cumple con la convención de commits, facilitando generación de changelogs.

---

## 4. Uso

1. Instalar pre-commit hooks:

```bash
pre-commit install
```

2. Hacer commits normalmente:

```bash
git add .
git commit -m "feat: nueva funcionalidad"
```

3. Push automático solo si el código pasa todas las validaciones:

```bash
git push
```

* Los cambios de Black e isort se aplicarán y harán commit automáticamente si es necesario.
* Si Rosemary detecta errores, el push se abortará.
