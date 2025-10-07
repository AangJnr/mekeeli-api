
from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6f379/0"
)

@celery_app.task
def query_mcp_task(mcp_url: str, api_key: str, query: str):
    from services.mcp_integration import query_mcp
    return query_mcp(mcp_url, api_key, query)
