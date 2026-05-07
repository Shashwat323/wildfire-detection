# Stage 1: Builder
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies in one layer to keep image small
# opencv-python-headless
# CPU-only torch index
RUN pip install --upgrade pip && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin appuser

# Install only essential runtime dependencies
# libgl1 and libglib2.0-0 are often needed by opencv, but headless needs fewer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser fire-models/ ./fire-models/

USER appuser

EXPOSE 8000

CMD ["python", "main.py"]
