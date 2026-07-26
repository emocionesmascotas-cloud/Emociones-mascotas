"""
Departments - Módulos de Agentes Especializados
===============================================
Contiene los agentes por departamento:
- Marketing: Dana (creación de contenido)
- Analytics: Rita (supervisión y calidad)
"""

from .marketing.dana_agent import DanaAgent
from .analytics.rita_supervisor import RitaSupervisor

__all__ = ["DanaAgent", "RitaSupervisor"]
