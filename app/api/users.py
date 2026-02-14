
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db import models
from app import schemas
from app.core import security
from app.db.session import get_db
from app.crud import users as crud_users

router = APIRouter()

@router.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticates a user via username/email and password, returning a JWT access token.
    Note: OAuth2 uses the form field name 'username' for either identifier.
    """
    user = security.authenticate_user(db, identifier=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    # The 'sub' of the token should be the user's unique identifier (email)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.User, tags=["Users"])
async def read_users_me(
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Retrieves the profile of the currently authenticated user.
    """
    return current_user
