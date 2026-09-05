FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gerar_contrato.py .
COPY pipedrive/ pipedrive/

ENV PYTHONUNBUFFERED=1

CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 60 pipedrive.webhook_server:app
