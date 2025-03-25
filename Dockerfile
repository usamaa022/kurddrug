# Use official Python image (match your dev version)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY requirements.txt .
COPY drug2.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot (important: use CMD, not ENTRYPOINT)
CMD ["python", "drug2.py"]