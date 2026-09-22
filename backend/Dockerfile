# VTON API — AWS Lightsail Container Service (or any Docker host)
FROM python:3.11-slim-bookworm

WORKDIR /app

# OpenCV / YOLO runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

# Long timeout for Flux polling; single worker for ML memory use
CMD gunicorn --bind 0.0.0.0:8080 --timeout 300 --workers 1 app:app
