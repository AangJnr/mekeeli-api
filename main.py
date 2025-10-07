
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from routers import users, roles, permissions, mcp_servers, tools, user_settings, app_settings, mcp, tool_runner, chat, admin, setup, uploads
import models
from database import engine
import security

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Serve files from the 'data/uploads' directory, which is inside our persistent volume.
# The URL path for users will still be '/uploads'.
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# Public routers
app.include_router(setup.router)
app.include_router(users.router)
app.include_router(chat.router)

# Authenticated routers
app.include_router(mcp.router)
app.include_router(tool_runner.router)
app.include_router(user_settings.router)
app.include_router(uploads.router)

# Admin-only routers
app.include_router(admin.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(mcp_servers.router)
app.include_router(tools.router)
app.include_router(app_settings.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the MCP API"}
