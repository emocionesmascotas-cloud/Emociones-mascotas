# 📝 Skill: Publicar en Blogger

> **Skill:** Publicación de artículos en Blogger  
> **Plataforma:** Blogger (blogs.google.com)  
> **Tipo:** API REST  
> **Última actualización:** 2024-01-15

---

## 🎯 Objetivo

Este skill guía la publicación de contenido en Blogger usando la API REST de Google.

---

## 📋 Prerrequisitos

### Configuración en Blogger
1. Crear un blog en [Blogger](https://www.blogger.com)
2. Obtener el Blog ID (está en la URL: `blogspot.com/blog_ID`)
3. Crear credenciales OAuth2 en [Google Cloud Console](https://console.cloud.google.com)
4. Obtener Access Token con permisos de `https://www.googleapis.com/auth/blogger`

### Variables de entorno requeridas
```bash
BLOGGER_BLOG_ID=1234567890123456789
BLOGGER_ACCESS_TOKEN=ya29.a0AfH6...
```

---

## 🔌 API de Blogger

### Endpoint
```
POST https://www.googleapis.com/blogger/v3/blogs/{blogId}/posts
```

### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

### Payload
```json
{
  "kind": "blogger#post",
  "blog": {
    "id": "BLOG_ID"
  },
  "title": "Título del artículo",
  "content": "<p>Contenido HTML...</p>",
  "labels": ["etiqueta1", "etiqueta2"]
}
```

### Respuesta exitosa
```json
{
  "kind": "blogger#post",
  "id": "post_id",
  "title": "Título del artículo",
  "url": "https://tu-blog.blogspot.com/2024/01/titulo.html",
  "selfLink": "https://www.googleapis.com/blogger/v3/blogs/.../posts/post_id"
}
```

---

## 📝 Estructura del Contenido

### Convertir texto a HTML
```python
def texto_a_html(texto):
    # Párrafos
    parrafos = texto.split('\n\n')
    html = ''.join(f'<p>{p.strip()}</p>' for p in parrafos if p.strip())
    
    # Listas
    html = html.replace('• ', '</p><ul><li>')
    html = html.replace('\n', '</li></ul><p>')
    
    return html
```

### Template de Artículo
```html
<div class="articulo">
  <!-- Contenido principal -->
  <p>...</p>
  
  <!-- Separador -->
  <hr/>
  
  <!-- Footer -->
  <p><i>Este contenido fue creado con Emociones Mascotas 🐾</i></p>
  
  <!-- CTA -->
  <p><a href="https://emocionesmascotas.com">Prueba Emociones Mascotas →</a></p>
</div>
```

---

## 🏷️ Etiquetas Recomendadas

| Categoría | Etiquetas |
|-----------|-----------|
| Perros | perros, emociones-caninas, bienestar-canino |
| Gatos | gatos, emociones-felinas, cuidado-felino |
| General | mascotas, emociones-animales, dueños-responsables |
| Tips | consejos, guia, tutorial |

---

## ⚠️ Límites de Blogger API

| Límite | Valor |
|--------|-------|
| Posts por día | 50 |
| Posts por segundo | 20 |
| Tamaño máximo post | 1 MB |
| Contenido HTML | Sin límite específico |

---

## 🔍 Checklist antes de Publicar

```markdown
□ Contenido verificado y aprobado
□ Título SEO-optimizado (máx 70 caracteres)
□ Etiquetas añadidas (3-5)
□ Imágenes con alt text
□ Links funcionando
□ Footer con marca
□ Preview revisada
```

---

## 🚫 Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| 401 Unauthorized | Token expirado | Refrescar access token |
| 403 Forbidden | Permisos insuficientes | Verificar scopes OAuth |
| 404 Not Found | Blog ID incorrecto | Verificar en URL del blog |
| 429 Too Many Requests | Rate limit | Esperar y reintentar |
| 500 Server Error | Error de Google | Reintentar más tarde |

---

## 📤 Ejemplo de Uso

### Python
```python
import httpx

def publicar_blogger(titulo, contenido, blog_id, access_token):
    api_url = "https://www.googleapis.com/blogger/v3"
    
    payload = {
        "kind": "blogger#post",
        "blog": {"id": blog_id},
        "title": titulo,
        "content": contenido,
        "labels": ["emociones-mascotas", "mascotas"]
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = httpx.post(
        f"{api_url}/blogs/{blog_id}/posts",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["url"]
    else:
        raise Exception(f"Error: {response.text}")
```

---

## 🔄 Flujo Completo

```
1. VERIFICAR contenido aprobado
   ↓
2. OBTENER access token válido
   ↓
3. PREPARAR payload (título + HTML + labels)
   ↓
4. LLAMAR Blogger API
   ↓
5. GUARDAR URL en Supabase
   ↓
6. NOTIFICAR por Telegram
```

---

*Skill creado para el sistema Oficina v2.0 - Agente Carlos*
