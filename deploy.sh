#!/bin/bash

# Exit on error
set -e

echo "=========================================="
echo "🚀 Starting Deployment Process"
echo "=========================================="

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "❌ pipenv is not installed. Please install it first."
    exit 1
fi

# Install/Update dependencies
echo "📦 Installing/Updating Python dependencies..."
pipenv install --deploy

# Run database migrations
echo "🗄️  Running database migrations..."
pipenv run python manage.py migrate --noinput

# Collect static files
echo "📂 Collecting static files..."
pipenv run python manage.py collectstatic --noinput

# Restart Docker services (PostgreSQL and Redis)
echo "🐳 Restarting Docker services..."
if [ -f docker-compose.yml ]; then
    docker-compose up -d
    echo "✅ Docker services restarted"
else
    echo "⚠️  docker-compose.yml not found, skipping Docker restart"
fi

# Restart Gunicorn service
echo "🔄 Restarting Gunicorn service..."
if systemctl is-active --quiet gunicorn; then
    sudo systemctl restart gunicorn
    echo "✅ Gunicorn service restarted"
elif [ -f gunicorn.pid ]; then
    # Alternative: kill and restart using PID file
    kill -HUP $(cat gunicorn.pid)
    echo "✅ Gunicorn reloaded"
else
    echo "⚠️  Gunicorn service not found. You may need to start it manually:"
    echo "   sudo systemctl start gunicorn"
fi

# Check application health
echo "🏥 Checking application health..."
sleep 2
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Application is responding"
else
    echo "⚠️  Application health check failed. Please check logs."
fi

echo "=========================================="
echo "✅ Deployment Completed Successfully!"
echo "=========================================="
