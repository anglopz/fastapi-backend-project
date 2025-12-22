#!/bin/bash

echo "🔍 Verificando dependencias del proyecto..."
echo ""

source .venv/bin/activate

# Función para verificar paquete
check_pkg() {
    local pkg=$1
    local name=$2
    
    if python -c "import $pkg" 2>/dev/null; then
        echo "✅ $name"
        return 0
    else
        echo "❌ $name"
        return 1
    fi
}

echo "📦 Paquetes esenciales:"
check_pkg fastapi "FastAPI"
check_pkg uvicorn "Uvicorn"
check_pkg sqlmodel "SQLModel"
check_pkg pydantic_settings "Pydantic Settings"

echo ""
echo "🔐 Autenticación:"
check_pkg jose "Python JOSE"
check_pkg passlib "Passlib"

echo ""
echo "🗄️  Base de datos:"
check_pkg asyncpg "AsyncPG"
check_pkg redis "Redis"

echo ""
echo "🔧 Herramientas:"
check_pkg black "Black"
check_pkg isort "Isort"
check_pkg pytest "Pytest"

echo ""
echo "📊 Resumen de pip:"
pip list | tail -20
