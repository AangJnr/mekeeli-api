from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import models
from app import schemas
from app.core import security
from app.crud import files as crud_files
from app.crud import rag as crud_rag
from app.db.session import get_db
from app.rag.ingest import ingest_file


router = APIRouter()

UPLOAD_DIRECTORY = Path("data/uploads/files")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


@router.post("/files/upload", response_model=schemas.File, tags=["Files"])
def upload_file(
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    original_name = Path(upload.filename).name
    safe_name = f"{current_user.id}-{original_name}"
    file_path = UPLOAD_DIRECTORY / safe_name
    with file_path.open("wb") as buffer:
        for chunk in iter(lambda: upload.file.read(1024 * 1024), b""):
            buffer.write(chunk)

    size_bytes = file_path.stat().st_size

    db_file = crud_files.create_file(
        db,
        user_id=current_user.id,
        org_id=current_user.org_id,
        conversation_id=None,
        name=original_name,
        mime=upload.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        storage_path=str(file_path),
        meta_data=None,
    )
    return db_file


@router.get("/files/{file_id}", tags=["Files"])
def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    db_file = crud_files.get_file(db, file_id)
    if not db_file or db_file.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(db_file.storage_path, filename=db_file.name)


@router.post("/files/{file_id}/ingest", response_model=schemas.RagDocument, tags=["Files"])
def ingest_file_endpoint(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    try:
        return ingest_file(db, file_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/files/{file_id}/status", response_model=schemas.RagDocument, tags=["Files"])
def file_status(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    db_file = crud_files.get_file(db, file_id)
    if not db_file or db_file.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    document = crud_rag.get_document_by_file(db, file_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RAG document not found")
    return document
