# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN chmod -R +x node_modules/.bin || true
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim

WORKDIR /opt/OunceAI

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ ./app/
COPY docs/ ./docs/

# Copy built frontend
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Start command (Flask directly to avoid node dependency)
CMD ["python", "-m", "flask", "--app", "app.main", "run", "--host=0.0.0.0", "--port=8000"]