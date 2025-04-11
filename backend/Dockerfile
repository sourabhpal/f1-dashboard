FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install sqlite3
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements.txt to final stage
COPY --from=builder /app/requirements.txt .

# Create necessary directories with proper permissions
RUN mkdir -p /app/cache /app/data && \
    chmod 777 /app/cache /app/data

# Copy only necessary files
COPY f1_backend.py .
COPY update_database.py .

# Expose port
EXPOSE 8000

# Run database population check and start the application
CMD /bin/bash -c '\
    if [ ! -f /app/data/f1_data.db ] || [ $(sqlite3 /app/data/f1_data.db "SELECT COUNT(*) FROM race_schedule WHERE year = 2025" 2>/dev/null || echo 0) -lt 24 ]; then \
        echo "Database needs to be populated or updated..." && \
        python update_database.py; \
    else \
        echo "Database already populated."; \
    fi && \
    exec uvicorn f1_backend:app --host 0.0.0.0 --port 8000' 