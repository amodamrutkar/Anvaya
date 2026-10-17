FROM python:3.11-slim

LABEL maintainer="M4 (Backend, Security, Audit)"
LABEL description="Sutradhar API — synthetic data, simulated connectors"

WORKDIR /app

# Copy dependency spec first for layer caching
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

# Copy service source
COPY sutradhar_api/ ./sutradhar_api/

# Copy contracts and data (mounted as volumes in compose, but needed for fallback)
# These are read-only at runtime; never write to them from the container
COPY ../../contracts /app/contracts
COPY ../../data /app/data

ENV PYTHONUNBUFFERED=1
ENV ARTIFACTS_DIR=/app/artifacts
ENV DEMO_TAMPER=0

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "sutradhar_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
