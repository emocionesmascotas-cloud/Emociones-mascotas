"""
=====================================================
PIPEDREAM STEP: Telegram → Supabase
=====================================================
Copia este código en tu paso "código1" de Pipedream

CONFIGURACIÓN PREVIA EN PIPEDREAM:
1. Ve a Project → Secrets
2. Añade:
   - SUPABASE_URL = https://pszlobjlqqwwacwyltce.supabase.co
   - SUPABASE_SERVICE_ROLE_KEY = tu_service_role_key
=====================================================
"""

import os
import logging
from datetime import datetime
import httpx

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("TelegramSupabase")


def handler(pd: "pipedream", event, steps):
    """
    Recibe mensaje de Telegram y lo guarda en Supabase.
    """
    log.info("=== Telegram → Supabase ===")
    
    # =============================================
    # 1. CONFIGURACIÓN
    # =============================================
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not SUPABASE_URL or not SERVICE_KEY:
        log.error("❌ Variables no configuradas en Secrets")
        return {"error": "Configuración missing"}
    
    # =============================================
    # 2. EXTRAER DATOS DE TELEGRAM
    # =============================================
    
    # El mensaje puede venir directo o de un paso anterior
    telegram_msg = None
    
    # Intentar del evento directo
    if event and event.get("message"):
        telegram_msg = event["message"]
    
    # Intentar de steps anteriores
    if not telegram_msg and steps:
        for step_key, step_data in steps.items():
            if isinstance(step_data, dict):
                if step_data.get("message"):
                    telegram_msg = step_data["message"]
                    break
                # Buscar en nested
                for k, v in step_data.items():
                    if isinstance(v, dict) and v.get("message"):
                        telegram_msg = v["message"]
                        break
    
    if not telegram_msg:
        log.warning("⚠️ No se encontró mensaje de Telegram")
        return {"status": "no_message"}
    
    # Extraer datos
    texto = telegram_msg.get("text", "")
    chat_id = str(telegram_msg.get("chat", {}).get("id", ""))
    username = telegram_msg.get("from", {}).get("username", "unknown")
    first_name = telegram_msg.get("from", {}).get("first_name", "")
    message_id = str(telegram_msg.get("message_id", ""))
    
    log.info(f"Chat: {chat_id}, User: @{username}")
    log.info(f"Mensaje: {texto[:50]}...")
    
    # =============================================
    # 3. CLASIFICAR INTENCIÓN
    # =============================================
    
    intencion = "general"
    tipo = "general"
    
    texto_lower = texto.lower()
    
    if any(k in texto_lower for k in ["registrar", "crear", "nuevo", "añadir", "agregar", "mascota"]):
        intencion = "registrar_mascota"
        tipo = "feature"
    elif any(k in texto_lower for k in ["emocion", "feliz", "triste", "ansioso", "estado"]):
        intencion = "registrar_emocion"
        tipo = "feature"
    elif any(k in texto_lower for k in ["estadistica", "reporte", "grafico", "informe"]):
        intencion = "estadisticas"
        tipo = "query"
    elif any(k in texto_lower for k in ["problema", "error", "no funciona", "bug"]):
        intencion = "problema"
        tipo = "bug"
    elif any(k in texto_lower for k in ["publicar", "enviar", "blog", "telegram"]):
        intencion = "publicar"
        tipo = "feature"
    
    log.info(f"Intensión: {intencion} ({tipo})")
    
    # =============================================
    # 4. GUARDAR EN SUPABASE
    # =============================================
    
    tarea_data = {
        "titulo": f"[{intencion.upper()}] {texto[:80]}",
        "descripcion": texto,
        "tipo": tipo,
        "estado": "pending",
        "intencion": intencion,
        "solicitante": username or first_name,
        "telegram_chat_id": chat_id,
        "telegram_message_id": message_id,
        "resultado": {
            "fuente": "telegram",
            "nombre_usuario": username,
            "primer_nombre": first_name
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    try:
        response = httpx.post(
            f"{SUPABASE_URL}/rest/v1/tareas",
            headers=headers,
            json=tarea_data,
            timeout=30.0
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            tarea_id = result[0].get("id") if result else None
            log.info(f"✅ Tarea creada: {tarea_id}")
            
            return {
                "success": True,
                "tarea_id": tarea_id,
                "intencion": intencion,
                "chat_id": chat_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            log.error(f"❌ Error {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": response.text
            }
            
    except httpx.ConnectError:
        log.error("❌ No se pudo conectar a Supabase")
        return {"error": "Connection failed"}
    except Exception as e:
        log.error(f"❌ Error: {str(e)}")
        return {"error": str(e)}


# =============================================
# NOTA: Pipedream pasa pd como primer argumento
# Si tu código es diferente, ajusta la firma
# =============================================
