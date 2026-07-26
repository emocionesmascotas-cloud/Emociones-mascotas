"""
Core - Núcleo del sistema Oficina v2.0
=====================================
Contiene los componentes centrales del sistema:
- BaseAgent: Clase base para todos los agentes
- PepitaRouter: Planificador y enrutador de tareas
- PlannerInterface: Interfaz abstracta para planificadores (Hermes-compatible)
"""

from .base_agent import BaseAgent, AgentStatus, AgentType
from .pepita_router import PepitaRouter, planificar, asignar, delegar

__all__ = [
    "BaseAgent",
    "AgentStatus", 
    "AgentType",
    "PepitaRouter",
    "planificar",
    "asignar",
    "delegar",
]
__version__ = "2.0.0"
