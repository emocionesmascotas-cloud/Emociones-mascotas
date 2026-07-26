# =============================================================================
# Dockerfile - Emociones Mascotas API
# =============================================================================
# Imagen optimizada para producción

FROM python:3.11-slim

# =============================================================================
# METADATA
# =============================================================================
LABEL maintainer="Emociones Mascotas Team"
LABEL description="FastAPI backend for Emociones Mascotas"

# =============================================================================
# CONFIGURACIÓN INICIAL
# =============================================================================
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# DEPENDENCIAS DE PYTHON
# =============================================================================
# Crear virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requirements primero (para cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias de producción
RUN pip install --no-cache-dir \
    gunicorn \
    uvloop \
    httpx \
    psycopg2-binary

# =============================================================================
# CÓDIGO DE LA APLICACIÓN
# =============================================================================
COPY . .

# =============================================================================
# USUARIO NO PRIVILEGIADO
# =============================================================================
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# =============================================================================
# EXPOSICIÓN DE PUERTOS
# =============================================================================
EXPOSE 8000

# =============================================================================
# HEALTHCHECK
# =============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# =============================================================================
# COMANDO DE INICIO
# =============================================================================
# Usa gunicorn con uvicorn workers para producción
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "--workers", "2", "--threads", "4", "main:app"]
