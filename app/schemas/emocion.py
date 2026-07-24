from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class EmocionBase(BaseModel):
    tipo: str = Field(..., min_length=1, max_length=50)
    intensidad: int = Field(..., ge=1, le=5)
    descripcion: Optional[str] = None
    contexto: Optional[str] = Field(None, max_length=200)

class EmocionCreate(EmocionBase):
    mascota_id: int = Field(..., gt=0)

class EmocionUpdate(BaseModel):
    tipo: Optional[str] = Field(None, min_length=1, max_length=50)
    intensidad: Optional[int] = Field(None, ge=1, le=5)
    descripcion: Optional[str] = None
    contexto: Optional[str] = Field(None, max_length=200)

class EmocionResponse(EmocionBase):
    id: int
    mascota_id: int
    fecha_hora: datetime
    created_at: datetime
    nombre_mascota: Optional[str] = None

    class Config:
        from_attributes = True

class EmocionStats(BaseModel):
    tipo: str
    count: int
    avg_intensidad: float
    percentage: float
