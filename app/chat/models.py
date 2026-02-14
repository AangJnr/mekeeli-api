
from sqlalchemy.orm import Session
from langchain_ollama.chat_models import ChatOllama
from app.db import models
from app.crud import settings as crud_settings


DEFAULT_TEXT_MODEL = "qwen3-vl:4b"
DEFAULT_VISION_MODEL = "qwen3-vl:4b"
DEFAULT_EMBED_MODEL = "embeddinggemma"


def get_text_model_name(db: Session, user: models.User) -> str:
    """Resolve text model with user-level override first, then app settings."""
    user_model_setting = db.query(models.UserSetting).filter_by(
        user_id=user.id, key="default_ollama_model"
    ).first()
    if user_model_setting and user_model_setting.value:
        return user_model_setting.value

    settings = crud_settings.get_settings(db)
    if settings.default_text_model:
        return settings.default_text_model

    app_model_setting = db.query(models.AppSetting).filter_by(
        key="default_ollama_model"
    ).first()
    if app_model_setting and app_model_setting.value:
        return app_model_setting.value

    return DEFAULT_TEXT_MODEL


def get_vision_model_name(db: Session) -> str:
    settings = crud_settings.get_settings(db)
    if settings.default_vision_model:
        return settings.default_vision_model
    return DEFAULT_VISION_MODEL


def get_embed_model_name(db: Session) -> str:
    settings = crud_settings.get_settings(db)
    if settings.default_embed_model:
        return settings.default_embed_model
    return DEFAULT_EMBED_MODEL


def get_base_llm(db: Session, user: models.User) -> ChatOllama:
    """
    Initializes a base ChatOllama model based on user or app settings.
    """
    llm_model_name = get_text_model_name(db, user)
    return ChatOllama(
        model=llm_model_name,
        temperature=0.8,
    )
