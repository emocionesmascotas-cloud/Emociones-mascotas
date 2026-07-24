from fastapi import APIRouter
from app.api.mascotas import router as mascotas_router
from app.api.emociones import router as emociones_router

api_router = APIRouter()
api_router.include_router(mascotas_router)
api_router.include_router(emociones_router)
