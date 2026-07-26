-- =============================================================================
-- SUPABASE SCHEMA: Oficina v2.0
-- =============================================================================
-- Archivo: docs/supabase_schema.sql
-- Descripción: Schema SQL para el sistema de Oficina con Agentes
-- Base de datos: PostgreSQL 15+ (Supabase Cloud)
-- 
-- USO:
--   Copia este contenido y pégalo en el SQL Editor de Supabase
--   O ejecuta: psql -f docs/supabase_schema.sql
-- =============================================================================

-- =============================================================================
-- EXTENSIONES
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Para búsqueda fuzzy

-- =============================================================================
-- TABLA: agentes
-- =============================================================================
-- Define los agentes disponibles en el sistema (Pepita, Backend, Frontend, Data)

CREATE TABLE IF NOT EXISTS agentes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL CHECK (tipo IN ('planificador', 'backend', 'frontend', 'data', 'general')),
    estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'en_tarea', 'error')),
    descripcion TEXT DEFAULT '',
    
    -- Configuración de IA
    gpt_model TEXT DEFAULT 'gpt-4o-mini',
    prompt_base TEXT DEFAULT '',
    temp_max_tokens INTEGER DEFAULT 1000,
    
    -- Metadatos
    config JSONB DEFAULT '{}',
    stats JSONB DEFAULT '{"tareas_completadas": 0, "tareas_fallidas": 0, "ultima_ejecucion": null}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para agentes
CREATE INDEX IF NOT EXISTS idx_agentes_tipo ON agentes(tipo);
CREATE INDEX IF NOT EXISTS idx_agentes_estado ON agentes(estado);
CREATE INDEX IF NOT EXISTS idx_agentes_nombre ON agentes(nombre);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agentes_updated_at
    BEFORE UPDATE ON agentes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- TABLA: departamentos
-- =============================================================================
-- Agrupa agentes por departamento/tema

CREATE TABLE IF NOT EXISTS departamentos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT DEFAULT '',
    agentes_ids UUID[] DEFAULT '{}',
    
    -- Integraciones
    webhook_url TEXT,
    notion_page_id TEXT,
    
    -- Configuración
    prioridad_default INTEGER DEFAULT 3 CHECK (prioridad_default BETWEEN 1 AND 5),
    timeout_minutos INTEGER DEFAULT 30,
    
    -- Estado
    estado TEXT DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'mantenimiento')),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_deptos_estado ON departamentos(estado);
CREATE INDEX IF NOT EXISTS idx_deptos_nombre ON departamentos(nombre);

-- Trigger
CREATE TRIGGER trigger_deptos_updated_at
    BEFORE UPDATE ON departamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- TABLA: tareas
-- =============================================================================
-- Registra todas las tareas del sistema

CREATE TABLE IF NOT EXISTS tareas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Datos básicos
    titulo TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    tipo TEXT NOT NULL CHECK (tipo IN ('bug', 'feature', 'refactor', 'docs', 'deploy', 'query', 'automation', 'general')),
    
    -- Estado y prioridad
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_progreso', 'completado', 'fallido', 'cancelado')),
    prioridad INTEGER DEFAULT 3 CHECK (prioridad BETWEEN 1 AND 5),
    
    -- Asignación
    departamento_id UUID REFERENCES departamentos(id) ON DELETE SET NULL,
    agente_asignado UUID REFERENCES agentes(id) ON DELETE SET NULL,
    
    -- Origen
    solicitante TEXT NOT NULL,
    telegram_chat_id TEXT,
    telegram_message_id TEXT,
    
    -- Clasificación (Pepita)
    intencion TEXT,
    urgencia TEXT CHECK (urgencia IN ('baja', 'normal', 'alta', 'urgente')),
    confianza_clasificacion DECIMAL(3,2) DEFAULT 0.0,
    
    -- Resultado
    resultado JSONB DEFAULT '{}',
    errores TEXT[],
    
    -- Logs de ejecución
    logs JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Restricciones
    CONSTRAINT valid_prioridad CHECK (prioridad BETWEEN 1 AND 5)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_tareas_estado ON tareas(estado);
CREATE INDEX IF NOT EXISTS idx_tareas_prioridad ON tareas(prioridad);
CREATE INDEX IF NOT EXISTS idx_tareas_departamento ON tareas(departamento_id);
CREATE INDEX IF NOT EXISTS idx_tareas_agente ON tareas(agente_asignado);
CREATE INDEX IF NOT EXISTS idx_tareas_created_at ON tareas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tareas_tipo ON tareas(tipo);
CREATE INDEX IF NOT EXISTS idx_tareas_telegram ON tareas(telegram_chat_id) WHERE telegram_chat_id IS NOT NULL;

-- Índices para búsqueda full-text
CREATE INDEX IF NOT EXISTS idx_tareas_titulo_search ON tareas USING gin(to_tsvector('spanish', titulo));

-- Trigger
CREATE TRIGGER trigger_tareas_updated_at
    BEFORE UPDATE ON tareas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- TABLA: system_config
-- =============================================================================
-- Configuración global del sistema

CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    descripcion TEXT DEFAULT '',
    categoria TEXT DEFAULT 'general' CHECK (categoria IN ('general', 'seguridad', 'integracion', 'ai', 'notificaciones')),
    
    -- Auditoría
    updated_by UUID REFERENCES agentes(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_config_categoria ON system_config(categoria);

-- Trigger
CREATE TRIGGER trigger_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- TABLA: conversaciones
-- =============================================================================
-- Historial de conversaciones por chat de Telegram

CREATE TABLE IF NOT EXISTS conversaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id TEXT NOT NULL,
    mensajes JSONB DEFAULT '[]',
    
    -- Metadatos
    ultimo_mensaje_at TIMESTAMPTZ,
    mensajes_count INTEGER DEFAULT 0,
    
    -- Contexto
    contexto JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_conversaciones_chat ON conversaciones(chat_id);
CREATE INDEX IF NOT EXISTS idx_conversaciones_ultimo ON conversaciones(ultimo_mensaje_at DESC);

-- =============================================================================
-- TABLA: logs_ejecucion
-- =============================================================================
-- Logs detallados de ejecución de agentes

CREATE TABLE IF NOT EXISTS logs_ejecucion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tarea_id UUID REFERENCES tareas(id) ON DELETE CASCADE,
    agente_id UUID REFERENCES agentes(id) ON DELETE SET NULL,
    
    -- Datos del log
    nivel TEXT NOT NULL CHECK (nivel IN ('debug', 'info', 'warning', 'error', 'critical')),
    mensaje TEXT NOT NULL,
    contexto JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_logs_tarea ON logs_ejecucion(tarea_id);
CREATE INDEX IF NOT EXISTS idx_logs_agente ON logs_ejecucion(agente_id);
CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs_ejecucion(nivel);
CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs_ejecucion(created_at DESC);

-- =============================================================================
-- TABLA: mascotas (Existente en Emociones Mascotas)
-- =============================================================================

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

-- Índices
CREATE INDEX IF NOT EXISTS idx_mascotas_tipo ON mascotas(tipo);

-- =============================================================================
-- TABLA: emociones (Existente en Emociones Mascotas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS emociones (
    id BIGSERIAL PRIMARY KEY,
    mascota_id BIGINT REFERENCES mascotas(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('feliz', 'triste', 'ansioso', 'tranquilo', 'jugueton', 'asustado', 'enfermizo', 'cansado', 'excitado', 'confundido')),
    intensidad INTEGER DEFAULT 3 CHECK (intensidad BETWEEN 1 AND 5),
    notas TEXT DEFAULT '',
    registrado_por TEXT DEFAULT '',
    fecha TIMESTAMPTZ DEFAULT NOW(),
    source TEXT DEFAULT 'telegram' CHECK (source IN ('telegram', 'notion', 'manual', 'web', 'api')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_emociones_mascota ON emociones(mascota_id);
CREATE INDEX IF NOT EXISTS idx_emociones_fecha ON emociones(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_emociones_tipo ON emociones(tipo);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE agentes ENABLE ROW LEVEL SECURITY;
ALTER TABLE departamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tareas ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs_ejecucion ENABLE ROW LEVEL SECURITY;
ALTER TABLE mascotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE emociones ENABLE ROW LEVEL SECURITY;

-- Políticas para agentes (service role tiene acceso completo)
CREATE POLICY "service_role_all_agentes" ON agentes
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_deptos" ON departamentos
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_tareas" ON tareas
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_config" ON system_config
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_conversaciones" ON conversaciones
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_logs" ON logs_ejecucion
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_mascotas" ON mascotas
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_emociones" ON emociones
    FOR ALL USING (true) WITH CHECK (true);

-- =============================================================================
-- DATOS INICIALES
-- =============================================================================

-- Insertar agentes por defecto
INSERT INTO agentes (nombre, tipo, descripcion, prompt_base, gpt_model) VALUES
    ('Pepita', 'planificador', 'Planificador principal. Clasifica mensajes y asigna tareas.', 
     'Eres Pepita, la asistente de emociones de mascotas. Clasifica mensajes y asigna tareas.', 
     'gpt-4o-mini'),
    ('Backend Agent', 'backend', 'Agente especializado en backend (FastAPI, Python, SQL).', 
     'Eres un agente de backend especializado.', 
     'gpt-4o-mini'),
    ('Frontend Agent', 'frontend', 'Agente especializado en frontend (HTML, CSS, JS).', 
     'Eres un agente de frontend especializado.', 
     'gpt-4o-mini'),
    ('Data Agent', 'data', 'Agente especializado en datos y estadísticas.', 
     'Eres un agente de datos especializado.', 
     'gpt-4o-mini')
ON CONFLICT (nombre) DO NOTHING;

-- Insertar departamentos
INSERT INTO departamentos (nombre, descripcion, prioridad_default) VALUES
    ('Backend', 'Tareas de backend, APIs, base de datos', 2),
    ('Frontend', 'Tareas de interfaz, CSS, JavaScript', 2),
    ('Data', 'Análisis de datos, estadísticas, reportes', 3),
    ('General', 'Tareas generales sin categoría específica', 3)
ON CONFLICT (nombre) DO NOTHING;

-- Insertar configuración inicial
INSERT INTO system_config (key, value, descripcion, categoria) VALUES
    ('telegram_enabled', '{"valor": true}', 'Habilitar notificaciones Telegram', 'notificaciones'),
    ('notion_enabled', '{"valor": true}', 'Habilitar sincronización Notion', 'integracion'),
    ('ai_temperature', '{"valor": 0.7}', 'Temperatura para modelos IA', 'ai'),
    ('max_tareas_concurrentes', '{"valor": 5}', 'Máximo de tareas simultáneas', 'general'),
    ('timeout_tarea_minutos', '{"valor": 10}', 'Timeout por tarea en minutos', 'general')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- =============================================================================
-- FUNCIONES DE UTILIDAD
-- =============================================================================

-- Función para actualizar stats de agente
CREATE OR REPLACE FUNCTION actualizar_stats_agente(
    p_agente_id UUID,
    p_tipo TEXT  -- 'completada' o 'fallida'
)
RETURNS VOID AS $$
BEGIN
    UPDATE agentes
    SET stats = jsonb_set(
        jsonb_set(stats, 
            CASE WHEN p_tipo = 'completada' 
                 THEN '{tareas_completadas}' 
                 ELSE '{tareas_fallidas}' END,
            to_jsonb((COALESCE(stats->>(
            CASE WHEN p_tipo = 'completada' 
                 THEN 'tareas_completadas' 
                 ELSE 'tareas_fallidas' END
            ), '0')::integer) + 1)
        ),
        '{ultima_ejecucion}',
        to_jsonb(NOW())
    ),
    estado = 'activo'
    WHERE id = p_agente_id;
END;
$$ LANGUAGE plpgsql;

-- Función para crear tarea desde Telegram
CREATE OR REPLACE FUNCTION crear_tarea_telegram(
    p_titulo TEXT,
    p_descripcion TEXT,
    p_solicitante TEXT,
    p_chat_id TEXT,
    p_departamento TEXT DEFAULT 'General'
)
RETURNS UUID AS $$
DECLARE
    v_tarea_id UUID;
    v_depto_id UUID;
BEGIN
    -- Buscar departamento
    SELECT id INTO v_depto_id 
    FROM departamentos 
    WHERE nombre = p_departamento;
    
    -- Crear tarea
    INSERT INTO tareas (titulo, descripcion, tipo, solicitante, telegram_chat_id, departamento_id)
    VALUES (p_titulo, p_descripcion, 'general', p_solicitante, p_chat_id, v_depto_id)
    RETURNING id INTO v_tarea_id;
    
    RETURN v_tarea_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VISTAS ÚTILES
-- =============================================================================

-- Vista: Tareas activas con detalles
CREATE OR REPLACE VIEW vista_tareas_activas AS
SELECT 
    t.id,
    t.titulo,
    t.estado,
    t.prioridad,
    t.created_at,
    a.nombre AS agente,
    d.nombre AS departamento,
    t.intencion,
    t.urgencia
FROM tareas t
LEFT JOIN agentes a ON t.agente_asignado = a.id
LEFT JOIN departamentos d ON t.departamento_id = d.id
WHERE t.estado IN ('pendiente', 'en_progreso')
ORDER BY t.prioridad ASC, t.created_at ASC;

-- Vista: Stats de agentes
CREATE OR REPLACE VIEW vista_stats_agentes AS
SELECT 
    a.id,
    a.nombre,
    a.tipo,
    a.estado,
    a.stats,
    COUNT(t.id) FILTER (WHERE t.estado = 'en_progreso') AS tareas_en_progreso,
    COUNT(t.id) FILTER (WHERE t.estado = 'completado' AND t.completed_at > NOW() - INTERVAL '24 hours') AS tareas_hoy
FROM agentes a
LEFT JOIN tareas t ON t.agente_asignado = a.id
GROUP BY a.id, a.nombre, a.tipo, a.estado, a.stats;

-- =============================================================================
-- PERMISOS
-- =============================================================================

-- Crear rol anon (para consultas públicas si es necesario)
-- GRANT USAGE ON SCHEMA public TO anon;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Permisos para service_role (usado por nuestra API)
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- =============================================================================
-- FIN DEL SCHEMA
-- =============================================================================

COMMENT ON TABLE agentes IS 'Agentes del sistema (Pepita, Backend, Frontend, Data)';
COMMENT ON TABLE departamentos IS 'Departamentos que agrupan agentes y tareas';
COMMENT ON TABLE tareas IS 'Tareas del sistema con seguimiento de estado';
COMMENT ON TABLE system_config IS 'Configuración global del sistema';
COMMENT ON TABLE conversaciones IS 'Historial de conversaciones de Telegram';
COMMENT ON TABLE logs_ejecucion IS 'Logs detallados de ejecución de agentes';

-- Verificar que todo se creó correctamente
SELECT 
    'Tablas creadas: ' || count(*) as resultado
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('agentes', 'departamentos', 'tareas', 'system_config', 'conversaciones', 'logs_ejecucion', 'mascotas', 'emociones');
