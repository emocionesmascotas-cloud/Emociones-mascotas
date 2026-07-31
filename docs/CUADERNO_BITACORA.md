# 📓 CUADERNO DE BITÁCORA - EMOCIONES MASCOTAS
## Documento Maestro de Arquitectura y Visión

> **Versión:** 1.0  
> **Última actualización:** 2026-07-24  
> **Estado:** Arquitectura Definida

---

## 🏛️ ARQUITECTURA DEL ECOSISTEMA

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           VISIÓN GENERAL                                  │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │  FAZ/GITHUB  │    │   CEREBRO    │    │       ALMACENAMIENTO      │  │
│  │   PAGES      │    │ REPLIT/PIPED │    │        SUPABASE           │  │
│  │  (Fachada)   │───▶│  (Lógica)    │───▶│     (Persistencia)       │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘  │
│         │                   │                          │                 │
│         │                   │                          │                 │
│         ▼                   ▼                          ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │  Landing +    │    │ Webhooks +   │    │ PostgreSQL + RLS +       │  │
│  │  Portfolio    │    │ Automatizac. │    │ Auth + Edge Functions    │  │
│  │  Estático     │    │ Agentes IA   │    │                          │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     SERVICIOS EXTERNOS                              │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │ │
│  │  │ Telegram │  │  DeepL   │  │ Blogger  │  │  Notion  │          │ │
│  │  │  (Chat) │  │ (Traduc) │  │ (Blog)   │  │  (Docs)  │          │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 CAPAS DE LA ARQUITECTURA

### 1️⃣ FAZ (GitHub Pages) - `emocionesmascotas-cloud.github.io`
**Propósito:** Presencia digital pública, portfolio, landing page.

- HTML/CSS/JS estático
- Carga ultra-rápida
- SEO optimizado
- Sin lógica de negocio
- Siempre disponible (CDN global)

**Archivos:**
```
/
├── index.html          # Landing principal
├── static/
│   ├── css/styles.css  # Estilos
│   └── js/app.js       # Frontend (solo UI)
```

**Regla de oro:** GitHub Pages NUNCA ejecuta Python ni conecta a bases de datos. Solo sirve archivos estáticos.

---

### 2️⃣ CEREBRO (Replit/Pipedream) - Lógica Inteligente

#### **Pipedream Workflows**
- Automatizaciones de eventos
- Conexión Telegram → Supabase
- Triggers y acciones
- Sin servidor propio

#### **Replit (Futuro)**
- API REST personalizada
- Agentes de IA (Pepita, Dana, Rita, Carlos)
- Procesamiento de lenguaje natural
- Scheduling de tareas

**Flujo actual Telegram:**
```
Telegram → Pipedream Webhook → Clasificar → Supabase → Notificar
```

---

### 3️⃣ ALMACENAMIENTO (Supabase) - `pszlobjlqqwwacwyltce.supabase.co`

**Tablas principales:**

| Tabla | Propósito |
|-------|-----------|
| `agentes` | Registro de agentes (Pepita, Dana, Rita, Carlos) |
| `tareas` | Tareas pendientes, en proceso, completadas |
| `system_config` | Configuración del sistema |

**Seguridad:**
- Row Level Security (RLS) habilitado
- Políticas públicas para desarrollo
- Service Role Key solo en servidor

---

### 4️⃣ TRADUCCIÓN INTELIGENTE (DeepL) - Preparado

**Casos de uso:**
- Contenido multilenguaje (ES/EN/PT)
- Traducción de descripciones de servicios
- Localización de FAQs y tutorials

**Placeholder preparado:** `integrations/deepl_connector.py` (futuro)

---

## 🎯 OBJETIVO SUPREMO

### Generación de Ingresos en Dólares

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EMBUDO DE MONETIZACIÓN                            │
│                                                                      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐    │
│   │   TRAFFIC   │────▶│   LEAD      │────▶│   CONVERSIÓN    │    │
│   │   (Telegram │     │   Magnet    │     │   Fiverr/       │    │
│   │    + SEO)   │     │   + Free    │     │   Afiliados     │    │
│   │             │     │   Content   │     │                 │    │
│   └─────────────┘     └─────────────┘     └─────────────────┘    │
│         │                   │                       │              │
│         ▼                   ▼                       ▼              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐    │
│   │  Automatiz. │     │  Email/     │     │  $ USD Income   │    │
│   │  Servicios  │     │  WhatsApp   │     │  + Calidad de  │    │
│   │  Fiverr     │     │  Sequence   │     │  Vida Familiar  │    │
│   └─────────────┘     └─────────────┘     └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Servicios para Fiverr
1. **Automatización de redes sociales** - Configuro flujos Telegram/IG
2. **Landing pages** - Creo landing pages estáticas optimizadas
3. **Integraciones API** - Conecto sistemas con Supabase/Pipedream
4. **Chatbots** - Bots de Telegram/WhatsApp personalizados

### Embudos de Afiliados
1. **Content Marketing** - Artículos en Blogger (automático)
2. **Notificaciones Telegram** - Promociones y contenido valioso
3. **Email Marketing** - Secuencias automatizadas

---

## 📜 REGLAS DE ORO PARA AUTOMATIZACIONES

### 🔐 SEGURIDAD

```python
# ✅ SIEMPRE usar variables de entorno
import os
API_KEY = os.environ.get("API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")

# ❌ NUNCA hardcodear secrets
# API_KEY = "mi_key_secreta"  # PROHIBIDO
```

**Secrets permitidos:**
- En `.env` local (para desarrollo)
- En Pipedream → Project → Secrets
- En Replit → Secrets
- En GitHub → Settings → Secrets

**Secrets PROHIBIDOS en código:**
- Nunca en archivos `.py`
- Nunca en commits
- Nunca en logs

---

### 🧩 TAREAS ATÓMICAS

**Principio:** Cada función hace UNA cosa bien hecha.

```python
# ✅ Correcto: Función pequeña y focused
def clasificar_intencion(texto: str) -> str:
    """Clasifica el mensaje en una intención."""
    pass

def guardar_tarea(tarea: dict) -> str:
    """Guarda en Supabase y retorna ID."""
    pass

def notificar_telegram(chat_id: str, mensaje: str) -> bool:
    """Envía mensaje y retorna éxito."""
    pass

# ❌ Incorrecto: Función gigante que hace todo
def proceso_completo(event):
    # 200 líneas de todo
    pass
```

**Ventajas:**
- Testable
- Reutilizable
- Debuggeable
- Mantenible

---

### 📦 CONTROL DE VERSIONES

```bash
# ✅ Commits atómicos y descriptivos
git commit -m "feat: add Telegram to Supabase webhook"
git commit -m "fix: correct static path in index.html"
git commit -m "docs: add Supabase schema"

# ❌ Commits vagos o grandes
git commit -m "fixes"
git commit -m "updates and stuff"
```

**Estructura de commits:**
```
tipo: descripción corta

- cambio 1
- cambio 2
```

**Tipos permitidos:**
| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Documentación |
| `chore` | Mantenimiento |
| `refactor` | Refactorización |

---

### 🔄 PIPEDREAM WORKFLOWS

```python
# ✅ Estructura recomendada
def handler(pd: "pipedream", event, steps):
    # 1. Extraer datos
    data = extract_data(event, steps)
    
    # 2. Validar
    if not validate(data):
        return {"error": "Invalid data"}
    
    # 3. Procesar
    result = process(data)
    
    # 4. Guardar
    save_to_supabase(result)
    
    # 5. Notificar
    notify(result)
    
    return {"success": True}

# ❌ Sin validación ni manejo de errores
def handler(pd, event, steps):
    return httpx.post(url, json=event)
```

---

### 🗄️ SUPABASE

```python
# ✅ Usar headers correctos
headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ✅ Nombres de tablas en singular
# tareas, agentes, mascotas (NO task_list, agents)

# ✅ Siempre validar antes de insertar
if not data.get("titulo"):
    return {"error": "Título requerido"}
```

---

### 📁 ESTRUCTURA DEL REPOSITORIO

```
Emociones-mascotas/
├── index.html              # Landing GitHub Pages (estático)
├── main.py                 # API FastAPI (futuro)
│
├── app/                    # Backend FastAPI
│   ├── api/                # Rutas
│   ├── models/             # Modelos SQLAlchemy
│   └── services/           # Lógica de negocio
│
├── integrations/           # Conectores externos
│   ├── supabase_connector.py
│   ├── deepl_connector.py   # Futuro
│   └── pipedream_*.py
│
├── departments/             # Agentes especializados
│   ├── marketing/           # Dana
│   ├── analytics/          # Rita
│   └── publishing/         # Carlos
│
├── core/                   # Motor de agentes
│   ├── base_agent.py
│   └── pepita_router.py
│
├── prompts/                # System prompts
│   ├── system_prompts/
│   └── skills/
│
├── docs/                   # Documentación
│   ├── CUADERNO_BITACORA.md  # ← Este archivo
│   ├── SUPABASE_SCHEMA.sql
│   └── PIPEDREAM_STEP.py
│
├── static/                 # Archivos estáticos (CSS, JS)
│
└── templates/              # Templates FastAPI
```

---

## 🚀 ROADMAP

### Fase 1: Fundamentos ✅
- [x] Landing en GitHub Pages
- [x] Schema Supabase
- [x] Pipeline Telegram → Supabase
- [x] Agente Carlos (publicador)

### Fase 2: Motor de Agentes (En curso)
- [ ] Pepita (planificador)
- [ ] Dana (marketing)
- [ ] Rita (supervisor)

### Fase 3: Monetización
- [ ] Integración DeepL
- [ ] Publicación automática Blogger
- [ ] Notificaciones Telegram premium

### Fase 4: Escalamiento
- [ ] Múltiples idiomas
- [ ] Embudos automatizados
- [ ] Integración Stripe/Paddle

---

## 📝 CHANGELOG

| Fecha | Commit | Descripción |
|-------|--------|-------------|
| 2026-07-24 | `32ed0b0` | docs: add schema y Pipedream step |
| 2026-07-24 | `6364a91` | feat: add index.html para GitHub Pages |
| 2026-07-24 | `776a8fc` | feat: add Pipedream Supabase step |
| 2026-07-24 | `6309224` | feat: add Carlos publisher agent |
| 2026-07-24 | `4943099` | feat: motor de agentes v2.0 |

---

## 💡 PRINCIPIOS FUNDAMENTALES

1. **Simplicidad primero** - No sobre-ingenierizar
2. **Automatizar lo repetitivo** - Tiempo es dinero
3. **Código legible** - El yo del futuro te lo agradecerá
4. **SIEMPRE testear** - No hacer push sin probar
5. **Documentar decisiones** - El why importa más que el what
6. **Ingresos en dólares** - Cada feature debe contribuir al objetivo

---

*Documento vivo - Actualizar con cada decisión arquitectural significativa.*
