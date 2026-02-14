def chunk_text(text: str, chunk_size: int = 3500, overlap: int = 300) -> list[dict]:
    chunks = []
    start = 0
    index = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(
            {
                "index": index,
                "text": text[start:end],
                "char_start": start,
                "char_end": end,
            }
        )
        index += 1
        if end == length:
            break
        start = max(end - overlap, 0)
    return chunks
