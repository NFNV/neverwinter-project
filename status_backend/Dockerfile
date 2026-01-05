FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY status_backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY status_backend /app/status_backend

EXPOSE 8080

CMD ["uvicorn", "status_backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
