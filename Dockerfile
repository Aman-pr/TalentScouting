# Use official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BACKEND_URL=http://localhost:8000

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nginx \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Backend requirements
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy and install Frontend requirements
COPY frontend/requirements.txt ./frontend/requirements.txt
RUN pip install --no-cache-dir -r ./frontend/requirements.txt

# Copy the entire project
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Start both services using the entrypoint script
CMD ["/app/entrypoint.sh"]
