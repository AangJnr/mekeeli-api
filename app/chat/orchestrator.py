
import os
from app.db import models
from sqlalchemy.orm import Session, joinedload

from mcp_use import MCPAgent, MCPClient
from app.chat.models import get_base_llm

def _get_user_capabilities(db: Session, user: models.User, task_id: str = None, tool_id: str = None):
    """
    Determines the set of allowed MCPs and Tools for a user based on the request context.
    """
    allowed_mcps = set()
    allowed_tools = set()

    # Case 1: Task-based chat (most specific context)
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
        # Check if the ID corresponds to a Tool or an McpServer
        tool = db.query(models.Tool).filter_by(id=tool_id).one_or_none()
        if tool:
            allowed_tools.add(tool)
        mcp = db.query(models.McpServer).filter_by(id=tool_id).one_or_none()
        if mcp:
            allowed_mcps.add(mcp)

    # Case 3: Open-ended chat (default behavior)
    else:
        # Gather all permissions from the user's direct assignments and their roles
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
    
    return allowed_mcps, allowed_tools


def get_agent_for_user(
    db: Session, 
    user: models.User, 
    task_id: str = None, 
    tool_id: str = None
):
    """
    Dynamically creates and configures an MCPAgent for a user by first
    determining their capabilities and then building the agent.
    """
    # 1. Determine user's allowed tools and MCPs using the helper function
    allowed_mcps, allowed_tools = _get_user_capabilities(db, user, task_id, tool_id)

    # 2. Build Agent Configuration from the determined capabilities
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
