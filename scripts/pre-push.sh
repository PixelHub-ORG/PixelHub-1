#!/bin/bash

echo "==== Ejecutando Rosemary Linter ===="
rosemary linter 
if [ $? -ne 0 ]; then
    echo "❌ Errores detectados por Rosemary. Abortando push."
    exit 1
fi

echo "==== Ejecutando Black ===="
black app
if [ $? -ne 0 ]; then
    echo "❌ Error al ejecutar Black. Abortando push."
    exit 1
fi

echo "==== Ejecutando isort ===="
isort app
if [ $? -ne 0 ]; then
    echo "❌ Error al ejecutar isort. Abortando push."
    exit 1
fi

# Revisar si hay cambios después de formatear
if [ -n "$(git status --porcelain)" ]; then
    echo "⚡ Cambios detectados tras formatear, haciendo commit automático..."
    git add .
    git commit -m "Auto: formateo con Black e isort antes del push" --no-verify
else
    echo "✅ No hay cambios adicionales."
fi

echo "✅ Todo listo. Push permitido."
exit 0
