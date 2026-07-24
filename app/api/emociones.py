from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.emocion import EmocionCreate, EmocionUpdate, EmocionResponse, EmocionStats
from app.services.emocion_service import EmocionService

router = APIRouter(prefix="/emociones", tags=["Emociones"])

@router.get("/", response_model=List[EmocionResponse])
def get_emociones(
    mascota_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    if mascota_id:
        return EmocionService.get_by_mascota(db, mascota_id, skip, limit)
    return EmocionService.get_all(db, skip, limit)

@router.get("/disponibles", response_model=List[str])
def get_emociones_disponibles():
    return EmocionService.get_disponibles()

@router.get("/stats", response_model=dict)
def get_stats(mascota_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    if mascota_id:
        return {"stats": EmocionService.get_stats_by_mascota(db, mascota_id)}
    return EmocionService.get_global_stats(db)

@router.get("/{emocion_id}", response_model=EmocionResponse)
def get_emocion(emocion_id: int, db: Session = Depends(get_db)):
    emocion = EmocionService.get_by_id(db, emocion_id)
    if not emocion:
        raise HTTPException(status_code=404, detail="Emocion no encontrada")
    return emocion

@router.post("/", response_model=EmocionResponse, status_code=status.HTTP_201_CREATED)
def create_emocion(emocion: EmocionCreate, db: Session = Depends(get_db)):
    db_emocion = EmocionService.create(db, emocion)
    if not db_emocion:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return db_emocion

@router.put("/{emocion_id}", response_model=EmocionResponse)
def update_emocion(emocion_id: int, emocion: EmocionUpdate, db: Session = Depends(get_db)):
    db_emocion = EmocionService.update(db, emocion_id, emocion)
    if not db_emocion:
        raise HTTPException(status_code=404, detail="Emocion no encontrada")
    return db_emocion

@router.delete("/{emocion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emocion(emocion_id: int, db: Session = Depends(get_db)):
    if not EmocionService.delete(db, emocion_id):
        raise HTTPException(status_code=404, detail="Emocion no encontrada")
    return None
