# Use a specific, lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Create a non-root user
RUN useradd --create-home appuser

# Install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using a production-ready server (Gunicorn)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
