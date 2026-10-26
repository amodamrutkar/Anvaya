FROM python:3.11-slim

LABEL maintainer="M4 (Backend, Security, Audit)"
LABEL description="Sutradhar API — synthetic data, simulated connectors"

WORKDIR /app

# Copy service dependencies and packages
COPY services/graph/ ./services/graph/
COPY services/api/ ./services/api/

# Copy canonical contracts and data fixtures
COPY contracts/ ./contracts/
COPY data/ ./data/

# Install both sutradhar_graph and sutradhar_api
RUN pip install --no-cache-dir -e ./services/graph -e ./services/api

ENV PYTHONUNBUFFERED=1
ENV APP_ROOT=/app
ENV ARTIFACTS_DIR=/app/artifacts
ENV DEMO_TAMPER=0

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "sutradhar_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
