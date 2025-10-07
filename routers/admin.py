
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models, security
from database import get_db
from crud import users as crud_users
from crud import roles as crud_roles
from crud import permission_groups as crud_pg
from crud import settings as crud_settings
from enums import UserType

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(security.get_current_admin_user)],
)

# --- User Management ---
@router.post("/users/", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(security.get_current_admin_user)
):
    """
    Creates a new user. Only available to admins in an ORGANIZATION setup.
    """
    # Verify that the admin is part of an ORGANIZATION
    if current_user.user_type != UserType.ORGANIZATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators in an organization can create new users.",
        )

    db_user = crud_users.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    return crud_users.create_user(db=db, user=user)

# --- Role Management ---
@router.post("/roles/{role_id}/permission_groups/{pg_id}")
def assign_permission_group_to_role(role_id: int, pg_id: int, db: Session = Depends(get_db)):
    role = crud_roles.get_role(db, role_id)
    pg = crud_pg.get_permission_group(db, pg_id)
    if not role or not pg:
        raise HTTPException(status_code=404, detail="Role or Permission Group not found")
    
    if pg not in role.permission_groups:
        role.permission_groups.append(pg)
        db.commit()
    return {"message": "Permission group assigned to role successfully"}

# --- App Settings ---
@router.get("/settings/is_first_run", response_model=bool)
def is_first_run(db: Session = Depends(get_db)):
    setting = crud_settings.get_app_setting(db, key="isFirstRun")
    if setting and not setting.isFirstRun:
        return False
    return True

@router.post("/settings/complete_setup")
def complete_setup(db: Session = Depends(get_db)):
    setting = crud_settings.get_app_setting(db, key="isFirstRun")
    if not setting:
        crud_settings.create_app_setting(db, schemas.AppSettingCreate(key="isFirstRun", value="False", isFirstRun=False))
    else:
        setting.isFirstRun = False
        db.commit()
    return {"message": "Setup complete"}
