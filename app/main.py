from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import models
from app.db.session import engine
from app.api import (
    admin,
    app_settings,
    chat,
    conversations,
    files,
    health,
    mcp,
    mcp_servers,
    permissions,
    rag,
    roles,
    settings,
    setup,
    tasks,
    tool_runner,
    tools,
    uploads,
    user_settings,
    users,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# Public routers
app.include_router(setup.router)
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(conversations.router)

# Authenticated routers
app.include_router(mcp.router)
app.include_router(user_settings.router)
app.include_router(uploads.router)
app.include_router(settings.router)
app.include_router(tasks.router)
app.include_router(files.router)
app.include_router(rag.router)
app.include_router(health.router)
app.include_router(tools.router)
app.include_router(tool_runner.router)

# Admin-only routers
app.include_router(admin.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(mcp_servers.router)
app.include_router(app_settings.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Mekeeli API"}
