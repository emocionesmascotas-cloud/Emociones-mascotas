# 🐾 Emociones Mascotas

Una aplicación web completa para registrar y gestionar las emociones de tus mascotas. Desarrollada con FastAPI, SQLAlchemy y un frontend moderno en HTML/CSS/JavaScript.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Características

- **🐶 Gestión de Mascotas**: CRUD completo (Crear, Leer, Actualizar, Eliminar)
- **💭 Registro de Emociones**: 10 tipos de emociones con intensidad (1-5)
- **📊 Estadísticas Visuales**: Gráficos interactivos con Chart.js
- **🔍 Búsqueda y Filtros**: Encuentra rápidamente lo que necesitas
- **📱 Diseño Responsivo**: Funciona en desktop y móviles
- **🎨 UI Moderna**: Interfaz intuitiva con animaciones suaves

## 📋 Tipos de Emociones

| Emoción | Emoji | Descripción |
|---------|-------|-------------|
| Feliz | 😊 | Mascota contenta y alegre |
| Triste | 😢 | Mascota melancólica |
| Ansioso | 😰 | Mascota preocupada |
| Tranquilo | 😌 | Mascota calmada |
| Juguetón | 🎾 | Mascota jugando |
| Asustado | 😨 | Mascota con miedo |
| Enfermizo | 🤒 | Mascota sintiéndose mal |
| Cansado | 😴 | Mascota fatigada |
| Excitado | 🤩 | Mascota muy emocionada |
| Confundido | 😕 | Mascota desorientada |

## 🚀 Inicio Rápido

### Requisitos

- Python 3.9+
- pip

### Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd emociones-mascotas

# Crear entorno virtual (opcional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar la Aplicación

```bash
# Opción 1: Directamente con Python
python main.py

# Opción 2: Con uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Acceso

Abre tu navegador en: **http://localhost:8000**

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Estructura del Proyecto

```
emociones-mascotas/
├── app/
│   ├── api/              # Rutas de la API
│   │   ├── mascotas.py
│   │   └── emociones.py
│   ├── core/             # Configuración core
│   │   ├── config.py
│   │   └── database.py
│   ├── models/           # Modelos SQLAlchemy
│   │   ├── mascota.py
│   │   └── emocion.py
│   ├── schemas/          # Schemas Pydantic
│   │   ├── mascota.py
│   │   └── emocion.py
│   └── services/        # Lógica de negocio
│       ├── mascota_service.py
│       └── emocion_service.py
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
├── templates/
│   └── index.html
├── data/                 # Base de datos SQLite
├── main.py              # Punto de entrada
├── requirements.txt
└── README.md
```

## 🔌 API Endpoints

### Mascotas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/mascotas` | Listar todas las mascotas |
| GET | `/api/v1/mascotas/{id}` | Obtener mascota por ID |
| POST | `/api/v1/mascotas` | Crear nueva mascota |
| PUT | `/api/v1/mascotas/{id}` | Actualizar mascota |
| DELETE | `/api/v1/mascotas/{id}` | Eliminar mascota |

### Emociones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/emociones` | Listar emociones (con filtros) |
| GET | `/api/v1/emociones/disponibles` | Listar tipos de emociones |
| GET | `/api/v1/emociones/stats` | Estadísticas globales |
| GET | `/api/v1/emociones/{id}` | Obtener emoción por ID |
| POST | `/api/v1/emociones` | Registrar nueva emoción |
| PUT | `/api/v1/emociones/{id}` | Actualizar emoción |
| DELETE | `/api/v1/emociones/{id}` | Eliminar emoción |

## 💾 Base de Datos

La aplicación usa SQLite por defecto. El archivo de base de datos se crea automáticamente en `data/emociones_mascotas.db`.

### Modelos

**Mascota**
- `id`: Identificador único
- `nombre`: Nombre de la mascota
- `especie`: Tipo de mascota (perro, gato, etc.)
- `raza`: Raza específica
- `fecha_nacimiento`: Fecha de nacimiento
- `notas`: Notas adicionales

**Emocion**
- `id`: Identificador único
- `mascota_id`: Referencia a la mascota
- `tipo`: Tipo de emoción
- `intensidad`: Nivel 1-5
- `descripcion`: Descripción detallada
- `contexto`: Situación o contexto
- `fecha_hora`: Timestamp del registro

## 🎯 Uso

1. **Registrar Mascota**: Ve a la pestaña "Mascotas" y haz clic en "Nueva Mascota"
2. **Registrar Emoción**: Ve a la pestaña "Emociones", selecciona tu mascota y la emoción
3. **Ver Estadísticas**: Explora gráficos y análisis en la pestaña "Estadísticas"

## 🛠️ Desarrollo

```bash
# Ejecutar en modo desarrollo
uvicorn main:app --reload

# Los cambios se recargan automáticamente
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

Hecho con ❤️ para los amantes de las mascotas 🐾
