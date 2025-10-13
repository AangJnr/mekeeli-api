
from sqlalchemy.orm import Session
from langchain_ollama.chat_models import ChatOllama
import models

def get_base_llm(db: Session, user: models.User) -> ChatOllama:
    """
    Initializes a base ChatOllama model based on user or app settings.
    """
    # Determine the LLM model from user settings, with an app-level fallback
    user_model_setting = db.query(models.UserSetting).filter_by(user_id=user.id, key="default_ollama_model").first()
    
    llm_model_name = "gemma3:4b" # System-wide default
    if user_model_setting:
        llm_model_name = user_model_setting.value
    else:
        app_model_setting = db.query(models.AppSetting).filter_by(key="default_ollama_model").first()
        if app_model_setting:
            llm_model_name = app_model_setting.value

    # This is where you can add other ChatOllama parameters
    return ChatOllama(
        model=llm_model_name,
        temperature=0.8,
    )
