FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uvx /usr/local/bin/uvx

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

RUN chmod +x ./entrypoint.sh
RUN useradd --create-home appuser && chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    ENVIRONMENT=production \
    OLLAMA_HOST=http://ollama:11434

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
