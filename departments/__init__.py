"""
Departments - Módulos de Agentes Especializados
===============================================
Contiene los agentes por departamento:
- Marketing: Dana (creación de contenido)
- Analytics: Rita (supervisión y calidad)
- Publishing: Carlos (publicación en Blogger y Telegram)
"""

from .marketing.dana_agent import DanaAgent
from .analytics.rita_supervisor import RitaSupervisor
from .publishing.carlos_publisher import CarlosPublisher

__all__ = ["DanaAgent", "RitaSupervisor", "CarlosPublisher"]
