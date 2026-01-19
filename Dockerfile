# Use a slim Python image
FROM python:3.11-slim

# Install system dependencies for network diagnostics
RUN apt-get update && apt-get install -y \
    iputils-ping \
    iputils-tracepath \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the Flask-SocketIO port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run the application
# Note: In production, you might want to use gunicorn with eventlet worker
CMD ["python", "app.py"]
