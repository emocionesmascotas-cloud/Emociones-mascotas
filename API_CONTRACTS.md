# 📋 API Contracts - Ecosistema Emociones Mascotas

## 📌 Resumen

Este documento define los contratos JSON entre Pipedream y Replit para la integración del ecosistema Emociones Mascotas.

---

## 🔐 Seguridad

### Headers de Autenticación

| Header | Descripción |
|--------|-------------|
| `X-Webhook-Signature` | Firma HMAC-SHA256 del payload |
| `X-GitHub-Event` | Tipo de evento GitHub (opcional) |
| `X-GitHub-Delivery` | ID único de entrega (opcional) |

### Formato de Firma

```
X-Webhook-Signature: sha256=<hmac_hex_digest>
```

El HMAC se calcula con:
- **Key**: `PIPEDREAM_WEBHOOK_SECRET` o `WEBHOOK_SECRET`
- **Algorithm**: HMAC-SHA256
- **Input**: Raw body del request

---

## 📥 Contrato: Pipedream → Replit

### Endpoint

```
POST https://tu-replit.your-repl.repl.co/api/webhook/pipedream
Content-Type: application/json
X-Webhook-Signature: sha256=<signature>
```

### Schema Base del Payload

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WebhookPayload",
  "type": "object",
  "required": ["event_type", "source"],
  "properties": {
    "event_type": {
      "type": "string",
      "description": "Tipo de evento",
      "enum": [
        "github_push",
        "github_pr",
        "github_issue",
        "scheduled",
        "manual",
        "test"
      ]
    },
    "source": {
      "type": "string",
      "description": "Fuente del evento",
      "default": "pipedream",
      "examples": ["pipedream", "github", "manual"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp del evento"
    },
    "payload": {
      "type": "object",
      "description": "Datos específicos del evento"
    }
  }
}
```

### Ejemplo: Push de GitHub

```json
{
  "event_type": "github_push",
  "source": "github",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "ref": "refs/heads/main",
    "repository": {
      "id": 123456789,
      "full_name": "emocionesmascotas-cloud/Emociones-mascotas",
      "name": "Emociones-mascotas",
      "owner": {
        "login": "emocionesmascotas-cloud"
      }
    },
    "commits": [
      {
        "id": "abc123def456",
        "message": "feat: agregar nueva funcionalidad",
        "author": {
          "name": "Usuario",
          "email": "usuario@example.com"
        }
      }
    ],
    "pusher": {
      "name": "usuario",
      "email": "usuario@example.com"
    },
    "sender": {
      "login": "usuario",
      "avatar_url": "https://avatars.githubusercontent.com/u/1234567"
    }
  }
}
```

### Ejemplo: Pull Request

```json
{
  "event_type": "github_pr",
  "source": "github",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "action": "opened",
    "number": 42,
    "pull_request": {
      "id": 987654321,
      "number": 42,
      "title": "feat: nueva característica",
      "body": "Descripción del PR",
      "state": "open",
      "draft": false,
      "user": {
        "login": "usuario",
        "avatar_url": "https://avatars.githubusercontent.com/u/1234567"
      },
      "head": {
        "ref": "feature/nueva-caracteristica",
        "sha": "abc123"
      },
      "base": {
        "ref": "main",
        "sha": "def456"
      },
      "labels": [
        {"id": 1, "name": "enhancement", "color": "84b6eb"}
      ],
      "url": "https://github.com/emocionesmascotas-cloud/Emociones-mascotas/pull/42"
    },
    "repository": {
      "id": 123456789,
      "full_name": "emocionesmascotas-cloud/Emociones-mascotas"
    },
    "sender": {
      "login": "usuario"
    }
  }
}
```

### Ejemplo: Issue

```json
{
  "event_type": "github_issue",
  "source": "github",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "action": "opened",
    "issue": {
      "id": 111222333,
      "number": 15,
      "title": "Bug: error al registrar emoción",
      "body": "Pasos para reproducir...",
      "state": "open",
      "user": {
        "login": "reportero",
        "avatar_url": "https://avatars.githubusercontent.com/u/7654321"
      },
      "labels": [
        {"id": 1, "name": "bug", "color": "d73a4a"},
        {"id": 2, "name": "priority:high", "color": "b60205"}
      ],
      "assignees": [
        {"login": "asignado"}
      ],
      "url": "https://github.com/emocionesmascotas-cloud/Emociones-mascotas/issues/15"
    },
    "repository": {
      "id": 123456789,
      "full_name": "emocionesmascotas-cloud/Emociones-mascotas"
    },
    "sender": {
      "login": "reportero"
    }
  }
}
```

### Ejemplo: Evento Programado (Cron)

```json
{
  "event_type": "scheduled",
  "source": "pipedream",
  "timestamp": "2024-01-15T09:00:00Z",
  "payload": {
    "schedule": "0 9 * * 1-5",
    "description": "Resumen diario - Lunes a Viernes 9:00 UTC",
    "context": {
      "last_run": "2024-01-14T09:00:00Z",
      "next_run": "2024-01-16T09:00:00Z"
    }
  }
}
```

---

## 📤 Contrato: Replit → Pipedream (Respuestas)

### Schema de Respuesta Exitosa

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WebhookResponse",
  "type": "object",
  "required": ["success", "message", "event_type", "processed_at"],
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Indica si el evento fue procesado exitosamente"
    },
    "message": {
      "type": "string",
      "description": "Mensaje descriptivo del resultado"
    },
    "event_type": {
      "type": "string",
      "description": "Tipo de evento que fue procesado"
    },
    "processed_at": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp de procesamiento"
    },
    "data": {
      "type": "object",
      "description": "Datos adicionales del procesamiento",
      "properties": {
        "github": {
          "type": "object",
          "description": "Resultado del procesamiento de GitHub"
        },
        "telegram": {
          "type": "object", 
          "description": "Resultado de notificación Telegram"
        },
        "notion": {
          "type": "object",
          "description": "Resultado de operación en Notion"
        }
      }
    }
  }
}
```

### Ejemplo: Respuesta Exitosa

```json
{
  "success": true,
  "message": "Evento github_push procesado exitosamente",
  "event_type": "github_push",
  "processed_at": "2024-01-15T10:30:05Z",
  "data": {
    "github": {
      "repository": "emocionesmascotas-cloud/Emociones-mascotas",
      "branch": "main",
      "commits": 3,
      "pusher": "usuario"
    },
    "telegram": {
      "status": "sent",
      "chat_id": "123456789"
    }
  }
}
```

### Ejemplo: Respuesta de Error

```json
{
  "success": false,
  "message": "Error procesando evento: Token de Notion inválido",
  "event_type": "github_issue",
  "processed_at": "2024-01-15T10:30:05Z",
  "data": null
}
```

---

## 🔄 Pipedream: Estructura de Workflow

### Step 1: Trigger (GitHub)

```javascript
// Configure trigger
module.exports = {
  type: "source",
  key: "github-newPush",
  name: "New Push",
  version: "0.0.3",
  props: {
    github: { type: "app", app: "github" },
    repo: { type: "string", label: "Repo", description: "Nombre del repositorio" }
  },
  hooks: {
    async activate() { /* subscribe */ },
    async deactivate() { /* unsubscribe */ }
  },
  async run(event) {
    this.$emit(event, { summary: `Push to ${event.repository.full_name}` });
  }
}
```

### Step 2: Transform (Node.js)

```javascript
async (steps, { axios }) => {
  // Transformar al schema esperado por Replit
  const eventType = detectEventType(steps.trigger.context);
  
  return {
    event_type: eventType,
    source: 'github',
    timestamp: new Date().toISOString(),
    payload: transformPayload(steps.trigger event)
  };
}

function detectEventType(context) {
  if (context.event === 'push') return 'github_push';
  if (context.event === 'pull_request') return 'github_pr';
  if (context.event === 'issues') return 'github_issue';
  return 'unknown';
}
```

### Step 3: HTTP Request (POST to Replit)

```javascript
async (steps, { axios }) => {
  const payload = steps.transform.$return_value;
  const secret = steps.auth.webhook_secret; // De tus credenciales
  
  // Calcular HMAC
  const crypto = require('crypto');
  const body = JSON.stringify(payload);
  const signature = 'sha256=' + crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');
  
  // Enviar a Replit
  const response = await axios.post(
    'https://tu-replit.your-repl.repl.co/api/webhook/pipedream',
    payload,
    {
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature
      }
    }
  );
  
  console.log('Response:', response.data);
  return response.data;
}
```

---

## 📊 Endpoints Adicionales

### GET /api/status

Estado de todos los servicios conectados.

```bash
curl https://tu-replit.your-repl.repl.co/api/status
```

**Respuesta:**

```json
{
  "status": "healthy",
  "services": {
    "notion": "healthy",
    "telegram": "healthy"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /api/health

Health check simple.

```bash
curl https://tu-replit.your-repl.repl.co/api/health
```

**Respuesta:**

```json
{
  "status": "ok",
  "service": "emociones-mascotas-api"
}
```

### GET /api/info

Información de la API.

```bash
curl https://tu-replit.your-repl.repl.co/api/info
```

**Respuesta:**

```json
{
  "name": "Emociones Mascotas API",
  "version": "1.0.0",
  "endpoints": {
    "webhook_pipedream": "POST /api/webhook/pipedream",
    "webhook_telegram": "POST /api/webhook/telegram",
    "status": "GET /api/status"
  },
  "integrations": ["Notion", "Telegram", "GitHub", "Pipedream"]
}
```

### POST /api/webhook/telegram

Webhook para el bot de Telegram.

```bash
curl -X POST https://tu-replit.your-repl.repl.co/api/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{"update_id": 123456789, "message": {...}}'
```

---

## 🔧 Variables de Entorno

### .env.example

```bash
# =============================================================================
# EMOCIONES MASCOTAS - CONFIGURACIÓN
# =============================================================================

# -----------------------------------------------------------------------------
# NOTION
# -----------------------------------------------------------------------------
# Token de integración de Notion
# Obtener en: https://www.notion.so/my-integrations
NOTION_INTEGRATION_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ID de la database de tareas (opcional)
NOTION_TASKS_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# -----------------------------------------------------------------------------
# TELEGRAM
# -----------------------------------------------------------------------------
# Token del bot de Telegram
# Obtener de @BotFather en Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Chat ID para notificaciones (tu ID o ID del canal)
TELEGRAM_CHAT_ID=123456789

# -----------------------------------------------------------------------------
# WEBHOOKS & SEGURIDAD
# -----------------------------------------------------------------------------
# Secreto para validar webhooks de Pipedream
PIPEDREAM_WEBHOOK_SECRET=your_webhook_secret_here

# Alias alternativo
WEBHOOK_SECRET=your_webhook_secret_here

# -----------------------------------------------------------------------------
# GITHUB (Opcional)
# -----------------------------------------------------------------------------
# Token personal de GitHub para API (opcional)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Repositorio por defecto
DEFAULT_REPO=emocionesmascotas-cloud/Emociones-mascotas

# -----------------------------------------------------------------------------
# APP CONFIG
# -----------------------------------------------------------------------------
# Modo debug (true/false)
DEBUG=true

# Nivel de logging
LOG_LEVEL=INFO

# Puerto del servidor
PORT=5000
```

---

## 📝 Notas de Implementación

### 1. Validación de Firmas

La validación de firmas es **crítica** para la seguridad:

```python
# ❌ NO HACER ESTO (inseguro)
def unsafe_verify(payload, signature, secret):
    return signature == secret  # Comparación directa

# ✅ HACER ESTO (seguro)
def safe_verify(payload, signature, secret):
    expected = 'sha256=' + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # Tiempo constante
```

### 2. Timeouts

Todos los requests HTTP deben tener timeouts:

```python
httpx.Client(timeout=30.0)  # Máximo 30 segundos
```

### 3. Logging

Registrar todos los eventos importantes:

```python
logger.info(f"Webhook recibido: {event_type}")
logger.error(f"Error: {str(e)}")
logger.warning(f"Webhook sin firma - desarrollo")
```

### 4. Rate Limits

Considerar rate limits de las APIs:

| Servicio | Límite |
|----------|--------|
| Notion | 3 requests/segundo |
| Telegram Bot | 30 msg/segundo |
| GitHub API | 5000 requests/hora |

---

## ✅ Checklist de Despliegue

- [ ] Configurar `PIPEDREAM_WEBHOOK_SECRET` en Replit
- [ ] Verificar que `notion_client.py` tiene acceso a la database
- [ ] Confirmar que `TELEGRAM_BOT_TOKEN` está configurado
- [ ] Probar webhook localmente con ngrok
- [ ] Configurar webhook en Pipedream
- [ ] Hacer test de flujo end-to-end
- [ ] Monitorear logs en Replit

---

## 📞 Soporte

Para preguntas sobre los contratos de API:
- Revisar `ARQUITECTURA_IMPLEMENTACION.md` para guía de setup
- Ver logs en Replit para debugging
- Consultar documentación de Pipedream
