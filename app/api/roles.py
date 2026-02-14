
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.db import models
from app.core import security
from app.crud import roles as crud_roles
from app.db.session import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/roles/", response_model=schemas.Role, dependencies=[Depends(security.get_current_admin_user)])
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    return crud_roles.create_role(db=db, role=role)

@router.get("/roles/", response_model=list[schemas.Role], dependencies=[Depends(security.get_current_admin_user)])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_roles.get_roles(db, skip=skip, limit=limit)

@router.get("/roles/{role_id}", response_model=schemas.Role, dependencies=[Depends(security.get_current_admin_user)])
def read_role(role_id: str, db: Session = Depends(get_db)):
    db_role = crud_roles.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role
