FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Combined health check and bot launcher
CMD sh -c "\
  echo 'Starting health endpoint...' && \
  (while true; do echo -e 'HTTP/1.1 200 OK\n\nOK' | nc -l -p 8000 -q 1; done) & \
  echo 'Starting bot with retries...' && \
  while true; do \
    python drug2.py || (echo 'Bot crashed, restarting...'; sleep 10); \
  done"