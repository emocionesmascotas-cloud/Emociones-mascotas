"""
PepitaRouter - Enrutador y Planificador del Sistema Oficina v2.0
================================================================
Implementa las funciones core de planificación, asignación y delegación.

NOTA PARA SWAP CON HERMES:
==========================
Este módulo implementa la lógica de Pepita. Para reemplazar por Hermes:

1. Crear `HermesRouter` que herede de `PlannerInterface`
2. Implementar los mismos métodos: planificar(), asignar(), delegar()
3. En el código que usa PepitaRouter, hacer:
   ```python
   # De:
   planner = PepitaRouter()
   
   # A:
   from core.interfaces import HermesRouter  # o config-driven
   planner = HermesRouter()
   ```

El contrato de interfaz está definido en `core.base_agent.PlannerInterface`.

Uso:
    from core import PepitaRouter, planificar, asignar, delegar
    
    # Opción 1: Clase
    router = PepitaRouter()
    clasificacion = router.planificar("registrar mi perro Firulais")
    agente_id = router.asignar({"tipo": "registro_mascota"})
    tarea = router.delegar(agente_id, {"titulo": "Registrar Firulais"})
    
    # Opción 2: Funciones sueltas
    clasificacion = planificar("quiero ver estadísticas")
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES DE CLASIFICACIÓN
# =============================================================================

INTENCIONES = {
    "registrar_mascota": {
        "keywords": ["registrar", "crear", "nuevo", "añadir", "agregar"],
        "agente": "Backend Agent",
        "departamento": "Backend",
        "urgencia_default": "normal"
    },
    "registrar_emocion": {
        "keywords": ["emocion", "sentimiento", "estado", "como esta", "esta"],
        "agente": "Backend Agent",
        "departamento": "Backend",
        "urgencia_default": "normal"
    },
    "estadisticas": {
        "keywords": ["estadistica", "reporte", "grafico", "informe", "resumen", "semana", "mes"],
        "agente": "Data Agent",
        "departamento": "Data",
        "urgencia_default": "normal"
    },
    "consulta": {
        "keywords": ["consultar", "buscar", "ver", "mostrar", "dime", "como"],
        "agente": "Data Agent",
        "departamento": "Data",
        "urgencia_default": "baja"
    },
    "problema_tecnico": {
        "keywords": ["problema", "error", "no funciona", "fallo", "bug", "ayar"],
        "agente": "Backend Agent",
        "departamento": "Backend",
        "urgencia_default": "alta"
    },
    "contenido_marketing": {
        "keywords": ["post", "redes", "instagram", "twitter", "facebook", "newsletter", "blog", "contenido"],
        "agente": "Dana Agent",
        "departamento": "Marketing",
        "urgencia_default": "normal"
    },
    "despliegue": {
        "keywords": ["deploy", "desplegar", "produccion", "publicar"],
        "agente": "Backend Agent",
        "departamento": "Backend",
        "urgencia_default": "alta"
    },
    "documentacion": {
        "keywords": ["doc", "documentar", "leer", "manual", "ayuda"],
        "agente": "General Agent",
        "departamento": "General",
        "urgencia_default": "baja"
    }
}

# =============================================================================
# CLIENTE SUPABASE (SINGLETON)
# =============================================================================

_supabase_client = None


def _get_supabase():
    """Obtiene cliente singleton de Supabase."""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            import sys
            from pathlib import Path
            
            integrations_path = Path(__file__).parent.parent / "integrations"
            if integrations_path.exists():
                sys.path.insert(0, str(integrations_path.parent))
            
            from integrations.supabase_connector import get_client
            _supabase_client = get_client()
            
        except ImportError as e:
            logger.error(f"No se pudo importar supabase_connector: {e}")
            return None
    
    return _supabase_client


# =============================================================================
# PEPITA ROUTER CLASS
# =============================================================================

class PepitaRouter:
    """
    Router principal del sistema. Implementa la lógica de Pepita.
    
    Atributos:
        supabase: Cliente de Supabase
        model: Modelo GPT a usar (default: gpt-4o-mini)
    
    Ejemplo:
        router = PepitaRouter()
        clasificacion = router.planificar("registrar mi perro Firulais")
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Inicializa el router.
        
        Args:
            model: Modelo GPT a usar para clasificación
        """
        self.supabase = _get_supabase()
        self.model = model
        self.logger = logging.getLogger("pepita_router")
        
        self.logger.info(f"PepitaRouter inicializado con modelo: {model}")
    
    def planificar(self, prompt: str) -> Dict[str, Any]:
        """
        Analiza y clasifica el mensaje del usuario.
        
        Usa keyword matching para determinar la intención.
        En producción, esto podría usar gpt-4o-mini para clasificación.
        
        Args:
            prompt: Mensaje del usuario (texto libre)
            
        Returns:
            Dict con:
            {
                "intencion": str,          # Tipo de intención
                "entidades": dict,          # Entidades extraídas
                "urgencia": str,            # baja, normal, alta, urgente
                "departamento": str,        # Departamento asignado
                "confianza": float,          # 0.0 - 1.0
                "respuesta_usuario": str    # Mensaje de confirmación
            }
        """
        self.logger.info(f"Planificando: '{prompt[:50]}...'")
        
        # Normalizar texto
        prompt_lower = prompt.lower().strip()
        
        # Extraer entidades básicas
        entidades = self._extraer_entidades(prompt)
        
        # Clasificar intención
        intencion, confianza = self._clasificar_intencion(prompt_lower)
        
        # Determinar urgencia
        urgencia = self._detectar_urgencia(prompt_lower)
        
        # Obtener配置 de la intención
        config = INTENCIONES.get(intencion, INTENCIONES["consulta"])
        
        # Generar respuesta de confirmación
        respuesta = self._generar_respuesta(intencion, entidades)
        
        resultado = {
            "intencion": intencion,
            "entidades": entidades,
            "urgencia": urgencia or config["urgencia_default"],
            "departamento": config["departamento"],
            "agente_asignado": config["agente"],
            "confianza": confianza,
            "respuesta_usuario": respuesta,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Planificación completada: {intencion} (confianza: {confianza:.2f})")
        
        return resultado
    
    def asignar(self, tarea: Dict[str, Any]) -> Optional[str]:
        """
        Busca y asigna la tarea al agente más apropiado.
        
        Busca agentes disponibles (estado = 'activo') con skills matching
        la intención de la tarea.
        
        Args:
            tarea: Dict con datos de la tarea (debe incluir 'intencion')
            
        Returns:
            ID del agente asignado o None si no hay disponible
        """
        intencion = tarea.get("intencion", "consulta")
        departamento = tarea.get("departamento", "General")
        urgencia = tarea.get("urgencia", "normal")
        
        self.logger.info(f"Asignando tarea: {intencion} -> {departamento}")
        
        if not self.supabase:
            # Modo desarrollo sin Supabase
            self.logger.warning("Supabase no disponible, asignando por defecto")
            return self._asignar_por_defecto(tarea)
        
        try:
            # Buscar agentes del departamento
            agentes = self.supabase.select(
                "agentes",
                filters={"tipo": departamento.lower()},
                use_admin=True
            )
            
            # Filtrar por estado activo
            agentes_activos = [
                a for a in agentes 
                if a.get("estado") == "activo"
            ]
            
            if not agentes_activos:
                # Buscar cualquier agente activo
                agentes_activos = self.supabase.select(
                    "agentes",
                    filters={"estado": "activo"},
                    use_admin=True
                )
            
            if not agentes_activos:
                self.logger.warning("No hay agentes disponibles")
                return None
            
            # Por ahora, tomar el primero disponible
            agente_seleccionado = agentes_activos[0]
            
            self.logger.info(f"Agente asignado: {agente_seleccionado['nombre']}")
            return agente_seleccionado["id"]
            
        except Exception as e:
            self.logger.error(f"Error en asignación: {e}")
            return self._asignar_por_defecto(tarea)
    
    def delegar(self, agente_id: str, tarea: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea la tarea en Supabase y actualiza el estado del agente.
        
        Args:
            agente_id: ID del agente (de Supabase)
            tarea: Datos de la tarea
            
        Returns:
            Dict con la tarea creada (incluye ID)
        """
        self.logger.info(f"Delegando tarea a agente: {agente_id}")
        
        if not self.supabase:
            self.logger.error("Supabase no disponible para delegar")
            return {"error": "Supabase no disponible"}
        
        try:
            # Obtener info del agente
            agente_info = None
            if self.supabase:
                agentes = self.supabase.select(
                    "agentes",
                    filters={"id": agente_id},
                    limit=1,
                    use_admin=True
                )
                if agentes:
                    agente_info = agentes[0]
            
            # Preparar datos de la tarea
            tarea_data = {
                "titulo": tarea.get("titulo", "Tarea sin título"),
                "descripcion": tarea.get("descripcion", ""),
                "tipo": self._map_intencion_a_tipo(tarea.get("intencion", "")),
                "estado": "pendiente",
                "prioridad": self._urgencia_a_prioridad(tarea.get("urgencia", "normal")),
                "intencion": tarea.get("intencion", ""),
                "urgencia": tarea.get("urgencia", "normal"),
                "departamento_id": None,  # TODO: Mapear a ID real
                "solicitante": tarea.get("solicitante", "telegram"),
                "telegram_chat_id": tarea.get("chat_id", ""),
                "resultado": {},
                "errores": []
            }
            
            # Crear tarea en Supabase
            tarea_creada = self.supabase.insert(
                "tareas",
                tarea_data,
                use_admin=True
            )
            
            tarea_id = tarea_creada.get("id")
            
            # Actualizar estado del agente a en_tarea
            if agente_info:
                self.supabase.update(
                    "agentes",
                    {"estado": "en_tarea"},
                    filters={"id": agente_id},
                    use_admin=True
                )
                
                # Log en logs_ejecucion
                self._crear_log(
                    tarea_id=tarea_id,
                    nivel="info",
                    mensaje=f"Tarea deleganda a {agente_info['nombre']}",
                    agente_id=agente_id
                )
            
            self.logger.info(f"Tarea creada: {tarea_id}")
            
            return {
                "tarea_id": tarea_id,
                "agente_id": agente_id,
                "agente_nombre": agente_info.get("nombre") if agente_info else None,
                "estado": "pendiente",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error delegando tarea: {e}")
            return {"error": str(e)}
    
    # =====================================================================
    # MÉTODOS AUXILIARES
    # =====================================================================
    
    def _extraer_entidades(self, texto: str) -> Dict[str, Any]:
        """Extrae entidades del texto (nombres, tipos, etc)."""
        entidades = {}
        
        # Detectar nombres de mascotas (palabras capitalizadas)
        palabras = texto.split()
        nombres_propios = [p for p in palabras if p and p[0].isupper() and len(p) > 2]
        if nombres_propios:
            entidades["nombre_mascota"] = nombres_propios[0]
        
        # Detectar tipo de mascota
        tipos_mascota = ["perro", "gato", "ave", "gato", "roedor", "reptil"]
        for tipo in tipos_mascota:
            if tipo in texto.lower():
                entidades["tipo_mascota"] = tipo
                break
        
        # Detectar emociones
        emociones = ["feliz", "triste", "ansioso", "tranquilo", "jugueton", 
                    "asustado", "enfermizo", "cansado", "excitado", "confundido"]
        for emocion in emociones:
            if emocion in texto.lower():
                if "emociones_detectadas" not in entidades:
                    entidades["emociones_detectadas"] = []
                entidades["emociones_detectadas"].append(emocion)
        
        return entidades
    
    def _clasificar_intencion(self, texto: str) -> tuple[str, float]:
        """Clasifica la intención basándose en keywords."""
        mejor_intencion = "consulta"
        mejor_puntaje = 0.0
        
        for intencion, config in INTENCIONES.items():
            keywords = config["keywords"]
            puntaje = sum(1 for kw in keywords if kw in texto)
            
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_intencion = intencion
        
        # Calcular confianza basada en keywords encontradas
        confianza = min(1.0, mejor_puntaje / 2.0) if mejor_puntaje > 0 else 0.5
        
        return mejor_intencion, confianza
    
    def _detectar_urgencia(self, texto: str) -> Optional[str]:
        """Detecta urgencia en el mensaje."""
        if any(kw in texto for kw in ["urgente", "ahora", "inmediato", "help", "ayuda"]):
            return "urgente"
        elif any(kw in texto for kw in ["importante", "pronto", "rapido"]):
            return "alta"
        elif any(kw in texto for kw in ["cuando puedas", "sin prisa", "despacio"]):
            return "baja"
        return None
    
    def _generar_respuesta(self, intencion: str, entidades: Dict) -> str:
        """Genera mensaje de confirmación para el usuario."""
        respuestas = {
            "registrar_mascota": f"¡Perfecto! Voy a registrar a {entidades.get('nombre_mascota', 'tu mascota')}.",
            "registrar_emocion": "Guardando el estado emocional... un momento.",
            "estadisticas": "Generando estadísticas... esto toma solo un momento.",
            "consulta": "Consultando la información... un momento.",
            "problema_tecnico": "Veo que hay un problema. Lo estoy revisando.",
            "contenido_marketing": "Creando contenido para redes sociales...",
            "despliegue": "Iniciando proceso de despliegue...",
            "documentacion": "Buscando en la documentación...",
        }
        
        return respuestas.get(intencion, "Procesando tu solicitud...")
    
    def _asignar_por_defecto(self, tarea: Dict) -> Optional[str]:
        """Asignación por defecto sin Supabase."""
        intencion = tarea.get("intencion", "consulta")
        config = INTENCIONES.get(intencion, INTENCIONES["consulta"])
        
        # Mapear nombre a ID placeholder (para desarrollo)
        return config["agente"]
    
    def _map_intencion_a_tipo(self, intencion: str) -> str:
        """Mapea intención a tipo de tarea."""
        mapeo = {
            "registrar_mascota": "feature",
            "registrar_emocion": "feature",
            "estadisticas": "query",
            "consulta": "query",
            "problema_tecnico": "bug",
            "contenido_marketing": "general",
            "despliegue": "deploy",
            "documentacion": "docs"
        }
        return mapeo.get(intencion, "general")
    
    def _urgencia_a_prioridad(self, urgencia: str) -> int:
        """Mapea urgencia a prioridad (1=máxima, 5=mínima)."""
        mapeo = {
            "urgente": 1,
            "alta": 2,
            "normal": 3,
            "baja": 4
        }
        return mapeo.get(urgencia, 3)
    
    def _crear_log(
        self, 
        tarea_id: str, 
        nivel: str, 
        mensaje: str, 
        agente_id: str = None
    ) -> bool:
        """Crea un log de ejecución."""
        if not self.supabase:
            return False
        
        try:
            self.supabase.insert(
                "logs_ejecucion",
                {
                    "tarea_id": tarea_id,
                    "agente_id": agente_id,
                    "nivel": nivel,
                    "mensaje": mensaje,
                    "contexto": {}
                },
                use_admin=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Error creando log: {e}")
            return False


# =============================================================================
# FUNCIONES SUELTAS (CONVENIENCE)
# =============================================================================

def planificar(prompt: str) -> Dict[str, Any]:
    """
    Función convenience para planificar.
    
    Args:
        prompt: Mensaje del usuario
        
    Returns:
        Resultado de clasificación
    """
    router = PepitaRouter()
    return router.planificar(prompt)


def asignar(tarea: Dict[str, Any]) -> Optional[str]:
    """
    Función convenience para asignar.
    
    Args:
        tarea: Datos de la tarea
        
    Returns:
        ID del agente asignado
    """
    router = PepitaRouter()
    return router.asignar(tarea)


def delegar(agente_id: str, tarea: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función convenience para delegar.
    
    Args:
        agente_id: ID del agente
        tarea: Datos de la tarea
        
    Returns:
        Tarea creada
    """
    router = PepitaRouter()
    return router.delegar(agente_id, tarea)


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Test del router
    print("=" * 50)
    print("TEST: PepitaRouter")
    print("=" * 50)
    
    router = PepitaRouter()
    
    # Test 1: Registrar mascota
    resultado = router.planificar("Quiero registrar mi perro Firulais")
    print(f"\n1. Registrar mascota:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Test 2: Solicitar estadísticas
    resultado = router.planificar("Necesito un reporte de emociones de esta semana")
    print(f"\n2. Estadísticas:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Test 3: Problema técnico
    resultado = router.planificar("Hay un error en el registro de mascotas")
    print(f"\n3. Problema técnico:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
