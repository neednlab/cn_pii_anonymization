FROM python:3.12-slim

LABEL maintainer="CN PII Team"
LABEL description="CN PII Anonymization API Server"
LABEL version="1.0.0"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --no-cache-dir uv && \
    uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache-dir -e .

ENV PATH="/opt/venv/bin:$PATH"

RUN python -m spacy download zh_core_web_lg || echo "Warning: spacy model download failed, will be downloaded at runtime"

COPY . .

RUN mkdir -p /app/logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "cn_pii_anonymization.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
