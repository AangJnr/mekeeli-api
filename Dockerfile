# ==========================
# Stage 1: Builder
# ==========================
FROM python:3.11-slim AS builder

# Install system dependencies
RUN set -x && apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only dependencies first
COPY requirements.txt .
RUN echo "=== Installing Python dependencies ===" && cat requirements.txt

# Install Python dependencies to a temporary path with verbose output
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt -v

# ==========================
# Stage 2: Runtime
# ==========================
FROM python:3.11-slim

# Create a non-root user
RUN set -x && useradd --create-home appuser

# Set working directory
WORKDIR /app

# Copy dependencies from builder
RUN echo "=== Copying dependencies from builder ==="
COPY --from=builder /install /usr/local

# Copy application files (as root first to set permissions)
RUN echo "=== Copying application files ==="
COPY . .

# Make sure entrypoint is executable BEFORE switching user
RUN chmod +x ./entrypoint.sh && ls -la ./entrypoint.sh

# Change ownership after setting permissions
RUN chown -R appuser:appuser /app

# Now switch to non-root user
USER appuser


# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    DATABASE_URL=sqlite:///./sql.db \
    OLLAMA_URL=http://ollama:11434

# Expose the port
EXPOSE 8000

# Entrypoint handles migrations + startup
ENTRYPOINT ["./entrypoint.sh"]

# Default command (Gunicorn for production)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "core.main:app"]