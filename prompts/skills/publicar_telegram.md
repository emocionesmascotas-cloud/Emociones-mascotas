# 📱 Skill: Publicar en Telegram

> **Skill:** Envío de contenido a canales de Telegram  
> **Plataforma:** Telegram Bot API  
> **Tipo:** REST API  
> **Última actualización:** 2024-01-15

---

## 🎯 Objetivo

Este skill guía el envío de contenido a canales de Telegram usando Bot API.

---

## 📋 Prerrequisitos

### Configuración de Telegram
1. Crear bot con [@BotFather](https://t.me/BotFather)
2. Obtener el Bot Token
3. Añadir bot como administrador del canal
4. Obtener Channel ID:
   - Para canales públicos: `@nombre_canal`
   - Para canales privados: Usar [@userinfobot](https://t.me/userinfobot)

### Variables de entorno requeridas
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@tu_canal
TELEGRAM_ADMIN_CHAT_ID=123456789  # Tu chat ID para notificaciones
```

---

## 🔌 Telegram Bot API

### Endpoint
```
POST https://api.telegram.org/bot{token}/sendMessage
```

### Payload
```json
{
  "chat_id": "@tu_canal",
  "text": "Mensaje a enviar",
  "parse_mode": "Markdown",
  "disable_web_page_preview": false
}
```

### Respuesta exitosa
```json
{
  "ok": true,
  "result": {
    "message_id": 123,
    "chat": {
      "id": -1001234567890,
      "title": "Nombre del Canal",
      "type": "channel"
    },
    "date": 1700000000,
    "text": "Mensaje..."
  }
}
```

---

## 📝 Formato del Mensaje

### Parse Modes
| Mode | Sintaxis | Uso |
|------|----------|-----|
| Markdown | `*bold*`, `_italic_` | Formato simple |
| HTML | `<b>bold</b>` | Más control |
| None | Texto plano | Sin formato |

### Template de Mensaje
```
📝 *Título del contenido*

[Contenido principal - máximo 4000 caracteres]

🐾 #Hashtag1 #Hashtag2

📢 @TuBlog
```

---

## ⚠️ Límites de Telegram

| Límite | Valor |
|--------|-------|
| Mensaje de texto | 4096 caracteres |
| Mensajes/segundo | 30 |
| Mensajes/segundo (grupo) | 20 |
| Tamaño de archivo | 50 MB |

---

## 🔄 Estrategias para Contenido Largo

### Truncar con预告
```
📝 *Título completo del artículo*

[Primeros 3500 caracteres del contenido]...

... (continúa en el blog 👇)

🔗 Leer artículo completo: [URL]

#Mascotas #EmocionesAnimales
```

### Dividir en partes
```
📝 *Artículo: Cómo entender a tu perro (1/3)*

[Parte 1]

⬇️ Continúa en el siguiente mensaje...
---
📝 *Artículo: Cómo entender a tu perro (2/3)*

[Parte 2]

⬇️ Continúa...
---
📝 *Artículo: Cómo entender a tu perro (3/3)*

[Parte 3 + CTA]

🔗 Leer completo: [URL]

#MascotasFelices
```

---

## 📤 Tipos de Mensaje

### Texto
```python
payload = {
    "chat_id": channel_id,
    "text": "Mensaje",
    "parse_mode": "Markdown"
}
```

### Foto
```python
payload = {
    "chat_id": channel_id,
    "photo": "https://example.com/imagen.jpg",
    "caption": "Descripción de la imagen",
    "parse_mode": "Markdown"
}
```

### Documento
```python
payload = {
    "chat_id": channel_id,
    "document": "https://example.com/archivo.pdf",
    "caption": "Nombre del archivo"
}
```

### Poll
```python
payload = {
    "chat_id": channel_id,
    "question": "¿Qué emoción detectas más en tu perro?",
    "options": ["Felicidad", "Ansiedad", "Tristeza", "Calma"],
    "type": "regular"
}
```

---

## 🔍 Checklist antes de Enviar

```markdown
□ Contenido verificado y aprobado
□ Longitud < 4096 caracteres
□ Parse mode correcto
□ @menciones o links correctos
□ Hashtags al final
□ CTA claro
```

---

## 🚫 Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| 400 Bad Request | Sintaxis inválida | Revisar Markdown/HTML |
| 401 Unauthorized | Token inválido | Verificar bot token |
| 400 Chat not found | ID incorrecto | Añadir bot al canal |
| 400 Bot was kicked | Sin acceso | Re-invitar bot |
| 429 Too Many Requests | Rate limit | Esperar entre envíos |

---

## 📤 Ejemplo de Uso

### Python básico
```python
import httpx

def enviar_telegram(mensaje, channel_id, bot_token):
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": channel_id,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    response = httpx.post(api_url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            return f"https://t.me/{channel_id.lstrip('@')}/{data['result']['message_id']}"
    else:
        raise Exception(f"Error: {response.text}")
```

### Python con reintentos
```python
import time
import httpx

def enviar_telegram_con_reintentos(mensaje, channel_id, bot_token, max_retries=3):
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    for intento in range(max_retries):
        try:
            response = httpx.post(api_url, json={
                "chat_id": channel_id,
                "text": mensaje,
                "parse_mode": "Markdown"
            }, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                if data["ok"]:
                    return data["result"]["message_id"]
            
            if response.status_code == 429:  # Rate limit
                time.sleep(2 ** intento)  # Backoff exponencial
                continue
                
        except httpx.TimeoutException:
            time.sleep(1)
            continue
    
    raise Exception("Max retries exceeded")
```

---

## 🔔 Notificaciones

### Notificar éxito
```markdown
✅ *Publicación exitosa*

📢 *@{nombre_canal}*
🔗 [URL del post]

🐾 Enviado por Carlos Publisher
```

### Notificar error
```markdown
⚠️ *Error en publicación*

❌ *Causa:* [descripción del error]

🐾 Revisar manualmente
```

---

## 🎨 Mejores Prácticas

1. **Horario óptimo:** Publicar entre 9-11 AM o 7-9 PM
2. **Frecuencia:** 1-3 posts por día máximo
3. **Interacción:** Responder comentarios
4. **Consistencia:** Mantener frecuencia regular
5. **Analytics:** Monitorear views y engagement

---

*Skill creado para el sistema Oficina v2.0 - Agente Carlos*
