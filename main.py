from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.core.config import settings
from app.core.database import engine, Base
from app.api import api_router

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

# Templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
