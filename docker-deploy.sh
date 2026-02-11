#!/bin/bash

# Exit on error
set -e

echo "=========================================="
echo "🐳 Docker Deployment Process Starting"
echo "=========================================="

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    # Export variables while preserving special characters
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        # Remove any trailing whitespace/newlines
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | sed 's/\r$//' | sed 's/[[:space:]]*$//')
        # Export the variable
        export "$key=$value"
    done < .env
fi

# Trim whitespace from critical Docker variables
ECR_REGISTRY=$(echo "${ECR_REGISTRY:-}" | xargs)
ECR_REPOSITORY=$(echo "${ECR_REPOSITORY:-gforms}" | xargs)
DOCKER_IMAGE_TAG=$(echo "${DOCKER_IMAGE_TAG:-latest}" | xargs)
AWS_REGION=$(echo "${AWS_REGION:-ap-south-1}" | xargs)

# Check if ECR registry is set
if [ -z "$ECR_REGISTRY" ]; then
    echo "❌ ECR_REGISTRY not set in .env file"
    exit 1
fi

# AWS ECR Login
echo "🔐 Logging into AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

# Pull latest Docker image
echo "📥 Pulling latest Docker image from ECR..."
docker pull $ECR_REGISTRY/$ECR_REPOSITORY:$DOCKER_IMAGE_TAG

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start database services first
echo "🗄️  Starting database services..."
docker-compose -f docker-compose.prod.yml up -d postgresql redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm django python manage.py migrate --noinput

# Collect static files
echo "📂 Collecting static files..."
docker-compose -f docker-compose.prod.yml run --rm django python manage.py collectstatic --noinput

# Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check container health
echo "🏥 Checking container health..."
docker-compose -f docker-compose.prod.yml ps

# Test application health
echo "🏥 Testing application health..."
for i in {1..10}; do
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Application health check failed"
        docker-compose -f docker-compose.prod.yml logs django
        exit 1
    fi
    echo "⏳ Waiting for application to be ready... ($i/10)"
    sleep 3
done

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

echo "=========================================="
echo "✅ Deployment Completed Successfully!"
echo "=========================================="
echo "🌐 Application: http://$(hostname -I | awk '{print $1}')"
echo "📊 Container Status:"
docker-compose -f docker-compose.prod.yml ps
