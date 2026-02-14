def build_task_graph() -> dict:
    # Placeholder graph shape until LangGraph flow is introduced.
    return {"nodes": ["load_due", "execute", "finalize"], "edges": [["load_due", "execute"], ["execute", "finalize"]]}
