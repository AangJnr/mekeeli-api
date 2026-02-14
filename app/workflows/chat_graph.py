def build_chat_graph() -> dict:
    # Placeholder graph shape until LangGraph flow is introduced.
    return {"nodes": ["input", "route", "respond"], "edges": [["input", "route"], ["route", "respond"]]}
