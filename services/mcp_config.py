
import os
import models
from sqlalchemy.orm import Session, joinedload

from mcp_use import MCPAgent, MCPClient
from .llm_service import get_base_llm # <-- IMPORT THE NEW SERVICE

# ... ( _get_user_capabilities function remains the same ) ...

def get_agent_for_user(
    db: Session, 
    user: models.User, 
    task_id: str = None, 
    tool_id: str = None
):
    """
    Dynamically creates and configures an MCPAgent for a user.
    """
    allowed_mcps, allowed_tools = _get_user_capabilities(db, user, task_id, tool_id)

    # --- Agent Configuration ---
    capability_types = {m.type for m in allowed_mcps if m.type} | {t.type for t in allowed_tools if t.type}
    
    mcp_servers_config = {mcp.key: mcp.config for mcp in allowed_mcps if mcp.config}
    client_config = {"mcpServers": mcp_servers_config}
    client = MCPClient.from_dict(client_config)

    system_prompt = "You are a helpful assistant that can answer questions and help with tasks."
    if capability_types:
        prompt_parts = sorted(list(capability_types))
        system_prompt += f" You have access to { ', '.join(prompt_parts) }."

    # Use the centralized LLM service to get the base model
    llm = get_base_llm(db, user)

    agent_config = {
        "llm": llm,
        "client": client,
        "system_prompt": system_prompt,
        "use_server_manager": True,
    }
    if os.getenv("APP_ENV") == "production":
        agent_config.update({"max_steps": 30, "disallowed_tools": ["file_system", "shell"], "memory_enabled": True})
    else:
        agent_config.update({"max_steps": 10, "verbose": True})
        
    return MCPAgent(**agent_config)
