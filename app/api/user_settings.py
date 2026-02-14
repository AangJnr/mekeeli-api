
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas
from app.db import models
from app.core import security
from app.crud import settings as crud_settings
from app.db.session import get_db

router = APIRouter()

def _can_manage_settings(current_user: models.User, user_id: str) -> bool:
    if str(current_user.id) == str(user_id):
        return True
    return any(role.name == "admin" for role in current_user.roles)


@router.post("/users/{user_id}/settings/", response_model=schemas.UserSetting)
def create_user_setting(
    user_id: str,
    setting: schemas.UserSettingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    if not _can_manage_settings(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update settings for this user.",
        )
    return crud_settings.create_user_setting(db=db, setting=setting, user_id=user_id)


@router.get("/users/{user_id}/settings/", response_model=list[schemas.UserSetting])
def read_user_settings(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    if not _can_manage_settings(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to read settings for this user.",
        )
    return crud_settings.get_user_settings(db, user_id=user_id, skip=skip, limit=limit)
