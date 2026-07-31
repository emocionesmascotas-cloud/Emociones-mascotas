-- =====================================================
-- SCHEMA OFICINA v2.0 - EMOCIONES MASCOTAS
-- =====================================================
-- Ejecutar en: Supabase → SQL Editor
-- =====================================================

-- Tabla agentes
CREATE TABLE IF NOT EXISTS agentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL DEFAULT 'general',
    estado TEXT NOT NULL DEFAULT 'activo',
    departamento TEXT DEFAULT '',
    rol TEXT DEFAULT '',
    descripcion TEXT DEFAULT '',
    habilidades TEXT[] DEFAULT '{}',
    gpt_model TEXT DEFAULT 'gpt-4o-mini',
    config JSONB DEFAULT '{}',
    stats JSONB DEFAULT '{"tareas_completadas": 0}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla tareas (principal)
CREATE TABLE IF NOT EXISTS tareas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    tipo TEXT DEFAULT 'general',
    estado TEXT DEFAULT 'pendiente',  -- pending, approved, published, failed
    prioridad INTEGER DEFAULT 3,
    intencion TEXT DEFAULT 'general',
    urgencia TEXT DEFAULT 'normal',
    solicitante TEXT DEFAULT '',
    telegram_chat_id TEXT,
    telegram_message_id TEXT,
    resultado JSONB DEFAULT '{}',
    errores TEXT[] DEFAULT '{}',
    agente_asignado UUID REFERENCES agentes(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de configuración del sistema
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    descripcion TEXT DEFAULT '',
    categoria TEXT DEFAULT 'general'
);

-- =====================================================
-- SEGURIDAD (RLS)
-- =====================================================

ALTER TABLE agentes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tareas ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;

-- Políticas públicas (desarrollo)
CREATE POLICY "public_all_agentes" ON agentes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "public_all_tareas" ON tareas FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "public_all_config" ON system_config FOR ALL USING (true) WITH CHECK (true);

-- =====================================================
-- DATOS INICIALES
-- =====================================================

INSERT INTO agentes (nombre, tipo, departamento, rol, estado, habilidades) VALUES
    ('Pepita', 'planificador', 'core', 'planificador', 'idle', ARRAY['clasificacion', 'enrutamiento']),
    ('Dana', 'marketing', 'marketing', 'ejecutor', 'idle', ARRAY['copywriting', 'seo']),
    ('Rita', 'supervisor', 'analytics', 'supervisor', 'idle', ARRAY['validacion', 'calidad']),
    ('Carlos', 'publicador', 'publishing', 'publicador', 'idle', ARRAY['publicacion', 'telegram', 'blogger'])
ON CONFLICT (nombre) DO NOTHING;

-- Configuración inicial
INSERT INTO system_config (key, value, descripcion, categoria) VALUES
    ('workflow_active', '{"value": true}', 'Workflow principal activo', 'workflow'),
    ('telegram_enabled', '{"value": true}', 'Integración Telegram habilitada', 'integrations')
ON CONFLICT (key) DO NOTHING;

-- =====================================================
-- FUNCIONES ÚTILES
-- =====================================================

-- Actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para tareas
DROP TRIGGER IF EXISTS trigger_tareas_updated_at ON tareas;
CREATE TRIGGER trigger_tareas_updated_at
    BEFORE UPDATE ON tareas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Trigger para agentes
DROP TRIGGER IF EXISTS trigger_agentes_updated_at ON agentes;
CREATE TRIGGER trigger_agentes_updated_at
    BEFORE UPDATE ON agentes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- VERIFICACIÓN
-- =====================================================

SELECT '✅ Schema creado exitosamente' as status;
SELECT COUNT(*) as total_agentes FROM agentes;
SELECT COUNT(*) as total_tareas FROM tareas;
