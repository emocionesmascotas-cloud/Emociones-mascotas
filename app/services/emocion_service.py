from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.emocion import Emocion, EMOCIONES_DISPONIBLES
from app.models.mascota import Mascota
from app.schemas.emocion import EmocionCreate, EmocionUpdate, EmocionStats

class EmocionService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Emocion]:
        return db.query(Emocion).order_by(Emocion.fecha_hora.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, emocion_id: int) -> Optional[Emocion]:
        return db.query(Emocion).filter(Emocion.id == emocion_id).first()

    @staticmethod
    def get_by_mascota(db: Session, mascota_id: int, skip: int = 0, limit: int = 100) -> List[Emocion]:
        return db.query(Emocion).filter(
            Emocion.mascota_id == mascota_id
        ).order_by(Emocion.fecha_hora.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, emocion: EmocionCreate) -> Optional[Emocion]:
        # Verificar que la mascota existe
        mascota = db.query(Mascota).filter(Mascota.id == emocion.mascota_id).first()
        if not mascota:
            return None
        
        db_emocion = Emocion(**emocion.model_dump())
        db.add(db_emocion)
        db.commit()
        db.refresh(db_emocion)
        return db_emocion

    @staticmethod
    def update(db: Session, emocion_id: int, emocion: EmocionUpdate) -> Optional[Emocion]:
        db_emocion = db.query(Emocion).filter(Emocion.id == emocion_id).first()
        if db_emocion:
            for key, value in emocion.model_dump(exclude_unset=True).items():
                setattr(db_emocion, key, value)
            db.commit()
            db.refresh(db_emocion)
        return db_emocion

    @staticmethod
    def delete(db: Session, emocion_id: int) -> bool:
        db_emocion = db.query(Emocion).filter(Emocion.id == emocion_id).first()
        if db_emocion:
            db.delete(db_emocion)
            db.commit()
            return True
        return False

    @staticmethod
    def get_stats_by_mascota(db: Session, mascota_id: int) -> List[EmocionStats]:
        results = db.query(
            Emocion.tipo,
            func.count(Emocion.id).label('count'),
            func.avg(Emocion.intensidad).label('avg_intensidad')
        ).filter(Emocion.mascota_id == mascota_id).group_by(Emocion.tipo).all()
        
        total = sum(r.count for r in results)
        stats = []
        for r in results:
            stats.append(EmocionStats(
                tipo=r.tipo,
                count=r.count,
                avg_intensidad=round(r.avg_intensidad, 2),
                percentage=round((r.count / total * 100) if total > 0 else 0, 1)
            ))
        return stats

    @staticmethod
    def get_global_stats(db: Session) -> dict:
        results = db.query(
            Emocion.tipo,
            func.count(Emocion.id).label('count'),
            func.avg(Emocion.intensidad).label('avg_intensidad')
        ).group_by(Emocion.tipo).all()
        
        total = sum(r.count for r in results)
        stats = []
        for r in results:
            stats.append(EmocionStats(
                tipo=r.tipo,
                count=r.count,
                avg_intensidad=round(r.avg_intensidad, 2),
                percentage=round((r.count / total * 100) if total > 0 else 0, 1)
            ))
        return {"stats": stats, "total": total}

    @staticmethod
    def get_disponibles() -> List[str]:
        return EMOCIONES_DISPONIBLES
