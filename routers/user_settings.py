
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

@router.post("/users/{user_id}/settings/", response_model=schemas.UserSetting, dependencies=[Depends(security.get_current_active_user)])
def create_user_setting(user_id: int, setting: schemas.UserSettingCreate, db: Session = Depends(get_db)):
    return crud.create_user_setting(db=db, setting=setting, user_id=user_id)

@router.get("/users/{user_id}/settings/", response_model=list[schemas.UserSetting], dependencies=[Depends(security.get_current_active_user)])
def read_user_settings(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    settings = crud.get_user_settings(db, user_id=user_id, skip=skip, limit=limit)
    return settings
