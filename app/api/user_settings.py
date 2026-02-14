
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.db import models
from app.core import security
from app.crud import settings as crud_settings
from app.db.session import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/{user_id}/settings/", response_model=schemas.UserSetting, dependencies=[Depends(security.get_current_active_user)])
def create_user_setting(user_id: str, setting: schemas.UserSettingCreate, db: Session = Depends(get_db)):
    return crud_settings.create_user_setting(db=db, setting=setting, user_id=user_id)

@router.get("/users/{user_id}/settings/", response_model=list[schemas.UserSetting], dependencies=[Depends(security.get_current_active_user)])
def read_user_settings(user_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_settings.get_user_settings(db, user_id=user_id, skip=skip, limit=limit)
