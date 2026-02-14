
from sqlalchemy.orm import Session
from app.db import models
from app import schemas

def create_organization(db: Session, org: schemas.OrganizationCreate):
    """
    Creates a new organization in the database.
    """
    db_org = models.Organization(name=org.name)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org
