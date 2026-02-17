#!/bin/bash

# Default port to 8080 if not provided by the cloud platform
export PORT=${PORT:-8080}

echo "Starting TalentScout AI Hiring Assistant (Unified Cloud Image)..."
echo "Public Port: ${PORT}"

# Substitute the PORT variable into the nginx template
envsubst '${PORT}' < /app/nginx.conf > /etc/nginx/sites-available/default

# Start the Backend (FastAPI) in the background
echo "Launching Backend on port 8000..."
cd /app/backend
python main.py &

# Start the Frontend (Streamlit) in the background
echo "Launching Frontend on port 8501..."
cd /app/frontend
# Streamlit configuration for proxy compatibility
streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.baseUrlPath="" --server.enableCORS=false --server.enableXsrfProtection=false --server.fileWatcherType none &

# Start Nginx in the foreground to keep the container alive
echo "Launching Nginx Reverse Proxy..."
nginx -g "daemon off;"
