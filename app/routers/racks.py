from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from .. import crud, schemas, database, models, auth
from typing import List

router = APIRouter(
    prefix="/api/racks",
    tags=["racks"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Rack])
def read_racks(site_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.get_racks(db=db, site_id=site_id)

@router.get("/{rack_id}", response_model=schemas.Rack)
def read_rack(rack_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    db_rack = crud.get_rack(db, rack_id=rack_id)
    if db_rack is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    return db_rack

@router.get("/{rack_id}/devices", response_model=List[schemas.Device])
def read_rack_devices(rack_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    db_rack = crud.get_rack(db, rack_id=rack_id)
    if db_rack is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    return db_rack.devices

@router.post("/", response_model=schemas.Rack)
def create_rack(rack: schemas.RackCreate = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    return crud.create_rack(db=db, rack=rack, username=current_user.username)

@router.put("/{rack_id}", response_model=schemas.Rack)
def update_rack(rack_id: int, rack: schemas.RackBase = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    return crud.update_rack(db=db, rack_id=rack_id, rack=rack, username=current_user.username)

@router.delete("/{rack_id}", response_model=schemas.Rack)
def delete_rack(rack_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    db_rack = crud.get_rack(db, rack_id=rack_id)
    if not db_rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    crud.delete_rack(db=db, rack_id=rack_id, username=current_user.username)
    return db_rack

