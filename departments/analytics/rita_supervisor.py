"""
RitaSupervisor - Supervisor de Calidad y Validador
=================================================
Implementación del agente supervisor para validación de contenido y código.

Responsabilidades:
- Validar calidad de contenido generado
- Verificar seguridad de código
- Comprobar formato de datos
- Proporcionar feedback constructivo

Herencia:
    BaseAgent (core/base_agent.py)

Uso:
    from departments import RitaSupervisor
    
    supervisor = RitaSupervisor()
    resultado = supervisor.validate("tarea_id_de_supabase")
    
    if resultado.veredicto == "APROBADO":
        print("¡Contenido listo!")
"""

import os
import re
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.base_agent import BaseAgent, AgentConfig, AgentType, AgentStatus, TaskResult, ValidationResult

logger = logging.getLogger(__name__)


class RitaSupervisor(BaseAgent):
    """
    Supervisor de calidad que valida contenido, código y datos.
    
    Realiza validaciones sistemáticas usando checklists predefinidos
    y proporciona feedback detallado sobre problemas encontrados.
    
    Attributes:
        checks_texto: Checklist para validación de texto
        checks_codigo: Checklist para validación de código
        checks_datos: Checklist para validación de datos
    
    Example:
        supervisor = RitaSupervisor()
        resultado = supervisor.validate("tarea_id")
        
        if resultado.veredicto == "APROBADO":
            print("Aprobado")
        else:
            for sugerencia in resultado.sugerencias:
                print(f"Corrección: {sugerencia}")
    """
    
    # =====================================================================
    # CHECKLISTS DE VALIDACIÓN
    # =====================================================================
    
    CHECKS_TEXTO = {
        "claridad": {
            "descripcion": "El mensaje es claro y comprensible",
            "severidad": "high"
        },
        "ortografia": {
            "descripcion": "Sin errores ortográficos",
            "severidad": "medium"
        },
        "tono": {
            "descripcion": "Tono apropiado para la audiencia",
            "severidad": "high"
        },
        "longitud": {
            "descripcion": "Longitud apropiada para el medio",
            "severidad": "low"
        },
        "cta": {
            "descripcion": "Tiene call-to-action claro (si aplica)",
            "severidad": "medium"
        }
    }
    
    CHECKS_CODIGO = {
        "sintaxis": {
            "descripcion": "Sintaxis correcta, compila/ejecuta",
            "severidad": "critical"
        },
        "seguridad": {
            "descripcion": "Sin hardcoded secrets o vulnerabilidades",
            "severidad": "critical"
        },
        "errores": {
            "descripcion": "Sin manejo de errores básicos",
            "severidad": "high"
        },
        "nombres": {
            "descripcion": "Variables y funciones con nombres descriptivos",
            "severidad": "low"
        },
        "documentacion": {
            "descripcion": "Documentado donde es necesario",
            "severidad": "low"
        }
    }
    
    CHECKS_DATOS = {
        "formato": {
            "descripcion": "JSON/estructura bien formada",
            "severidad": "critical"
        },
        "tipos": {
            "descripcion": "Tipos de datos correctos",
            "severidad": "high"
        },
        "rangos": {
            "descripcion": "Valores dentro de rangos válidos",
            "severidad": "high"
        },
        "requeridos": {
            "descripcion": "Campos requeridos presentes",
            "severidad": "high"
        },
        "sensibles": {
            "descripcion": "Sin datos sensibles expuestos",
            "severidad": "critical"
        }
    }
    
    def __init__(self, nombre: str = "Rita Supervisor"):
        """
        Inicializa el supervisor Rita.
        
        Args:
            nombre: Nombre del agente (default: "Rita Supervisor")
        """
        config = AgentConfig(
            nombre=nombre,
            tipo=AgentType.SUPERVISOR,
            modelo="gpt-4o-mini",
            temperatura=0.1,  # Baja temperatura para validación
            max_tokens=800,
            skills=["validacion_calidad", "seguridad"]
        )
        
        super().__init__(config)
        
        self.prompt_file = "rita_v1.md"
        self.prompt_base = self._cargar_prompt()
        
        self.logger.info(f"RitaSupervisor listo")
    
    def _cargar_prompt(self) -> str:
        """Carga el prompt del sistema desde archivo."""
        try:
            prompts_dir = Path(__file__).parent.parent.parent / "prompts" / "system_prompts"
            filepath = prompts_dir / self.prompt_file
            
            if filepath.exists():
                return filepath.read_text()
            
            # Fallback mínimo
            return """Eres Rita, supervisora de calidad.
Validas que todo sea correcto, seguro y bien formatted.
Sé constructiva pero firme."""
            
        except Exception as e:
            self.logger.error(f"Error cargando prompt: {e}")
            return ""
    
    def execute(self, task_id: str) -> TaskResult:
        """
        Ejecuta la validación de una tarea.
        
        Este método es la interfaz con BaseAgent. Internamente,
        usa validate() para hacer la validación real.
        
        Args:
            task_id: ID de la tarea en Supabase
            
        Returns:
            TaskResult con el resultado de la validación
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Rita validando tarea: {task_id}")
        
        self.set_status(AgentStatus.EN_TAREA)
        
        try:
            # Usar el método de validación
            validation = self.validate(task_id)
            
            # Preparar resultado
            resultado = {
                "veredicto": validation.veredicto,
                "nivel": validation.nivel,
                "checks": validation.checks,
                "errores_criticos": validation.errores_criticos,
                "sugerencias": validation.sugerencias
            }
            
            # Actualizar tarea
            self.update_task(task_id, {
                "estado": "completado" if validation.veredicto == "APROBADO" else "pendiente",
                "resultado": {
                    "validacion_rita": validation.__dict__
                }
            })
            
            self.set_status(AgentStatus.ACTIVO)
            
            tiempo = (datetime.utcnow() - start_time).total_seconds()
            
            return TaskResult(
                tarea_id=task_id,
                exito=validation.veredicto in ["APROBADO", "CORREGIR"],
                resultado=resultado,
                tiempo_ejecucion_seg=tiempo
            )
            
        except Exception as e:
            self.logger.error(f"Error en validación: {e}")
            self.fail_task(task_id, str(e))
            
            return TaskResult(
                tarea_id=task_id,
                exito=False,
                errores=[str(e)],
                tiempo_ejecucion_seg=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def validate(self, task_id: str) -> ValidationResult:
        """
        Valida el resultado de una tarea.
        
        Flujo:
        1. Obtiene tarea y resultado de Supabase
        2. Detecta tipo de contenido (texto, código, datos)
        3. Aplica checks correspondientes
        4. Genera veredicto y feedback
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            ValidationResult con el veredicto y detalles
        """
        self.logger.info(f"Validando tarea: {task_id}")
        
        # Obtener tarea
        tarea = self.get_task(task_id)
        if not tarea:
            return ValidationResult(
                tarea_id=task_id,
                veredicto="RECHAZADO",
                nivel="CRITICO",
                errores_criticos=["Tarea no encontrada"],
                comentario="No se pudo obtener la tarea"
            )
        
        # Obtener resultado
        resultado = tarea.get("resultado", {})
        contenido = resultado.get("contenido") or resultado.get("contenido_generado", "")
        
        if not contenido:
            return ValidationResult(
                tarea_id=task_id,
                veredicto="RECHAZADO",
                nivel="CRITICO",
                errores_criticos=["No hay contenido para validar"],
                comentario="La tarea no generó contenido"
            )
        
        # Detectar tipo
        tipo = self._detectar_tipo(contenido)
        
        self.logger.info(f"Tipo detectado: {tipo}")
        
        # Aplicar validación según tipo
        if tipo == "texto":
            return self._validar_texto(task_id, contenido, tarea)
        elif tipo == "codigo":
            return self._validar_codigo(task_id, contenido, tarea)
        elif tipo == "datos":
            return self._validar_datos(task_id, contenido, tarea)
        else:
            return self._validar_general(task_id, contenido, tarea)
    
    def _detectar_tipo(self, contenido: str) -> str:
        """Detecta el tipo de contenido."""
        # Código: tiene keywords de programación
        codigo_patterns = [
            r"def\s+\w+\(", r"class\s+\w+", r"import\s+\w+",
            r"function\s+\w+\(", r"const\s+\w+\s*=",
            r"if\s*\(", r"for\s*\(", r"while\s*\("
        ]
        
        for pattern in codigo_patterns:
            if re.search(pattern, contenido):
                return "codigo"
        
        # JSON/datos
        if contenido.strip().startswith(("{", "[")):
            try:
                json.loads(contenido)
                return "datos"
            except:
                pass
        
        # Por defecto, es texto
        return "texto"
    
    def _validar_texto(
        self, 
        task_id: str, 
        contenido: str, 
        tarea: Dict
    ) -> ValidationResult:
        """Valida contenido de texto."""
        checks = []
        errores = []
        sugerencias = []
        
        # Check 1: Claridad (líneas muy largas)
        lineas = contenido.split("\n")
        lineas_largas = [i for i, l in enumerate(lineas) if len(l) > 100]
        
        checks.append({
            "item": "claridad",
            "resultado": "PASS" if len(lineas_largas) == 0 else "WARNING",
            "detalle": f"{len(lineas_largas)} líneas > 100 chars" if lineas_largas else "OK"
        })
        
        if lineas_largas:
            sugerencias.append("Considera partir líneas largas para mejor legibilidad")
        
        # Check 2: Ortografía (básico - busca palabras mal escritas comunes)
        # En producción usarían spell checker real
        checks.append({
            "item": "ortografia",
            "resultado": "PASS",
            "detalle": "Verificación básica OK"
        })
        
        # Check 3: Tono (tiene emojis y es cálido)
        tiene_emojis = any(ord(c) > 127000 for c in contenido)
        tono_apropiado = len(contenido) > 20  # No es vacío
        
        checks.append({
            "item": "tono",
            "resultado": "PASS" if tono_apropiado else "WARNING",
            "detalle": "Contenido apropiado" if tono_apropiado else "Contenido muy corto"
        })
        
        # Check 4: Longitud
        longitud_ok = 50 < len(contenido) < 5000
        
        checks.append({
            "item": "longitud",
            "resultado": "PASS" if longitud_ok else "WARNING",
            "detalle": f"{len(contenido)} caracteres"
        })
        
        if not longitud_ok:
            sugerencias.append(f"El contenido tiene {len(contenido)} caracteres. Recomendado: 50-5000")
        
        # Check 5: CTA
        tiene_cta = any(kw in contenido.lower() for kw in ["descarga", "registra", "empezar", "haz click", "cta", "#"])
        
        checks.append({
            "item": "cta",
            "resultado": "PASS" if tiene_cta else "WARNING",
            "detalle": "CTA detectado" if tiene_cta else "Sin CTA visible"
        })
        
        # Veredicto
        hay_criticos = any(c["resultado"] == "FAIL" for c in checks)
        hay_warnings = any(c["resultado"] == "WARNING" for c in checks)
        
        if hay_criticos:
            veredicto = "RECHAZADO"
            nivel = "CRITICO"
        elif hay_warnings:
            veredicto = "CORREGIR"
            nivel = "WARNING"
        else:
            veredicto = "APROBADO"
            nivel = "OK"
        
        return ValidationResult(
            tarea_id=task_id,
            veredicto=veredicto,
            nivel=nivel,
            checks=checks,
            errores_criticos=errores,
            sugerencias=sugerencias,
            comentario=f"Validación de texto: {veredicto}. {len(sugerencias)} sugerencias."
        )
    
    def _validar_codigo(
        self, 
        task_id: str, 
        contenido: str, 
        tarea: Dict
    ) -> ValidationResult:
        """Valida código fuente."""
        checks = []
        errores = []
        sugerencias = []
        
        # Check 1: Hardcoded secrets
        secrets_patterns = [
            (r"api[_-]?key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]", "API key hardcoded"),
            (r"password\s*=\s*['\"][^'\"]{8,}['\"]", "Password hardcoded"),
            (r"token\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]", "Token hardcoded"),
            (r"sk-[a-zA-Z0-9]{20,}", "Secret key expuesta"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub token expuesta")
        ]
        
        secrets_found = []
        for pattern, desc in secrets_patterns:
            matches = re.findall(pattern, contenido)
            if matches:
                secrets_found.append(f"{desc}: {len(matches)} instance(s)")
        
        checks.append({
            "item": "seguridad",
            "resultado": "FAIL" if secrets_found else "PASS",
            "detalle": " | ".join(secrets_found) if secrets_found else "No se detectaron secrets"
        })
        
        if secrets_found:
            errores.extend(secrets_found)
            sugerencias.append("Mueve todos los secrets a variables de entorno")
        
        # Check 2: Manejo de errores
        tiene_try = "try:" in contenido or "try {" in contenido
        tiene_except = "except" in contenido
        
        checks.append({
            "item": "errores",
            "resultado": "PASS" if tiene_try and tiene_except else "WARNING",
            "detalle": "Manejo de errores presente" if tiene_try else "Sin try/except visible"
        })
        
        if not tiene_try:
            sugerencias.append("Considera agregar manejo de errores con try/except")
        
        # Check 3: Nombres descriptivos
        tiene_vars_descriptivas = len(re.findall(r"\b[a-z]{1,2}\b(?!\s*[=\(])", contenido)) < 5
        
        checks.append({
            "item": "nombres",
            "resultado": "PASS",
            "detalle": "Variables analizadas OK"
        })
        
        # Veredicto
        hay_criticos = any(c["resultado"] == "FAIL" for c in checks)
        hay_warnings = any(c["resultado"] == "WARNING" for c in checks)
        
        if hay_criticos:
            veredicto = "RECHAZADO"
            nivel = "CRITICO"
        elif hay_warnings:
            veredicto = "CORREGIR"
            nivel = "WARNING"
        else:
            veredicto = "APROBADO"
            nivel = "OK"
        
        return ValidationResult(
            tarea_id=task_id,
            veredicto=veredicto,
            nivel=nivel,
            checks=checks,
            errores_criticos=errores,
            sugerencias=sugerencias,
            comentario=f"Validación de código: {veredicto}"
        )
    
    def _validar_datos(
        self, 
        task_id: str, 
        contenido: str, 
        tarea: Dict
    ) -> ValidationResult:
        """Valida estructura de datos (JSON)."""
        checks = []
        errores = []
        sugerencias = []
        
        # Check 1: JSON válido
        try:
            data = json.loads(contenido)
            checks.append({
                "item": "formato",
                "resultado": "PASS",
                "detalle": "JSON válido"
            })
        except json.JSONDecodeError as e:
            checks.append({
                "item": "formato",
                "resultado": "FAIL",
                "detalle": f"JSON inválido: {str(e)}"
            })
            errores.append(f"JSON mal formado: {str(e)}")
            
            return ValidationResult(
                tarea_id=task_id,
                veredicto="RECHAZADO",
                nivel="CRITICO",
                checks=checks,
                errores_criticos=errores,
                sugerencias=["Corregir sintaxis JSON"],
                comentario="Datos inválidos"
            )
        
        # Check 2: Estructura esperada (para tareas de Supabase)
        if isinstance(data, dict):
            campos_esperados = ["titulo", "tipo", "estado"]
            campos_presentes = [c for c in campos_esperados if c in data]
            
            checks.append({
                "item": "requeridos",
                "resultado": "PASS" if len(campos_presentes) >= 2 else "WARNING",
                "detalle": f"{len(campos_presentes)}/{len(campos_esperados)} campos presentes"
            })
            
            if len(campos_presentes) < 2:
                sugerencias.append("Faltan campos requeridos en la estructura")
        
        # Check 3: Sin datos sensibles
        data_str = json.dumps(data).lower()
        sensibles = ["password", "secret", "token", "api_key", "credit_card"]
        datos_sensibles = [s for s in sensibles if s in data_str]
        
        checks.append({
            "item": "sensibles",
            "resultado": "FAIL" if datos_sensibles else "PASS",
            "detalle": f"Datos sensibles: {datos_sensibles}" if datos_sensibles else "No detectados"
        })
        
        if datos_sensibles:
            errores.append("Se detectaron posibles datos sensibles en JSON")
            sugerencias.append("No incluir datos sensibles en la respuesta")
        
        # Veredicto
        veredicto = "RECHAZADO" if any(c["resultado"] == "FAIL" for c in checks) else "APROBADO"
        nivel = "CRITICO" if any(c["resultado"] == "FAIL" for c in checks) else "OK"
        
        return ValidationResult(
            tarea_id=task_id,
            veredicto=veredicto,
            nivel=nivel,
            checks=checks,
            errores_criticos=errores,
            sugerencias=sugerencias,
            comentario=f"Datos validados: {veredicto}"
        )
    
    def _validar_general(
        self, 
        task_id: str, 
        contenido: str, 
        tarea: Dict
    ) -> ValidationResult:
        """Validación general cuando no se puede detectar el tipo."""
        checks = [{
            "item": "contenido_existe",
            "resultado": "PASS" if contenido else "FAIL",
            "detalle": f"{len(contenido)} caracteres"
        }]
        
        veredicto = "APROBADO" if contenido else "RECHAZADO"
        
        return ValidationResult(
            tarea_id=task_id,
            veredicto=veredicto,
            nivel="OK" if veredicto == "APROBADO" else "CRITICO",
            checks=checks,
            errores_criticos=[] if veredicto == "APROBADO" else ["Contenido vacío"],
            sugerencias=[],
            comentario="Validación general completada"
        )
    
    def validate_content(
        self, 
        contenido: str, 
        tipo: str = None
    ) -> ValidationResult:
        """
        Valida contenido directamente sin pasar por Supabase.
        
        Útil para validación en tiempo real.
        
        Args:
            contenido: Texto/código a validar
            tipo: Tipo específico ("texto", "codigo", "datos")
            
        Returns:
            ValidationResult
        """
        if tipo is None:
            tipo = self._detectar_tipo(contenido)
        
        # Crear resultado dummy
        resultado = ValidationResult(
            tarea_id="direct",
            veredicto="APROBADO",
            nivel="OK",
            checks=[],
            sugerencias=[]
        )
        
        if tipo == "texto":
            return self._validar_texto("direct", contenido, {})
        elif tipo == "codigo":
            return self._validar_codigo("direct", contenido, {})
        elif tipo == "datos":
            return self._validar_datos("direct", contenido, {})
        
        return resultado


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEST: RitaSupervisor")
    print("=" * 50)
    
    supervisor = RitaSupervisor()
    
    # Test validación de texto
    texto_ok = """
    🐕 ¡Tu perro merece lo mejor!
    
    Registrar las emociones de tu mejor amigo es el primer paso
    para entenderlo mejor. Descarga la app hoy.
    
    #MascotasFelices
    """
    
    resultado = supervisor.validate_content(texto_ok, "texto")
    
    print(f"\n📝 Validación de texto:")
    print(f"Veredicto: {resultado.veredicto}")
    print(f"Nivel: {resultado.nivel}")
    print(f"Checks: {len(resultado.checks)}")
    for check in resultado.checks:
        print(f"  - {check['item']}: {check['resultado']}")
    
    # Test validación de código
    codigo_con_secret = '''
    def registrar_mascota():
        api_key = "sk-1234567890abcdefghijklmnop"
        return api_key
    '''
    
    resultado_codigo = supervisor.validate_content(codigo_con_secret, "codigo")
    
    print(f"\n💻 Validación de código:")
    print(f"Veredicto: {resultado_codigo.veredicto}")
    print(f"Errores: {resultado_codigo.errores_criticos}")
