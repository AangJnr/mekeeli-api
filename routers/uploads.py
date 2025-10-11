
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pathlib import Path
import models, security, schemas

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"],
    dependencies=[Depends(security.get_current_admin_user)],
)

UPLOAD_DIRECTORY = Path("data/uploads/attachments")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

def get_unique_filename(filename: str) -> str:
    """Generates a unique filename to prevent overwrites."""
    file_extension = Path(filename).suffix
    unique_id = uuid.uuid4()
    return f"{unique_id}{file_extension}"

@router.post("/attachment", response_model=schemas.Attachment)
async def upload_attachment(file: UploadFile = File(...)):
    """
    Uploads a file and returns its attachment metadata.
    """
    unique_filename = get_unique_filename(file.filename)
    file_path = UPLOAD_DIRECTORY / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return schemas.Attachment(
        id=unique_filename,
        name=file.filename,
        type=file.content_type,
        url=f"/uploads/attachments/{unique_filename}"
    )

@router.delete("/attachment/{filename}")
async def delete_attachment(filename: str):
    """
    Deletes a specific attachment from the server.
    """
    file_path = UPLOAD_DIRECTORY / filename
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
        
    file_path.unlink()
    
    return {"message": f"Attachment '{filename}' deleted successfully."}
