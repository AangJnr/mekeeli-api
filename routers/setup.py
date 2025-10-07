
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from crud import users as crud_users, roles as crud_roles, settings as crud_settings

router = APIRouter(
    prefix="/setup",
    tags=["Setup"],
)

@router.post("/initial", response_model=schemas.User)
def create_initial_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Creates the initial administrator user for the application.
    This endpoint is only available if the application has not been set up yet.
    """
    # 1. Verify that this is the first run
    is_first_run_setting = crud_settings.get_app_setting(db, key="isFirstRun")
    if is_first_run_setting and not is_first_run_setting.isFirstRun:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Application setup has already been completed.",
        )
        
    # 2. Additional check: ensure no other users exist
    existing_users = crud_users.get_users(db, limit=1)
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An initial user already exists.",
        )

    # 3. Create the new user
    db_user = crud_users.create_user(db=db, user=user)

    # 4. Find or create the 'admin' role
    admin_role = crud_roles.get_role_by_name(db, name="admin")
    if not admin_role:
        admin_role = crud_roles.create_role(db, schemas.RoleCreate(name="admin"))

    # 5. Assign the admin role to the new user
    db_user.roles.append(admin_role)
    db.commit()
    db.refresh(db_user)

    # 6. Mark the setup as complete
    if not is_first_run_setting:
        crud_settings.create_app_setting(db, schemas.AppSettingCreate(key="isFirstRun", value="False", isFirstRun=False))
    else:
        is_first_run_setting.isFirstRun = False
        db.commit()

    return db_user
