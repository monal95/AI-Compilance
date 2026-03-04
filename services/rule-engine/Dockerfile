# Rule Engine Service Dockerfile
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies with retry logic
RUN for i in 1 2 3; do apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && break || sleep 2; done \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY services/rule-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared library
COPY shared/ /app/shared/

# Copy service code
COPY services/rule-engine/app/ /app/

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
