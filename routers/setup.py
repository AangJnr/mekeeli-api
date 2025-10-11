
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from crud import users as crud_users, roles as crud_roles, settings as crud_settings, organizations as crud_orgs
from enums import UserType

router = APIRouter(
    prefix="/setup",
    tags=["Setup"],
)

@router.post("/initial-admin", response_model=schemas.User)
def create_initial_admin(setup_data: schemas.InitialAdminCreate, db: Session = Depends(get_db)):
    """
    Creates the initial administrator and, if applicable, the organization.
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
    if crud_users.get_users(db, limit=1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An initial user already exists.",
        )
        
    # 3. Handle Organization Creation
    user_data = setup_data.admin_user
    if user_data.user_type == UserType.ORGANIZATION:
        if not setup_data.organization:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization details are required for ORGANIZATION user type.",
            )
        # Create the organization using the full schema
        crud_orgs.create_organization(db, org=setup_data.organization)
        
    # 4. Create the new user
    db_user = crud_users.create_user(db=db, user=user_data)
    
    # 5. Find or create the 'admin' role and assign it
    admin_role = crud_roles.get_role_by_name(db, name="admin")
    if not admin_role:
        admin_role = crud_roles.create_role(db, schemas.RoleCreate(name="admin"))
    
    db_user.roles.append(admin_role)
    db.commit()
    db.refresh(db_user)
    
    # 6. Mark the setup as complete
    crud_settings.create_app_setting(
        db, 
        schemas.AppSettingCreate(key="isFirstRun", value="False", isFirstRun=False)
    )
    
    return db_user
