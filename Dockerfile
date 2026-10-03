FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend
WORKDIR /app
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY migrations ./migrations
COPY alembic.ini ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -e ".[document-engine]"
RUN mkdir -p /app/data/storage /app/data/logs
EXPOSE 8000
CMD ["uvicorn","moduleiq.main:app","--host","0.0.0.0","--port","8000"]
