FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin veklom \
    && mkdir -p /data/veklom-mcp \
    && chown -R veklom:veklom /data/veklom-mcp

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

USER veklom
EXPOSE 8787
VOLUME ["/data/veklom-mcp"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health', timeout=3).read()" || exit 1

CMD ["uvicorn", "veklom_ops_mcp.main:app", "--host", "0.0.0.0", "--port", "8787", "--proxy-headers", "--forwarded-allow-ips=*"]
