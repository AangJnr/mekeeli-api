
from sqlalchemy.orm import Session
import models, schemas

def get_user_setting(db: Session, setting_id: int):
    return db.query(models.UserSetting).filter(models.UserSetting.id == setting_id).first()

def get_user_settings(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.UserSetting).filter(models.UserSetting.user_id == user_id).offset(skip).limit(limit).all()

def create_user_setting(db: Session, setting: schemas.UserSettingCreate, user_id: int):
    db_setting = models.UserSetting(**setting.dict(), user_id=user_id)
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def get_app_setting(db: Session, key: str):
    return db.query(models.AppSetting).filter(models.AppSetting.key == key).first()

def get_app_settings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AppSetting).offset(skip).limit(limit).all()

def create_app_setting(db: Session, setting: schemas.AppSettingCreate):
    db_setting = models.AppSetting(**setting.dict())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting
