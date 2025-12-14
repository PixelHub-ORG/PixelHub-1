#!/bin/bash

# ============================================================================
# Pre-commit Hook - Formateo y Linting Automático
# ============================================================================
# Este script se ejecuta antes de cada commit y:
# 1. Ejecuta el linter personalizado de Rosemary
# 2. Formatea el código con Black
# 3. Corrige automáticamente errores de PEP8 con autopep8
# 4. Ordena los imports con isort
# 5. Verifica que todo pase flake8
# 6. Añade automáticamente los cambios al staging area del commit actual
# ============================================================================

set -e 

echo "🔥 PRE-COMMIT HOOK EJECUTÁNDOSE 🔥"
echo ""
echo "🚀 ===== INICIANDO PRE-COMMIT CHECKS ====="
echo ""

# Obtener lista de archivos Python en staging
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "ℹ️  No hay archivos Python en staging. Saltando checks."
    exit 0
fi

echo "📁 Archivos Python detectados:"
echo "$STAGED_FILES" | sed 's/^/   - /'
echo ""

# ----------------------------------------------------------------------------
# PASO 1: Rosemary Linter
# ----------------------------------------------------------------------------
echo "📋 Ejecutando Rosemary Linter..."
rosemary linter 
if [ $? -ne 0 ]; then
    echo "❌ Errores detectados por Rosemary. Abortando commit."
    exit 1
fi
echo "✅ Rosemary linter pasado"
echo ""

# ----------------------------------------------------------------------------
# PASO 2: Formatear con Black
# ----------------------------------------------------------------------------
echo "🎨 Formateando código con Black..."
black app rosemary core
if [ $? -ne 0 ]; then
    echo "❌ Error al ejecutar Black. Abortando commit."
    exit 1
fi
echo "✅ Black ejecutado correctamente"
echo ""

# ----------------------------------------------------------------------------
# PASO 3: Corregir errores de PEP8 con autopep8
# ----------------------------------------------------------------------------
echo "🔧 Corrigiendo errores de PEP8 con autopep8..."
if ! command -v autopep8 &> /dev/null; then
    echo "📦 Instalando autopep8..."
    pip install -q autopep8
fi
autopep8 --in-place --aggressive --aggressive --recursive app rosemary core
echo "✅ Correcciones de PEP8 aplicadas"
echo ""

# ----------------------------------------------------------------------------
# PASO 4: Ordenar imports con isort
# ----------------------------------------------------------------------------
echo "📚 Ordenando imports con isort..."
isort app rosemary core
if [ $? -ne 0 ]; then
    echo "❌ Error al ejecutar isort. Abortando commit."
    exit 1
fi
echo "✅ isort ejecutado correctamente"
echo ""

# ----------------------------------------------------------------------------
# PASO 5: Verificación final con flake8
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
        echo "🔧 Detectados solo errores E122, aplicando corrección con yapf..."
        
        if ! command -v yapf &> /dev/null; then
            echo "📦 Instalando yapf..."
            pip install -q yapf
        fi
        
        yapf -i -r app rosemary core --style='{based_on_style: pep8, indent_width: 4}'
        
        # Verificar nuevamente
        flake8 app rosemary core 2>/dev/null
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ No se pudieron corregir automáticamente todos los errores."
            echo "   Algunos errores requieren intervención manual."
            flake8 app rosemary core
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

# ----------------------------------------------------------------------------
# PASO 6: Añadir cambios al staging area
# ----------------------------------------------------------------------------
# Detectar archivos modificados por el formateo
CHANGED_FILES=$(git diff --name-only app rosemary core 2>/dev/null | grep '\.py$' || true)

if [ -n "$CHANGED_FILES" ]; then
    echo "⚡ Archivos modificados por el formateo automático:"
    echo "$CHANGED_FILES" | sed 's/^/   - /'
    echo ""
    
    # Añadir SOLO los archivos modificados al staging area
    echo "$CHANGED_FILES" | xargs git add
    
    echo "✅ Cambios de formato añadidos al commit actual"
else
    echo "✅ No hay cambios adicionales tras el formateo"
fi

echo ""
echo "✨ ===== TODOS LOS CHECKS PASADOS ====="
echo "🚀 Commit permitido. Continuando..."
echo ""

exit 0