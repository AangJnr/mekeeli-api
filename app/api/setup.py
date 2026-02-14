
from datetime import timedelta
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import models
from app import schemas
from app.core import security
from app.db.session import get_db
from app.crud import users as crud_users, roles as crud_roles, settings as crud_settings, organizations as crud_orgs
from app.enums import UserType

router = APIRouter(
    prefix="/setup",
    tags=["Setup"],
)


def _is_setup_completed(db: Session) -> bool:
    is_first_run_setting = crud_settings.get_app_setting(db, key="isFirstRun")
    if is_first_run_setting is not None:
        return not bool(is_first_run_setting.isFirstRun)
    return db.query(models.User).count() > 0


def _mark_setup_completed(db: Session):
    is_first_run_setting = crud_settings.get_app_setting(db, key="isFirstRun")
    if is_first_run_setting:
        is_first_run_setting.isFirstRun = False
        is_first_run_setting.value = "False"
        db.commit()
        return
    crud_settings.create_app_setting(
        db,
        schemas.AppSettingCreate(key="isFirstRun", value="False", isFirstRun=False),
    )


def _to_local_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "", value.strip().lower().replace(" ", "_"))


def _next_available_username(db: Session, base_username: str) -> str:
    candidate = base_username
    suffix = 1
    while crud_users.get_user_by_username(db, username=candidate):
        candidate = f"{base_username}{suffix}"
        suffix += 1
    return candidate


def _next_available_local_email(db: Session, base_local_part: str) -> str:
    candidate_local = base_local_part
    suffix = 1
    while crud_users.get_user_by_email(db, email=f"{candidate_local}@local.mekeeli"):
        candidate_local = f"{base_local_part}{suffix}"
        suffix += 1
    return f"{candidate_local}@local.mekeeli"


def _resolve_bootstrap_identity(db: Session, raw_identifier: str) -> tuple[str, str]:
    identifier = raw_identifier.strip()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is required.",
        )

    if "@" in identifier:
        email = identifier.lower()
        if crud_users.get_user_by_email(db, email=email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        base_username = _to_local_part(email.split("@", 1)[0])
        if not base_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email local part must contain alphanumeric characters.",
            )
        username = _next_available_username(db, base_username)
        return username, email

    if crud_users.get_user_by_username(db, username=identifier):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )

    email_local_part = _to_local_part(identifier)
    if not email_local_part:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must contain alphanumeric characters.",
        )
    email = _next_available_local_email(db, email_local_part)
    return identifier, email


@router.get("/status", response_model=schemas.SetupStatus)
def get_setup_status(db: Session = Depends(get_db)):
    setup_completed = _is_setup_completed(db)
    return schemas.SetupStatus(
        setup_completed=setup_completed,
        setup_required=not setup_completed,
    )


@router.post("/bootstrap", response_model=schemas.SetupBootstrapResponse)
def bootstrap_initial_admin(
    payload: schemas.SetupBootstrapRequest,
    db: Session = Depends(get_db),
):
    if _is_setup_completed(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Application setup has already been completed.",
        )

    username, email = _resolve_bootstrap_identity(db, payload.username)

    db_org = crud_orgs.create_organization(
        db,
        org=schemas.OrganizationCreate(name=f"{username}'s Workspace"),
    )
    db_user = crud_users.create_user(
        db=db,
        user=schemas.UserCreate(
            username=username,
            email=email,
            password=payload.password,
            user_type=UserType.INDIE,
        ),
        org_id=db_org.id,
    )

    admin_role = crud_roles.get_role_by_name(db, name="admin")
    if not admin_role:
        admin_role = crud_roles.create_role(db, schemas.RoleCreate(name="admin"))

    if admin_role not in db_user.roles:
        db_user.roles.append(admin_role)
        db.commit()
        db.refresh(db_user)

    _mark_setup_completed(db)

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires,
    )
    return schemas.SetupBootstrapResponse(
        access_token=access_token,
        token_type="bearer",
        user=db_user,
    )


@router.post("/initial-admin", response_model=schemas.User)
def create_initial_admin(setup_data: schemas.InitialAdminCreate, db: Session = Depends(get_db)):
    """
    Creates the initial administrator and their organization (default for INDIE).
    This endpoint is only available if the application has not been set up yet.
    """
    # 1. Verify that this is the first run
    if _is_setup_completed(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Application setup has already been completed.",
        )
        
    user_data = setup_data.admin_user

    # 2. Check if a user with this email already exists
    if crud_users.get_user_by_email(db, email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
        
    # 3. Handle Organization Creation based on User Type
    org_to_create = None
    
    if user_data.user_type == UserType.ORGANIZATION:
        if not setup_data.organization:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization details are required for ORGANIZATION user type.",
            )
        org_to_create = setup_data.organization
    
    elif user_data.user_type == UserType.INDIE:
        # Create a default organization for the INDIE user
        org_to_create = schemas.OrganizationCreate(name=f"{user_data.username}'s Workspace")

    # Create the organization and get the db object back
    db_org = crud_orgs.create_organization(db, org=org_to_create)
        
    # 4. Create the new user and assign the new org_id
    db_user = crud_users.create_user(db=db, user=user_data, org_id=db_org.id)
    
    # 5. Find or create the 'admin' role and assign it
    admin_role = crud_roles.get_role_by_name(db, name="admin")
    if not admin_role:
        admin_role = crud_roles.create_role(db, schemas.RoleCreate(name="admin"))
    
    db_user.roles.append(admin_role)
    db.commit()
    db.refresh(db_user)
    
    # 6. Mark the setup as complete
    _mark_setup_completed(db)
    
    return db_user
