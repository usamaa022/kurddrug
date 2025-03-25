FROM python:3.11-slim

# Install system dependencies + curl for health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Create fake HTTP endpoint for health checks
RUN echo "from flask import Flask; app = Flask(__name__); @app.route('/'); def health(): return 'OK'" > health.py

# Combined command: Run both health endpoint and bot
CMD sh -c "python health.py & python drug2.py"