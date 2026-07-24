from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Emociones Mascotas"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/emociones_mascotas.db"
    
    class Config:
        case_sensitive = True

settings = Settings()
