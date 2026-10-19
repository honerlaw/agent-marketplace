FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    META_ADS_SPEC_PATH=/app/specs

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
# Unlike the sibling servers, the image also carries Meta's endpoint specs: the build
# fetches the pinned codegen commit and fails unless its content hash matches
# (src/meta_ads_mcp/spec_fetch.py), so a running container never fetches from GitHub.
RUN pip install --no-cache-dir . \
    && meta-ads-fetch-specs /app/specs \
    && useradd --create-home --uid 10001 mcp

USER mcp
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"MCP_PORT\"]}/healthz')"

CMD ["meta-ads-mcp"]
