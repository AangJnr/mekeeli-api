
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud, models, security
from database import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/roles/", response_model=schemas.Role, dependencies=[Depends(security.get_current_active_user)])
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    return crud.create_role(db=db, role=role)

@router.get("/roles/", response_model=list[schemas.Role], dependencies=[Depends(security.get_current_active_user)])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles

@router.get("/roles/{role_id}", response_model=schemas.Role, dependencies=[Depends(security.get_current_active_user)])
def read_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role
