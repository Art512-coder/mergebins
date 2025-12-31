@echo off
REM BIN Search Web Application - Quick Start Script for Windows

echo 🚀 Starting BIN Search Web Application...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is required but not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is required but not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy backend\.env.example .env
    echo ⚠️  Please edit .env file with your actual API keys before proceeding!
    echo    Required: NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_SECRET, COINBASE_API_KEY, COINBASE_WEBHOOK_SECRET
    pause
)

REM Copy BIN data file
if not exist merged_bin_data.csv (
    if exist ..\merged_bin_data.csv (
        echo 📊 Copying BIN data file...
        copy ..\merged_bin_data.csv .\merged_bin_data.csv
    ) else (
        echo ❌ BIN data file (merged_bin_data.csv) not found!
        echo    Please copy your BIN database file to this directory.
        pause
        exit /b 1
    )
)

REM Build and start services
echo 🏗️  Building and starting services...
docker-compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

echo 🎉 Application started successfully!
echo.
echo 📍 Access Points:
echo    🌐 Web Application: http://localhost:3000
echo    🔧 API Backend: http://localhost:8000
echo    📖 API Docs: http://localhost:8000/docs
echo    🗄️  Database: localhost:5432
echo    💾 Redis: localhost:6379
echo.
echo 🛠️  Management Commands:
echo    📊 View logs: docker-compose logs -f
echo    🛑 Stop: docker-compose down
echo    🔄 Restart: docker-compose restart
echo    🧹 Clean: docker-compose down -v
echo.
echo ⚠️  Don't forget to:
echo    1. Set up your crypto payment webhooks:
echo       - NOWPayments IPN: http://yourdomain.com/api/v1/payments/webhook/nowpayments
echo       - Coinbase Commerce: http://yourdomain.com/api/v1/payments/webhook/coinbase
echo    2. Update CORS_ORIGINS in production
echo    3. Use a strong SECRET_KEY in production
echo    4. Set BASE_URL to your production domain

pause
