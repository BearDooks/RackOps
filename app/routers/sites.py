from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from .. import crud, schemas, database, models, auth
from typing import List

router = APIRouter(
    prefix="/api/sites",
    tags=["sites"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Site)
def create_site(site: schemas.SiteCreate = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    return crud.create_site(db=db, site=site, username=current_user.username)

@router.get("/", response_model=List[schemas.Site])
def read_sites(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.get_sites(db=db)

@router.get("/{site_id}", response_model=schemas.Site)
def read_site(site_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    db_site = crud.get_site(db, site_id=site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return db_site

@router.put("/{site_id}", response_model=schemas.Site)
def update_site(site_id: int, site: schemas.SiteCreate = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    return crud.update_site(db=db, site_id=site_id, site=site, username=current_user.username)

@router.delete("/{site_id}", response_model=schemas.Site)
def delete_site(site_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_operator_user)):
    db_site = crud.get_site(db, site_id=site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    crud.delete_site(db=db, site_id=site_id, username=current_user.username)
    return db_site

