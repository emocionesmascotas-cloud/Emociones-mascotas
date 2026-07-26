"""
Script de Migración: Notion → Supabase
======================================
Mueve datos desde Notion a Supabase Cloud (Free Tier).

Uso:
    # Configurar variables de entorno primero
    export SUPABASE_URL=https://xxx.supabase.co
    export SUPABASE_SERVICE_KEY=eyJ...
    export NOTION_TOKEN=ntn_...
    export NOTION_DATABASE_ID=xxx...

    # Ejecutar migración
    python scripts/migrate_notion_to_supabase.py

    # O con argumentos
    python scripts/migrate_notion_to_supabase.py --notion-db-id xxx --dry-run
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("Migration")


# =============================================================================
# SCHEMAS DE TABLAS SUPABASE
# =============================================================================

SCHEMA_SQL = """
-- =====================================================
-- SCHEMA PARA EMOCIONES MASCOTAS
-- Ejecutar en Supabase SQL Editor
-- =====================================================

-- Tabla de mascotas
CREATE TABLE IF NOT EXISTS mascotas (
    id BIGSERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('perro', 'gato', 'ave', 'roedor', 'reptil', 'otro')),
    raza TEXT DEFAULT '',
    edad INTEGER DEFAULT 0,
    dueno_id TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de emociones
CREATE TABLE IF NOT EXISTS emociones (
    id BIGSERIAL PRIMARY KEY,
    mascota_id BIGINT REFERENCES mascotas(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('feliz', 'triste', 'ansioso', 'tranquilo', 'jugueton', 'asustado', 'enfermizo', 'cansado', 'excitado', 'confundido')),
    intensidad INTEGER DEFAULT 3 CHECK (intensidad >= 1 AND intensidad <= 5),
    notas TEXT DEFAULT '',
    registrado_por TEXT DEFAULT '',
    fecha TIMESTAMPTZ DEFAULT NOW(),
    source TEXT DEFAULT 'notion' CHECK (source IN ('notion', 'telegram', 'manual', 'web')),
    notion_page_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_mascotas_tipo ON mascotas(tipo);
CREATE INDEX IF NOT EXISTS idx_mascotas_dueno ON mascotas(dueno_id);
CREATE INDEX IF NOT EXISTS idx_emociones_mascota ON emociones(mascota_id);
CREATE INDEX IF NOT EXISTS idx_emociones_fecha ON emociones(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_emociones_tipo ON emociones(tipo);

-- Habilitar RLS
ALTER TABLE mascotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE emociones ENABLE ROW LEVEL SECURITY;

-- Políticas RLS ( Row Level Security)
CREATE POLICY "admin_all_mascotas" ON mascotas FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "admin_all_emociones" ON emociones FOR ALL USING (true) WITH CHECK (true);
"""


# =============================================================================
# MAPEO DE DATOS NOTION → SUPABASE
# =============================================================================

EMOCION_MAP = {
    "feliz": "feliz", "triste": "triste", "contento": "feliz",
    "enojado": "ansioso", "ansioso": "ansioso", "nervioso": "ansioso",
    "tranquilo": "tranquilo", "calmado": "tranquilo",
    "juguetón": "jugueton", "jugueton": "jugueton", "jugando": "jugueton",
    "asustado": "asustado", "miedoso": "asustado",
    "enfermizo": "enfermizo", "enfermo": "enfermizo",
    "cansado": "cansado", "dormido": "cansado",
    "excitado": "excitado", "emocionado": "excitado",
    "confundido": "confundido", "desorientado": "confundido",
}

TIPO_MASCOTA_MAP = {
    "perro": "perro", "dog": "perro",
    "gato": "gato", "cat": "gato",
    "ave": "ave", "bird": "ave", "pájaro": "ave",
    "roedor": "roedor", "hamster": "roedor", "cobayo": "roedor",
    "reptil": "reptil", "lagarto": "reptil", "serpiente": "reptil",
    "otro": "otro", "other": "otro",
}


def normalize_emocion(tipo: str) -> str:
    tipo_lower = tipo.lower().strip()
    return EMOCION_MAP.get(tipo_lower, tipo_lower)


def normalize_tipo_mascota(tipo: str) -> str:
    tipo_lower = tipo.lower().strip()
    return TIPO_MASCOTA_MAP.get(tipo_lower, tipo_lower)


# =============================================================================
# CLIENTES
# =============================================================================

def get_notion_client():
    token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_INTEGRATION_KEY")
    if not token:
        raise EnvironmentError("NOTION_TOKEN o NOTION_INTEGRATION_KEY no configurado")
    
    import httpx
    
    class NotionRESTClient:
        def __init__(self, token):
            self.token = token
            self.base_url = "https://api.notion.com/v1"
            self.headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
        
        def query_database(self, db_id: str) -> List[Dict]:
            results = []
            cursor = None
            while True:
                payload = {"page_size": 100}
                if cursor:
                    payload["start_cursor"] = cursor
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        f"{self.base_url}/databases/{db_id}/query",
                        headers=self.headers, json=payload
                    )
                    if response.status_code != 200:
                        raise Exception(f"Notion error: {response.text}")
                    data = response.json()
                    results.extend(data.get("results", []))
                    cursor = data.get("next_cursor")
                    if not cursor:
                        break
            return results
    
    return NotionRESTClient(token)


def get_supabase_client():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from integrations.supabase_connector import SupabaseClient, SupabaseConfig
    
    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # Usar service role key
    
    if not url or not anon_key:
        raise EnvironmentError("SUPABASE_URL y SUPABASE_ANON_KEY son requeridos")
    
    config = SupabaseConfig(url=url, anon_key=anon_key, service_key=service_key)
    return SupabaseClient(config)


# =============================================================================
# EXTRACTORES DE DATOS NOTION
# =============================================================================

def extract_mascota_properties(page: Dict) -> Optional[Dict]:
    props = page.get("properties", {})
    
    nombre = ""
    for title_key in ["Nombre", "Name", "name", "Title", "title"]:
        if props.get(title_key):
            title_field = props[title_key].get("title", [])
            if title_field:
                nombre = title_field[0].get("text", {}).get("content", "")
                break
    
    tipo = ""
    for tipo_key in ["Tipo", "tipo", "Type", "type"]:
        if props.get(tipo_key):
            select = props[tipo_key].get("select", {})
            if select:
                tipo = select.get("name", "")
                break
    
    raza = props.get("Raza", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
    edad = props.get("Edad", {}).get("number", 0) or 0
    
    if not nombre:
        return None
    
    return {
        "nombre": nombre,
        "tipo": normalize_tipo_mascota(tipo) if tipo else "otro",
        "raza": raza,
        "edad": edad,
        "dueno_id": "",
        "notion_page_id": page.get("id")
    }


def extract_emocion_properties(page: Dict) -> Optional[Dict]:
    props = page.get("properties", {})
    
    tipo = ""
    for emocion_key in ["Emocion", "Emoción", "Tipo", "tipo"]:
        if props.get(emocion_key):
            select = props[emocion_key].get("select", {})
            if select:
                tipo = select.get("name", "")
                break
    
    intensidad = props.get("Intensidad", {}).get("number", 3) or 3
    
    notas = ""
    if props.get("Notas", {}).get("rich_text"):
        notas = props["Notas"]["rich_text"][0].get("text", {}).get("content", "")
    
    fecha = page.get("created_time", datetime.utcnow().isoformat())
    
    return {
        "tipo": normalize_emocion(tipo) if tipo else "feliz",
        "intensidad": max(1, min(5, intensidad)),
        "notas": notas,
        "fecha": fecha,
        "mascota_id": None,
        "notion_page_id": page.get("id")
    }


# =============================================================================
# MIGRACIÓN
# =============================================================================

class NotionToSupabaseMigrator:
    def __init__(self, notion_db_id: str, dry_run: bool = False):
        self.notion_db_id = notion_db_id
        self.dry_run = dry_run
        self.notion = get_notion_client()
        self.supabase = get_supabase_client()
        self.stats = {
            "mascotas_created": 0, "mascotas_skipped": 0,
            "emociones_created": 0, "emociones_skipped": 0,
            "errors": []
        }
    
    def run(self):
        logger.info("=" * 60)
        logger.info("INICIANDO MIGRACIÓN: NOTION → SUPABASE")
        logger.info(f"Modo: {'DRY RUN' if self.dry_run else 'LIVE'}")
        
        self._verify_connections()
        self._migrate_mascotas()
        self._migrate_emociones()
        self._print_summary()
        return self.stats
    
    def _verify_connections(self):
        logger.info("Verificando conexiones...")
        health = self.supabase.health_check()
        if health.get("status") == "healthy":
            logger.info("  ✅ Supabase: Conectado")
    
    def _migrate_mascotas(self):
        logger.info("\n📦 FASE 1: Migrando mascotas...")
        
        try:
            pages = self.notion.query_database(self.notion_db_id)
        except Exception as e:
            logger.error(f"Error consultando Notion: {str(e)}")
            return
        
        logger.info(f"Encontradas {len(pages)} páginas en Notion")
        
        for page in pages:
            try:
                data = extract_mascota_properties(page)
                if not data:
                    self.stats["mascotas_skipped"] += 1
                    continue
                
                if self.supabase.exists("mascotas", {"notion_page_id": data["notion_page_id"]}):
                    self.stats["mascotas_skipped"] += 1
                    continue
                
                if self.dry_run:
                    logger.info(f"[DRY RUN] Crearía: {data['nombre']}")
                    self.stats["mascotas_created"] += 1
                else:
                    result = self.supabase.insert("mascotas", data)
                    logger.info(f"  ✅ {data['nombre']}")
                    self.stats["mascotas_created"] += 1
            except Exception as e:
                self.stats["errors"].append(f"Mascota: {str(e)}")
    
    def _migrate_emociones(self):
        logger.info("\n😊 FASE 2: Migrando emociones...")
        emociones_db_id = os.environ.get("NOTION_EMOCIONES_DB_ID")
        if not emociones_db_id:
            logger.warning("  ⚠️ NOTION_EMOCIONES_DB_ID no configurado")
            return
        
        try:
            pages = self.notion.query_database(emociones_db_id)
            logger.info(f"Encontradas {len(pages)} emociones")
            
            for page in pages:
                data = extract_emocion_properties(page)
                if self.supabase.exists("emociones", {"notion_page_id": data["notion_page_id"]}):
                    self.stats["emociones_skipped"] += 1
                    continue
                
                data["source"] = "notion"
                
                if self.dry_run:
                    self.stats["emociones_created"] += 1
                else:
                    self.supabase.insert("emociones", data)
                    self.stats["emociones_created"] += 1
        except Exception as e:
            logger.error(f"Error: {str(e)}")
    
    def _print_summary(self):
        logger.info("\n" + "=" * 60)
        logger.info("RESUMEN")
        logger.info(f"Mascotas: {self.stats['mascotas_created']} creadas, {self.stats['mascotas_skipped']} saltadas")
        logger.info(f"Emociones: {self.stats['emociones_created']} creadas, {self.stats['emociones_skipped']} saltadas")
        if self.stats["errors"]:
            logger.warning(f"Errores: {len(self.stats['errors'])}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Migrar datos de Notion a Supabase")
    parser.add_argument("--notion-db-id", help="ID de database de mascotas")
    parser.add_argument("--emociones-db-id", help="ID de database de emociones")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin escribir")
    parser.add_argument("--schema-only", action="store_true", help="Solo mostrar SQL")
    
    args = parser.parse_args()
    
    if args.schema_only:
        print(SCHEMA_SQL)
        return
    
    notion_db_id = args.notion_db_id or os.environ.get("NOTION_DATABASE_ID")
    
    if not notion_db_id:
        print("❌ Se requiere --notion-db-id o NOTION_DATABASE_ID")
        sys.exit(1)
    
    if args.emociones_db_id:
        os.environ["NOTION_EMOCIONES_DB_ID"] = args.emociones_db_id
    
    migrator = NotionToSupabaseMigrator(notion_db_id, args.dry_run)
    migrator.run()


if __name__ == "__main__":
    main()
