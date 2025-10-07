
from sqlalchemy.orm import Session
import models, schemas

def get_permission_group(db: Session, group_id: int):
    return db.query(models.PermissionGroup).filter(models.PermissionGroup.id == group_id).first()

def get_permission_groups(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PermissionGroup).offset(skip).limit(limit).all()

def create_permission_group(db: Session, group: schemas.PermissionGroupCreate):
    db_group = models.PermissionGroup(name=group.name)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def add_permission_to_group(db: Session, group: models.PermissionGroup, permission: models.Permission):
    if permission not in group.permissions:
        group.permissions.append(permission)
        db.commit()
    return group

def remove_permission_from_group(db: Session, group: models.PermissionGroup, permission: models.Permission):
    if permission in group.permissions:
        group.permissions.remove(permission)
        db.commit()
    return group
