FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements for all services
COPY platform_api/requirements.txt /app/platform_api/requirements.txt
COPY streamlit_portal/requirements.txt /app/streamlit_portal/requirements.txt
COPY bot_runner/requirements.txt /app/bot_runner/requirements.txt

# Install dependencies combined
RUN pip install --no-cache-dir -r platform_api/requirements.txt \
    && pip install --no-cache-dir -r streamlit_portal/requirements.txt \
    && pip install --no-cache-dir -r bot_runner/requirements.txt

# Copy shared code
COPY shared /app/shared

# Copy service code
COPY platform_api /app/platform_api
COPY streamlit_portal /app/streamlit_portal
COPY bot_runner /app/bot_runner

# Set Python Path to root to allow imports like 'from platform_api...' or 'from shared...'
ENV PYTHONPATH=/app

# Default command (overwritten by docker-compose or Easypanel)
CMD ["echo", "Please specify a command"]
