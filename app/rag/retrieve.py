import math

from sqlalchemy.orm import Session

from app.crud import rag as crud_rag
from app.chat.models import get_embed_model_name


def _cosine_similarity(a: list, b: list) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed_query(model: str, query: str) -> list:
    import ollama

    if hasattr(ollama, "embeddings"):
        response = ollama.embeddings(model=model, prompt=query)
        return response.get("embedding", [])
    if hasattr(ollama, "embed"):
        response = ollama.embed(model=model, input=query)
        return response.get("embedding", [])
    return []


def retrieve_top_k(db: Session, user_id: str, query: str, top_k: int):
    embed_model = get_embed_model_name(db)
    query_embedding = _embed_query(embed_model, query)

    chunks = crud_rag.list_chunks_for_user(db, user_id)
    scored = []
    for chunk in chunks:
        score = _cosine_similarity(query_embedding, chunk.embedding or [])
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top_k]
