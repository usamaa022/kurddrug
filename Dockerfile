FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "drug2.py"]