"""
DanaAgent - Agente de Marketing
================================
Implementación del agente de marketing para creación de contenido.

Responsabilidades:
- Generar posts para redes sociales
- Crear contenido de newsletter
- Escribir artículos de blog
- Mantener tono de marca consistente

Herencia:
    BaseAgent (core/base_agent.py)

Uso:
    from departments import DanaAgent
    
    agent = DanaAgent()
    result = agent.execute("tarea_id_de_supabase")
"""

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.base_agent import BaseAgent, AgentConfig, AgentType, AgentStatus, TaskResult

logger = logging.getLogger(__name__)


class DanaAgent(BaseAgent):
    """
    Agente especializado en marketing y creación de contenido.
    
    Utiliza templates de prompts para generar contenido variado:
    - Posts de Twitter/Instagram
    - Newsletter
    - Artículos de blog
    - Notificaciones push
    
    Attributes:
        prompt_file: Archivo de prompt base (default: dana_v1.md)
    
    Example:
        agent = DanaAgent()
        result = agent.execute("abc-123-def-456")
        
        if result.exito:
            print(f"Contenido creado: {result.resultado['contenido']}")
    """
    
    def __init__(self, nombre: str = "Dana Agent"):
        """
        Inicializa el agente Dana.
        
        Args:
            nombre: Nombre del agente (default: "Dana Agent")
        """
        config = AgentConfig(
            nombre=nombre,
            tipo=AgentType.MARKETING,
            modelo="gpt-4o-mini",
            temperatura=0.7,
            max_tokens=1000,
            skills=["seo", "redaccion_empatica", "contenido_redes"]
        )
        
        super().__init__(config)
        
        self.prompt_file = "dana_v1.md"
        self.prompt_base = self._cargar_prompt()
        
        self.logger.info(f"DanaAgent listo. Prompt cargado: {bool(self.prompt_base)}")
    
    def _cargar_prompt(self) -> str:
        """Carga el prompt del sistema desde archivo."""
        try:
            prompts_dir = Path(__file__).parent.parent.parent / "prompts" / "system_prompts"
            filepath = prompts_dir / self.prompt_file
            
            if filepath.exists():
                return filepath.read_text()
            
            # Fallback: prompt inline mínimo
            return """Eres Dana, agente de marketing de Emociones Mascotas.
Creas contenido empático y efectivo para dueños de mascotas.
Tono: cálido, cercano, profesional.
Siempre usa emojis relevantes."""
            
        except Exception as e:
            self.logger.error(f"Error cargando prompt: {e}")
            return ""
    
    def execute(self, task_id: str) -> TaskResult:
        """
        Ejecuta la tarea de marketing asignada.
        
        Flujo:
        1. Obtiene tarea de Supabase
        2. Analiza el tipo de contenido solicitado
        3. Genera el contenido usando el prompt
        4. Guarda resultado en Supabase
        5. Marca tarea como completada
        
        Args:
            task_id: ID de la tarea en Supabase
            
        Returns:
            TaskResult con el resultado de la ejecución
        """
        start_time = datetime.utcnow()
        self.logger.info(f"DanaAgent ejecutando tarea: {task_id}")
        
        # Marcar como en tarea
        self.set_status(AgentStatus.EN_TAREA)
        self.add_log(task_id, "info", f"Iniciando ejecución de {task_id}")
        
        try:
            # 1. Obtener tarea
            tarea = self.get_task(task_id)
            if not tarea:
                return TaskResult(
                    tarea_id=task_id,
                    exito=False,
                    errores=["Tarea no encontrada"]
                )
            
            # 2. Extraer parámetros
            titulo = tarea.get("titulo", "")
            descripcion = tarea.get("descripcion", "")
            intencion = tarea.get("intencion", "contenido_marketing")
            entidades = tarea.get("resultado", {}).get("entidades", {})
            
            self.logger.info(f"Procesando: {titulo}")
            
            # 3. Determinar tipo de contenido
            tipo_contenido = self._detectar_tipo_contenido(descripcion)
            
            # 4. Generar contenido
            contenido = self._generar_contenido(
                tipo=tipo_contenido,
                tema=descripcion,
                entidades=entidades
            )
            
            # 5. Preparar resultado
            resultado = {
                "contenido": contenido,
                "tipo": tipo_contenido,
                "plataforma": self._detectar_plataforma(descripcion),
                "hashtags": self._generar_hashtags(contenido),
                "prompt_usado": self.prompt_base[:100] + "..."
            }
            
            # 6. Guardar resultado
            self.update_task(task_id, {
                "estado": "en_progreso",
                "resultado": resultado
            })
            
            # 7. Completar tarea
            self.complete_task(task_id, resultado)
            
            # Calcular tiempo
            tiempo = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"Tarea {task_id} completada en {tiempo:.2f}s")
            
            return TaskResult(
                tarea_id=task_id,
                exito=True,
                resultado=resultado,
                tiempo_ejecucion_seg=tiempo
            )
            
        except Exception as e:
            self.logger.error(f"Error ejecutando tarea {task_id}: {e}")
            
            self.fail_task(task_id, str(e))
            
            return TaskResult(
                tarea_id=task_id,
                exito=False,
                errores=[str(e)],
                tiempo_ejecucion_seg=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _detectar_tipo_contenido(self, descripcion: str) -> str:
        """Detecta qué tipo de contenido generar."""
        desc_lower = descripcion.lower()
        
        if "twitter" in desc_lower or "x" in desc_lower:
            return "twitter"
        elif "instagram" in desc_lower or "foto" in desc_lower:
            return "instagram"
        elif "newsletter" in desc_lower or "email" in desc_lower:
            return "newsletter"
        elif "blog" in desc_lower or "articulo" in desc_lower:
            return "blog"
        elif "push" in desc_lower or "notificacion" in desc_lower:
            return "push"
        else:
            return "general"
    
    def _detectar_plataforma(self, descripcion: str) -> str:
        """Detecta la plataforma objetivo."""
        desc_lower = descripcion.lower()
        
        if "twitter" in desc_lower or "x" in desc_lower:
            return "Twitter/X"
        elif "instagram" in desc_lower:
            return "Instagram"
        elif "facebook" in desc_lower:
            return "Facebook"
        elif "linkedin" in desc_lower:
            return "LinkedIn"
        else:
            return "General"
    
    def _generar_contenido(
        self, 
        tipo: str, 
        tema: str, 
        entidades: Dict
    ) -> str:
        """
        Genera contenido según el tipo.
        
        En producción, esto usaría OpenAI API.
        Por ahora, usa templates.
        """
        nombre_mascota = entidades.get("nombre_mascota", "tu mascota")
        tipo_mascota = entidades.get("tipo_mascota", "")
        
        templates = {
            "twitter": f"""🐾 ¿Sabías que puedes mejorar la vida de {nombre_mascota}?

Registrar las emociones de tu mejor amigo te ayuda a entenderlo mejor.

#MascotasFelices #EmocionesAnimales""",
            
            "instagram": f"""🐾 {nombre_mascota} tiene algo que decirte...

Cada movimiento, cada mirada... todo tiene un significado.

En @EmocionesMascotas te ayudamos a descifrar las emociones de tu mejor amigo.

Porque entenderlo es amarlo mejor 💛

#Mascotas #PerrosFelices #DueñosResponsables #EmocionesCaninas""",
            
            "newsletter": f"""¡Hola! 👋

¿Te has preguntado cómo se siente realmente {nombre_mascota}?

En Emociones Mascotas creemos que entender las emociones de tu mascota 
es el primer paso para darle la mejor vida posible.

📊 Esta semana en tu comunidad:
• 156 emociones registradas
• 89 mascotas monitoreadas
• Top emoción: feliz 🐕

---

💡 TIP: Observa la cola de tu perro. 
Una cola alta y movimientos rápidos = ¡está emocionado!

¡Sigue registrando las emociones de {nombre_mascota}!

- El equipo de Emociones Mascotas 💛""",
            
            "blog": f"""# Cómo Entender las Emociones de Tu Mascota

¿Alguna vez te has preguntado qué siente tu {tipo_mascota or 'mascota'}?

## ¿Por qué es importante?

Las mascotas expresan sus emociones de formas sutiles. 
Aprender a reconocerlas fortalece el vínculo entre ustedes.

## Señales a observar

### Perros:
- Cola: Alta = feliz, baja = triste o asustado
- Orejas: Alert = curioso, atrás = sumiso o nervioso
- Respiración: Rápida = excitado o ansioso

### Gatos:
- Cola erizada = miedo o agresión
- Ronroneando = generalmente contento
- Ojos dilatados = miedo o caza

## Cómo registrar

1. Abre Emociones Mascotas
2. Selecciona a {nombre_mascota}
3. Registra cómo se siente
4. Añade notas si quieres

---

*¿Tienes dudas? Responde este email, estamos para ayudarte.*""",
            
            "general": f"""Contenido sobre: {tema}

[TODO: Generar con IA]

Este contenido está siendo creado por Dana, 
tu agente de marketing de Emociones Mascotas. 🐾"""
        }
        
        return templates.get(tipo, templates["general"])
    
    def _generar_hashtags(self, contenido: str) -> List[str]:
        """Genera hashtags relevantes para el contenido."""
        hashtags_base = [
            "#Mascotas",
            "#EmocionesAnimales", 
            "#DueñosResponsables"
        ]
        
        # Detectar tipo de contenido
        if "perro" in contenido.lower():
            hashtags_base.append("#PerrosFelices")
        if "gato" in contenido.lower():
            hashtags_base.append("#GatosFelices")
        if "ave" in contenido.lower():
            hashtags_base.append("#AvesExóticas")
        
        return hashtags_base
    
    def generar_post_marketing(
        self, 
        tipo: str,
        mensaje: str,
        nombre_mascota: str = None
    ) -> Dict[str, Any]:
        """
        Método público para generar contenido de marketing.
        
        Útil para generar contenido sin pasar por Supabase.
        
        Args:
            tipo: Tipo de contenido (twitter, instagram, etc.)
            mensaje: Tema o descripción del contenido
            nombre_mascota: Nombre de mascota (opcional)
            
        Returns:
            Dict con contenido generado y metadata
        """
        self.logger.info(f"Generando contenido tipo: {tipo}")
        
        contenido = self._generar_contenido(
            tipo=tipo,
            tema=mensaje,
            entidades={"nombre_mascota": nombre_mascota or "tu mascota"}
        )
        
        return {
            "contenido": contenido,
            "tipo": tipo,
            "hashtags": self._generar_hashtags(contenido),
            "timestamp": datetime.utcnow().isoformat()
        }


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEST: DanaAgent")
    print("=" * 50)
    
    agent = DanaAgent()
    
    # Test generar contenido directo
    resultado = agent.generar_post_marketing(
        tipo="instagram",
        mensaje="Registrar emociones de mascotas",
        nombre_mascota="Firulais"
    )
    
    print("\n📱 Post generado:")
    print(resultado["contenido"])
    print(f"\n#Hashtags: {resultado['hashtags']}")
