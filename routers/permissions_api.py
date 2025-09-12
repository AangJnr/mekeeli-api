
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import security
from database import get_db

router = APIRouter()

@router.post("/roles/{role_id}/permissions/{permission_id}", tags=["Permissions API"], dependencies=[Depends(security.get_current_admin_user)])
def grant_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
):
    """Grants a permission to a role."""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()

    return {"message": f"Permission '{permission.name}' granted to role '{role.name}'"}

@router.delete("/roles/{role_id}/permissions/{permission_id}", tags=["Permissions API"], dependencies=[Depends(security.get_current_admin_user)])
def revoke_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
):
    """Revokes a permission from a role."""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()

    return {"message": f"Permission '{permission.name}' revoked from role '{role.name}'"}
