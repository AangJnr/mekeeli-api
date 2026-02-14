import asyncio

from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


@celery_app.task
def query_mcp_task(mcp_url: str, api_key: str, query: str):
    from app.tools.mcp_integration import query_mcp

    # MCP HTTP helper is async; run it to completion inside the Celery worker process.
    return asyncio.run(query_mcp(mcp_url, api_key, query))
