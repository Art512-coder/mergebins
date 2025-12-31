#!/bin/bash

# BIN Search Web Application - Quick Start Script
echo "🚀 Starting BIN Search Web Application..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp backend/.env.example .env
    echo "⚠️  Please edit .env file with your actual API keys before proceeding!"
    echo "   Required: NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_SECRET, COINBASE_API_KEY, COINBASE_WEBHOOK_SECRET"
    read -p "Press Enter after you've updated the .env file..."
fi

# Copy BIN data file
if [ ! -f ./merged_bin_data.csv ]; then
    if [ -f ../merged_bin_data.csv ]; then
        echo "📊 Copying BIN data file..."
        cp ../merged_bin_data.csv ./merged_bin_data.csv
    else
        echo "❌ BIN data file (merged_bin_data.csv) not found!"
        echo "   Please copy your BIN database file to this directory."
        exit 1
    fi
fi

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend API is running at http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
else
    echo "❌ Backend API is not responding"
fi

# Check frontend
if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "⚠️  Frontend may still be starting..."
fi

# Show logs
echo ""
echo "📋 Recent logs:"
docker-compose logs --tail=20

echo ""
echo "🎉 Application started successfully!"
echo ""
echo "📍 Access Points:"
echo "   🌐 Web Application: http://localhost:3000"
echo "   🔧 API Backend: http://localhost:8000"
echo "   📖 API Docs: http://localhost:8000/docs"
echo "   🗄️  Database: localhost:5432"
echo "   💾 Redis: localhost:6379"
echo ""
echo "🛠️  Management Commands:"
echo "   📊 View logs: docker-compose logs -f"
echo "   🛑 Stop: docker-compose down"
echo "   🔄 Restart: docker-compose restart"
echo "   🧹 Clean: docker-compose down -v"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Set up your crypto payment webhooks:"
echo "      - NOWPayments IPN: http://yourdomain.com/api/v1/payments/webhook/nowpayments"
echo "      - Coinbase Commerce: http://yourdomain.com/api/v1/payments/webhook/coinbase"
echo "   2. Update CORS_ORIGINS in production"
echo "   3. Use a strong SECRET_KEY in production"
echo "   4. Set BASE_URL to your production domain"
