from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, database, models, auth

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_admin_user)
):
    return db.query(models.User).all()

@router.post("/", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_admin_user)
):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.put("/me/preferences", response_model=schemas.User)
def update_my_preferences(
    prefs: schemas.UserPreferencesUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    if prefs.tooltips_enabled is not None:
        current_user.tooltips_enabled = prefs.tooltips_enabled
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserBase, # Use UserBase for updates to exclude password for now, or create UserUpdate
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_admin_user)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simple update
    db_user.role = user_update.role
    db_user.is_active = user_update.is_active
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_admin_user)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return db_user
