# syntax=docker/dockerfile:1
FROM node:22-alpine AS web
WORKDIR /build/web
COPY web/package.json web/package-lock.json* ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    ROOTCAUSE_RUNTIME=/data \
    ROOTCAUSE_DB=/data/rootcause.sqlite3
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*
COPY server/ /app/server/
RUN pip install --no-cache-dir "./server[pdf,docx,npu]"
COPY --from=web /build/web/dist /app/web/dist
RUN mkdir -p /data && useradd -m -u 10001 rootcause && chown -R rootcause:rootcause /app /data
USER rootcause
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"
CMD ["uvicorn", "rootcause.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/app/server"]
