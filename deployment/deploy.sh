#!/bin/bash

# BIN Search Bot Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
echo "🚀 Deploying BIN Search Bot to $ENVIRONMENT environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure your settings."
    exit 1
fi

echo "📋 Pre-deployment checks..."

# Validate .env file has required variables
required_vars=("BOT_TOKEN" "DATABASE_URL" "REDIS_URL" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" .env; then
        echo "❌ Required environment variable $var not found in .env file"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Build and deploy
echo "🔨 Building Docker images..."
docker-compose -f webapp/docker-compose.yml build

echo "🚀 Starting services..."
docker-compose -f webapp/docker-compose.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Health check
echo "🏥 Running health checks..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    docker-compose -f webapp/docker-compose.yml logs backend
    exit 1
fi

echo "🎉 Deployment completed successfully!"
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements_clean.txt
  pkill -f "python BINSearchCCGbot.py" || true
  nohup python3 BINSearchCCGbot.py > bot.out 2>&1 &
EOF
echo "Deployment complete! Check bot.out for logs."
