from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.db import models
from app.core import security
from app.db.session import get_db
from app.crud import users as crud_users
from app.crud import roles as crud_roles
from app.enums import UserType

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(security.get_current_admin_user)],
)


def _ensure_org_admin(current_user: models.User) -> str:
    if current_user.user_type != UserType.ORGANIZATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators in an organization can manage users.",
        )
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Administrator is not associated with an organization.",
        )
    return current_user.org_id


def _get_org_user(db: Session, user_id: str, org_id: str) -> models.User:
    user = crud_users.get_user(db, user_id=user_id)
    if not user or user.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users/", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_admin_user),
):
    org_id = _ensure_org_admin(current_user)

    if crud_users.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    if crud_users.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    return crud_users.create_user(db=db, user=user, org_id=org_id)


@router.get("/users/", response_model=list[schemas.User])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_admin_user),
):
    org_id = _ensure_org_admin(current_user)
    return (
        db.query(models.User)
        .filter(models.User.org_id == org_id)
        .order_by(models.User.username.asc())
        .all()
    )


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_admin_user),
):
    org_id = _ensure_org_admin(current_user)
    return _get_org_user(db, user_id=user_id, org_id=org_id)


@router.post("/users/{user_id}/roles/{role_id}", response_model=schemas.User)
def assign_role(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_admin_user),
):
    org_id = _ensure_org_admin(current_user)
    user = _get_org_user(db, user_id=user_id, org_id=org_id)
    role = crud_roles.get_role(db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)
    return user


@router.delete("/users/{user_id}/roles/{role_id}", response_model=schemas.User)
def remove_role(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_admin_user),
):
    org_id = _ensure_org_admin(current_user)
    user = _get_org_user(db, user_id=user_id, org_id=org_id)
    role = crud_roles.get_role(db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
        db.refresh(user)
    return user


@router.post("/users/{user_id}/activate", response_model=schemas.User)
def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_admin_user),
):
    org_id = _ensure_org_admin(current_user)
    user = _get_org_user(db, user_id=user_id, org_id=org_id)
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/deactivate", response_model=schemas.User)
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_admin_user),
):
    org_id = _ensure_org_admin(current_user)
    user = _get_org_user(db, user_id=user_id, org_id=org_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
