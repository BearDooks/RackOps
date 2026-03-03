from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, database, auth, models
from typing import List

router = APIRouter(
    prefix="/api/audit_logs",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.AuditLog])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_admin_user)):
    return crud.get_audit_logs(db, skip=skip, limit=limit)
