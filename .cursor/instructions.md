# 🚀 Proyecto FastAPI - Instrucciones para Cursor

## 📋 CONTEXTO DEL PROYECTO
Backend en FastAPI para sistema de cursos con:
- Autenticación JWT
- PostgreSQL + SQLModel
- Redis para cache
- Docker Compose para servicios

## 🏗️ ESTRUCTURA ACTUAL
\`\`\`
/home/angelo/proyectos/cursos/app/
├── app/                 # Código principal
│   ├── main.py         # Punto de entrada
│   └── (otros módulos)
├── .venv/              # Entorno virtual Python
├── docker-compose.yml  # Servicios (PostgreSQL, Redis)
├── requirements.txt    # Dependencias
├── Dockerfile          # Contenedor de la app
└── scripts.sh         # Comandos automatizados
\`\`\`

## 🎯 TECNOLOGÍAS PRINCIPALES
- **FastAPI**: Framework web async
- **SQLModel**: ORM con SQLAlchemy + Pydantic
- **PostgreSQL**: Base de datos principal
- **Redis**: Cache y sesiones
- **Docker**: Contenedores para servicios

## 📝 CONVENCIONES DE CÓDIGO
1. **Imports**: Usar imports absolutos (\`from app.module import X\`)
2. **Async**: Todas las operaciones de DB son async/await
3. **SQLModel v1.x**:
   - Usar \`session.exec()\` en lugar de \`session.execute()\`
   - Usar \`.first()\` / \`.all()\` en lugar de \`.scalars().first()\`
4. **Nombres**:
   - snake_case para funciones/variables
   - PascalCase para clases
   - UPPER_CASE para constantes

## 🔧 SCRIPTS DISPONIBLES
\`\`\`bash
# Iniciar proyecto completo
./scripts.sh start

# Ver estado
./scripts.sh status

# Instalar dependencias
./scripts.sh install

# Formatear código
./scripts.sh format

# Ejecutar tests
./scripts.sh test
\`\`\`

## 🐛 PROBLEMAS COMUNES Y SOLUCIONES

### 1. ImportError: No module named 'app'
**Solución**: Asegurar que los imports usen la ruta completa:
\`\`\`python
# INCORRECTO: from api import router
# CORRECTO: from app.api import router
\`\`\`

### 2. AttributeError con SQLModel
**Solución**: Usar métodos correctos de SQLModel v1.x:
\`\`\`python
# INCORRECTO: result = session.execute(query).scalars().first()
# CORRECTO: result = session.exec(query).first()
\`\`\`

### 3. PostgreSQL connection error
**Verificar**: 
\`\`\`bash
./scripts.sh status  # Ver si servicios están corriendo
docker-compose ps    # Estado de contenedores
\`\`\`

### 4. Puerto 8000 ya en uso
**Solución**:
\`\`\`bash
./scripts.sh stop    # Detener API anterior
./scripts.sh start   # Reiniciar
\`\`\`

## 🔗 ENDPOINTS PRINCIPALES
- \`GET /health\` - Health check de la API
- \`GET /docs\` - Documentación Swagger UI
- \`GET /redoc\` - Documentación Redoc
- \`POST /api/v1/auth/register\` - Registrar usuario
- \`POST /api/v1/auth/login\` - Login de usuario
- \`GET /api/v1/auth/me\` - Perfil de usuario actual

## 🚀 FLUJO DE DESARROLLO RECOMENDADO

### 1. Configuración inicial
\`\`\`bash
# Activar entorno virtual (si no está activo)
source .venv/bin/activate

# Instalar dependencias (si es primera vez)
./scripts.sh install

# Iniciar servicios
./scripts.sh start
\`\`\`

### 2. Durante el desarrollo
- Usar \`./scripts.sh status\` para ver estado
- Usar \`./scripts.sh format\` antes de commits
- Ver logs con \`./scripts.sh logs\`

### 3. Al terminar
\`\`\`bash
./scripts.sh stop    # Detener servicios
# o dejar corriendo para pruebas
\`\`\`

## 💡 CONSEJOS PARA CURSOR
1. **Ctrl+I** para preguntar sobre código específico
2. **Ctrl+K** para comandos rápidos
3. **Revisar estructura** en el explorador de archivos
4. **Usar terminal integrada** para scripts

## 📊 MONITOREO
- **Health check**: http://localhost:8000/health
- **Swagger UI**: http://localhost:8000/docs  
- **Logs en tiempo real**: \`./scripts.sh logs\`
- **Estado de servicios**: \`./scripts.sh status\`

## 🔄 MANTENIMIENTO
\`\`\`bash
# Limpiar caché
./scripts.sh clean

# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Verificar tipos (si mypy está instalado)
mypy app/
\`\`\`

---

**📌 Nota para la IA (Cursor)**: 
Este proyecto ya tiene scripts automatizados (\`scripts.sh\`) que manejan la mayoría de tareas. 
Cuando el usuario necesite ejecutar comandos, sugerir usar estos scripts en lugar de comandos manuales.
