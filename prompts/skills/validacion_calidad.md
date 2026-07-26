# ✅ Skill: Validación de Calidad

> **Skill:** Verificación de Estándares y Calidad  
> **Nivel:** Intermedio  
> **Última actualización:** 2024-01-15

---

## 🎯 Objetivo

Este skill proporciona un framework sistemático para **validar que el contenido y código cumpla los estándares** antes de ser publicado o usado en producción.

---

## 📋 Niveles de Validación

| Nivel | Nombre | Uso | Quién |
|-------|--------|-----|-------|
| 1 | Revisión Rápida | Contenido casual | Agente que crea |
| 2 | Validación Completa | Contenido público | Rita |
| 3 | Auditoría | Código/datos sensibles | Senior Dev |

---

## 🔍 Checklist por Tipo

### Para Texto/Contenido

```markdown
## 📝 Validación de Contenido

### Claridad
- [ ] ¿El mensaje principal es claro?
- [ ] ¿Un lector nuevo entendería?
- [ ] ¿Hay jerga sin explicar?
- [ ] ¿Las oraciones son muy largas? (máx 20 palabras)

### Precisión
- [ ] ¿Los datos son correctos?
- [ ] ¿Las afirmaciones son verificables?
- [ ] ¿No hay contradicciones?
- [ ] ¿Las fechas/números son reales?

### Ortografía y Gramática
- [ ] ¿Sin errores ortográficos?
- [ ] ¿Puntuación correcta?
- [ ] ¿Concordancia correcta? (género, número)
- [ ] ¿Tildes en su lugar?

### Tono
- [ ] ¿El tono es apropiado para la audiencia?
- [ ] ¿Es consistente en todo el texto?
- [ ] ¿No hay sarcasmo no intencional?

### Formato
- [ ] ¿El formato es consistente?
- [ ] ¿Los títulos reflejan el contenido?
- [ ] ¿El espaciado es correcto?
```

### Para Código

```markdown
## 💻 Validación de Código

### Funcionalidad
- [ ] El código hace lo que debe?
- [ ] Maneja casos borde?
- [ ] Los tests pasan?
- [ ] No hay loops infinitos?

### Seguridad
- [ ] Sin hardcoded secrets?
- [ ] Input sanitizado?
- [ ] Sin SQL injection?
- [ ] Permisos correctos?

### Best Practices
- [ ] Nombres descriptivos?
- [ ] Funciones pequeñas? (máx 50 líneas)
- [ ] DRY? (Don't Repeat Yourself)
- [ ] Documentado donde necesario?

### Performance
- [ ] Sin queries N+1?
- [ ] Índices usados correctamente?
- [ ] Memoria liberada?
```

### Para Datos

```markdown
## 📊 Validación de Datos

### Formato
- [ ] JSON bien formado?
- [ ] Tipos correctos?
- [ ] Encoding UTF-8?

### Contenido
- [ ] Campos requeridos presentes?
- [ ] Valores en rango válido?
- [ ] Sin valores nulos inesperados?
- [ ] No hay datos sensibles expuestos?

### Relaciones
- [ ] Foreign keys válidos?
- [ ] No hay orphan records?
- [ ] Consistencia entre tablas?
```

---

## 🚦 Sistema de Semáforo

### 🟢 VERDE - Aprobado
```
Estado: LISTO PARA USAR
Significado: Cumple todos los estándares
Acción: Publicar / Desplegar
```

### 🟡 AMARILLO - Con Advertencias
```
Estado: APROBADO CON CONDICIONES
Significado: Funcional pero hay mejoras posibles
Acción: Documentar advertencias y proceder
```

### 🔴 ROJO - Rechazado
```
Estado: NO APROBADO
Significado: Tiene problemas que impiden uso
Acción: Corregir antes de proceder
```

---

## 📝 Templates de Reporte

### Reporte de Validación de Texto
```
📝 REPORTE DE VALIDACIÓN DE CONTENIDO
=====================================
Fecha: [YYYY-MM-DD]
Validador: [Nombre/Rita]
Tipo: [Artículo/Post/Email/Notificación]

ESTADO: 🟢 APROBADO / 🟡 ADVERTENCIAS / 🔴 RECHAZADO

CLARIDAD: 🟢 / 🟡 / 🔴
- Puntuación: [OK/Issues]
- Estructura: [OK/Issues]
- Observaciones: [...]

PRECISIÓN: 🟢 / 🟡 / 🔴
- Datos verificables: [OK/Issues]
- Afirmaciones: [OK/Issues]
- Observaciones: [...]

TONO: 🟢 / 🟡 / 🔴
- Apropiado: [OK/Issues]
- Consistente: [OK/Issues]
- Observaciones: [...]

COMENTARIOS:
[Comentarios adicionales]

RECOMENDACIONES:
[Si hay mejoras sugeridas]

FIRMA: ________________
FECHA: ________________
```

### Reporte de Validación de Código
```
💻 REPORTE DE VALIDACIÓN DE CÓDIGO
===================================
Fecha: [YYYY-MM-DD]
Validador: [Nombre/Rita]
Archivo: [path/to/file]

ESTADO: 🟢 APROBADO / 🟡 ADVERTENCIAS / 🔴 RECHAZADO

SEGURIDAD: 🟢 / 🟡 / 🔴
- Secrets: [OK/ISSUE]
- Injections: [OK/ISSUE]
- Permisos: [OK/ISSUE]

BEST PRACTICES: 🟢 / 🟡 / 🔴
- Nombres: [OK/ISSUE]
- Estructura: [OK/ISSUE]
- Documentación: [OK/ISSUE]

FUNCIONALIDAD: 🟢 / 🟡 / 🔴
- Tests: [OK/ISSUE]
- Casos borde: [OK/ISSUE]

ISSUES CRÍTICOS:
1. [Descripción] - Línea [N]
2. [Descripción] - Línea [N]

SUGERENCIAS:
1. [Sugerencia]
2. [Sugerencia]

FIRMA: ________________
FECHA: ________________
```

---

## 🔧 Guía de Corrección Rápida

### Errores comunes y soluciones

| Error | Solución rápida |
|-------|-----------------|
| Tono muy formal | Reescribir con "tú" |
| Muy largo | Cortar a la mitad, dejar lo esencial |
| Confuso | Agregar举例 o explicar concepto |
| Jerga técnica | Reemplazar con explicación simple |
| Sin CTA claro | Añadir una acción específica al final |

### Para código

| Error | Solución rápida |
|-------|-----------------|
| Variable mal nombrada | `x` → `user_id` |
| Función larga | Separar en funciones más pequeñas |
| Sin manejo de errores | Añadir try/catch |
| SQL vulnerable | Usar prepared statements |

---

## 📊 Métricas de Calidad

### Para Contenido
| Métrica | Meta | Cómo medir |
|---------|------|------------|
| Legibilidad | >60 (Flesch) | Hemingway app |
| Tiempo de lectura | <3 min | ~200 palabras/min |
| CTR esperado | >3% | Benchmark histórico |
| Engagement | >5% | Interacciones/views |

### Para Código
| Métrica | Meta | Cómo medir |
|---------|------|------------|
| Cobertura tests | >80% | Coverage tools |
| Complejidad ciclomática | <10 | SonarQube |
| Líneas por función | <50 | Linting |
| Bugs conocidos | 0 críticos | Bug tracker |

---

## 🎯 Casos de Decisión

### Caso 1: Contenido casi perfecto pero un typo
```
Decisión: 🟡 AMARILLO
Razón: No bloqueante pero debe corregirse
Acción: Corregir typo, luego aprobar
```

### Caso 2: Código funcional pero sin tests
```
Decisión: 🟡 AMARILLO  
Razón: Técnicamente funciona, pero no mantenible
Acción: Aprobar con deuda técnica documentada
```

### Caso 3: Contenido técnicamente correcto pero ofensivo
```
Decisión: 🔴 RECHAZADO
Razón: Daña la reputación de la marca
Acción: Reescribir completamente
```

### Caso 4: Pequeño warning de seguridad en dev
```
Decisión: 🟢 APROBADO
Razón: No afecta producción, warning documentado
Acción: Añadir a backlog para corregir
```

---

## 🔄 Proceso de Validación Rita

```
1. RECIBIR output
   ↓
2. IDENTIFICAR tipo (texto/código/datos)
   ↓
3. APLICAR checklist correspondiente
   ↓
4. EVALUAR severidad de issues
   ↓
5. DECIDIR: 🟢/🟡/🔴
   ↓
6. DOCUMENTAR findings
   ↓
7. SI 🟡/🔴 → Generar feedback
   ↓
8. SI 🟢 → Aprobar yarchivar
```

---

## 📝 Template de Feedback Correctivo

```
🔍 FEEDBACK DE VALIDACIÓN
=========================
Item: [Nombre del contenido/código]
Validador: Rita
Fecha: [Fecha]

Hola,

He revisado tu [contenido/código] y tiene algunos puntos 
que necesitamos corregir antes de aprobar.

🔴 ISSUES QUE DEBES CORREGIR:
--------------------------------
1. [Issue 1 específico]
   - Dónde: [Ubicación exacta]
   - Por qué: [Razón de la corrección]
   - Cómo corregir: [Instrucciones claras]

2. [Issue 2 específico]
   - ...

🟡 SUGERENCIAS (opcionales):
--------------------------------
1. [Sugerencia 1]

Cuando hayas hecho las correcciones, reenvíamelo para 
una nueva validación.

¡Gracias por tu trabajo!

- Rita (Quality Supervisor)
```

---

## ✅ Firma de Aprobación

```markdown
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   VALIDACIÓN COMPLETADA                              ║
║                                                      ║
║   Estado: 🟢 APROBADO                               ║
║   Nivel de confianza: 95%                            ║
║   Fecha: [YYYY-MM-DD]                               ║
║   Validador: Rita v1.0                              ║
║                                                      ║
║   _______________________________________________    ║
║   [Firma]                                           ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
```

---

## 🎓 Tips para Validadores

1. **Sé sistemático** - Sigue el checklist, no te saltes pasos
2. **Sé específico** - "Hay un error" no ayuda, "Línea 42: typo" sí
3. **Sé constructivo** - El objetivo es mejorar, no humillar
4. **Prioriza** - Críticos primero, detalles después
5. **Documenta** - Guarda evidencia de decisiones

---

*Skill creado para el sistema Oficina v2.0*
