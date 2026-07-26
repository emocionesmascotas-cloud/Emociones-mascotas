"""
BaseAgent - Clase Base para Agentes del Sistema Oficina v2.0
============================================================
Define la interfaz común y funcionalidades base para todos los agentes.

Arquitectura:
    BaseAgent (ABC)
        ├── PepitaRouter (planificador)
        ├── DanaAgent (marketing)
        └── RitaSupervisor (quality)

El diseño sigue el principio de Dependency Inversion:
    Los módulos de alto nivel (Router) no dependen de
    implementaciones concretas (DanaAgent), sino de abstracciones
    (BaseAgent).
"""

import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS Y DATACLASSES
# =============================================================================

class AgentType(Enum):
    """Tipos de agente disponibles en el sistema."""
    PLANIFICADOR = "planificador"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATA = "data"
    MARKETING = "marketing"
    SUPERVISOR = "supervisor"
    GENERAL = "general"


class AgentStatus(Enum):
    """Estados posibles de un agente."""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    EN_TAREA = "en_tarea"
    ERROR = "error"
    IDLE = "idle"  # Alias para ACTIVO y disponible


@dataclass
class AgentConfig:
    """Configuración de un agente."""
    nombre: str
    tipo: AgentType
    modelo: str = "gpt-4o-mini"
    temperatura: float = 0.7
    max_tokens: int = 1000
    timeout_minutos: int = 10
    skills: List[str] = field(default_factory=list)
    prompt_base: str = ""


@dataclass
class TaskResult:
    """Resultado de la ejecución de una tarea."""
    tarea_id: str
    exito: bool
    resultado: Optional[Dict[str, Any]] = None
    errores: List[str] = field(default_factory=list)
    tiempo_ejecucion_seg: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ValidationResult:
    """Resultado de validación de Rita."""
    tarea_id: str
    veredicto: str  # APROBADO, CORREGIR, RECHAZADO
    nivel: str  # OK, WARNING, CRITICO
    checks: List[Dict[str, Any]] = field(default_factory=list)
    errores_criticos: List[str] = field(default_factory=list)
    sugerencias: List[str] = field(default_factory=list)
    comentario: str = ""


# =============================================================================
# BASE AGENT (ABSTRACT)
# =============================================================================

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes del sistema.
    
    Implementa la interfaz común y funcionalidades compartidas.
    Cada agente específico hereda de esta clase y define su execute().
    
    Uso:
        class MiAgente(BaseAgent):
            def __init__(self):
                super().__init__(
                    config=AgentConfig(
                        nombre="MiAgente",
                        tipo=AgentType.BACKEND
                    )
                )
            
            def execute(self, task_id: str) -> TaskResult:
                # Implementar lógica específica
                pass
    
    Attributes:
        config (AgentConfig): Configuración del agente
        supabase: Cliente de Supabase para persistencia
        status (AgentStatus): Estado actual del agente
    
    Methods:
        execute(task_id: str) -> TaskResult: Ejecuta una tarea
        get_task(task_id: str) -> Dict: Obtiene tarea de Supabase
        update_task(task_id: str, data: Dict) -> bool: Actualiza tarea
        complete_task(task_id: str, result: Dict) -> bool: Marca como completada
        fail_task(task_id: str, error: str) -> bool: Marca como fallida
        set_status(status: AgentStatus) -> bool: Cambia estado del agente
    """
    
    def __init__(self, config: AgentConfig):
        """
        Inicializa el agente.
        
        Args:
            config: Configuración del agente
        
        Raises:
            ValueError: Si config es inválida
        """
        if not config.nombre:
            raise ValueError("El nombre del agente es requerido")
        
        self.config = config
        self.status = AgentStatus.ACTIVO
        self.supabase = self._init_supabase()
        self.logger = logging.getLogger(f"agent.{config.nombre}")
        
        self.logger.info(f"Agente {config.nombre} ({config.tipo.value}) inicializado")
    
    def _init_supabase(self):
        """Inicializa conexión a Supabase."""
        try:
            # Importación tardía para evitar circular imports
            import sys
            from pathlib import Path
            
            # Buscar supabase_connector en el path
            integrations_path = Path(__file__).parent.parent / "integrations"
            if integrations_path.exists():
                sys.path.insert(0, str(integrations_path.parent))
            
            from integrations.supabase_connector import get_client
            return get_client()
            
        except ImportError as e:
            self.logger.warning(f"No se pudo importar supabase_connector: {e}")
            return None
    
    @abstractmethod
    def execute(self, task_id: str) -> TaskResult:
        """
        Ejecuta la tarea asignada.
        
        Este método debe ser implementado por cada agente específico.
        
        Args:
            task_id: ID de la tarea en Supabase
            
        Returns:
            TaskResult con el resultado de la ejecución
            
        Raises:
            NotImplementedError: Si no está implementado
        """
        raise NotImplementedError("Cada agente debe implementar execute()")
    
    # =====================================================================
    # MÉTODOS DE UTILIDAD
    # =====================================================================
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una tarea de Supabase.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Dict con datos de la tarea o None si no existe
        """
        if not self.supabase:
            self.logger.error("Supabase no disponible")
            return None
        
        try:
            results = self.supabase.select(
                "tareas",
                filters={"id": task_id},
                limit=1
            )
            return results[0] if results else None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo tarea {task_id}: {e}")
            return None
    
    def update_task(
        self, 
        task_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Actualiza campos de una tarea en Supabase.
        
        Args:
            task_id: ID de la tarea
            data: Campos a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        if not self.supabase:
            self.logger.error("Supabase no disponible")
            return False
        
        try:
            self.supabase.update("tareas", data, filters={"id": task_id})
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando tarea {task_id}: {e}")
            return False
    
    def complete_task(
        self, 
        task_id: str, 
        result: Dict[str, Any]
    ) -> bool:
        """
        Marca una tarea como completada.
        
        Args:
            task_id: ID de la tarea
            result: Resultado de la ejecución
            
        Returns:
            True si se completó correctamente
        """
        data = {
            "estado": "completado",
            "resultado": result,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        success = self.update_task(task_id, data)
        
        if success:
            self.logger.info(f"Tarea {task_id} completada exitosamente")
            self.set_status(AgentStatus.ACTIVO)
        
        return success
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """
        Marca una tarea como fallida.
        
        Args:
            task_id: ID de la tarea
            error: Mensaje de error
            
        Returns:
            True si se actualizó correctamente
        """
        data = {
            "estado": "fallido",
            "errores": [error],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        success = self.update_task(task_id, data)
        
        if success:
            self.logger.error(f"Tarea {task_id} fallida: {error}")
            self.set_status(AgentStatus.ERROR)
        
        return success
    
    def set_status(self, status: AgentStatus) -> bool:
        """
        Actualiza el estado del agente en Supabase.
        
        Args:
            status: Nuevo estado
            
        Returns:
            True si se actualizó correctamente
        """
        if not self.supabase:
            self.status = status
            return True  # Solo actualizar estado local
        
        try:
            # Buscar el agente en Supabase por nombre
            agents = self.supabase.select(
                "agentes",
                filters={"nombre": self.config.nombre},
                limit=1,
                use_admin=True
            )
            
            if agents:
                self.supabase.update(
                    "agentes",
                    {
                        "estado": status.value,
                        "last_seen_at": datetime.utcnow().isoformat()
                    },
                    filters={"id": agents[0]["id"]},
                    use_admin=True
                )
            
            self.status = status
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando estado del agente: {e}")
            self.status = status
            return False
    
    def add_log(self, tarea_id: str, nivel: str, mensaje: str, contexto: Dict = None) -> bool:
        """
        Añade un log de ejecución.
        
        Args:
            tarea_id: ID de la tarea
            nivel: debug, info, warning, error, critical
            mensaje: Mensaje del log
            contexto: Datos adicionales (opcional)
            
        Returns:
            True si se creó el log
        """
        if not self.supabase:
            return False
        
        try:
            self.supabase.insert(
                "logs_ejecucion",
                {
                    "tarea_id": tarea_id,
                    "agente_id": self.config.nombre,
                    "nivel": nivel,
                    "mensaje": mensaje,
                    "contexto": contexto or {}
                },
                use_admin=True
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando log: {e}")
            return False
    
    def load_prompt(self, filename: str) -> str:
        """
        Carga un prompt desde archivo.
        
        Args:
            filename: Nombre del archivo en prompts/system_prompts/
            
        Returns:
            Contenido del prompt o string vacío si no existe
        """
        try:
            prompts_dir = Path(__file__).parent.parent / "prompts" / "system_prompts"
            filepath = prompts_dir / filename
            
            if filepath.exists():
                return filepath.read_text()
            else:
                self.logger.warning(f"Prompt no encontrado: {filepath}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error cargando prompt {filename}: {e}")
            return ""
    
    def call_llm(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Llama al modelo de lenguaje (stub para OpenAI).
        
        En producción, esto usará OpenAI API con el modelo configurado.
        
        Args:
            prompt: Prompt para el modelo
            **kwargs: Parámetros adicionales (temperature, max_tokens, etc.)
            
        Returns:
            Respuesta del modelo o None si falla
        """
        # TODO: Implementar con OpenAI API
        # Por ahora, logueamos y retornamos None
        self.logger.info(f"Llamando LLM con prompt de {len(prompt)} chars")
        self.logger.debug(f"Config: modelo={self.config.modelo}, temp={self.config.temperatura}")
        
        # Stub para desarrollo
        return None
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}('{self.config.nombre}', status={self.status.value})>"


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_agent(tipo: AgentType, nombre: str = None) -> BaseAgent:
    """
    Factory para crear agentes por tipo.
    
    Args:
        tipo: Tipo de agente a crear
        nombre: Nombre personalizado (opcional)
        
    Returns:
        Instancia del agente correspondiente
        
    Raises:
        ValueError: Si el tipo no está soportado
    """
    from departments.marketing.dana_agent import DanaAgent
    from departments.analytics.rita_supervisor import RitaSupervisor
    
    # Si no hay nombre, usar el tipo como nombre por defecto
    if nombre is None:
        nombre = tipo.value.capitalize()
    
    config = AgentConfig(nombre=nombre, tipo=tipo)
    
    if tipo == AgentType.MARKETING:
        return DanaAgent()
    elif tipo == AgentType.SUPERVISOR:
        return RitaSupervisor()
    else:
        raise ValueError(f"Tipo de agente no soportado: {tipo}")


# =============================================================================
# TIPO PARA TYPE HINTS (HERMES-COMPATIBLE)
# =============================================================================

class PlannerInterface(ABC):
    """
    Interfaz abstracta para planificadores (PEPITA / HERMES).
    
    Esta interfaz define el contrato que cualquier planificador
    debe cumplir. Permite swap entre Pepita y Hermes sin cambiar
    el código que los usa.
    
    Para implementar Hermes como替代 de Pepita:
        1. Crear HermesPlanner que herede de esta interfaz
        2. Implementar planificar(), asignar(), delegar()
        3. En el código, usar PlannerInterface en vez de PepitaRouter
        4. Inyectar la implementación deseada via constructor
    
    Ejemplo de swap:
        # Antes (Pepita):
        planner = PepitaRouter()
        
        # Después (Hermes):
        planner = HermesPlanner()  # Misma interfaz
    """
    
    @abstractmethod
    def planificar(self, prompt: str) -> Dict[str, Any]:
        """
        Analiza y clasifica un mensaje del usuario.
        
        Args:
            prompt: Mensaje del usuario
            
        Returns:
            Dict con clasificación:
            {
                "intencion": str,
                "entidades": dict,
                "urgencia": str,
                "departamento": str,
                "confianza": float
            }
        """
        pass
    
    @abstractmethod
    def asignar(self, tarea: Dict[str, Any]) -> str:
        """
        Asigna una tarea al agente más apropiado.
        
        Args:
            tarea: Datos de la tarea
            
        Returns:
            ID del agente asignado
        """
        pass
    
    @abstractmethod
    def delegar(self, agente_id: str, tarea: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea la tarea y la delega al agente.
        
        Args:
            agente_id: ID del agente
            tarea: Datos de la tarea
            
        Returns:
            Dict con la tarea creada en Supabase
        """
        pass
