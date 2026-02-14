from sqlalchemy.orm import Session

from app.crud import rag as crud_rag
from app.rag.ingest import ingest_document


def run_ingestion_tick(db: Session, limit: int = 3):
    pending_docs = crud_rag.list_pending_documents(db, limit=limit)
    for document in pending_docs:
        try:
            ingest_document(db, document)
        except Exception:
            crud_rag.update_document_status(db, document, "failed")
