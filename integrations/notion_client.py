"""
Notion Client - Emociones Mascotas
Cliente para CRUD en Notion usando la biblioteca notion-client
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NotionPage:
    """Estructura de una página de Notion"""
    id: str
    title: str
    properties: Dict[str, Any]
    created_time: Optional[str] = None
    last_edited_time: Optional[str] = None


class NotionClient:
    """
    Cliente para interactuar con Notion API.
    
    Uso:
        client = NotionClient()
        page = client.create_page("Mi página", {"status": "pendiente"})
        pages = client.search_pages("mascotas")
    """
    
    def __init__(self):
        """Inicializa el cliente de Notion."""
        self.token = os.environ.get('NOTION_INTEGRATION_KEY')
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        if not self.token:
            logger.warning("NOTION_INTEGRATION_KEY no configurada. Funcionalidad limitada.")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Hace una petición HTTP a la API de Notion."""
        import httpx
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP Notion: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error en petición Notion: {str(e)}")
            raise
    
    # =========================================================================
    # PÁGINAS
    # =========================================================================
    
    def create_page(
        self,
        title: str,
        parent_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        content: Optional[List[Dict]] = None
    ) -> NotionPage:
        """
        Crea una nueva página en Notion.
        
        Args:
            title: Título de la página
            parent_id: ID de la página padre o database
            properties: Propiedades adicionales (status, priority, etc.)
            content: Contenido en bloques (paragraphs, headings, etc.)
        
        Returns:
            NotionPage con los datos de la página creada
        """
        if not parent_id:
            raise ValueError("Se requiere parent_id para crear una página")
        
        # Construir propiedades
        page_properties = {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        }
        
        # Agregar propiedades adicionales
        if properties:
            for key, value in properties.items():
                if isinstance(value, str):
                    page_properties[key] = {"select": {"name": value}}
                elif isinstance(value, int):
                    page_properties[key] = {"number": value}
                elif isinstance(value, bool):
                    page_properties[key] = {"checkbox": value}
        
        # Construir payload
        payload = {
            "parent": {"page_id": parent_id} if not self._is_database(parent_id) else {"database_id": parent_id},
            "properties": page_properties
        }
        
        # Agregar contenido si existe
        if content:
            payload["children"] = content
        
        result = self._make_request("POST", "pages", payload)
        
        return NotionPage(
            id=result["id"],
            title=title,
            properties=result.get("properties", {}),
            created_time=result.get("created_time"),
            last_edited_time=result.get("last_edited_time")
        )
    
    def get_page(self, page_id: str) -> NotionPage:
        """Obtiene una página por su ID."""
        result = self._make_request("GET", f"pages/{page_id}")
        
        title = ""
        if result.get("properties", {}).get("title"):
            title = result["properties"]["title"]["title"][0]["text"]["content"]
        
        return NotionPage(
            id=result["id"],
            title=title,
            properties=result.get("properties", {}),
            created_time=result.get("created_time"),
            last_edited_time=result.get("last_edited_time")
        )
    
    def update_page(self, page_id: str, properties: Dict[str, Any]) -> NotionPage:
        """Actualiza las propiedades de una página."""
        payload = {"properties": {}}
        
        for key, value in properties.items():
            if isinstance(value, str):
                payload["properties"][key] = {"select": {"name": value}}
            elif isinstance(value, int):
                payload["properties"][key] = {"number": value}
            elif isinstance(value, bool):
                payload["properties"][key] = {"checkbox": value}
        
        result = self._make_request("PATCH", f"pages/{page_id}", payload)
        
        title = ""
        if result.get("properties", {}).get("title"):
            title = result["properties"]["title"]["title"][0]["text"]["content"]
        
        return NotionPage(
            id=result["id"],
            title=title,
            properties=result.get("properties", {}),
            created_time=result.get("created_time"),
            last_edited_time=result.get("last_edited_time")
        )
    
    def delete_page(self, page_id: str) -> bool:
        """Archiva una página (No elimina permanentemente en Notion)."""
        try:
            self._make_request("PATCH", f"pages/{page_id}", {"archived": True})
            return True
        except Exception as e:
            logger.error(f"Error archivando página: {str(e)}")
            return False
    
    # =========================================================================
    # BASES DE DATOS
    # =========================================================================
    
    def query_database(
        self,
        database_id: str,
        filter_props: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        page_size: int = 100
    ) -> List[NotionPage]:
        """
        Consulta una base de datos con filtros opcionales.
        
        Args:
            database_id: ID de la base de datos
            filter_props: Filtros en formato Notion
            sorts: Ordenamiento
            page_size: Número máximo de resultados
        
        Returns:
            Lista de NotionPage
        """
        payload = {"page_size": page_size}
        
        if filter_props:
            payload["filter"] = filter_props
        
        if sorts:
            payload["sorts"] = sorts
        
        results = []
        cursor = None
        
        while True:
            if cursor:
                payload["start_cursor"] = cursor
            
            response = self._make_request("POST", f"databases/{database_id}/query", payload)
            results.extend(response.get("results", []))
            
            cursor = response.get("next_cursor")
            if not cursor:
                break
        
        pages = []
        for item in results:
            title = ""
            if item.get("properties", {}).get("title"):
                title = item["properties"]["title"]["title"][0]["text"]["content"]
            
            pages.append(NotionPage(
                id=item["id"],
                title=title,
                properties=item.get("properties", {}),
                created_time=item.get("created_time"),
                last_edited_time=item.get("last_edited_time")
            ))
        
        return pages
    
    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Dict]
    ) -> Dict:
        """
        Crea una nueva base de datos.
        
        Args:
            parent_page_id: ID de la página padre
            title: Título de la base de datos
            properties: Definición de columnas
        """
        payload = {
            "parent": {"page_id": parent_page_id},
            "title": [{"text": {"content": title}}],
            "properties": properties
        }
        
        return self._make_request("POST", "databases", payload)
    
    # =========================================================================
    # BÚSQUEDA
    # =========================================================================
    
    def search_pages(self, query: str, filter_type: str = "page") -> List[NotionPage]:
        """
        Busca páginas y databases por título.
        
        Args:
            query: Texto a buscar
            filter_type: "page" o "database"
        
        Returns:
            Lista de páginas encontradas
        """
        payload = {
            "query": query,
            "filter": {"property": "object", "value": filter_type}
        }
        
        response = self._make_request("POST", "search", payload)
        
        pages = []
        for item in response.get("results", []):
            title = ""
            if "title" in item:
                if item["title"]:
                    title = item["title"][0]["text"]["content"]
            elif item.get("properties", {}).get("title"):
                title = item["properties"]["title"]["title"][0]["text"]["content"]
            
            pages.append(NotionPage(
                id=item["id"],
                title=title,
                properties=item.get("properties", {}),
                created_time=item.get("created_time"),
                last_edited_time=item.get("last_edited_time")
            ))
        
        return pages
    
    # =========================================================================
    # BLOQUES (Contenido)
    # =========================================================================
    
    def append_block_children(
        self,
        block_id: str,
        children: List[Dict]
    ) -> Dict:
        """Agrega bloques de contenido a una página o bloque existente."""
        payload = {"children": children}
        return self._make_request("PATCH", f"blocks/{block_id}/children", payload)
    
    def create_task_page(
        self,
        database_id: str,
        title: str,
        status: str = "pending",
        priority: str = "medium",
        source: str = "manual"
    ) -> NotionPage:
        """Crea una tarea en una database de Notion."""
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}},
            "Priority": {"select": {"name": priority}},
            "Source": {"select": {"name": source}}
        }
        
        return self.create_page(title, parent_id=database_id, properties=properties)
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _is_database(self, parent_id: str) -> bool:
        """Determina si el parent es una database basándose en el contexto."""
        # Esta es una heurística simple - en producción podrías verificar explícitamente
        return len(parent_id.replace("-", "")) == 32
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica la conexión con Notion."""
        try:
            self._make_request("GET", "users/me")
            return {"status": "healthy", "service": "notion"}
        except Exception as e:
            return {"status": "error", "service": "notion", "error": str(e)}


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def create_github_issue_page(
    client: NotionClient,
    database_id: str,
    issue_data: Dict
) -> NotionPage:
    """
    Crea una página de issue de GitHub en Notion.
    
    Args:
        client: Instancia de NotionClient
        database_id: ID de la database de tareas
        issue_data: Datos del issue de GitHub
    
    Returns:
        NotionPage creada
    """
    title = issue_data.get("title", "Issue sin título")
    status = "done" if issue_data.get("state") == "closed" else "in_progress"
    priority = _map_priority(issue_data.get("labels", []))
    
    content = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Información del Issue"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"Repository: {issue_data.get('repository', 'N/A')}"}}
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"URL: {issue_data.get('url', '')}"}}
                ]
            }
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {"type": "text", "text": {"content": issue_data.get("body", "Sin descripción")[:2000]}}
                ],
                "icon": {"emoji": "🐙"}
            }
        }
    ]
    
    return client.create_task_page(
        database_id=database_id,
        title=title,
        status=status,
        priority=priority,
        source="github"
    )


def _map_priority(labels: List[str]) -> str:
    """Mapea labels de GitHub a prioridades de Notion."""
    priority_map = {
        "urgent": "high",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "bug": "high",
        "enhancement": "medium",
        "documentation": "low"
    }
    
    for label in labels:
        label_lower = label.lower()
        if label_lower in priority_map:
            return priority_map[label_lower]
    
    return "medium"
