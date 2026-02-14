def read_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return {"content": handle.read()}
