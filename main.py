from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
