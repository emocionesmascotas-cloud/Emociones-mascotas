from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Emocion(Base):
    __tablename__ = "emociones"

    id = Column(Integer, primary_key=True, index=True)
    mascota_id = Column(Integer, ForeignKey("mascotas.id"), nullable=False)
    tipo = Column(String(50), nullable=False)
    intensidad = Column(Integer, nullable=False)  # 1-5
    descripcion = Column(Text, nullable=True)
    contexto = Column(String(200), nullable=True)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    mascota = relationship("Mascota", back_populates="emociones")

# Tipos de emociones predefinidas
EMOCIONES_DISPONIBLES = [
    "feliz",
    "triste",
    "ansioso",
    "tranquilo",
    "juguetón",
    "asustado",
    "enfermizo",
    "cansado",
    "excitado",
    "confundido"
]
