FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

RUN mkdir -p /data/uploads /data/chroma

ENV DATA_DIR=/data \
    UPLOADS_DIR=/data/uploads \
    CHROMA_DIR=/data/chroma

EXPOSE 8000

CMD ["python", "run.py"]
