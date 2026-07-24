"""
Replit API - Emociones Mascotas
Endpoints FastAPI para recibir webhooks de Pipedream
"""

import os
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class WebhookPayload(BaseModel):
    """Schema del payload recibido de Pipedream."""
    event_type: str = Field(..., description="Tipo de evento: github, scheduled, manual, etc.")
    source: str = Field(default="pipedream", description="Fuente del evento")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    """Respuesta estándar del webhook."""
    success: bool
    message: str
    event_type: Optional[str] = None
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    data: Optional[Dict[str, Any]] = None


class GitHubPushPayload(BaseModel):
    """Payload para eventos de push de GitHub."""
    ref: str
    repository: Dict[str, Any]
    commits: List[Dict] = field(default_factory=list)
    sender: Dict[str, Any]


class GitHubPRPayload(BaseModel):
    """Payload para eventos de PR de GitHub."""
    action: str
    number: int
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]
    sender: Dict[str, Any]


class GitHubIssuePayload(BaseModel):
    """Payload para eventos de issues de GitHub."""
    action: str
    issue: Dict[str, Any]
    repository: Dict[str, Any]
    sender: Dict[str, Any]


class StatusCheckResponse(BaseModel):
    """Respuesta del endpoint de estado."""
    status: str
    services: Dict[str, str]
    timestamp: str


# =============================================================================
# VALIDACIÓN DE FIRMA
# =============================================================================

def verify_webhook_signature(
    payload: bytes,
    signature: Optional[str],
    secret: Optional[str] = None
) -> bool:
    """
    Verifica la firma HMAC-SHA256 del webhook.
    
    Args:
        payload: Cuerpo de la petición en bytes
        signature: Header X-Webhook-Signature o X-Hub-Signature-256
        secret: Secreto configurado (usa variable de entorno por defecto)
    
    Returns:
        True si la firma es válida
    """
    if not signature:
        logger.warning("No se proporcionó firma de webhook")
        return False
    
    webhook_secret = secret or os.environ.get('PIPEDREAM_WEBHOOK_SECRET') or os.environ.get('WEBHOOK_SECRET')
    
    if not webhook_secret:
        logger.warning("No hay secreto de webhook configurado -跳过 validación")
        return True  # En desarrollo, permitir sin validación
    
    # Soportar múltiples formatos de firma
    if signature.startswith('sha256='):
        expected = signature[7:]
    elif signature.startswith('v1='):
        expected = signature[3:]
    else:
        expected = signature
    
    computed = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(expected, computed)
    
    if not is_valid:
        logger.warning(f"Firma inválida. Expected: {expected[:16]}...")
    
    return is_valid


async def verify_request_signature(request: Request) -> bool:
    """Versión async para verificar firma desde request FastAPI."""
    body = await request.body()
    signature = request.headers.get('x-webhook-signature') or \
               request.headers.get('x-hub-signature-256')
    
    return verify_webhook_signature(body, signature)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(prefix="/api", tags=["Integrations"])


# =============================================================================
# WEBHOOK ENDPOINT
# =============================================================================

@router.post("/webhook/pipedream", response_model=WebhookResponse)
async def handle_pipedream_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    x_hub_signature: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery")
):
    """
    Endpoint principal para recibir webhooks de Pipedream.
    
    Este endpoint:
    1. Valida la firma HMAC (seguridad)
    2. Parsea el payload
    3. Despacha al módulo correspondiente (Notion/Telegram)
    4. Devuelve respuesta estandarizada
    
    Headers típicos:
    - X-Webhook-Signature: Firma HMAC-SHA256
    - X-GitHub-Event: Tipo de evento GitHub
    - X-GitHub-Delivery: ID único de entrega
    """
    body = await request.body()
    
    # Verificar firma
    signature = x_webhook_signature or x_hub_signature
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Firma de webhook inválida")
    
    # Parsear payload
    try:
        import json
        data = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")
    
    # Extraer tipo de evento
    event_type = data.get('event_type') or x_github_event or 'unknown'
    
    logger.info(f"Webhook recibido: {event_type}")
    
    # Procesar según tipo de evento
    try:
        result = await dispatch_event(event_type, data)
        
        return WebhookResponse(
            success=True,
            message=f"Evento {event_type} procesado exitosamente",
            event_type=event_type,
            data=result
        )
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return WebhookResponse(
            success=False,
            message=f"Error procesando evento: {str(e)}",
            event_type=event_type
        )


# =============================================================================
# DISPATCHER
# =============================================================================

async def dispatch_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Despacha el evento al módulo correspondiente.
    
    Args:
        event_type: Tipo de evento (github_push, github_pr, scheduled, etc.)
        payload: Datos del evento
    
    Returns:
        Resultado del procesamiento
    """
    results = {}
    
    # GitHub Events
    if event_type in ['github_push', 'push', 'push']:
        results['github'] = await handle_github_push(payload)
    
    elif event_type in ['github_pr', 'pull_request', 'pull_request.opened']:
        results['github'] = await handle_github_pr(payload)
    
    elif event_type in ['github_issue', 'issues', 'issues.opened']:
        results['github'] = await handle_github_issue(payload)
    
    # Scheduled Events
    elif event_type in ['scheduled', 'cron', 'schedule']:
        results['scheduler'] = await handle_scheduled_event(payload)
    
    # Manual Events
    elif event_type in ['manual', 'test']:
        results['test'] = {"status": "test_event_processed"}
    
    # Desconocido
    else:
        logger.warning(f"Tipo de evento desconocido: {event_type}")
        results['unknown'] = {"event_type": event_type}
    
    return results


async def handle_github_push(payload: Dict) -> Dict:
    """Procesa eventos de push de GitHub."""
    logger.info(f"Procesando push: {payload.get('repository', {}).get('full_name', 'unknown')}")
    
    # Extraer datos relevantes
    repo = payload.get('repository', {}).get('full_name', 'N/A')
    branch = payload.get('ref', 'N/A').replace('refs/heads/', '')
    commits_count = len(payload.get('commits', []))
    pusher = payload.get('pusher', {}).get('name', 'unknown')
    
    # Enviar notificación a Telegram
    try:
        from .telegram_bot import TelegramBot
        bot = TelegramBot()
        bot.send_alert(
            title=f"📦 Push a {repo}",
            message=f"Branch: `{branch}`\nCommits: {commits_count}\nPor: {pusher}",
            severity="info"
        )
    except Exception as e:
        logger.error(f"Error enviando notificación: {str(e)}")
    
    return {
        "repository": repo,
        "branch": branch,
        "commits": commits_count,
        "pusher": pusher
    }


async def handle_github_pr(payload: Dict) -> Dict:
    """Procesa eventos de Pull Request de GitHub."""
    action = payload.get('action', 'unknown')
    pr = payload.get('pull_request', {})
    repo = payload.get('repository', {}).get('full_name', 'N/A')
    pr_number = payload.get('number', 0)
    pr_title = pr.get('title', 'N/A')
    sender = payload.get('sender', {}).get('login', 'unknown')
    
    logger.info(f"Procesando PR #{pr_number}: {action}")
    
    # Enviar notificación a Telegram
    try:
        from .telegram_bot import TelegramBot
        bot = TelegramBot()
        
        emoji = "🆕" if action == "opened" else "🔄" if action == "synchronize" else "✅"
        bot.send_alert(
            title=f"{emoji} PR #{pr_number} - {action}",
            message=f"Repo: `{repo}`\nTítulo: {pr_title}\nPor: {sender}",
            severity="info" if action == "opened" else "success"
        )
    except Exception as e:
        logger.error(f"Error enviando notificación: {str(e)}")
    
    # Crear tarea en Notion si es PR nuevo
    if action == "opened":
        try:
            from .notion_client import NotionClient
            notion = NotionClient()
            # Aquí necesitarías el database_id configurado
            # notion.create_task_page(database_id, f"PR: {pr_title}", source="github")
        except Exception as e:
            logger.error(f"Error creando tarea en Notion: {str(e)}")
    
    return {
        "action": action,
        "pr_number": pr_number,
        "pr_title": pr_title,
        "repository": repo
    }


async def handle_github_issue(payload: Dict) -> Dict:
    """Procesa eventos de issues de GitHub."""
    action = payload.get('action', 'unknown')
    issue = payload.get('issue', {})
    repo = payload.get('repository', {}).get('full_name', 'N/A')
    issue_number = payload.get('issue', {}).get('number', 0)
    issue_title = issue.get('title', 'N/A')
    sender = payload.get('sender', {}).get('login', 'unknown')
    labels = [l.get('name', '') for l in issue.get('labels', [])]
    
    logger.info(f"Procesando Issue #{issue_number}: {action}")
    
    # Enviar notificación
    try:
        from .telegram_bot import TelegramBot
        bot = TelegramBot()
        
        emoji = "🐛" if "bug" in labels else "✨" if "enhancement" in labels else "📝"
        bot.send_alert(
            title=f"{emoji} Issue #{issue_number} - {action}",
            message=f"Repo: `{repo}`\nTítulo: {issue_title}\nLabels: {', '.join(labels) if labels else 'Ninguna'}\nPor: {sender}",
            severity="warning" if "bug" in labels else "info"
        )
    except Exception as e:
        logger.error(f"Error enviando notificación: {str(e)}")
    
    return {
        "action": action,
        "issue_number": issue_number,
        "issue_title": issue_title,
        "labels": labels,
        "repository": repo
    }


async def handle_scheduled_event(payload: Dict) -> Dict:
    """Procesa eventos programados (cron)."""
    logger.info("Procesando evento programado")
    
    # Aquí podrías:
    # 1. Consultar métricas de GitHub
    # 2. Actualizar dashboard de Notion
    # 3. Enviar resumen diario
    
    return {
        "status": "scheduled_event_processed",
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# ENDPOINTS DE UTILIDAD
# =============================================================================

@router.get("/status", response_model=StatusCheckResponse)
async def get_status():
    """
    Endpoint de estado del sistema.
    Verifica la conectividad con todos los servicios.
    """
    services = {}
    
    # Verificar Notion
    try:
        from .notion_client import NotionClient
        notion = NotionClient()
        services['notion'] = notion.health_check().get('status', 'unknown')
    except Exception as e:
        services['notion'] = f"error: {str(e)[:50]}"
    
    # Verificar Telegram
    try:
        from .telegram_bot import TelegramBot
        bot = TelegramBot()
        services['telegram'] = bot.health_check().get('status', 'unknown')
    except Exception as e:
        services['telegram'] = f"error: {str(e)[:50]}"
    
    # Estado general
    all_healthy = all(s == 'healthy' for s in services.values())
    
    return StatusCheckResponse(
        status="healthy" if all_healthy else "degraded",
        services=services,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "emociones-mascotas-api"}


# =============================================================================
# TELEGRAM WEBHOOK
# =============================================================================

@router.post("/webhook/telegram")
async def handle_telegram_webhook(request: Request):
    """
    Endpoint para recibir actualizaciones del bot de Telegram.
    
    Telegram envía updates cuando alguien envía un mensaje al bot.
    """
    try:
        from .telegram_bot import TelegramBot
        import json
        
        body = await request.body()
        update = json.loads(body.decode('utf-8'))
        
        bot = TelegramBot()
        response = bot.process_update(update)
        
        if response:
            # Log de respuesta (no necesariamente enviamos reply aquí)
            logger.info(f"Respuesta del bot: {response[:100]}...")
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"Error procesando webhook de Telegram: {str(e)}")
        return {"ok": False, "error": str(e)}


# =============================================================================
# INFO ENDPOINT
# =============================================================================

@router.get("/info")
async def get_info():
    """Información sobre la API y versiones."""
    return {
        "name": "Emociones Mascotas API",
        "version": "1.0.0",
        "description": "API para integrar Emociones Mascotas con servicios externos",
        "endpoints": {
            "webhook_pipedream": "POST /api/webhook/pipedream",
            "webhook_telegram": "POST /api/webhook/telegram",
            "status": "GET /api/status",
            "health": "GET /api/health",
            "info": "GET /api/info"
        },
        "integrations": ["Notion", "Telegram", "GitHub", "Pipedream"]
    }
