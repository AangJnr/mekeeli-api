from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.db import models
from app.crud import rag as crud_rag
from app.crud import files as crud_files
from app.chat.models import get_embed_model_name


def _extract_text(file_path: Path, mime: str) -> str:
    if mime.startswith("text/"):
        return file_path.read_text(errors="ignore")

    if mime in {"application/pdf"}:
        try:
            from pypdf import PdfReader
        except Exception:
            return ""
        try:
            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""

    if mime in {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
        try:
            import docx
        except Exception:
            return ""
        try:
            doc = docx.Document(str(file_path))
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        except Exception:
            return ""

    return ""


def _chunk_text(text: str, chunk_size: int = 3500, overlap: int = 300) -> List[dict]:
    chunks = []
    start = 0
    index = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk_text = text[start:end]
        chunks.append(
            {
                "index": index,
                "text": chunk_text,
                "char_start": start,
                "char_end": end,
            }
        )
        index += 1
        if end == length:
            break
        start = max(end - overlap, 0)
    return chunks


def _embed_texts(model: str, texts: List[str]) -> List[list]:
    try:
        import ollama
    except Exception as exc:
        raise RuntimeError("Ollama client not available") from exc

    embeddings = []
    for text in texts:
        if hasattr(ollama, "embeddings"):
            response = ollama.embeddings(model=model, prompt=text)
            embeddings.append(response.get("embedding"))
        elif hasattr(ollama, "embed"):
            response = ollama.embed(model=model, input=text)
            embeddings.append(response.get("embedding"))
        else:
            raise RuntimeError("Ollama embeddings API not found")
    return embeddings


def ingest_document(db: Session, document: models.RagDocument):
    file_record = crud_files.get_file(db, document.file_id)
    if not file_record or file_record.user_id != document.user_id:
        raise ValueError("File not found")

    document.status = "pending"
    db.commit()
    db.refresh(document)

    text = _extract_text(Path(file_record.storage_path), file_record.mime)
    if not text.strip():
        crud_rag.update_document_status(db, document, "failed")
        raise ValueError("No extractable text found")

    extracted_path = Path(file_record.storage_path).with_suffix(".txt")
    extracted_path.write_text(text, encoding="utf-8")
    file_record.extracted_text_path = str(extracted_path)
    db.commit()

    embed_model = get_embed_model_name(db)

    # Chunk text first, then generate embeddings in matching order for deterministic persistence.
    chunks = _chunk_text(text)
    embeddings = _embed_texts(embed_model, [chunk["text"] for chunk in chunks])

    # Re-ingestion replaces previous chunks for the same document.
    crud_rag.delete_chunks_for_document(db, document.id)
    for chunk, embedding in zip(chunks, embeddings):
        crud_rag.create_chunk(
            db,
            user_id=document.user_id,
            document_id=document.id,
            file_id=file_record.id,
            chunk_index=chunk["index"],
            text=chunk["text"],
            char_start=chunk["char_start"],
            char_end=chunk["char_end"],
            meta_data=None,
            embedding=embedding,
            created_at=datetime.now(timezone.utc),
        )

    db.commit()
    crud_rag.update_document_status(db, document, "ready")
    return document


def ingest_file(db: Session, file_id: str, user_id: str):
    file_record = crud_files.get_file(db, file_id)
    if not file_record or file_record.user_id != user_id:
        raise ValueError("File not found")

    document = crud_rag.get_document_by_file(db, file_id)
    if not document:
        document = crud_rag.create_document(db, user_id=user_id, file_id=file_id, status="pending")

    return ingest_document(db, document)
