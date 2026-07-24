from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.mascota import Mascota
from app.models.emocion import Emocion
from app.schemas.mascota import MascotaCreate, MascotaUpdate

class MascotaService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
        mascotas = db.query(Mascota).offset(skip).limit(limit).all()
        result = []
        for m in mascotas:
            total = db.query(func.count(Emocion.id)).filter(Emocion.mascota_id == m.id).scalar()
            result.append({
                "id": m.id,
                "nombre": m.nombre,
                "especie": m.especie,
                "raza": m.raza,
                "created_at": m.created_at,
                "total_emociones": total or 0
            })
        return result

    @staticmethod
    def get_by_id(db: Session, mascota_id: int) -> Optional[Mascota]:
        return db.query(Mascota).filter(Mascota.id == mascota_id).first()

    @staticmethod
    def create(db: Session, mascota: MascotaCreate) -> Mascota:
        db_mascota = Mascota(**mascota.model_dump())
        db.add(db_mascota)
        db.commit()
        db.refresh(db_mascota)
        return db_mascota

    @staticmethod
    def update(db: Session, mascota_id: int, mascota: MascotaUpdate) -> Optional[Mascota]:
        db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
        if db_mascota:
            for key, value in mascota.model_dump(exclude_unset=True).items():
                setattr(db_mascota, key, value)
            db.commit()
            db.refresh(db_mascota)
        return db_mascota

    @staticmethod
    def delete(db: Session, mascota_id: int) -> bool:
        db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
        if db_mascota:
            db.delete(db_mascota)
            db.commit()
            return True
        return False
