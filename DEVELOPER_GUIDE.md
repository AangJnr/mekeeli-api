# Mekeeli API Maintainer Guide

This guide is for engineers inheriting `mekeeli-api`. It documents the current backend structure, where critical logic lives, and the safest places to extend functionality.

## 1) Runtime entry points

- `main.py` (repo root in `mekeeli-api/`) exports ASGI app from `app.main`.
- `app/main.py` builds the FastAPI app, mounts static uploads, and registers all routers.
- `worker.py` (repo root in `mekeeli-api/`) starts the background worker loop from `app.worker`.
- `app/worker.py` executes scheduler + RAG ingestion ticks and writes worker heartbeat JSON.
- `app/celery_worker.py` defines a Celery app used for async MCP queries.

## 2) Layered structure

- `app/api/*`: HTTP route handlers, auth guards, request/response orchestration.
- `app/crud/*`: direct SQLAlchemy persistence helpers.
- `app/db/models.py`: SQLAlchemy models and relationships.
- `app/schemas.py`: Pydantic DTOs used by API and CRUD boundaries.
- `app/chat/*`: LLM model selection, MCP agent orchestration, memory helpers.
- `app/rag/*`: file-to-text extraction, chunking, embeddings, retrieval, ingestion worker.
- `app/tasks/*`: schedule calculation, task payload execution, scheduler tick.
- `app/tools/*`: tool registry/runner helpers and MCP integration.
- `app/core/*`: config, security/auth, logging, offline mode helper.
- `app/workflows/*`: LangGraph placeholders (`chat_graph`, `task_graph`) for future orchestration.

## 3) Key API modules and important functions

### Chat + Conversations

- `app/api/chat.py`
  - `run_chat`: main chat endpoint; routes requests to:
    - agent chat (`task_id` or `tool_id` present),
    - vision chat (image attachments present),
    - base text chat (default).
  - `stream_simple_response`, `stream_agent_response`, `stream_vision_response`: streaming variants that persist final assistant output to DB.
- `app/api/conversations.py`
  - `get_owned_session`: ownership guard used by all conversation routes.
  - `list_messages`: cursor/limit message pagination.
- `app/crud/chat_sessions.py`
  - `create_chat_session`, `create_chat_message`, `get_session_messages`, `update_chat_session`, `delete_chat_session`.

### Files + RAG

- `app/api/files.py`
  - `upload_file`: writes file to `data/uploads/files`, creates `File` record.
  - `ingest_file_endpoint`: creates/uses RAG document and runs ingestion.
  - `file_status`: checks ingestion state via RAG document.
- `app/rag/ingest.py`
  - `_extract_text`: MIME-based extraction (text/pdf/docx).
  - `_chunk_text`: char-window chunking with overlap.
  - `_embed_texts`: calls Ollama embedding API.
  - `ingest_document`: full pipeline; extracts, stores `.txt`, replaces chunks, marks ready/failed.
  - `ingest_file`: entrypoint from uploaded `file_id`.
- `app/rag/retrieve.py`
  - `retrieve_top_k`: embeds query, scores stored chunk embeddings by cosine similarity.
- `app/api/rag.py`
  - `rag_query`: retrieval endpoint returning scored chunks.
  - `get_chunk`: returns a single user-owned chunk.

### Tasks + Worker

- `app/api/tasks.py`
  - user-scoped task CRUD, enable/disable, run history.
- `app/crud/tasks.py`
  - `create_task`, `update_task`, `set_task_enabled`: computes `next_run_at` via recurrence rules.
  - `create_task_run`, `get_task_runs`: execution audit records.
- `app/tasks/recurrence.py`
  - `compute_next_run_at`: schedule parser for once/interval/cron-like patterns.
- `app/tasks/runner.py`
  - `run_task_payload`: executes payload types (`post_message`, `tool_run`, `noop` fallback).
- `app/tasks/scheduler.py`
  - `run_scheduler_tick`: pulls due tasks, executes payloads, records success/failure, reschedules/deactivates.
- `app/worker.py`
  - worker loop: runs scheduler tick and RAG ingestion tick continuously.

### Tools + MCP

- `app/api/tools.py`
  - admin tool management and permission grant endpoints.
  - `validate_tool_payload`: schema + script config validation.
- `app/api/tool_runner.py`
  - `run_tool`: main runtime path for dynamic tool scripts:
    - checks enabled state, offline mode, permission grants, high-danger confirmation,
    - validates input schema,
    - executes script entrypoint,
    - validates output schema,
    - persists full run status in `tool_runs`.
  - `list_tool_runs`, `test_tool`: operational support endpoints.
- `app/api/mcp.py`
  - `query_mcp`: checks offline mode, resolves user MCP API key, dispatches Celery job.
- `app/tools/mcp_integration.py`
  - `get_mcp_api_key`: reads key from user settings.
  - `query_mcp`: async HTTP call to MCP `/query`.
- `app/chat/orchestrator.py`
  - `_get_user_capabilities`: derives allowed MCP servers/tools based on task, tool, or role/permission groups.
  - `get_agent_for_user`: builds `MCPAgent` with allowed capability config.

### Settings, auth, health

- `app/core/security.py`
  - password hash/verify, JWT creation, auth dependencies:
    - `get_current_user`, `get_current_active_user`, `get_current_admin_user`.
- `app/api/users.py`
  - `/token` login endpoint (OAuth2 password flow).
- `app/api/setup.py`
  - one-time initial admin bootstrap + organization creation.
- `app/api/settings.py`
  - global settings update and diagnostics summary.
- `app/api/health.py`
  - health checks for DB, Ollama, worker heartbeat.

## 4) Data model map (high level)

- Identity & access: `User`, `Role`, `PermissionGroup`, `Permission`, join tables.
- External capabilities: `McpServer`, `Tool`, `ToolPermission`, `ToolRun`.
- Chat: `ChatSession`, `ChatMessage`.
- File/RAG: `File`, `RagDocument`, `RagChunk`.
- Automation: `Task`, `TaskRun`.
- Config: `UserSetting`, `AppSetting`, `Settings`, `Organization`.

## 5) Critical request/data flows

### A) Chat (text/vision/agent)

1. `POST /chat` (`app/api/chat.py`).
2. Resolve/create conversation (`crud/chat_sessions.py`).
3. Persist user message (attachments in `meta_data`).
4. Route:
   - Agent flow: `app/chat/orchestrator.py` + MCP agent.
   - Vision flow: `app/files/image_pipeline.py` + vision model.
   - Text flow: `app/chat/models.py` + base `ChatOllama`.
5. Persist assistant response and return/stream output.

### B) RAG ingest and retrieval

1. Upload: `POST /files/upload`.
2. Ingest: `POST /files/{file_id}/ingest` -> `app/rag/ingest.py`.
3. Store chunk embeddings in `rag_chunks`.
4. Query: `POST /rag/query` -> `retrieve_top_k`.

### C) Scheduled tasks

1. Create task via `POST /tasks` with schedule + payload.
2. Worker loop (`app/worker.py`) calls `run_scheduler_tick`.
3. Due tasks execute via `run_task_payload`; run records persisted in `task_runs`.

### D) Tool execution

1. `POST /tools/run`.
2. Pre-flight checks (tool state, offline mode, permission scope, confirmation).
3. Dynamic script execution from DB config.
4. Run audit updates in `tool_runs`.

## 6) Where to add new functionality

- New API endpoint: add route in `app/api/<domain>.py`, DTOs in `app/schemas.py`, persistence in `app/crud/<domain>.py`.
- New background job type:
  - task payload path: extend `run_task_payload` in `app/tasks/runner.py`,
  - periodic execution path: add into `app/worker.py` loop or dedicated worker module.
- New RAG strategy: update `app/rag/ingest.py` and/or `app/rag/retrieve.py`.
- New model defaults: `app/chat/models.py` + `/settings` update path.

## 7) Operational notes

- Python dependency management uses `uv` with `pyproject.toml`.
- Root bootstrap script: `./setup.sh` (from repo root) installs/checks prerequisites and starts the local Docker stack.
- Automated backups are handled by `mekeeli-backup` (Compose service) and written to `./volumes/backups`.
- Upload paths:
  - attachments: `data/uploads/attachments`
  - files: `data/uploads/files`
- Worker heartbeat file defaults to `data/worker_heartbeat.json` and is consumed by `/health`.
- FastAPI docs are available by default (`/docs`, `/redoc`) unless disabled in app init.

## 8) Docker command quick-reference (from repo root)

- Helper script:
  - `./scripts/docker-ops.sh help`
  - Wraps common `docker compose` operations used below.
- Stack status:
  - `docker compose ps`
  - `docker compose ps -a`
- Start / rebuild all services:
  - `docker compose up -d --build`
- Start specific services:
  - `docker compose up -d db ollama`
  - `docker compose up -d mekeeli-api mekeeli-ui`
- Stop all services (keep containers):
  - `docker compose stop`
- Stop specific services:
  - `docker compose stop mekeeli-api`
  - `docker compose stop mekeeli-ui`
- Start previously stopped services:
  - `docker compose start`
  - `docker compose start mekeeli-api`
- Restart services:
  - `docker compose restart`
  - `docker compose restart ollama`
  - `docker compose restart mekeeli-api mekeeli-ui`
- Tail logs:
  - `docker compose logs -f`
  - `docker compose logs -f ollama`
  - `docker compose logs -f mekeeli-api`
  - `docker compose logs -f mekeeli-ui`
- Tail recent logs only:
  - `docker compose logs --tail=200 mekeeli-api`
- Run one-off command inside container:
  - `docker compose exec mekeeli-api uv run alembic upgrade head`
  - `docker compose exec ollama ollama list`
- Remove stopped containers:
  - `docker compose rm -f`
  - `docker compose rm -f mekeeli-api`
- Full teardown:
  - `docker compose down`
- Full teardown + delete volumes:
  - `docker compose down -v` (destructive; deletes DB and persisted data volumes)

## 9) Cleanup status and verification

- `DB dependency standardization` (addressed):
  - API modules now use shared `app.db.session.get_db` instead of local `SessionLocal` wrappers.
  - Updated modules: `app/api/app_settings.py`, `app/api/permissions.py`, `app/api/roles.py`, `app/api/mcp_servers.py`, `app/api/tools.py`, `app/api/user_settings.py`.
- `User settings authorization` (addressed):
  - `app/api/user_settings.py` now enforces owner-or-admin checks for read/write.
  - Requests for a different `user_id` return `403` unless caller has `admin` role.
- `Pydantic v2 config key migration` (addressed):
  - `app/schemas.py` uses `from_attributes` and `validate_by_name` in model config blocks.
  - This removes startup warnings tied to old v1 keys.

Quick verification checklist:
- `docker compose logs --tail=200 mekeeli-api` (confirm no `orm_mode` / `allow_population_by_field_name` warnings).
- `docker compose exec mekeeli-api uv run python -m py_compile app/api/user_settings.py app/schemas.py`.
- Call `GET /users/{other_user_id}/settings/` as non-admin and verify `403`.
