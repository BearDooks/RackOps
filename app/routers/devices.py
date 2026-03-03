from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from .. import crud, schemas, database, models, auth
from typing import List

router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)

@router.get("/search", response_model=List[schemas.DeviceSearchResponse])
def search_devices(q: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.search_devices(db=db, query=q)

@router.post("/", response_model=schemas.Device)
def create_device(device: schemas.DeviceCreate = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    return crud.create_device(db=db, device=device, username=current_user.username)

@router.put("/{device_id}", response_model=schemas.Device)
def update_device(device_id: int, device: schemas.DeviceUpdate = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    db_device = crud.update_device(db=db, device_id=device_id, device_update=device, username=current_user.username)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device

@router.delete("/{device_id}", response_model=schemas.Device)
def delete_device(device_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    crud.delete_device(db=db, device_id=device_id, username=current_user.username)
    return db_device


