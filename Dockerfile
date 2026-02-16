# Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Build backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Create directories
RUN mkdir -p /app/storage/generations /app/storage/temp /app/logs /app/data

# Expose port
EXPOSE 8000

# Run application (migrations + start)
ENTRYPOINT ["./entrypoint.sh"]
