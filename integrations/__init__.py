"""
Integrations Module - Emociones Mascotas Ecosystem

Módulos de integración para conectar:
- Notion (documentación y tareas)
- Telegram (notificaciones y comandos)
- Pipedream (automatización y webhooks)
"""

from .notion_client import NotionClient
from .telegram_bot import TelegramBot
from .replit_api import router as replit_router

__all__ = ["NotionClient", "TelegramBot", "replit_router"]
__version__ = "1.0.0"
