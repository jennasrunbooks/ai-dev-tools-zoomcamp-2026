FROM node:20-slim

RUN npm install -g @anthropic-ai/claude-code

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/
ENV UV_PYTHON_PREFERENCE=only-system
WORKDIR /service
COPY incident-response/pyproject.toml incident-response/uv.lock ./
RUN uv sync --frozen --no-dev
COPY incident-response/main.py ./

RUN chown -R node:node /service
ENV HOME=/tmp
USER node

EXPOSE 8001
CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
