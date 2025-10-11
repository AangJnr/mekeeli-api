
import os
import models
from sqlalchemy.orm import Session, joinedload

from mcp_use.agents import MCPAgent, MCPClient
from mcp_use.llms import OllamaLlm

def get_agent_for_user(
    db: Session, 
    user: models.User, 
    task_id: str = None, 
    tool_id: str = None
):
    """
    Dynamically creates and configures an MCPAgent for a user based on the
    context of the request (task, single tool, or open-ended).
    """
    allowed_mcps = set()
    allowed_tools = set()

    # Case 1: Task-based chat (most specific)
    if task_id:
        task = db.query(models.Task).filter_by(id=task_id).one_or_none()
        if task and task.tool_ids:
            # Fetch all tools and MCPs whose IDs are in the task's tool_ids list
            task_tools = db.query(models.Tool).filter(models.Tool.id.in_(task.tool_ids)).all()
            task_mcps = db.query(models.McpServer).filter(models.McpServer.id.in_(task.tool_ids)).all()
            allowed_tools.update(task_tools)
            allowed_mcps.update(task_mcps)

    # Case 2: Single-tool chat
    elif tool_id:
        # Check if the ID corresponds to a Tool
        tool = db.query(models.Tool).filter_by(id=tool_id).one_or_none()
        if tool:
            allowed_tools.add(tool)

        # Also check if the ID corresponds to an McpServer
        mcp = db.query(models.McpServer).filter_by(id=tool_id).one_or_none()
        if mcp:
            allowed_mcps.add(mcp)

    # Case 3: Open-ended chat (default behavior)
    else:
        user_with_permissions = db.query(models.User).options(
            joinedload(models.User.roles).joinedload(models.Role.permission_groups),
            joinedload(models.User.permission_groups)
        ).filter(models.User.id == user.id).one()

        all_permission_groups = set(user_with_permissions.permission_groups)
        for role in user_with_permissions.roles:
            all_permission_groups.update(role.permission_groups)

        for group in all_permission_groups:
            if group.mcp_server:
                allowed_mcps.add(group.mcp_server)
            if group.tool:
                allowed_tools.add(group.tool)

    # --- Agent Configuration ---

    capability_types = {m.type for m in allowed_mcps if m.type} | {t.type for t in allowed_tools if t.type}
    
    mcp_servers_config = {mcp.name: mcp.config for mcp in allowed_mcps if mcp.config}
    client_config = {"mcpServers": mcp_servers_config}
    client = MCPClient.from_dict(client_config)

    system_prompt = "You are an expert assistant."
    if capability_types:
        prompt_parts = sorted(list(capability_types))
        system_prompt += f" You have access to { ', '.join(prompt_parts) }."

    user_model_setting = db.query(models.UserSetting).filter_by(user_id=user.id, key="default_ollama_model").first()
    llm_model = user_model_setting.value if user_model_setting else "gemma2"
    llm = OllamaLlm(model=llm_model)

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
