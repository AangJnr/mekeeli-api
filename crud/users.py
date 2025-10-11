
from sqlalchemy.orm import Session
import models, schemas, security
import uuid

def get_user(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate, org_id: str = None):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password,
        user_type=user.user_type,
        org_id=org_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
