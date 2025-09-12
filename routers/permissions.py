
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

@router.post("/permissions/", response_model=schemas.Permission, dependencies=[Depends(security.get_current_admin_user)])
def create_permission(permission: schemas.PermissionCreate, db: Session = Depends(get_db)):
    return crud.create_permission(db=db, permission=permission)

@router.get("/permissions/", response_model=list[schemas.Permission], dependencies=[Depends(security.get_current_admin_user)])
def read_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    permissions = crud.get_permissions(db, skip=skip, limit=limit)
    return permissions

@router.get("/permissions/{permission_id}", response_model=schemas.Permission, dependencies=[Depends(security.get_current_admin_user)])
def read_permission(permission_id: int, db: Session = Depends(get_db)):
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return db_permission
