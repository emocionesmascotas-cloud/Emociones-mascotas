"""
Pipedream Step: Crear página en Notion desde Telegram
=====================================================
Segundo paso del workflow de Pipedream.

Paso anterior (Python): Procesa mensaje de Telegram y devuelve:
- usuario_id
- nombre_usuario
- mensaje_limpio
- intencion_detectada
- fecha_humana

Este paso: Crea una página en Notion con los datos procesados.
"""

import os
import sys
from datetime import datetime

# Importar notion-client
try:
    from notion_client import NotionClient
except ImportError:
    # En Pipedream, la librería suele estar preinstalada
    # Pero si no, intentamos con el módulo principal
    import notion_client
    NotionClient = notion_client.Client


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

def get_env_or_raise(key: str) -> str:
    """
    Obtiene variable de entorno o lanza excepción.
    
    Args:
        key: Nombre de la variable de entorno
    
    Returns:
        Valor de la variable
    
    Raises:
        EnvironmentError: Si la variable no está configurada
    """
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(
            f"❌ Variable de entorno '{key}' no configurada. "
            f"Configure el secret '{key}' en Pipedream."
        )
    return value


# =============================================================================
# CLIENTE NOTION
# =============================================================================

def create_notion_client() -> NotionClient:
    """
    Crea cliente de Notion con credenciales de entorno.
    
    Returns:
        Instancia de NotionClient
    
    Raises:
        EnvironmentError: Si las credenciales no están configuradas
        Exception: Si la autenticación falla
    """
    api_key = get_env_or_raise("NOTION_API_KEY")
    db_id = get_env_or_raise("NOTION_DB_ID")
    
    print(f"🔑 Inicializando cliente Notion...")
    print(f"   DB ID: {db_id[:8]}...{db_id[-4:]}")
    
    client = NotionClient(auth=api_key)
    
    # Verificar conexión con un test simple
    try:
        client.users.me()
        print("   ✅ Cliente Notion autenticado correctamente")
    except Exception as e:
        print(f"   ❌ Error de autenticación: {e}")
        raise
    
    return client


# =============================================================================
# CREAR PÁGINA EN NOTION
# =============================================================================

def create_notion_page(client: NotionClient, db_id: str, data: dict) -> str:
    """
    Crea una página en la base de datos de Notion.
    
    Args:
        client: Cliente de Notion autenticado
        db_id: ID de la base de datos destino
        data: Diccionario con los datos procesados
    
    Returns:
        ID de la página creada
    
    Raises:
        Exception: Errores de API de Notion
    """
    # Extraer datos del paso anterior
    usuario_id = data.get("usuario_id", "desconocido")
    nombre_usuario = data.get("nombre_usuario", "Usuario")
    mensaje_limpio = data.get("mensaje_limpio", "")
    intencion = data.get("intencion_detectada", "general")
    fecha_humana = data.get("fecha_humana", datetime.now().strftime("%Y-%m-%d"))
    
    # Debug: Mostrar datos recibidos
    print(f"\n📝 Datos recibidos:")
    print(f"   Usuario ID: {usuario_id}")
    print(f"   Nombre: {nombre_usuario}")
    print(f"   Mensaje: {mensaje_limpio[:50]}...")
    print(f"   Intención: {intencion}")
    print(f"   Fecha: {fecha_humana}")
    
    # Construir propiedades de la página
    # NOTA: Los nombres de propiedades deben coincidir EXACTAMENTE con tu database
    properties = {
        # Título (propiedad de tipo Title)
        "Nombre": {
            "title": [
                {
                    "text": {
                        "content": f"Mensaje de {nombre_usuario}"
                    }
                }
            ]
        },
        
        # Texto enriquecido (Rich Text)
        "Mensaje": {
            "rich_text": [
                {
                    "text": {
                        "content": mensaje_limpio
                    },
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default"
                    }
                }
            ]
        },
        
        # Selector (Select) - debe existir en tu DB
        "Intencion": {
            "select": {
                "name": intencion.capitalize()
            }
        },
        
        # Fecha
        "Fecha": {
            "date": {
                "start": fecha_humana
            }
        },
        
        # Usuario ID (texto adicional)
        "UsuarioID": {
            "rich_text": [
                {
                    "text": {
                        "content": str(usuario_id)
                    }
                }
            ]
        }
    }
    
    # Contenido adicional (opcional - bloques dechildren)
    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "text": {"content": "📱 Detalles del Mensaje"}
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"text": {"content": f"👤 Usuario: {nombre_usuario} (ID: {usuario_id})"}}
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"text": {"content": f"📋 Intención detectada: {intencion}"}}
                ]
            }
        },
        {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [
                    {"text": {"content": mensaje_limpio}}
                ]
            }
        }
    ]
    
    # Payload completo
    payload = {
        "parent": {"database_id": db_id},
        "properties": properties,
        "children": children
    }
    
    print(f"\n📤 Enviando a Notion...")
    print(f"   Parent DB: {db_id[:8]}...{db_id[-4:]}")
    
    try:
        page = client.pages.create(**payload)
        page_id = page["id"]
        
        print(f"\n✅ Página creada exitosamente!")
        print(f"   Page ID: {page_id}")
        print(f"   URL: https://notion.so/{page_id.replace('-', '')}")
        
        return page_id
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error creando página: {error_msg}")
        
        # Manejo específico de errores comunes
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            raise Exception(
                "🔒 ERROR 401: Token de Notion inválido o expirado. "
                "Verifica NOTION_API_KEY en los secrets de Pipedream."
            ) from e
            
        elif "404" in error_msg or "Could not find" in error_msg:
            raise Exception(
                "🔍 ERROR 404: Database no encontrada. "
                f"Verifica que NOTION_DB_ID={db_id} sea correcto "
                "y que la integración tenga acceso a la database."
            ) from e
            
        elif "400" in error_msg:
            # Error de validación de propiedades
            raise Exception(
                f"⚠️ ERROR 400: Error de validación. "
                f"Mensaje: {error_msg}. "
                "Verifica que las propiedades (Nombre, Mensaje, Intencion, Fecha, UsuarioID) "
                "existan en tu database de Notion."
            ) from e
            
        elif "500" in error_msg or "internal" in error_msg.lower():
            raise Exception(
                "🖥️ ERROR 500: Error interno de Notion. "
                "Intenta de nuevo en unos minutos."
            ) from e
        
        # Re-lanzar error genérico
        raise Exception(f"Error desconocido de Notion: {error_msg}") from e


# =============================================================================
# HANDLER PRINCIPAL (Pipedream)
# =============================================================================

def handler(event, steps):
    """
    Función principal que Pipedream ejecuta.
    
    Args:
        event: Evento de Pipedream (no usado directamente)
        steps: Diccionario con resultados de pasos anteriores
    
    Returns:
        Dict con page_id y metadatos
    """
    print("=" * 60)
    print("🚀 PIPEDREAM STEP: Crear página en Notion")
    print("=" * 60)
    
    # Obtener datos del paso anterior
    # El paso de Python anterior debería estar en steps.default
    # o con el nombre que le hayas dado (ej: steps.procesar_telegram)
    previous_step_name = list(steps.keys())[0] if steps else None
    
    if not previous_step_name:
        raise ValueError(
            "❌ No se encontraron datos del paso anterior. "
            "Asegúrate de que el paso de Python esté conectado a este paso."
        )
    
    payload_procesado = steps[previous_step_name]
    
    print(f"\n📥 Datos del paso anterior: {previous_step_name}")
    print(f"   Keys disponibles: {list(payload_procesado.keys())}")
    
    # Validar campos requeridos
    required_fields = ["usuario_id", "nombre_usuario", "mensaje_limpio"]
    missing_fields = [f for f in required_fields if f not in payload_procesado]
    
    if missing_fields:
        print(f"\n⚠️ Campos faltantes: {missing_fields}")
        print("   Usando valores por defecto para campos faltantes...")
    
    # Crear cliente Notion
    client = create_notion_client()
    db_id = os.environ.get("NOTION_DB_ID")
    
    # Crear página
    page_id = create_notion_page(client, db_id, payload_procesado)
    
    # Preparar resultado
    result = {
        "page_id": page_id,
        "notion_url": f"https://notion.so/{page_id.replace('-', '')}",
        "usuario": payload_procesado.get("nombre_usuario"),
        "intencion": payload_procesado.get("intencion_detectada"),
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n" + "=" * 60)
    print("✅ STEP COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print(f"\n📤 Resultado para próximos pasos:")
    print(f"   $notion_page_id: {page_id}")
    
    return result


# =============================================================================
# EJECUCIÓN DIRECTA (para testing local)
# =============================================================================

if __name__ == "__main__":
    # Simular datos de Pipedream para testing local
    print("🧪 Modo testing local")
    print("-" * 40)
    
    # Configurar variables de test si no existen
    if not os.environ.get("NOTION_API_KEY"):
        os.environ["NOTION_API_KEY"] = "ntn_test_key_placeholder"
        print("⚠️ NOTION_API_KEY configurada con valor de test")
    
    if not os.environ.get("NOTION_DB_ID"):
        os.environ["NOTION_DB_ID"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        print("⚠️ NOTION_DB_ID configurada con valor de test")
    
    # Simular steps de Pipedream
    mock_steps = {
        "default": {
            "usuario_id": "123456789",
            "nombre_usuario": "Juan Pérez",
            "mensaje_limpio": "Quiero información sobre las emociones de mi perro",
            "intencion_detectada": "consulta",
            "fecha_humana": "2024-01-15"
        }
    }
    
    try:
        result = handler(event=None, steps=mock_steps)
        print(f"\n✅ Resultado: {result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
