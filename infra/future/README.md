# 🚀 Infraestructura Futura - Coolify + Supabase Self-Hosted

> **⚠️ NOTA:** Esta carpeta es para **FASE 2** cuando tengas presupuesto para auto-hospedar.

---

## 📋 Índice

1. [¿Qué es esto?](#qué-es-esto)
2. [Requisitos](#requisitos)
3. [Arquitectura](#arquitectura)
4. [Despliegue en Coolify](#despliegue-en-coolify)
5. [Variables de Entorno](#variables-de-entorno)
6. [Migración desde Supabase Cloud](#migración-desde-supabase-cloud)

---

## ¿Qué es esto?

Este directorio contiene los archivos para desplegar **Emociones Mascotas** usando:

- **Coolify**: Plataforma de auto-hosting (alternativa a Heroku/Vercel)
- **Supabase Self-Hosted**: Tu propia instancia de Supabase (Postgres, Auth, Storage)
- **Nginx**: Proxy reverso y balanceador de carga

### Cuándo usar esto

| Escenario | Solución |
|----------|----------|
| Prototipo / Free Tier | Supabase Cloud ✅ (Fase 1) |
| Proyecto personal / Startup | Supabase Cloud |
| **Empresa / Alto volumen** | Supabase Self-Hosted + Coolify (Fase 2) |
| Compliance / Datos sensibles | Supabase Self-Hosted (requerido) |

---

## Requisitos

### Hardware (mínimo para VPS)

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| RAM | 4 GB | 8 GB |
| CPU | 2 cores | 4 cores |
| Disco | 40 GB SSD | 100 GB SSD |

### Software

- Docker 20.10+
- Docker Compose 2.0+
- Un VPS o servidor propio (Hetzner, DigitalOcean, etc.)

---

## Arquitectura

```
                                    ┌──────────────┐
                                    │   USUARIOS   │
                                    └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                              ┌─────│    NGINX     │─────┐
                              │     │  (SSL, SSL)  │     │
                              │     └──────────────┘     │
                              │            │            │
                              ▼            ▼            ▼
                    ┌──────────────┐ ┌──────────┐ ┌──────────┐
                    │  Emociones   │ │  Supabase │ │  Supabase │
                    │    API       │ │    DB     │ │   Auth    │
                    │  (FastAPI)   │ │ (Postgres)│ │ (GoTrue) │
                    └──────────────┘ └──────────┘ └──────────┘
```

---

## Despliegue en Coolify

### Paso 1: Preparar el servidor

1. Instalar Coolify en tu VPS:
   ```bash
   curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
   ```

2. Acceder a Coolify via navegador: `https://tu-servidor:3000`

### Paso 2: Crear el proyecto

1. **New Project** → Nombre: `Emociones Mascotas`
2. **Add Server** → Conecta tu VPS

### Paso 3: Desplegar la base de datos

1. **Add Resource** → **Database** → **PostgreSQL**
2. Configuración:
   - Nombre: `emociones-db`
   - Imagen: `supabase/postgres:15.1.0.147`
   - Puerto: `5432`
   - Variables:
     - `POSTGRES_PASSWORD`: Tu contraseña segura

3. **Deploy**

### Paso 4: Desplegar la API

1. **Add Resource** → **Application** → **Dockerfile**
2. Repository: `https://github.com/emocionesmascotas-cloud/Emociones-mascotas`
3. Build Pack: Dockerfile
4. Dockerfile Path: `infra/future/Dockerfile.app`

5. Variables de Entorno (desde .env.local):
   ```
   DATABASE_URL=postgres://postgres:PASSWORD@IP-SERVIDOR:5432/postgres
   SUPABASE_URL=http://localhost:8000
   ```

### Paso 5: Configurar dominio

1. **Settings** → **Domain**
2. Añadir dominio: `api.emocionesmascotas.com`
3. SSL automático (Let's Encrypt)

---

## Variables de Entorno

### .env (Producción)

```bash
# =============================================================================
# SUPABASE SELF-HOSTED
# =============================================================================
POSTGRES_PASSWORD=tu-contraseña-super-secreta-min-32-chars
JWT_SECRET=tu-jwt-secret-de-al-menos-32-caracteres

# Claves públicas (generadas por ti)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# =============================================================================
# APLICACIÓN
# =============================================================================
DATABASE_URL=postgres://postgres:TU_PASSWORD@db:5432/postgres
DEBUG=false
LOG_LEVEL=INFO

# =============================================================================
# OPCIONALES
# =============================================================================
NOTION_INTEGRATION_KEY=ntn_...
TELEGRAM_BOT_TOKEN=123456:ABC...
PIPEDREAM_WEBHOOK_SECRET=tu-secret
```

---

## Migración desde Supabase Cloud

### Exportar datos de Supabase Cloud

1. Ve a tu proyecto en [supabase.com](https://supabase.com)
2. **SQL Editor** → Ejecuta:
   ```sql
   -- Exportar mascotas
   COPY mascotas TO '/tmp/mascotas.csv' WITH (FORMAT csv, HEADER);
   
   -- Exportar emociones
   COPY emociones TO '/tmp/emociones.csv' WITH (FORMAT csv, HEADER);
   ```

3. Descarga los archivos CSV

### Importar a Supabase Self-Hosted

```bash
# Conectar a tu servidor
psql -h tu-servidor -U postgres -d postgres

# En psql:
\i migrations/001_initial_schema.sql

# Importar datos
\copy mascotas(nombre,tipo,raza,edad,dueno_id) FROM '/tmp/mascotas.csv' CSV HEADER;
\copy emociones(mascota_id,tipo,intensidad,notas,fecha) FROM '/tmp/emociones.csv' CSV HEADER;
```

### Cambiar URL en tu app

Actualiza `SUPABASE_URL`:
```bash
# Antes (Cloud)
SUPABASE_URL=https://tu-proyecto.supabase.co

# Después (Self-hosted)
SUPABASE_URL=https://api.tu-dominio.com
```

---

## Comandos Útiles

```bash
# Iniciar todo
docker-compose -f docker-compose.supabase-coolify.yml up -d

# Ver logs
docker-compose -f docker-compose.supabase-coolify.yml logs -f

# Reiniciar un servicio
docker-compose -f docker-compose.supabase-coolify.yml restart db

# Backup de la base de datos
docker-compose exec db pg_dump -U postgres > backup_$(date +%Y%m%d).sql

# Actualizar imagenes
docker-compose -f docker-compose.supabase-coolify.yml pull
docker-compose -f docker-compose.supabase-coolify.yml up -d
```

---

## Costos Estimados

### Supabase Cloud (Fase 1)
| Plan | Precio |
|------|--------|
| Free | $0/mes |
| Pro | $25/mes |

### Self-Hosted (Fase 2)
| Recurso | Proveedor | Precio |
|---------|-----------|--------|
| VPS 4GB RAM | Hetzner | €5/mes |
| VPS 8GB RAM | Hetzner | €10/mes |
| VPS 16GB RAM | Hetzner | €20/mes |
| Dominio | Namecheap | $12/año |
| SSL | Let's Encrypt | $0 |

**Total Fase 2: ~$5-20/mes** (vs $25+ en cloud)

---

## Recursos

- [Coolify Documentation](https://docs.coollabs.io/coolify/)
- [Supabase Self-Hosted](https://supabase.com/docs/guides/self-hosting)
- [Docker Compose](https://docs.docker.com/compose/)

---

## Status: 🚧 PARA FASE 2

Este código está **preparado pero no instalado**. 

Usa **Supabase Cloud Free Tier** ahora y migrarás cuando tengas tráfico real.
