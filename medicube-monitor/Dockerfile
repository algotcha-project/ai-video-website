FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY *.py ./

# Create data volume
RUN mkdir -p /app/data
VOLUME /app/data

# Environment
ENV PYTHONUNBUFFERED=1

# Run in daemon mode by default
CMD ["python", "monitor.py", "--daemon", "--interval", "24"]
