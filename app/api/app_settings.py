
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas
from app.core import security
from app.crud import settings as crud_settings
from app.db.session import get_db

router = APIRouter()

@router.post("/app/settings/", response_model=schemas.AppSetting, dependencies=[Depends(security.get_current_admin_user)])
def create_app_setting(setting: schemas.AppSettingCreate, db: Session = Depends(get_db)):
    return crud_settings.create_app_setting(db=db, setting=setting)

@router.get("/app/settings/", response_model=list[schemas.AppSetting], dependencies=[Depends(security.get_current_admin_user)])
def read_app_settings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_settings.get_app_settings(db, skip=skip, limit=limit)
