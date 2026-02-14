from sqlalchemy.orm import Session

from app.db import models


def create_document(db: Session, user_id: str, file_id: str, status: str = "pending"):
    doc = models.RagDocument(user_id=user_id, file_id=file_id, status=status)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: str):
    return db.query(models.RagDocument).filter(models.RagDocument.id == document_id).first()


def get_document_by_file(db: Session, file_id: str):
    return db.query(models.RagDocument).filter(models.RagDocument.file_id == file_id).first()


def update_document_status(db: Session, document: models.RagDocument, status: str):
    document.status = status
    db.commit()
    db.refresh(document)
    return document


def list_pending_documents(db: Session, limit: int = 10):
    return (
        db.query(models.RagDocument)
        .filter(models.RagDocument.status == "pending")
        .order_by(models.RagDocument.created_at.asc())
        .limit(limit)
        .all()
    )


def create_chunk(db: Session, **kwargs):
    chunk = models.RagChunk(**kwargs)
    db.add(chunk)
    return chunk


def delete_chunks_for_document(db: Session, document_id: str):
    db.query(models.RagChunk).filter(models.RagChunk.document_id == document_id).delete()
    db.commit()


def list_chunks_for_user(db: Session, user_id: str):
    return db.query(models.RagChunk).filter(models.RagChunk.user_id == user_id).all()


def get_chunk(db: Session, chunk_id: str):
    return db.query(models.RagChunk).filter(models.RagChunk.id == chunk_id).first()
