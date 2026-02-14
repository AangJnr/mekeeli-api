# Mekeeli API

FastAPI backend for chat, tools, MCP integration, scheduled tasks, and RAG ingestion/retrieval.

## Dependency management (uv)

- This backend now uses `uv` + `pyproject.toml` as the package/dependency source of truth.
- `uv` is installed and used inside Docker images, so host `uv` is optional.
- One-command local bootstrap from repo root:
  - `./setup.sh`
- Non-interactive bootstrap (CI/provisioning):
  - `./setup.sh --yes`
- `setup.sh` checks/installs prerequisites (`docker`, `docker compose`) on macOS and Debian/Ubuntu, builds containers, starts the stack, and pulls default Ollama models.
- Platform entry URL for users: `http://localhost:3000` (`mekeeli-ui`).

## Maintainer docs

- See `DEVELOPER_GUIDE.md` for module/function ownership, request flows, and extension guidance.
- See `../mekeeli-ui/API_CONTRACT.md` for endpoint-level request/response contracts used by UI integrations.
