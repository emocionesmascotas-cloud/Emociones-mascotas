"""
Supabase Connector - Emociones Mascotas
======================================
Cliente Python para conectar FastAPI a Supabase Cloud (Free Tier)

Uso:
    from integrations.supabase_connector import SupabaseClient, get_client
    
    # Cliente singleton
    client = get_client()
    
    # CRUD básico
    client.insert("mascotas", {"nombre": "Firulais", "tipo": "perro"})
    client.select("mascotas", columns="*", filters={"tipo": "perro"})
    client.update("mascotas", {"nombre": "Firulais Jr"}, filters={"id": 1})
    client.delete("mascotas", filters={"id": 1})
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

def get_env_or_raise(key: str, description: str = "") -> str:
    """Obtiene variable de entorno o lanza excepción."""
    value = os.environ.get(key)
    if not value:
        desc = f" - {description}" if description else ""
        raise EnvironmentError(
            f"❌ Variable de entorno '{key}' no configurada{desc}. "
            f"Configure este secret en su plataforma de hosting."
        )
    return value


# =============================================================================
# EXCEPCIONES
# =============================================================================

class SupabaseError(Exception):
    """Error base de Supabase."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class SupabaseAuthError(SupabaseError):
    """Error de autenticación."""
    pass


class SupabaseConnectionError(SupabaseError):
    """Error de conexión."""
    pass


class SupabaseValidationError(SupabaseError):
    """Error de validación."""
    pass


# =============================================================================
# CLIENTE SUPABASE
# =============================================================================

@dataclass
class SupabaseConfig:
    """Configuración de conexión a Supabase."""
    url: str
    anon_key: str
    service_key: Optional[str] = None
    schema: str = "public"


class SupabaseClient:
    """
    Cliente para interactuar con Supabase.
    
    Usa la API REST de Supabase directamente (sin SDK adicional).
    Ideal para Free Tier donde queremos minimizar dependencias.
    
    Uso:
        config = SupabaseConfig(
            url="https://xxx.supabase.co",
            anon_key="eyJ...",
            service_key="eyJ..."  # Opcional, para admin
        )
        client = SupabaseClient(config)
        result = client.select("mascotas")
    """
    
    def __init__(self, config: Optional[SupabaseConfig] = None):
        """Inicializa el cliente de Supabase."""
        
        # Cargar desde config o entorno
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
        self.base_url = f"{config.url}/rest/v1"
        self.headers = {
            "apikey": config.anon_key,
            "Authorization": f"Bearer {config.anon_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Headers para admin (service key)
        self.admin_headers = self.headers.copy()
        if config.service_key:
            self.admin_headers["Authorization"] = f"Bearer {config.service_key}"
        
        self._verify_connection()
    
    def _load_config_from_env(self) -> SupabaseConfig:
        """Carga configuración desde variables de entorno."""
        return SupabaseConfig(
            url=get_env_or_raise("SUPABASE_URL", "URL del proyecto Supabase"),
            anon_key=get_env_or_raise("SUPABASE_ANON_KEY", "Clave pública anon"),
            service_key=os.environ.get("SUPABASE_SERVICE_KEY"),  # Opcional
            schema=os.environ.get("SUPABASE_SCHEMA", "public")
        )
    
    def _verify_connection(self):
        """Verifica que podemos conectar con Supabase."""
        import httpx
        
        try:
            response = httpx.get(
                f"{self.config.url}/rest/v1/",
                headers=self.headers,
                timeout=10.0
            )
            if response.status_code == 200:
                logger.info("✅ Conexión a Supabase verificada")
            else:
                logger.warning(f"⚠️ Respuesta inesperada: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo verificar conexión: {str(e)}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        use_admin: bool = False
    ) -> Any:
        """
        Hace una petición HTTP a la API REST de Supabase.
        
        Args:
            method: GET, POST, PUT, PATCH, DELETE
            endpoint: Ruta del endpoint (ej: "mascotas")
            data: Cuerpo de la petición
            params: Query parameters
            use_admin: Usar service key para bypass RLS
        
        Returns:
            Respuesta de la API
        """
        import httpx
        
        url = f"{self.base_url}/{endpoint}"
        headers = self.admin_headers if use_admin else self.headers
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                
                # Manejo de errores
                if response.status_code >= 400:
                    error_detail = response.json().get("message", response.text)
                    raise SupabaseError(
                        f"Error {response.status_code}: {error_detail}",
                        status_code=response.status_code
                    )
                
                # Parsear respuesta
                if response.status_code == 204:
                    return None
                
                return response.json()
                
        except httpx.ConnectError as e:
            raise SupabaseConnectionError(
                f"No se pudo conectar a Supabase: {str(e)}"
            ) from e
        except httpx.TimeoutException:
            raise SupabaseConnectionError(
                "Timeout conectando a Supabase. Revisa tu conexión."
            ) from e
        except SupabaseError:
            raise
        except Exception as e:
            raise SupabaseError(f"Error inesperado: {str(e)}") from e
    
    # =====================================================================
    # CRUD BÁSICO
    # =====================================================================
    
    def insert(
        self,
        table: str,
        data: Dict[str, Any],
        returning: str = "representation"
    ) -> Dict[str, Any]:
        """
        Inserta un registro en una tabla.
        
        Args:
            table: Nombre de la tabla
            data: Datos a insertar
        
        Returns:
            Registro insertado con ID
        """
        logger.info(f"INSERT into {table}")
        
        headers = self.admin_headers.copy()
        headers["Prefer"] = f"return={returning}"
        
        import httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/{table}",
                headers=headers,
                json=data
            )
            
            if response.status_code >= 400:
                error = response.json()
                raise SupabaseError(
                    f"Error insertando: {error.get('message', response.text)}",
                    status_code=response.status_code
                )
            
            return response.json()
    
    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        use_admin: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Selecciona registros de una tabla.
        
        Args:
            table: Nombre de la tabla
            columns: Columnas a seleccionar (default: *)
            filters: Filtros en formato {"columna": valor}
            order: Ordenamiento {"columna": "asc|desc"}
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            Lista de registros
        """
        params = {"select": columns}
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    params[key] = f"eq.{value[0]}" if len(value) == 1 else f"in.({','.join(str(v) for v in value)})"
                elif isinstance(value, bool):
                    params[key] = f"eq.{str(value).lower()}"
                elif isinstance(value, str) and "," in value:
                    params[key] = f"in.({value})"
                else:
                    params[key] = f"eq.{value}"
        
        if order:
            col, direction = list(order.items())[0]
            params["order"] = f"{col}.{direction}"
        
        if limit:
            params["limit"] = str(limit)
        
        if offset:
            params["offset"] = str(offset)
        
        logger.info(f"SELECT from {table} with filters: {filters or {}}")
        
        headers = self.admin_headers.copy() if use_admin else self.headers
        headers["Prefer"] = "count=exact"
        
        import httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/{table}",
                headers=headers,
                params=params
            )
            
            if response.status_code >= 400:
                raise SupabaseError(
                    f"Error consultando: {response.text}",
                    status_code=response.status_code
                )
            
            # Verificar total count en headers
            total = response.headers.get("content-range", "").split("/")
            if len(total) > 1:
                logger.info(f"Total registros: {total[1]}")
            
            return response.json()
    
    def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        use_admin: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Actualiza registros en una tabla.
        
        Args:
            table: Nombre de la tabla
            data: Datos a actualizar
            filters: Filtros para seleccionar registros
            use_admin: Usar service key (requerido para RLS)
        
        Returns:
            Registros actualizados
        """
        if not filters:
            raise SupabaseValidationError("Se requieren filtros para UPDATE")
        
        params = {}
        for key, value in filters.items():
            if isinstance(value, (list, tuple)):
                params[key] = f"in.({','.join(str(v) for v in value)})"
            else:
                params[key] = f"eq.{value}"
        
        logger.info(f"UPDATE {table} where {filters}")
        
        headers = self.admin_headers.copy() if use_admin else self.headers
        headers["Prefer"] = "return=representation"
        
        import httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{self.base_url}/{table}",
                headers=headers,
                params=params,
                json=data
            )
            
            if response.status_code >= 400:
                raise SupabaseError(
                    f"Error actualizando: {response.text}",
                    status_code=response.status_code
                )
            
            return response.json()
    
    def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        use_admin: bool = True
    ) -> bool:
        """
        Elimina registros de una tabla.
        
        Args:
            table: Nombre de la tabla
            filters: Filtros para seleccionar registros a eliminar
            use_admin: Usar service key (requerido para RLS)
        
        Returns:
            True si se eliminó correctamente
        """
        if not filters:
            raise SupabaseValidationError("Se requieren filtros para DELETE")
        
        params = {}
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        
        logger.info(f"DELETE from {table} where {filters}")
        
        headers = self.admin_headers.copy() if use_admin else self.headers
        headers["Prefer"] = "return=minimal"
        
        import httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.delete(
                f"{self.base_url}/{table}",
                headers=headers,
                params=params
            )
            
            if response.status_code >= 400:
                raise SupabaseError(
                    f"Error eliminando: {response.text}",
                    status_code=response.status_code
                )
            
            return response.status_code == 204
    
    def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        on_conflict: Optional[str] = None,
        ignore_duplicates: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Inserta o actualiza (upsert) registros.
        
        Args:
            table: Nombre de la tabla
            data: Datos a upsert
            on_conflict: Columna para resolver conflictos
            ignore_duplicates: Ignorar duplicados
        
        Returns:
            Registros affected
        """
        headers = self.admin_headers.copy()
        
        prefer_options = []
        if ignore_duplicates:
            prefer_options.append("resolution=ignore-duplicates")
        elif on_conflict:
            prefer_options.append(f"resolution=merge-duplicates")
            headers["X-Upsert"] = "true"
            headers["On-Conflict"] = on_conflict
        
        if prefer_options:
            headers["Prefer"] = ",".join(prefer_options)
        
        logger.info(f"UPSERT into {table}")
        
        import httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/{table}",
                headers=headers,
                json=data
            )
            
            if response.status_code >= 400:
                raise SupabaseError(
                    f"Error upsert: {response.text}",
                    status_code=response.status_code
                )
            
            return response.json()
    
    # =====================================================================
    # FUNCIONES DE UTILIDAD
    # =====================================================================
    
    def count(self, table: str, filters: Optional[Dict] = None) -> int:
        """Cuenta registros en una tabla."""
        params = {"select": "id"}
        
        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"
        
        import httpx
        headers = self.admin_headers.copy()
        headers["Prefer"] = "count=exact"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/{table}",
                headers=headers,
                params=params
            )
            
            if response.status_code >= 400:
                return 0
            
            total = response.headers.get("content-range", "/0").split("/")
            return int(total[1]) if len(total) > 1 else 0
    
    def exists(self, table: str, filters: Dict[str, Any]) -> bool:
        """Verifica si existe un registro."""
        params = {"select": "id", "limit": 1}
        
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        
        import httpx
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{self.base_url}/{table}",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return len(data) > 0
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica el estado de la conexión."""
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{self.config.url}/rest/v1/",
                    headers=self.headers
                )
                
                return {
                    "status": "healthy" if response.status_code == 200 else "error",
                    "project": self.config.url.split("//")[1].split(".")[0],
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# =============================================================================
# SINGLETON
# =============================================================================

_client: Optional[SupabaseClient] = None


def get_client() -> SupabaseClient:
    """Obtiene instancia singleton del cliente."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client


def reset_client():
    """Resetea el cliente (útil para testing)."""
    global _client
    _client = None


# =============================================================================
# MODELOS PARA MASCOTAS Y EMOCIONES
# =============================================================================

class MascotaRepository:
    """Repositorio para la tabla mascotas."""
    
    def __init__(self, client: Optional[SupabaseClient] = None):
        self.client = client or get_client()
    
    def create(self, nombre: str, tipo: str, raza: str = "", edad: int = 0, 
               dueno_id: str = "") -> Dict[str, Any]:
        """Crea una nueva mascota."""
        data = {
            "nombre": nombre,
            "tipo": tipo,
            "raza": raza,
            "edad": edad,
            "dueno_id": dueno_id,
            "created_at": datetime.utcnow().isoformat()
        }
        return self.client.insert("mascotas", data)
    
    def get_all(self, tipo: Optional[str] = None) -> List[Dict]:
        """Obtiene todas las mascotas."""
        filters = {"tipo": tipo} if tipo else None
        return self.client.select("mascotas", filters=filters, order={"created_at": "desc"})
    
    def get_by_id(self, id: int) -> Optional[Dict]:
        """Obtiene mascota por ID."""
        results = self.client.select("mascotas", filters={"id": id}, limit=1)
        return results[0] if results else None
    
    def update(self, id: int, data: Dict) -> Dict:
        """Actualiza una mascota."""
        data["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.update("mascotas", data, filters={"id": id})
        return result[0] if result else None
    
    def delete(self, id: int) -> bool:
        """Elimina una mascota."""
        return self.client.delete("mascotas", filters={"id": id})
    
    def count(self, tipo: Optional[str] = None) -> int:
        """Cuenta mascotas."""
        filters = {"tipo": tipo} if tipo else None
        return self.client.count("mascotas", filters=filters)


class EmocionRepository:
    """Repositorio para la tabla emociones."""
    
    def __init__(self, client: Optional[SupabaseClient] = None):
        self.client = client or get_client()
    
    def create(self, mascota_id: int, tipo: str, intensidad: int = 3,
               notas: str = "", registrado_por: str = "") -> Dict:
        """Registra una emoción."""
        data = {
            "mascota_id": mascota_id,
            "tipo": tipo,
            "intensidad": intensidad,
            "notas": notas,
            "registrado_por": registrado_por,
            "fecha": datetime.utcnow().isoformat()
        }
        return self.client.insert("emociones", data)
    
    def get_by_mascota(self, mascota_id: int, limit: int = 50) -> List[Dict]:
        """Obtiene emociones de una mascota."""
        return self.client.select(
            "emociones",
            filters={"mascota_id": mascota_id},
            order={"fecha": "desc"},
            limit=limit
        )
    
    def get_recent(self, hours: int = 24) -> List[Dict]:
        """Obtiene emociones recientes."""
        from datetime import timedelta
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        return self.client.select(
            "emociones",
            filters={"fecha": f"gte.{since}"},
            order={"fecha": "desc"}
        )
    
    def get_stats(self, mascota_id: Optional[int] = None) -> Dict:
        """Obtiene estadísticas de emociones."""
        filters = {"mascota_id": mascota_id} if mascota_id else None
        emociones = self.client.select(
            "emociones",
            filters=filters,
            use_admin=True
        )
        
        if not emociones:
            return {"total": 0, "by_tipo": {}}
        
        by_tipo = {}
        intensidades = []
        
        for e in emociones:
            tipo = e.get("tipo", "unknown")
            by_tipo[tipo] = by_tipo.get(tipo, 0) + 1
            if e.get("intensidad"):
                intensidades.append(e["intensidad"])
        
        return {
            "total": len(emociones),
            "by_tipo": by_tipo,
            "avg_intensidad": sum(intensidades) / len(intensidades) if intensidades else 0
        }
