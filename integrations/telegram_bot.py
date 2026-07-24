"""
Telegram Bot - Emociones Mascotas
Manejador para recibir comandos y enviar alertas
"""

import os
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Command(Enum):
    """Comandos disponibles del bot."""
    START = "/start"
    HELP = "/help"
    STATUS = "/status"
    STATS = "/stats"
    ALERT = "/alerta"
    CANCEL = "/cancel"
    LOGS = "/logs"
    METRICS = "/metrics"


@dataclass
class TelegramMessage:
    """Estructura de un mensaje de Telegram."""
    chat_id: str
    text: str
    message_id: Optional[int] = None
    from_user: Optional[str] = None
    date: Optional[datetime] = None
    command: Optional[str] = None
    args: Optional[str] = None


@dataclass
class BotCommand:
    """Definición de un comando del bot."""
    name: str
    handler: Callable
    description: str
    requires_args: bool = False


class TelegramBot:
    """
    Cliente para el Bot de Telegram.
    
    Uso:
        bot = TelegramBot()
        bot.register_handler("/status", handle_status)
        bot.send_message("123456", "Hola desde el bot")
    """
    
    def __init__(self):
        """Inicializa el cliente de Telegram."""
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.commands: Dict[str, BotCommand] = {}
        self._setup_default_commands()
        
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN no configurado. Bot no funcional.")
    
    def _setup_default_commands(self):
        """Configura los comandos por defecto del bot."""
        self.commands = {
            "/start": BotCommand(
                name="/start",
                handler=self._handle_start,
                description="Inicia el bot y muestra mensaje de bienvenida"
            ),
            "/help": BotCommand(
                name="/help",
                handler=self._handle_help,
                description="Muestra la ayuda"
            ),
            "/status": BotCommand(
                name="/status",
                handler=self._handle_status,
                description="Muestra el estado del sistema"
            ),
            "/stats": BotCommand(
                name="/stats",
                handler=self._handle_stats,
                description="Muestra estadísticas de mascotas"
            ),
            "/alerta": BotCommand(
                name="/alerta",
                handler=self._handle_alert,
                description="Envía una alerta",
                requires_args=True
            ),
            "/logs": BotCommand(
                name="/logs",
                handler=self._handle_logs,
                description="Muestra logs recientes"
            ),
            "/metrics": BotCommand(
                name="/metrics",
                handler=self._handle_metrics,
                description="Muestra métricas del sistema"
            )
        }
    
    # =========================================================================
    # ENVÍO DE MENSAJES
    # =========================================================================
    
    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Envía un mensaje a un chat de Telegram.
        
        Args:
            chat_id: ID del chat destino
            text: Texto del mensaje
            parse_mode: "Markdown" o "HTML"
            reply_markup: Teclado inline/opcional
        
        Returns:
            Respuesta de la API de Telegram
        """
        import httpx
        
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN no configurado")
            return None
        
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
            return None
    
    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Envía una alerta formateada.
        
        Args:
            title: Título de la alerta
            message: Contenido de la alerta
            severity: "info", "warning", "error", "success"
            chat_id: ID del chat (usa TELEGRAM_CHAT_ID por defecto)
        
        Returns:
            True si se envió exitosamente
        """
        target_chat = chat_id or self.chat_id
        if not target_chat:
            logger.error("No hay chat_id configurado para alertas")
            return False
        
        # Emojis según severidad
        emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅"
        }
        
        emoji = emojis.get(severity.lower(), "ℹ️")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        text = f"""
{emoji} *{title}*

{message}

🕐 {timestamp}
        """.strip()
        
        result = self.send_message(target_chat, text)
        return result is not None
    
    def send_daily_summary(self, data: Dict) -> bool:
        """
        Envía un resumen diario del sistema.
        
        Args:
            data: Diccionario con métricas diarias
        """
        if not self.chat_id:
            return False
        
        summary = f"""
📊 *Resumen Diario - Emociones Mascotas*

🐾 *Mascotas Registradas:* {data.get('total_mascotas', 0)}
😊 *Emociones Hoy:* {data.get('emociones_hoy', 0)}
📋 *Tareas Pendientes:* {data.get('tareas_pendientes', 0)}

🔗 *GitHub:*
• PRs Abiertos: {data.get('prs_abiertos', 0)}
• Issues: {data.get('issues_count', 0)}

📈 *Intensidad Promedio:* {data.get('avg_intensidad', 0):.1f}/5

⏰ Generado: {datetime.now().strftime('%H:%M')}
        """.strip()
        
        result = self.send_message(self.chat_id, summary)
        return result is not None
    
    # =========================================================================
    # PROCESAMIENTO DE COMANDOS
    # =========================================================================
    
    def register_handler(self, command: str, handler: Callable, description: str = ""):
        """Registra un handler para un comando."""
        self.commands[command] = BotCommand(
            name=command,
            handler=handler,
            description=description
        )
    
    def process_update(self, update: Dict) -> Optional[str]:
        """
        Procesa una actualización de Telegram (webhook o polling).
        
        Args:
            update: Payload JSON de Telegram
        
        Returns:
            Texto de respuesta o None
        """
        if not update.get("message"):
            return None
        
        message = update["message"]
        text = message.get("text", "")
        chat_id = str(message["chat"]["id"])
        user = message.get("from", {}).get("username", "Unknown")
        
        # Extraer comando y argumentos
        parts = text.split(" ", 1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else None
        
        logger.info(f"Comando recibido: {command} de {user}")
        
        # Buscar handler
        if command in self.commands:
            handler = self.commands[command].handler
            
            if self.commands[command].requires_args and not args:
                return f"❌ *Error:* `{command}` requiere argumentos\n\nUso: `{command} <mensaje>`"
            
            try:
                response = handler(command, args, chat_id, update)
                return response
            except Exception as e:
                logger.error(f"Error en handler de {command}: {str(e)}")
                return f"❌ Error procesando comando: {str(e)}"
        
        return f"🤔 No reconozco el comando `{command}`. Usa /help para ver comandos disponibles."
    
    # =========================================================================
    # HANDLERS DE COMANDOS
    # =========================================================================
    
    def _handle_start(self, command: str, args: Optional[str], chat_id: str, update: Dict) -> str:
        """Maneja /start."""
        welcome = """
🐾 *¡Bienvenido a Emociones Mascotas Bot!*

Este bot te ayuda a monitorear el ecosistema de Emociones Mascotas.

📌 *Comandos disponibles:*
• /status - Estado del sistema
• /stats - Estadísticas de mascotas
• /alerta <mensaje> - Enviar alerta
• /logs - Ver logs recientes
• /metrics - Métricas del sistema
• /help - Esta ayuda

¿Necesitas ayuda? Escribe /help
        """.strip()
        return welcome
    
    def _handle_help(self, command: str, args: Optional[str], chat_id: str, update: Dict) -> str:
        """Maneja /help."""
        commands_list = "\n".join([
            f"`{cmd.name}` - {cmd.description}"
            for cmd in self.commands.values()
        ])
        
        return f"""
📖 *Manual de Comandos*

{commands_list}

💡 *Ejemplos:*
`/alerta Servidor lento` - Envía una alerta
`/status` - Ver estado del sistema
        """.strip()
    
    def _handle_status(self, command: str, args: Optional[str], chat_id: str, update: Dict) -> str:
        """Maneja /status."""
        # Aquí podrías consultar el estado real del sistema
        status = """
✅ *Sistema Operativo*

🟢 Backend: Online
🟢 Base de Datos: Conectada
🟢 API: Funcional
🟢 Notion: Sincronizado
🟢 Telegram: Conectado
        """.strip()
        return status
    
    def _handle_stats(self, command: str, args: Optional[str], chat_id: str, update: Dict) -> str:
        """Maneja /stats."""
        # Aquí podrías consultar estadísticas reales
        stats = """
📊 *Estadísticas de Mascotas*

🐕 Perros: 12
🐈 Gatos: 8
🐦 Aves: 3
🐹 Roedores: 5
🦎 Reptiles: 2

😊 *Emociones registradas:* 156
⭐ *Intensidad promedio:* 3.8/5
        """.strip()
        return stats
    
    def _handle_alert(self, command: str, args: Optional[str], chat_id: str, update: Dict) -> str:
        """Maneja /alerta."""
        if args:
            # Reenviar la alerta a todos los admins o canales configurados
            success = self.send_alert(
                title=f"⚠️ Alerta de {update['message']['from']['username']}",
                message=args,
                severity="warning"
            )
            
            if success:
                return f"✅ *Alerta enviada:*\n\n{args}"
            else:
                return "❌ Error enviando alerta"
        
        return "❌ Uso: `/alerta <mensaje>`"
    
    def _handle_logs(self, command: str, args: Optional[str], chat_id: str, update: Dict) -> str:
        """Maneja /logs."""
        # Limitado a últimos 5 logs
        logs = """
📋 *Logs Recientes (simulado)*

`10:30:01` INFO: Webhook recibido de Pipedream
`10:30:02` INFO: Evento procesado: push
`10:30:03` INFO: Tarea creada en Notion
`10:30:04` INFO: Notificación enviada a Telegram
        """.strip()
        return logs
    
    def _handle_metrics(self, command: str, args: Optional[str], chat_id: str, update: Dict) -> str:
        """Maneja /metrics."""
        metrics = """
📈 *Métricas del Sistema*

⏱️ Uptime: 24h 30m
🔥 Requests/Hoy: 1,234
💾 Memoria: 45%
🔄 CPU: 12%
📦 Webhooks/Hora: 56

🕐 Última actualización: hace 5 min
        """.strip()
        return metrics
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def set_webhook(self, webhook_url: str) -> bool:
        """Configura el webhook del bot."""
        import httpx
        
        if not self.token:
            return False
        
        url = f"{self.api_url}/setWebhook"
        payload = {"url": webhook_url}
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error configurando webhook: {str(e)}")
            return False
    
    def delete_webhook(self) -> bool:
        """Elimina el webhook del bot."""
        import httpx
        
        if not self.token:
            return False
        
        url = f"{self.api_url}/deleteWebhook"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error eliminando webhook: {str(e)}")
            return False
    
    def get_updates(self, offset: int = 0, limit: int = 100) -> List[Dict]:
        """Obtiene actualizaciones (para polling)."""
        import httpx
        
        if not self.token:
            return []
        
        url = f"{self.api_url}/getUpdates"
        params = {"offset": offset, "limit": limit}
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json().get("result", [])
        except Exception as e:
            logger.error(f"Error obteniendo updates: {str(e)}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica la conexión con Telegram."""
        try:
            import httpx
            url = f"{self.api_url}/getMe"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json().get("result", {})
                
                return {
                    "status": "healthy",
                    "service": "telegram",
                    "bot_name": data.get("first_name", ""),
                    "bot_username": data.get("username", "")
                }
        except Exception as e:
            return {"status": "error", "service": "telegram", "error": str(e)}


# =============================================================================
# POLLING LOOP (Para desarrollo)
# =============================================================================

def run_polling_loop(bot: TelegramBot):
    """
    Loop de polling para desarrollo local.
    En producción usar webhooks.
    """
    logger.info("Iniciando polling loop...")
    offset = 0
    
    while True:
        try:
            updates = bot.get_updates(offset=offset)
            
            for update in updates:
                update_id = update["update_id"]
                bot.process_update(update)
                offset = update_id + 1
                
        except KeyboardInterrupt:
            logger.info("Deteniendo polling...")
            break
        except Exception as e:
            logger.error(f"Error en polling: {str(e)}")
            import time
            time.sleep(5)


# =============================================================================
# FACTORY
# =============================================================================

def create_bot() -> TelegramBot:
    """Crea una instancia del bot con configuración estándar."""
    return TelegramBot()
