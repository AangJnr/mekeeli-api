
import os
import models
from sqlalchemy.orm import Session, joinedload

# Imports from the 'mcp-use' package
from mcp_use.agents import MCPAgent, MCPClient
from mcp_use.llms import OllamaLlm

def get_agent_for_user(db: Session, user: models.User):
    """
    Dynamically creates and configures an MCPAgent instance for a specific user
    based on their permissions and settings from the database.
    """

    # 1. Get User's Allowed MCP Servers and their types for the system prompt
    user_with_permissions = db.query(models.User).options(
        joinedload(models.User.role)
        .joinedload(models.Role.permissions)
        .joinedload(models.Permission.mcps)
    ).filter(models.User.id == user.id).one_or_none()

    mcp_servers_config = {}
    capability_types = set()
    if user_with_permissions and user_with_permissions.role:
        allowed_mcps = set()
        for permission in user_with_permissions.role.permissions:
            for mcp_server in permission.mcps:
                allowed_mcps.add(mcp_server)
                if mcp_server.type:
                    capability_types.add(mcp_server.type)

        mcp_servers_config = {
            mcp.name: mcp.config for mcp in allowed_mcps if mcp.config
        }

    client_config = {"mcpServers": mcp_servers_config}
    client = MCPClient.from_dict(client_config)

    # 2. Dynamically generate the system prompt from the collected capability types
    system_prompt = "You are a helpful assistant."
    if capability_types:
        prompt_parts = sorted(list(capability_types))
        system_prompt += f" You have access to { ', '.join(prompt_parts) }."

    # 3. Determine the LLM model from user settings, with an app-level fallback
    user_model_setting = db.query(models.UserSetting).filter(
        models.UserSetting.user_id == user.id,
        models.UserSetting.key == "default_ollama_model"
    ).first()

    llm_model = None
    if user_model_setting:
        llm_model = user_model_setting.value
    else:
        app_model_setting = db.query(models.AppSetting).filter(
            models.AppSetting.key == "default_ollama_model"
        ).first()
        if app_model_setting:
            llm_model = app_model_setting.value

    if not llm_model:
        llm_model = "gemma2"

    llm = OllamaLlm(model=llm_model)

    # 4. Create and return the agent with the dynamic prompt and server manager
    if os.getenv("APP_ENV") == "production":
        # Production config
        agent = MCPAgent(
            llm=llm,
            client=client,
            system_prompt=system_prompt,
            max_steps=30,
            disallowed_tools=["file_system", "shell"],
            use_server_manager=True,
            memory_enabled=True
        )
    else:
        # Development config
        agent = MCPAgent(
            llm=llm,
            client=client,
            system_prompt=system_prompt,
            max_steps=10,
            use_server_manager=True,
            verbose=True
        )
        
    return agent
