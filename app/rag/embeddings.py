def embed_texts(model: str, texts: list[str]) -> list[list]:
    import ollama

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


def embed_query(model: str, query: str) -> list:
    import ollama

    if hasattr(ollama, "embeddings"):
        response = ollama.embeddings(model=model, prompt=query)
        return response.get("embedding", [])
    if hasattr(ollama, "embed"):
        response = ollama.embed(model=model, input=query)
        return response.get("embedding", [])
    return []
