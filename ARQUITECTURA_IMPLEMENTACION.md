# 🏗️ Arquitectura de Implementación - Ecosistema Emociones Mascotas

## 📊 Vista General de la Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ECOSISTEMA EMOCIONES MASCOTAS                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐     Webhooks      ┌───────────────┐      Triggers          │
│  │ PIPEDREAM│◄────────────────►│  REPLIT       │◄─────────────────┐     │
│  │  (Auto)  │   POST /webhook  │  FastAPI      │   Scheduled/Cron  │     │
│  └──────────┘                  └───────┬───────┘                   │     │
│                                        │                            │     │
│                          ┌─────────────┼─────────────┐              │     │
│                          ▼             ▼             ▼              │     │
│                    ┌──────────┐  ┌──────────┐  ┌──────────┐         │     │
│                    │ NOTION   │  │ TELEGRAM │  │ GITHUB   │         │     │
│                    │ (Docs)   │  │  (Bot)   │  │ (Repos)  │         │     │
│                    └──────────┘  └──────────┘  └──────────┘         │     │
│                                                                          │
│                          OFICINA DE CONTROL                              │
│                    (Tu sistema interno de gestión)                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Modelo de Seguridad

### Variables de Entorno (Simuladas)
El código usa `os.environ.get('KEY')` - Tú despliegas las variables reales en cada plataforma.

```python
# Ejemplo de uso seguro en código
import os

NOTION_TOKEN = os.environ.get('NOTION_INTEGRATION_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('PIPEDREAM_WEBHOOK_SECRET')
```

### Flujo de Validación
```
Pipedream → (HMAC-SHA256) → Replit → (Validar) → Procesar → Notion/Telegram
```

---

## 📁 Estructura de Carpetas

```
emociones-mascotas/
├── integrations/              # Módulos de integración
│   ├── __init__.py
│   ├── notion_client.py      # Cliente Notion
│   ├── telegram_bot.py       # Bot de Telegram
│   └── replit_api.py         # API endpoints (local)
├── .env.example              # Template de variables
├── main.py                    # Entry point con webhook handler
├── API_CONTRACTS.md          # Documentación de contratos
└── ARQUITECTURA_IMPLEMENTACION.md  # Este archivo
```

---

## 🚀 PASO 1: Configurar en Replit

### 1.1 Crear Proyecto Replit

1. Ve a [replit.com](https://replit.com)
2. Crea nuevo proyecto → **Python (FastAPI)**
3. Nombre: `emociones-mascotas-backend`

### 1.2 Configurar Secrets (Secrets → "Add Secret")

```env
# Notion
NOTION_INTEGRATION_KEY=ntn_xxxxxxxxxxxx

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Webhook Security
PIPEDREAM_WEBHOOK_SECRET=your_webhook_secret_here
WEBHOOK_SECRET=your_webhook_secret_here

# App Config
DEBUG=true
LOG_LEVEL=INFO
```

### 1.3 Subir Archivos a Replit

1. Copia todos los archivos del repositorio a tu proyecto Replit
2. Estructura:
   ```
   main.py
   integrations/
     __init__.py
     notion_client.py
     telegram_bot.py
     replit_api.py
   ```

### 1.4 Instalar Dependencias (En Replit's `pyproject.toml` o `requirements.txt`)

```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
notion-client>=2.2.0
python-telegram-bot>=20.0
httpx>=0.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### 1.5 Ejecutar en Replit

1. Click **Run** (▶️)
2. Replit mostrará la URL: `https://tu-proyecto.your-repl.repl.co`
3. Esta será tu `REPLIT_URL`

---

## 🌊 PASO 2: Configurar en Pipedream

### 2.1 Crear Cuenta

1. Ve a [pipedream.com](https://pipedream.com)
2. Conecta tu cuenta de GitHub

### 2.2 Crear Nuevo Workflow

1. **New Workflow** → **HTTP Webhook**
2. Nombre: `emociones-mascotas-sync`

### 2.3 Configurar Trigger (HTTP Webhook)

1. Copia la URL del webhook: `https://webhook.pipedream.com/...`
2. **⚠️ IMPORTANTE:** Copia esta URL para usarla en la configuración de Pipedream

### 2.4 Configurar Steps (Flujo de Automatización)

#### Step 1: GitHub (Source)
```
Trigger: New Push / New PR / New Issue
Repository: emocionesmascotas-cloud/Emociones-mascotas
```

#### Step 2: Code - Transformar Payload

```javascript
// Node.js code
async () => {
  const { data } = steps;
  
  // Transformar al schema esperado
  return {
    event_type: data.type || 'push',
    source: 'github',
    timestamp: new Date().toISOString(),
    payload: {
      action: data.action,
      repository: data.repository.full_name,
      sender: data.sender.login,
      data: data
    }
  };
}
```

#### Step 3: HTTP Request → POST a Replit

```javascript
// POST al webhook de Replit
await $http.post('https://tu-proyecto.your-repl.repl.co/webhook/pipedream', {
  headers: {
    'Content-Type': 'application/json',
    'X-Webhook-Signature': 'sha256=' + computeHmac(secret, body)
  },
  body: transformPayload(data)
});
```

### 2.5 Recursos de Pipedream

| Recurso | Descripción |
|---------|-------------|
| **GitHub Source** | Detecta eventos de repositorio |
| **Schedule** | Cron para tareas periódicas |
| **HTTP Webhook** | Recibe webhooks externos |
| **Slack** | Notificaciones |
| **Notion** | Actualizar databases |

---

## 📋 PASO 3: Configurar en Notion

### 3.1 Crear Integración

1. Ve a [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. **New integration** → Nombre: `Emociones Mascotas Bot`
3. Copia el **Internal Integration Token** (`ntn_...`)

### 3.2 Compartir Base de Datos

1. Abre tu página/database de Notion
2. Click en **...** → **Add connections** → Selecciona tu integración
3. La integración tendrá acceso de lectura/escritura

### 3.3 Estructura Sugerida de Database

```
📊 Emociones Mascotas - Dashboard
├── Page: Resumen Semanal
│   ├── 📝 Tareas Pendientes
│   ├── 📈 Métricas de GitHub
│   └── 📢 Alertas de Telegram
├── 📋 Tasks
│   ├── Nombre (title)
│   ├── Estado (select: pending, in_progress, done)
│   ├── Prioridad (select: low, medium, high)
│   ├── Fuente (select: github, telegram, manual)
│   └── Fecha Creación (date)
└── 📖 Conocimiento
    ├── Título
    ├── Contenido (rich_text)
    └── Tags (multi_select)
```

---

## 📱 PASO 4: Configurar Bot de Telegram

### 4.1 Crear Bot con BotFather

1. Abre Telegram → Busca `@BotFather`
2. Envía `/newbot`
3. Sigue las instrucciones:
   - Nombre: `Emociones Mascotas Bot`
   - Username: `emociones_mascotas_bot`
4. Copia el **Bot Token** (`123456789:ABC...`)

### 4.2 Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Mensaje de bienvenida |
| `/status` | Estado del sistema |
| `/stats` | Estadísticas de mascotas |
| `/help` | Ayuda |
| `/alerta <mensaje>` | Enviar alerta manual |

### 4.3 Configurar en Replit

Agrega el token a tus Secrets:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=tu_chat_id  # Tu ID de chat para notificaciones
```

---

## 🔄 PASO 5: Flujos de Automatización

### 5.1 GitHub → Replit → Notion → Telegram

```
GitHub Event (PR/Issue)
        │
        ▼
Pipedream (detecta evento)
        │
        ▼
POST /webhook/pipedream (Replit)
        │
        ├──► Validar firma HMAC
        │
        ▼
Procesar según tipo de evento
        │
        ├──► Notion: Crear tarea/documento
        │
        └──► Telegram: Notificar al usuario
```

### 5.2 Comandos de Telegram → Replit

```
Usuario envía mensaje a Telegram
        │
        ▼
Telegram Bot (webhook)
        │
        ▼
Procesar comando
        │
        ├──► Consultar estado
        │
        ├──► Actualizar Notion
        │
        └──► Responder al usuario
```

### 5.3 Scheduled Tasks (Cron)

```
Pipedream Schedule (cada hora)
        │
        ▼
Replit /webhook/pipedream (event_type: "scheduled")
        │
        ├──► Consultar métricas GitHub
        │
        ├──► Actualizar dashboard Notion
        │
        └──► Enviar resumen por Telegram
```

---

## 🔒 PASO 6: Validación de Seguridad

### 6.1 Firmas HMAC para Webhooks

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verifica que el webhook viene de Pipedream"""
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 6.2 Configurar en Pipedream

En tu step de HTTP Request, añade header:
```
X-Webhook-Signature: sha256=<hmac_computed>
```

### 6.3 Validar en Replit

El endpoint `/webhook/pipedream` valida automáticamente:
- Header `X-Webhook-Signature`
- Timestamp (máx 5 minutos)
- Hash HMAC-SHA256

---

## 📊 PASO 7: Monitoreo y Logs

### 7.1 Endpoints de Estado

| Endpoint | Descripción |
|----------|-------------|
| `GET /health` | Estado de salud del sistema |
| `GET /api/health` | Estado de la API |
| `GET /api/status` | Estado detallado con métricas |

### 7.2 Logging

```python
import logging

logger = logging.getLogger(__name__)

# En cada endpoint
logger.info(f"Webhook recibido: {event_type}")
logger.error(f"Error procesando evento: {error}")
```

### 7.3 Almacenar Logs

- **Replit**: Usa el panel de logs integrado
- **Notion**: Crea página de logs
- **Pipedream**: Historial de ejecuciones

---

## ✅ Checklist de Implementación

- [ ] Crear proyecto en Replit
- [ ] Configurar Secrets en Replit
- [ ] Subir archivos `integrations/` a Replit
- [ ] Crear workflow en Pipedream
- [ ] Conectar GitHub source en Pipedream
- [ ] Configurar HTTP POST a Replit
- [ ] Crear integración en Notion
- [ ] Compartir database con integración
- [ ] Crear bot en Telegram (BotFather)
- [ ] Agregar bot token a Replit secrets
- [ ] Probar flujo end-to-end
- [ ] Configurar alertas en Telegram

---

## 🆘 Troubleshooting

### Error: "Webhook signature verification failed"
- Verifica que `WEBHOOK_SECRET` en Replit coincide con Pipedream
- Asegúrate de incluir el prefijo `sha256=` en la firma

### Error: "Notion token invalid"
- Verifica que compartiste el database con la integración
- Confirma que el token empieza con `ntn_`

### Error: "Telegram bot not responding"
- Verifica que el bot está activo en @BotFather
- Confirma que `TELEGRAM_BOT_TOKEN` está configurado

### Error: "Replit URL not reachable"
- Asegúrate de que el proyecto está "Running" en Replit
- Verifica que el puerto 5000 está expuesto

---

## 📞 Próximos Pasos

1. **Desplegar en Replit** siguiendo los pasos
2. **Configurar Pipedream** con los workflows
3. **Conectar Notion** y Telegram
4. **Probar flujos** con eventos reales
5. **Monitorear** y ajustar según necesidad

¿Necesitas ayuda con algún paso específico? 🚀
