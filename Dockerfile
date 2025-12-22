FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /code

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto (incluyendo el paquete app)
COPY . /code

# Asegurar que el paquete raíz `app` sea importable (para `app.main`)
ENV PYTHONPATH=/code

# Arrancar la aplicación FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
