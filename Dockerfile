FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_PATH=/data/tasks.db

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --no-create-home app

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

COPY app.py .
COPY templates ./templates
COPY static ./static

RUN mkdir -p /data && chown -R app:app /app /data

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=2", "--threads=4", "--preload", "--access-logfile=-", "--error-logfile=-", "app:app"]
