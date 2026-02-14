
import httpx
from sqlalchemy.orm import Session
from app.crud import settings as crud_settings

def get_mcp_api_key(db: Session, user_id: str, mcp_name: str) -> str | None:
    """Retrieves the API key for a given MCP from the user's settings."""
    # MCP API keys are stored in the format 'mcp_apikey_{mcp_name}'
    api_key_setting = crud_settings.get_user_setting_by_key(
        db,
        user_id=user_id,
        key=f"mcp_apikey_{mcp_name}",
    )
    if api_key_setting:
        return api_key_setting.value
    return None

async def query_mcp(mcp_url: str, api_key: str, query: str) -> dict:
    """Queries an MCP with the given URL, API key, and query."""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{mcp_url}/query", headers=headers, json={"query": query})
        response.raise_for_status()
        return response.json()
