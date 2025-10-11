
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
    Creates a new user within the administrator's organization.
    Only available to admins in an ORGANIZATION setup.
    """
    if current_user.user_type != UserType.ORGANIZATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators in an organization can create new users.",
        )

    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Administrator is not associated with an organization.",
        )

    db_user = crud_users.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Automatically assign the new user to the admin's organization
    return crud_users.create_user(db=db, user=user, org_id=current_user.org_id)

# ... (rest of admin router remains the same) ...
