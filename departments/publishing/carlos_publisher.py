"""
CarlosPublisher - Agente Publicador
==================================
Implementación del agente publicador que distribuye contenido.

Responsabilidades:
- Publicar artículos en Blogger (API gratuita)
- Enviar contenido a canales de Telegram
- Notificar resultados
- Mantener registro de publicaciones

Herencia:
    BaseAgent (core/base_agent.py)

Plataformas soportadas:
- Blogger: API REST de Google
- Telegram: Bot API

Uso:
    from departments import CarlosPublisher
    
    publisher = CarlosPublisher()
    resultado = publisher.publish("tarea_id_de_supabase")
"""

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.base_agent import BaseAgent, AgentConfig, AgentType, AgentStatus, TaskResult

logger = logging.getLogger(__name__)


class CarlosPublisher(BaseAgent):
    """
    Agente especializado en publicación de contenido.
    
    Gestiona la publicación en múltiples plataformas:
    - Blogger (blogs.google.com)
    - Telegram (canales)
    
    Attributes:
        blogger_config: Configuración de Blogger API
        telegram_config: Configuración de Telegram Bot
    
    Example:
        publisher = CarlosPublisher()
        resultado = publisher.publish("abc-123")
        
        if resultado.exito:
            print(f"Publicado en: {resultado.resultado['urls']}")
    """
    
    def __init__(self, nombre: str = "Carlos Publisher"):
        """
        Inicializa el publicador Carlos.
        
        Args:
            nombre: Nombre del agente (default: "Carlos Publisher")
        """
        config = AgentConfig(
            nombre=nombre,
            tipo=AgentType.GENERAL,  # Publishing es cross-department
            modelo="gpt-4o-mini",
            temperatura=0.3,
            max_tokens=500,
            skills=["publicar_blogger", "publicar_telegram"]
        )
        
        super().__init__(config)
        
        # Cargar skills
        self.skills = self._cargar_skills()
        
        # Configuraciones de plataformas
        self.blogger_config = self._load_blogger_config()
        self.telegram_config = self._load_telegram_config()
        
        self.logger.info(f"CarlosPublisher listo. Blogger: {bool(self.blogger_config)}, Telegram: {bool(self.telegram_config)}")
    
    def _load_blogger_config(self) -> Optional[Dict[str, str]]:
        """Carga configuración de Blogger desde entorno."""
        blog_id = os.environ.get("BLOGGER_BLOG_ID")
        access_token = os.environ.get("BLOGGER_ACCESS_TOKEN")
        
        if not blog_id:
            self.logger.warning("BLOGGER_BLOG_ID no configurado")
            return None
        
        return {
            "blog_id": blog_id,
            "access_token": access_token,
            "api_url": "https://www.googleapis.com/blogger/v3"
        }
    
    def _load_telegram_config(self) -> Optional[Dict[str, str]]:
        """Carga configuración de Telegram desde entorno."""
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
        
        if not bot_token:
            self.logger.warning("TELEGRAM_BOT_TOKEN no configurado")
            return None
        
        return {
            "bot_token": bot_token,
            "channel_id": channel_id or os.environ.get("TELEGRAM_PUBLISH_CHANNEL"),
            "api_url": f"https://api.telegram.org/bot{bot_token}"
        }
    
    def _cargar_skills(self) -> Dict[str, str]:
        """Carga los prompts de skills de publicación."""
        skills = {}
        skills_dir = Path(__file__).parent.parent.parent / "prompts" / "skills"
        
        skill_files = {
            "publicar_blogger": "publicar_blogger.md",
            "publicar_telegram": "publicar_telegram.md"
        }
        
        for skill_name, filename in skill_files.items():
            try:
                filepath = skills_dir / filename
                if filepath.exists():
                    skills[skill_name] = filepath.read_text()
                else:
                    self.logger.warning(f"Skill no encontrado: {filepath}")
                    skills[skill_name] = ""
            except Exception as e:
                self.logger.error(f"Error cargando skill {skill_name}: {e}")
                skills[skill_name] = ""
        
        return skills
    
    def execute(self, task_id: str) -> TaskResult:
        """
        Ejecuta la publicación de contenido.
        
        Flujo:
        1. Obtiene tarea de Supabase
        2. Verifica que esté en estado 'approved'
        3. Determina plataformas destino
        4. Publica en cada plataforma
        5. Actualiza estado y guarda URLs
        6. Notifica por Telegram
        
        Args:
            task_id: ID de la tarea en Supabase
            
        Returns:
            TaskResult con URLs de publicación
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Carlos publicando tarea: {task_id}")
        
        self.set_status(AgentStatus.EN_TAREA)
        self.add_log(task_id, "info", f"Iniciando publicación de {task_id}")
        
        try:
            # 1. Obtener tarea
            tarea = self.get_task(task_id)
            if not tarea:
                return TaskResult(
                    tarea_id=task_id,
                    exito=False,
                    errores=["Tarea no encontrada"]
                )
            
            # 2. Verificar estado
            estado = tarea.get("estado", "")
            if estado != "approved":
                return TaskResult(
                    tarea_id=task_id,
                    exito=False,
                    errores=[f"Tarea en estado '{estado}', se requiere 'approved'"]
                )
            
            # 3. Obtener resultado aprobado (contenido)
            resultado_tarea = tarea.get("resultado", {})
            contenido = resultado_tarea.get("contenido", "")
            
            if not contenido:
                return TaskResult(
                    tarea_id=task_id,
                    exito=False,
                    errores=["No hay contenido para publicar"]
                )
            
            # 4. Determinar plataformas
            plataformas = self._detectar_plataformas(tarea)
            
            if not plataformas:
                return TaskResult(
                    tarea_id=task_id,
                    exito=False,
                    errores=["No se especificó plataforma de publicación"]
                )
            
            self.logger.info(f"Publicando en: {plataformas}")
            
            # 5. Publicar en cada plataforma
            urls_publicadas = []
            errores_publicacion = []
            
            for plataforma in plataformas:
                try:
                    if plataforma == "blogger":
                        url = self._publicar_blogger(task_id, contenido, tarea)
                        if url:
                            urls_publicadas.append({"plataforma": "blogger", "url": url})
                    
                    elif plataforma == "telegram":
                        url = self._publicar_telegram(task_id, contenido, tarea)
                        if url:
                            urls_publicadas.append({"plataforma": "telegram", "url": url})
                    
                except Exception as e:
                    self.logger.error(f"Error publicando en {plataforma}: {e}")
                    errores_publicacion.append(f"{plataforma}: {str(e)}")
            
            # 6. Actualizar tarea
            publicaciones = {
                "urls": urls_publicadas,
                "plataformas": plataformas,
                "errores": errores_publicacion,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            nuevo_estado = "publicado" if urls_publicadas else "failed"
            
            self.update_task(task_id, {
                "estado": nuevo_estado,
                "resultado": {
                    **resultado_tarea,
                    "publicaciones": publicaciones
                }
            })
            
            # 7. Notificar
            if urls_publicadas:
                self._notificar_exito(task_id, urls_publicadas)
            if errores_publicacion:
                self._notificar_error(task_id, errores_publicacion)
            
            self.set_status(AgentStatus.ACTIVO)
            
            tiempo = (datetime.utcnow() - start_time).total_seconds()
            
            return TaskResult(
                tarea_id=task_id,
                exito=bool(urls_publicadas),
                resultado=publicaciones,
                errores=errores_publicacion,
                tiempo_ejecucion_seg=tiempo
            )
            
        except Exception as e:
            self.logger.error(f"Error en publicación: {e}")
            self.fail_task(task_id, str(e))
            
            return TaskResult(
                tarea_id=task_id,
                exito=False,
                errores=[str(e)],
                tiempo_ejecucion_seg=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _detectar_plataformas(self, tarea: Dict) -> List[str]:
        """Detecta las plataformas de publicación."""
        plataformas = []
        
        # Desde descripción o metadata
        descripcion = tarea.get("descripcion", "").lower()
        resultado = tarea.get("resultado", {})
        
        # Detectar Blogger
        if any(kw in descripcion for kw in ["blog", "blogger", "articulo", "post"]):
            if self.blogger_config:
                plataformas.append("blogger")
        
        # Detectar Telegram
        if any(kw in descripcion for kw in ["telegram", "canal", "notificar", "enviar"]):
            if self.telegram_config:
                plataformas.append("telegram")
        
        # Si no se detectó, publicar en todas las disponibles
        if not plataformas:
            if self.blogger_config:
                plataformas.append("blogger")
            if self.telegram_config:
                plataformas.append("telegram")
        
        return list(set(plataformas))  # Eliminar duplicados
    
    def _publicar_blogger(
        self, 
        task_id: str, 
        contenido: str, 
        tarea: Dict
    ) -> Optional[str]:
        """
        Publica contenido en Blogger usando la API REST.
        
        Args:
            task_id: ID de la tarea
            contenido: Contenido HTML a publicar
            tarea: Datos de la tarea
            
        Returns:
            URL del post publicado o None si falla
        """
        if not self.blogger_config:
            self.logger.warning("Blogger no configurado")
            return None
        
        self.logger.info("Publicando en Blogger...")
        
        try:
            import httpx
            
            blog_id = self.blogger_config["blog_id"]
            access_token = self.blogger_config["access_token"]
            api_url = self.blogger_config["api_url"]
            
            # Preparar post
            titulo = tarea.get("titulo", "Artículo de Emociones Mascotas")
            
            # Convertir contenido simple a HTML si es texto plano
            if not contenido.strip().startswith("<"):
                html_content = f"<p>{contenido.replace(chr(10), '</p><p>')}</p>"
            else:
                html_content = contenido
            
            # Agregar footer
            html_content += """
            <hr/>
            <p><i>Este contenido fue creado con Emociones Mascotas 🐾</i></p>
            """
            
            payload = {
                "kind": "blogger#post",
                "blog": {"id": blog_id},
                "title": titulo,
                "content": html_content,
                "labels": ["emociones-mascotas", "mascotas", "bienestar"]
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{api_url}/blogs/{blog_id}/posts",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    url = data.get("url", "")
                    self.logger.info(f"Publicado en Blogger: {url}")
                    self.add_log(task_id, "info", f"Publicado en Blogger: {url}")
                    return url
                else:
                    error_msg = f"Blogger API error: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    return None
                    
        except httpx.ConnectError:
            self.logger.error("No se pudo conectar a Blogger API")
            return None
        except Exception as e:
            self.logger.error(f"Error publicando en Blogger: {e}")
            return None
    
    def _publicar_telegram(
        self, 
        task_id: str, 
        contenido: str, 
        tarea: Dict
    ) -> Optional[str]:
        """
        Envía contenido a un canal de Telegram.
        
        Args:
            task_id: ID de la tarea
            contenido: Contenido a enviar
            tarea: Datos de la tarea
            
        Returns:
            URL del mensaje o None si falla
        """
        if not self.telegram_config:
            self.logger.warning("Telegram no configurado")
            return None
        
        self.logger.info("Enviando a Telegram...")
        
        try:
            import httpx
            
            bot_token = self.telegram_config["bot_token"]
            channel_id = self.telegram_config.get("channel_id")
            api_url = self.telegram_config["api_url"]
            
            if not channel_id:
                self.logger.error("TELEGRAM_CHANNEL_ID no configurado")
                return None
            
            # Preparar mensaje
            titulo = tarea.get("titulo", "")
            
            # Formatear para Telegram (máx 4096 chars)
            if len(contenido) > 4000:
                contenido = contenido[:4000] + "\n\n... (continúa en el blog)"
            
            mensaje = f"📝 *{titulo}*\n\n{contenido}\n\n🐾 #EmocionesMascotas"
            
            # Enviar mensaje
            payload = {
                "chat_id": channel_id,
                "text": mensaje,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{api_url}/sendMessage",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        message_id = data.get("result", {}).get("message_id")
                        url = f"https://t.me/{channel_id.lstrip('@')}/{message_id}"
                        self.logger.info(f"Enviado a Telegram: {url}")
                        self.add_log(task_id, "info", f"Publicado en Telegram: {url}")
                        return url
                    else:
                        self.logger.error(f"Telegram error: {data}")
                        return None
                else:
                    self.logger.error(f"Telegram API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error enviando a Telegram: {e}")
            return None
    
    def _notificar_exito(self, task_id: str, urls: List[Dict]):
        """Envía notificación de éxito por Telegram."""
        if not self.telegram_config:
            return
        
        try:
            import httpx
            
            bot_token = self.telegram_config["bot_token"]
            chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
            
            if not chat_id:
                return
            
            # Construir mensaje
            plataformas = [u["plataforma"] for u in urls]
            mensaje = f"✅ *Publicación exitosa*\n\n"
            mensaje += f"Tarea: `{task_id}`\n"
            mensaje += f"Plataformas: {', '.join(plataformas)}\n\n"
            
            for u in urls:
                mensaje += f"🔗 {u['plataforma']}: {u['url']}\n"
            
            payload = {
                "chat_id": chat_id,
                "text": mensaje,
                "parse_mode": "Markdown"
            }
            
            with httpx.Client(timeout=10.0) as client:
                client.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json=payload)
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación: {e}")
    
    def _notificar_error(self, task_id: str, errores: List[str]):
        """Envía notificación de error por Telegram."""
        if not self.telegram_config:
            return
        
        try:
            import httpx
            
            bot_token = self.telegram_config["bot_token"]
            chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
            
            if not chat_id:
                return
            
            mensaje = f"⚠️ *Error en publicación*\n\n"
            mensaje += f"Tarea: `{task_id}`\n\n"
            for error in errores:
                mensaje += f"❌ {error}\n"
            
            payload = {
                "chat_id": chat_id,
                "text": mensaje,
                "parse_mode": "Markdown"
            }
            
            with httpx.Client(timeout=10.0) as client:
                client.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json=payload)
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación de error: {e}")
    
    def publish_direct(
        self, 
        contenido: str,
        titulo: str,
        plataformas: List[str]
    ) -> Dict[str, Any]:
        """
        Publica contenido directamente sin pasar por Supabase.
        
        Args:
            contenido: Texto/HTML a publicar
            titulo: Título del contenido
            plataformas: Lista de plataformas ["blogger", "telegram"]
            
        Returns:
            Dict con resultados por plataforma
        """
        self.logger.info(f"Publicación directa en: {plataformas}")
        
        resultados = {}
        
        for plataforma in plataformas:
            if plataforma == "blogger":
                url = self._publicar_blogger("direct", contenido, {"titulo": titulo})
                resultados["blogger"] = {"exito": bool(url), "url": url}
            
            elif plataforma == "telegram":
                url = self._publicar_telegram("direct", contenido, {"titulo": titulo})
                resultados["telegram"] = {"exito": bool(url), "url": url}
        
        return resultados


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEST: CarlosPublisher")
    print("=" * 50)
    
    publisher = CarlosPublisher()
    
    print(f"\nConfig Blogger: {bool(publisher.blogger_config)}")
    print(f"Config Telegram: {bool(publisher.telegram_config)}")
    
    # Test publicación directa
    resultado = publisher.publish_direct(
        contenido="""🐕 ¡Tu perro te dice más de lo que crees!

Las mascotas expresan sus emociones de formas sutiles. 
Aprender a reconocerlas fortalece el vínculo entre ustedes.

En Emociones Mascotas te ayudamos a descifrar sus emociones.

#MascotasFelices""",
        titulo="Cómo entender las emociones de tu perro",
        plataformas=["telegram"]  # Solo telegram para test
    )
    
    print(f"\n📤 Resultado:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
