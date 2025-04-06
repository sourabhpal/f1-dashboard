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

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create cache directory with proper permissions
RUN mkdir -p /app/cache && chmod 777 /app/cache

# Copy only necessary files
COPY f1_backend.py .
COPY populate_2025_data.py .
COPY populate_historical_data.py .

# Create database directory with proper permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "f1_backend:app", "--host", "0.0.0.0", "--port", "8000"] 