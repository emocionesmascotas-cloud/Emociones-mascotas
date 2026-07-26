# 🏢 Oficina v2.0 - Arquitectura del Sistema

> **Estado:** Diseño estructural  
> **Versión:** 2.0  
> **Planificador:** Pepita (interino, reemplaçable por Hermes)  
> **Modelo IA:** gpt-4o-mini (clasificación)

---

## 📊 Diagrama de Flujo

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              🏢 OFICINA v2.0                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                    │
│  │   USUARIO   │──────│  TELEGRAM   │──────│   PEPITA    │                    │
│  │  (Humano)   │      │   (Bot)     │      │ (Planificador)│                   │
│  └─────────────┘      └─────────────┘      └──────┬──────┘                    │
│                                                    │                            │
│                                    ┌───────────────┼───────────────┐            │
│                                    ▼               ▼               ▼            │
│                             ┌───────────┐   ┌───────────┐   ┌───────────┐      │
│                             │   AGENTE  │   │   AGENTE  │   │   AGENTE  │      │
│                             │  BACKEND  │   │ FRONTEND  │   │   DATA    │      │
│                             └─────┬─────┘   └─────┬─────┘   └─────┬─────┘      │
│                                   │               │               │            │
│                                   └───────────────┼───────────────┘            │
│                                                   │                            │
│                                                   ▼                            │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │                          📦 SUPABASE CLOUD                             │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐       │    │
│  │  │ agentes  │  │ tareas   │  │deptos    │  │ system_config   │       │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘       │    │
│  │       └─────────────┴─────────────┴─────────────────┘                  │    │
│  └───────────────────────────────────────┬───────────────────────────────────┘    │
│                                          │                                      │
│                                          ▼                                      │
│                              ┌───────────────────┐                             │
│                              │      NOTION       │                             │
│                              │   (Documentación) │                             │
│                              └───────────────────┘                             │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Datos Detallado

### Paso 1: Mensaje del Usuario
```
Usuario → Telegram Bot → Mensaje de texto
```

### Paso 2: Clasificación (Pepita)
```
Telegram → Pepita → Clasifica intención
         ↓
    gpt-4o-mini
         ↓
    { intención, urgencia, departamento_asignado }
```

### Paso 3: Distribución a Agentes
```
Pepita → Agent Router → Agente Backend
                        → Agente Frontend
                        → Agente Data
```

### Paso 4: Ejecución
```
Agente → Ejecuta tarea
       ↓
       → Registra en Supabase (agentes, tareas)
       → Documenta en Notion
       → Responde a Telegram
```

---

## 🗄️ Esquema de Tablas

### Tabla: `agentes`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| nombre | TEXT | Nombre del agente |
| tipo | TEXT | backend, frontend, data, general |
| estado | TEXT | activo, inactivo, en_tarea |
| gpt_model | TEXT | Modelo GPT utilizado |
| prompt_base | TEXT | Prompt de sistema |
| config | JSONB | Configuración adicional |
| created_at | TIMESTAMPTZ | Fecha de creación |
| updated_at | TIMESTAMPTZ | Última actualización |

### Tabla: `tareas`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| titulo | TEXT | Título de la tarea |
| descripcion | TEXT | Descripción detallada |
| tipo | TEXT | bug, feature, refactor, docs, deploy |
| estado | TEXT | pendiente, en_progreso, completado, fallido |
| prioridad | INTEGER | 1-5 (1=muy alta, 5=muy baja) |
| departamento_id | UUID | FK a departamentos |
| agente_asignado | UUID | FK a agentes (nullable) |
| solicitante | TEXT | Quién solicitó la tarea |
| telegram_chat_id | TEXT | Chat de origen |
| resultado | JSONB | Resultado de la ejecución |
| errores | TEXT | Mensajes de error |
| created_at | TIMESTAMPTZ | Fecha de creación |
| updated_at | TIMESTAMPTZ | Última actualización |
| completed_at | TIMESTAMPTZ | Fecha de completado |

### Tabla: `departamentos`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| nombre | TEXT | Nombre del departamento |
| descripcion | TEXT | Descripción |
| agentes_ids | UUID[] | Lista de agentes del depto |
| webhook_url | TEXT | Webhook para notificaciones |
| notion_page_id | TEXT | Página de Notion del depto |
| prioridad_default | INTEGER | Prioridad por defecto |
| created_at | TIMESTAMPTZ | Fecha de creación |
| updated_at | TIMESTAMPTZ | Última actualización |

### Tabla: `system_config`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| key | TEXT | Clave de configuración (PK) |
| value | JSONB | Valor (cualquier tipo) |
| descripcion | TEXT | Descripción del setting |
| categoria | TEXT | categoria, seguridad, integracion |
| updated_by | UUID | FK a agentes |
| updated_at | TIMESTAMPTZ | Última actualización |

---

## 🔌 Contratos de Interfaz

### 1. Telegram → Pepita

**Entrada:**
```json
{
  "update_id": 123456789,
  "message": {
    "chat": { "id": "123456789", "type": "private" },
    "from": { "id": 123456789, "username": "usuario" },
    "text": "Registrar nueva mascota",
    "date": 1700000000
  }
}
```

**Salida:**
```json
{
  "intencion": "registrar_mascota",
  "entidades": {
    "tipo": "mascota",
    "accion": "crear"
  },
  "urgencia": "normal",
  "departamento": "backend",
  "confianza": 0.95
}
```

---

### 2. Pepita → Agente

**Entrada:**
```json
{
  "tarea_id": "uuid-xxx",
  "instruccion": "Registrar Firulais como perro",
  "contexto": {
    "usuario": "usuario",
    "chat_id": "123456789"
  },
  "recursos": {
    "supabase_url": "https://xxx.supabase.co",
    "notion_token": "ntn_xxx"
  }
}
```

**Salida:**
```json
{
  "tarea_id": "uuid-xxx",
  "resultado": {
    "status": "completado",
    "datos": { "mascota_id": 123 },
    "mensaje": "Mascota Firulais registrada exitosamente"
  },
  "siguiente_paso": null,
  "errores": []
}
```

---

### 3. Agente → Supabase

**Insertar Tarea:**
```json
POST /tareas
{
  "titulo": "Registrar mascota Firulais",
  "tipo": "feature",
  "estado": "en_progreso",
  "departamento_id": "uuid-xxx",
  "solicitante": "usuario",
  "telegram_chat_id": "123456789"
}
```

**Actualizar Tarea:**
```json
PATCH /tareas?id=eq.uuid-xxx
{
  "estado": "completado",
  "resultado": { "mascota_id": 123 },
  "completed_at": "2024-01-15T10:30:00Z"
}
```

---

### 4. Agente → Notion

**Crear Página:**
```json
POST /pages
{
  "parent": { "database_id": "xxx" },
  "properties": {
    "title": { "title": [{ "text": { "content": "Tarea: Registrar mascota" }}]},
    "Estado": { "select": { "name": "Completado" }},
    "Agente": { "select": { "name": "Backend Agent" }}
  },
  "children": [
    { "type": "paragraph", "paragraph": { "rich_text": [{ "text": { "content": "Resultado..." }}]}}
  ]
}
```

---

## 🛡️ Seguridad

### Row Level Security (RLS)

```sql
-- Solo el agente puede modificar sus tareas
CREATE POLICY "agente_tareas_own" ON tareas
FOR ALL USING (agente_asignado = auth.uid());

-- system_config solo para admins
CREATE POLICY "admin_config" ON system_config
FOR ALL USING (categoria = 'admin');
```

### Variables de Entorno Requeridas

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Notion
NOTION_INTEGRATION_KEY=ntn_xxx

# Telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_ADMIN_CHAT_ID=xxx

# IA
OPENAI_API_KEY=sk-xxx
GPT_MODEL=gpt-4o-mini
```

---

## 📁 Estructura de Archivos

```
emociones-mascotas/
├── ARCHITECTURE.md          # Este documento
├── docs/
│   └── supabase_schema.sql  # Schema SQL para Supabase
├── integrations/
│   ├── supabase_connector.py
│   ├── notion_client.py
│   └── telegram_bot.py
├── agents/
│   ├── __init__.py
│   ├── base_agent.py        # Clase base
│   ├── backend_agent.py     # Agente de backend
│   ├── frontend_agent.py    # Agente de frontend
│   └── data_agent.py        # Agente de datos
├── scripts/
│   ├── migrate_notion_to_supabase.py
│   └── setup_supabase.py
└── infra/
    └── future/             # Para Fase 2
```

---

## 🚀 Despliegue

### 1. Crear tablas en Supabase
```bash
# Ejecutar en SQL Editor de Supabase
# Archivo: docs/supabase_schema.sql
```

### 2. Configurar integraciones
```bash
# Variables de entorno en Replit/Vercel/Coolify
```

### 3. Iniciar agentes
```python
from agents import BackendAgent, FrontendAgent, DataAgent

backend = BackendAgent()
frontend = FrontendAgent()
data = DataAgent()
```

---

## 📝 Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 2.0 | 2024-01 | Nueva estructura con Pepita como planificador |
| 1.0 | 2023-12 | Versión inicial |
