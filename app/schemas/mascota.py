from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class MascotaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    especie: str = Field(..., min_length=1, max_length=50)
    raza: Optional[str] = Field(None, max_length=100)
    fecha_nacimiento: Optional[datetime] = None
    foto_url: Optional[str] = Field(None, max_length=500)
    notas: Optional[str] = None

class MascotaCreate(MascotaBase):
    pass

class MascotaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    especie: Optional[str] = Field(None, min_length=1, max_length=50)
    raza: Optional[str] = Field(None, max_length=100)
    fecha_nacimiento: Optional[datetime] = None
    foto_url: Optional[str] = Field(None, max_length=500)
    notas: Optional[str] = None

class EmocionSummary(BaseModel):
    id: int
    tipo: str
    intensidad: int
    fecha_hora: datetime

    class Config:
        from_attributes = True

class MascotaResponse(MascotaBase):
    id: int
    created_at: datetime
    updated_at: datetime
    emociones: List[EmocionSummary] = []

    class Config:
        from_attributes = True

class MascotaListResponse(BaseModel):
    id: int
    nombre: str
    especie: str
    raza: Optional[str]
    created_at: datetime
    total_emociones: int = 0

    class Config:
        from_attributes = True
