from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Mascota(Base):
    __tablename__ = "mascotas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    especie = Column(String(50), nullable=False)
    raza = Column(String(100), nullable=True)
    fecha_nacimiento = Column(DateTime, nullable=True)
    foto_url = Column(String(500), nullable=True)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    emociones = relationship("Emocion", back_populates="mascota", cascade="all, delete-orphan")
