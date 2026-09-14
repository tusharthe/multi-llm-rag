# RAG From Scratch — production image (cloud APIs, USE_OLLAMA=false).
# Build: docker build -t multi-llm-rag .
# Run:   docker run -p 127.0.0.1:8501:8501 --env-file .env.prod -v ... (see chat)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# onnxruntime (RapidOCR PDF parsing) needs libgomp on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv binary for fast, locked installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Deps first for better layer caching (needs pyproject + lock only).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then the app source.
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# API keys arrive via -e / --env-file at runtime, never baked into the image.
CMD ["uv", "run", "--no-sync", "streamlit", "run", "app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
