
import shutil
from fastapi import APIRouter, UploadFile, File, Depends
from pathlib import Path
import models, security

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"],
    dependencies=[Depends(security.get_current_admin_user)],
)

# Change the upload path to be inside the persistent /app/data volume
UPLOAD_DIRECTORY = Path("data/uploads/icons")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

@router.post("/icon")
async def upload_icon(file: UploadFile = File(...)):
    """
    Uploads an icon for a Tool or MCP Server.
    """
    file_path = UPLOAD_DIRECTORY / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # The URL path remains the same for the frontend
    return {"icon_url": f"/uploads/icons/{file.filename}"}
