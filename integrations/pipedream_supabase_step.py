"""
Pipedream Step: Telegram → Supabase
===================================
Conecta Telegram con Supabase para guardar tareas.

⚠️ NOTA: Configura las credenciales en Pipedream → Project → Secrets
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("TelegramSupabase")


def get_env_or_raise(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"❌ Variable '{key}' no configurada en Secrets")
    return value


class SupabaseClient:
    def __init__(self, url: str, service_key: str):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def insert(self, table: str, data: Dict) -> Any:
        import httpx
        url = f"{self.url}/rest/v1/{table}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self.headers, json=data)
                if response.status_code in [200, 201]:
                    log.info(f"✅ Insertado en {table}")
                    return response.json()
                else:
                    log.error(f"❌ Error {response.status_code}: {response.text}")
                    return None
        except Exception as e:
            log.error(f"❌ Error: {str(e)}")
            return None


INTENCIONES = {
    "registrar_mascota": {"keywords": ["registrar", "crear", "nuevo", "mascota"], "tipo": "feature"},
    "registrar_emocion": {"keywords": ["emocion", "estado", "feliz", "triste"], "tipo": "feature"},
    "estadisticas": {"keywords": ["estadistica", "reporte", "grafico"], "tipo": "query"},
    "problema": {"keywords": ["problema", "error", "bug"], "tipo": "bug"}
}


def clasificar_intencion(texto: str) -> Dict[str, str]:
    texto_lower = texto.lower()
    for intencion, config in INTENCIONES.items():
        if any(kw in texto_lower for kw in config["keywords"]):
            return {"intencion": intencion, "tipo": config["tipo"]}
    return {"intencion": "general", "tipo": "general"}


def handler(event, steps):
    log.info("=" * 50)
    log.info("INICIO: Telegram → Supabase")
    log.info("=" * 50)
    
    # Configuración desde Secrets
    supabase_url = get_env_or_raise("SUPABASE_URL")
    service_key = get_env_or_raise("SUPABASE_SERVICE_ROLE_KEY")
    
    log.info(f"URL: {supabase_url}")
    
    # Obtener datos de Telegram
    telegram_data = None
    if event and event.get("message"):
        telegram_data = event["message"]
    elif steps:
        for step_data in steps.values() if isinstance(steps, dict) else []:
            if isinstance(step_data, dict) and step_data.get("message"):
                telegram_data = step_data["message"]
                break
    
    if not telegram_data:
        telegram_data = {
            "chat": {"id": "test"},
            "from": {"id": "test", "username": "test"},
            "text": "Test de conexión"
        }
    
    chat_id = str(telegram_data.get("chat", {}).get("id", "unknown"))
    username = telegram_data.get("from", {}).get("username", "unknown")
    mensaje = telegram_data.get("text", "")
    
    log.info(f"Chat: {chat_id}, Mensaje: {mensaje[:50]}...")
    
    # Clasificar
    clasificacion = clasificar_intencion(mensaje)
    log.info(f"Intención: {clasificacion['intencion']}")
    
    # Crear tarea
    client = SupabaseClient(supabase_url, service_key)
    
    tarea_data = {
        "titulo": f"[{clasificacion['intencion'].upper()}] {mensaje[:100]}",
        "descripcion": mensaje,
        "tipo": clasificacion["tipo"],
        "estado": "pendiente",
        "prioridad": 3,
        "solicitante": username,
        "telegram_chat_id": chat_id,
        "intencion": clasificacion["intencion"],
        "created_at": datetime.utcnow().isoformat()
    }
    
    resultado = client.insert("tareas", tarea_data)
    
    response = {
        "success": bool(resultado),
        "chat_id": chat_id,
        "intencion": clasificacion["intencion"],
        "tarea_creada": resultado is not None,
        "tarea_id": resultado[0].get("id") if resultado else None,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if resultado:
        log.info(f"✅ Tarea creada: {response['tarea_id']}")
    else:
        log.error("❌ Error creando tarea")
    
    return response
