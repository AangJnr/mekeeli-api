from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import models
from app import schemas
from app.core import security
from app.crud import rag as crud_rag
from app.db.session import get_db
from app.rag.retrieve import retrieve_top_k


router = APIRouter()


@router.post("/rag/query", response_model=schemas.RagQueryResponse, tags=["RAG"])
def rag_query(
    request: schemas.RagQueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    try:
        scored = retrieve_top_k(db, current_user.id, request.query, request.top_k)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="RAG query failed")

    chunks = []
    for score, chunk in scored:
        chunks.append(
            schemas.RagQueryChunk(
                text=chunk.text,
                file_id=chunk.file_id,
                page=chunk.page,
                chunk_id=chunk.id,
                score=score,
            )
        )
    return schemas.RagQueryResponse(chunks=chunks)


@router.get("/rag/chunks/{chunk_id}", response_model=schemas.RagChunk, tags=["RAG"])
def get_chunk(
    chunk_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    chunk = crud_rag.get_chunk(db, chunk_id)
    if not chunk or chunk.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return chunk
