
from fastapi import FastAPI
from routers import users, roles, permissions, mcp_servers, tools, user_settings, app_settings, mcp, tool_runner, chat, permissions_api
import models
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router, tags=["Users"])
app.include_router(roles.router, tags=["Roles"])
app.include_router(permissions.router, tags=["Permissions"])
app.include_router(mcp_servers.router, tags=["MCP Servers"])
app.include_router(tools.router, tags=["Tools"])
app.include_router(user_settings.router, tags=["User Settings"])
app.include_router(app_settings.router, tags=["App Settings"])
app.include_router(mcp.router, tags=["MCP"])
app.include_router(tool_runner.router, tags=["Tool Runner"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(permissions_api.router, tags=["Permissions API"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the MCP API"}

@app.get("/health")
def health():
    return {"status": "ok"}