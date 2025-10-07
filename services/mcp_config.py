
import os
import models
from sqlalchemy.orm import Session, joinedload

# Imports from the 'mcp-use' package
from mcp_use.agents import MCPAgent, MCPClient
from mcp_use.llms import OllamaLlm

def get_agent_for_user(db: Session, user: models.User):
    """
    Dynamically creates and configures an MCPAgent instance for a specific user
    based on their new, granular permissions.
    """

    # 1. Get User's direct and role-based Permission Groups
    user_with_permissions = db.query(models.User).options(
        joinedload(models.User.roles).joinedload(models.Role.permission_groups).joinedload(models.PermissionGroup.permissions),
        joinedload(models.User.permission_groups).joinedload(models.PermissionGroup.permissions)
    ).filter(models.User.id == user.id).one()

    all_permission_groups = set(user_with_permissions.permission_groups)
    for role in user_with_permissions.roles:
        all_permission_groups.update(role.permission_groups)

    # 2. Collect all unique MCPs and Tools from the permission groups
    allowed_mcps = set()
    allowed_tools = set() # Assuming you'll use this later
    capability_types = set()

    for group in all_permission_groups:
        if group.mcp_server:
            allowed_mcps.add(group.mcp_server)
            if group.mcp_server.type:
                capability_types.add(group.mcp_server.type)
        if group.tool:
            allowed_tools.add(group.tool)
            # Add tool types to the prompt as well if they exist
            if group.tool.type:
                capability_types.add(group.tool.type)

    mcp_servers_config = {mcp.name: mcp.config for mcp in allowed_mcps if mcp.config}
    
    client_config = {"mcpServers": mcp_servers_config}
    client = MCPClient.from_dict(client_config)

    # 3. Dynamically generate the system prompt
    system_prompt = "You are a helpful assistant."
    if capability_types:
        prompt_parts = sorted(list(capability_types))
        system_prompt += f" You have access to { ', '.join(prompt_parts) }."

    # 4. Determine the LLM model
    user_model_setting = db.query(models.UserSetting).filter_by(user_id=user.id, key="default_ollama_model").first()
    llm_model = user_model_setting.value if user_model_setting else "gemma2"

    llm = OllamaLlm(model=llm_model)

    # 5. Create and return the agent
    agent_config = {
        "llm": llm,
        "client": client,
        "system_prompt": system_prompt,
        "use_server_manager": True,
    }
    if os.getenv("APP_ENV") == "production":
        agent_config.update({
            "max_steps": 30,
            "disallowed_tools": ["file_system", "shell"],
            "memory_enabled": True,
        })
    else:
        agent_config.update({"max_steps": 10, "verbose": True})
        
    return MCPAgent(**agent_config)
