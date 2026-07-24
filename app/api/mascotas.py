from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.mascota import MascotaCreate, MascotaUpdate, MascotaResponse, MascotaListResponse
from app.services.mascota_service import MascotaService

router = APIRouter(prefix="/mascotas", tags=["Mascotas"])

@router.get("/", response_model=List[MascotaListResponse])
@router.get("", response_model=List[MascotaListResponse])
def get_mascotas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return MascotaService.get_all(db, skip, limit)

@router.get("/{mascota_id}", response_model=MascotaResponse)
def get_mascota(mascota_id: int, db: Session = Depends(get_db)):
    mascota = MascotaService.get_by_id(db, mascota_id)
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return mascota

@router.post("/", response_model=MascotaResponse, status_code=status.HTTP_201_CREATED)
def create_mascota(mascota: MascotaCreate, db: Session = Depends(get_db)):
    return MascotaService.create(db, mascota)

@router.put("/{mascota_id}", response_model=MascotaResponse)
def update_mascota(mascota_id: int, mascota: MascotaUpdate, db: Session = Depends(get_db)):
    db_mascota = MascotaService.update(db, mascota_id, mascota)
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return db_mascota

@router.delete("/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mascota(mascota_id: int, db: Session = Depends(get_db)):
    if not MascotaService.delete(db, mascota_id):
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return None
