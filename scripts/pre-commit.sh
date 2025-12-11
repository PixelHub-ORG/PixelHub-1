#!/bin/bash

# ============================================================================
# Pre-commit Hook - Formateo y Linting Automático
# ============================================================================
# Este script se ejecuta antes de cada commit y:
# 1. Ejecuta el linter personalizado de Rosemary
# 2. Corrige automáticamente errores de PEP8 con autopep8
# 3. Formatea el código con Black
# 4. Ordena los imports con isort
# 5. Verifica que todo pase flake8
# 6. Hace commit automático si hay cambios
# ============================================================================

set -e 

echo "🔥 PRE-COMMIT HOOK EJECUTÁNDOSE 🔥"

echo ""
echo "🚀 ===== INICIANDO PRE-COMMIT CHECKS ====="
echo ""


# Rosemary Linter
echo "📋 Ejecutando Rosemary Linter..."
rosemary linter 
if [ $? -ne 0 ]; then
    echo "❌ Errores detectados por Rosemary. Abortando commit."
    exit 1
fi
echo "✅ Rosemary linter pasado"
echo ""

# Instalar autopep8 si no está disponible
if ! command -v autopep8 &> /dev/null; then
    echo "📦 Instalando autopep8..."
    pip install -q autopep8
fi


# Formatear con Black PRIMERO (corrige indentación automáticamente)
echo "🎨 Formateando código con Black (esto puede tardar un momento)..."
black app rosemary core
BLACK_EXIT=$?
if [ $BLACK_EXIT -ne 0 ]; then
    echo "❌ Error al ejecutar Black. Abortando commit."
    exit 1
fi
echo "✅ Black ejecutado correctamente - código formateado"
echo ""

# Corregir otros errores de PEP8 con autopep8
echo "🔧 Corrigiendo errores adicionales de PEP8 con autopep8..."
# autopep8 después de Black para corregir cosas que Black no toca
autopep8 --in-place --aggressive --aggressive --recursive app rosemary core
echo "✅ Correcciones de PEP8 aplicadas"
echo ""

# Ordenar imports con isort
echo "📚 Ordenando imports con isort..."
isort app rosemary core
if [ $? -ne 0 ]; then
    echo "❌ Error al ejecutar isort. Abortando commit."
    exit 1
fi
echo "✅ isort ejecutado correctamente"
echo ""

# ----------------------------------------------------------------------------
# PASO 6: Verificación final con flake8
# ----------------------------------------------------------------------------
echo "🔍 Verificando código con flake8..."

flake8 app rosemary core 2>/dev/null
FLAKE8_EXIT=$?

if [ $FLAKE8_EXIT -ne 0 ]; then
    echo "⚠️  Se detectaron algunos errores de flake8."
    echo ""
    
    flake8 app rosemary core
    
    E122_COUNT=$(flake8 app rosemary core 2>/dev/null | grep -c "E122" || true)
    TOTAL_ERRORS=$(flake8 app rosemary core 2>/dev/null | wc -l || echo "0")
    
    if [ "$E122_COUNT" -gt 0 ] && [ "$E122_COUNT" -eq "$TOTAL_ERRORS" ]; then
        echo ""
        echo "🔧 Detectados solo errores E122, aplicando corrección agresiva..."
        
        if command -v yapf &> /dev/null; then
            yapf -i -r app rosemary core --style='{based_on_style: pep8, indent_width: 4}'
        else
            pip install -q yapf
            yapf -i -r app rosemary core --style='{based_on_style: pep8, indent_width: 4}'
        fi
        
        flake8 app rosemary core
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ No se pudieron corregir automáticamente todos los errores."
            echo "   Algunos errores requieren intervención manual."
            exit 1
        fi
    else
        echo ""
        echo "❌ Errores de flake8 detectados después del formateo."
        echo "   Por favor, revisa los errores anteriores."
        exit 1
    fi
fi

echo "✅ flake8 pasado correctamente"
echo ""

CHANGED_FILES=$(git diff --name-only)
if [ -n "$CHANGED_FILES" ]; then
    echo "⚡ Cambios detectados tras el formateo automático:"
    echo "$CHANGED_FILES" | sed 's/^/   - /'
    echo ""
    
    git add app rosemary core *.py 2>/dev/null || true
    
    if [ -n "$(git diff --cached --name-only)" ]; then
        git commit -m "chore: formateo automático de código (autopep8, black, isort)"
        echo "✅ Commit automático creado"
        echo ""
        echo "ℹ️  Se ha creado un nuevo commit con las correcciones de formato."
        echo "   El commit continuará con este commit adicional."
    else
        echo "⚠️  No se pudo añadir archivos al staging area."
        exit 1
    fi
else
    echo "✅ No hay cambios adicionales tras el formateo."
fi

echo ""
echo "✨ ===== TODOS LOS CHECKS PASADOS ====="
echo "🚀 Commit permitido. Continuando..."
echo ""

exit 0
