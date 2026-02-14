def build_citations(chunks: list) -> list[dict]:
    citations = []
    for chunk in chunks:
        citations.append(
            {
                "chunk_id": str(chunk.id),
                "file_id": str(chunk.file_id),
                "page": chunk.page,
            }
        )
    return citations
