#!/bin/bash

# Buscar la línea donde está "help"|"") y agregar check antes
sed -i '/"help"|"")/i \
    "check"|"verify")\
        print_header "VERIFICANDO DEPENDENCIAS Y CONFIGURACIÓN"\
        \
        check_venv || exit 1\
        \
        echo "📦 DEPENDENCIAS PRINCIPALES:"\
        if python -c "import fastapi" 2>/dev/null; then\
            print_success "  FastAPI"\
        else\
            print_error "  FastAPI - FALTANTE"\
        fi\
        \
        if python -c "import uvicorn" 2>/dev/null; then\
            print_success "  Uvicorn"\
        else\
            print_error "  Uvicorn - FALTANTE"\
        fi\
        \
        if python -c "import sqlmodel" 2>/dev/null; then\
            print_success "  SQLModel"\
        else\
            print_error "  SQLModel - FALTANTE"\
        fi\
        \
        if python -c "import pydantic_settings" 2>/dev/null; then\
            print_success "  Pydantic Settings"\
        else\
            print_error "  Pydantic Settings - FALTANTE"\
        fi\
        \
        echo ""\
        echo "🔐 AUTENTICACIÓN:"\
        if python -c "import jose" 2>/dev/null; then\
            print_success "  Python-JOSE (JWT)"\
        else\
            print_error "  Python-JOSE - FALTANTE"\
        fi\
        \
        if python -c "import passlib" 2>/dev/null; then\
            print_success "  Passlib (Password Hashing)"\
        else\
            print_error "  Passlib - FALTANTE"\
        fi\
        \
        echo ""\
        echo "🗄️  BASE DE DATOS:"\
        if python -c "import asyncpg" 2>/dev/null; then\
            print_success "  AsyncPG (PostgreSQL)"\
        else\
            print_error "  AsyncPG - FALTANTE"\
        fi\
        \
        if python -c "import redis" 2>/dev/null; then\
            print_success "  Redis"\
        else\
            print_error "  Redis - FALTANTE"\
        fi\
        \
        echo ""\
        echo "🔧 HERRAMIENTAS:"\
        if command -v black &>/dev/null; then\
            print_success "  Black (formateador)"\
        else\
            print_info "  Black - Opcional"\
        fi\
        \
        if command -v pytest &>/dev/null; then\
            print_success "  Pytest (testing)"\
        else\
            print_info "  Pytest - Opcional"\
        fi\
        \
        echo ""\
        echo "📁 ESTRUCTURA:"\
        if [ -f "app/main.py" ]; then\
            print_success "  app/main.py (punto de entrada)"\
        else\
            print_error "  app/main.py - FALTANTE"\
        fi\
        \
        if [ -f ".env" ]; then\
            print_success "  .env (variables)"\
        else\
            print_info "  .env - Opcional"\
        fi\
        \
        if [ -f "docker-compose.yml" ]; then\
            print_success "  docker-compose.yml"\
        else\
            print_info "  docker-compose.yml - Opcional"\
        fi\
        \
        echo ""\
        echo "🌐 API:"\
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then\
            print_success "  API corriendo en :8000"\
        else\
            print_info "  API no iniciada (usa: ./scripts.sh start)"\
        fi\
        \
        print_success "✅ Verificación completada"\
        ;;' scripts.sh
