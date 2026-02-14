from sqlalchemy.orm import Session

from app.crud import settings as crud_settings


def is_offline_mode(db: Session) -> bool:
    settings = crud_settings.get_settings(db)
    return bool(settings.offline_mode)
