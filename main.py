from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.core.database import engine, Base
from app.api import api_router
from integrations.replit_api import router as integrations_router
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear tablas de la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para registrar y gestionar las emociones de tus mascotas",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rutas para archivos estáticos
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Router de integraciones (webhooks, telegram, etc.)
app.include_router(integrations_router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    html_path = BASE_DIR / "templates" / "index.html"
    return FileResponse(html_path)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    html_path = BASE_DIR / "templates" / "index.html"
    return FileResponse(html_path)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.PROJECT_NAME}

@app.on_event("startup")
async def startup_event():
    """Se ejecuta cuando la aplicación inicia."""
    logger.info("🚀 Iniciando Emociones Mascotas API")
    logger.info(f"📚 Documentación: /docs")
    logger.info(f"🔗 Webhook Pipedream: /api/webhook/pipedream")
    logger.info(f"💬 Telegram Bot: /api/webhook/telegram")

@app.on_event("shutdown")
async def shutdown_event():
    """Se ejecuta cuando la aplicación se detiene."""
    logger.info("👋 Deteniendo Emociones Mascotas API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
