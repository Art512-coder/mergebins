@echo off
REM Enhanced Windows Deployment Script for CryptoBinChecker.cc
REM Version: 2.0 - November 2025

echo 🚀 CryptoBinChecker.cc - Enhanced Windows Deployment
echo =====================================================

set PROJECT_DIR=%~dp0
set VENV_PATH=%PROJECT_DIR%.venv-1
set BACKEND_DIR=%PROJECT_DIR%webapp\backend
set FRONTEND_DIR=%PROJECT_DIR%webapp\frontend

echo 📂 Project Directory: %PROJECT_DIR%

REM Check if virtual environment exists
if not exist "%VENV_PATH%" (
    echo ❌ Virtual environment not found at %VENV_PATH%
    echo Please create virtual environment first: python -m venv .venv-1
    pause
    exit /b 1
)

echo ✅ Virtual environment found

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"

REM Install/update Python dependencies
echo 📦 Installing Python dependencies...
cd /d "%BACKEND_DIR%"
pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)

echo ✅ Python dependencies installed

REM Initialize database
echo 🗄️ Initializing database...
python init_db.py

if %ERRORLEVEL% neq 0 (
    echo ❌ Database initialization failed
    pause
    exit /b 1
)

echo ✅ Database initialized

REM Populate sample data
echo 📊 Populating sample data...
python populate_sample_data.py

if %ERRORLEVEL% neq 0 (
    echo ❌ Sample data population failed
    pause
    exit /b 1
)

echo ✅ Sample data populated

REM Build frontend (if Node.js is available)
echo 🎨 Building frontend...
cd /d "%FRONTEND_DIR%"

if exist package.json (
    if exist node_modules\ (
        echo Frontend dependencies already installed
    ) else (
        echo Installing frontend dependencies...
        npm install
        if %ERRORLEVEL% neq 0 (
            echo ❌ Frontend dependency installation failed
            pause
            exit /b 1
        )
    )
    
    echo Building frontend...
    npm run build
    
    if %ERRORLEVEL% neq 0 (
        echo ⚠️ Frontend build failed, but continuing...
    ) else (
        echo ✅ Frontend built successfully
    )
) else (
    echo ⚠️ No package.json found, skipping frontend build
)

REM Return to backend directory
cd /d "%BACKEND_DIR%"

REM Create enhanced startup script
echo 📝 Creating startup scripts...

(
echo @echo off
echo cd /d "%BACKEND_DIR%"
echo call "%VENV_PATH%\Scripts\activate.bat"
echo echo 🚀 Starting CryptoBinChecker.cc Backend API...
echo echo 🌐 API will be available at: http://localhost:8000
echo echo 📊 Health Check: http://localhost:8000/health
echo echo 📖 API Docs: http://localhost:8000/docs
echo echo.
echo python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
echo pause
) > "%PROJECT_DIR%start_api.bat"

(
echo @echo off
echo cd /d "%PROJECT_DIR%"
echo call "%VENV_PATH%\Scripts\activate.bat"
echo echo 🤖 Starting CryptoBinChecker.cc Telegram Bot...
echo echo Make sure to set your TELEGRAM_BOT_TOKEN environment variable
echo echo.
echo if "%TELEGRAM_BOT_TOKEN%"=="" (
echo     echo ❌ TELEGRAM_BOT_TOKEN environment variable not set
echo     echo Please set it with: set TELEGRAM_BOT_TOKEN=your_token_here
echo     pause
echo     exit /b 1
echo ^)
echo python telegram_bot.py
echo pause
) > "%PROJECT_DIR%start_telegram_bot.bat"

(
echo @echo off
echo cd /d "%PROJECT_DIR%"
echo call "%VENV_PATH%\Scripts\activate.bat"
echo echo 📊 CryptoBinChecker.cc System Status
echo echo =====================================
echo python system_status.py
echo pause
) > "%PROJECT_DIR%check_status.bat"

(
echo @echo off
echo echo 🚀 CryptoBinChecker.cc - Starting All Services
echo echo =============================================
echo.
echo Starting API server...
echo start "CryptoBinChecker API" cmd /k "%PROJECT_DIR%start_api.bat"
echo.
echo Waiting for API to start...
echo timeout /t 5 /nobreak >nul
echo.
echo Starting Telegram Bot...
echo start "CryptoBinChecker Telegram Bot" cmd /k "%PROJECT_DIR%start_telegram_bot.bat"
echo.
echo Waiting for services to initialize...
echo timeout /t 10 /nobreak >nul
echo.
echo Opening system status...
echo start "System Status" cmd /k "%PROJECT_DIR%check_status.bat"
echo.
echo Opening browser...
echo timeout /t 3 /nobreak >nul
echo start http://localhost:8000/docs
echo.
echo ✅ All services started!
echo Press any key to exit...
echo pause >nul
) > "%PROJECT_DIR%start_all.bat"

echo ✅ Startup scripts created

REM Test API import
echo 🧪 Testing API imports...
python -c "from app.models import User, Subscription, BinData; print('✅ Models imported successfully')"

if %ERRORLEVEL% neq 0 (
    echo ❌ API import test failed
    pause
    exit /b 1
)

python -c "from app.routes import bins, cards, crypto, webhooks, health, auth; print('✅ Routes imported successfully')"

if %ERRORLEVEL% neq 0 (
    echo ❌ Routes import test failed
    pause
    exit /b 1
)

echo ✅ API imports successful

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env configuration file...
    
    (
    echo # CryptoBinChecker.cc Configuration
    echo # Generated on %date% %time%
    echo.
    echo # Environment
    echo DEBUG=true
    echo ENVIRONMENT=development
    echo.
    echo # Database
    echo DATABASE_URL=sqlite:///./bin_search.db
    echo.
    echo # JWT Configuration
    echo JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production-12345678901234567890
    echo JWT_REFRESH_SECRET_KEY=dev-jwt-refresh-secret-change-in-production-12345678901234567890
    echo.
    echo # CORS
    echo ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000
    echo.
    echo # External APIs ^(Optional^)
    echo # ETHERSCAN_API_KEY=your-etherscan-api-key
    echo # BLOCKFROST_API_KEY=your-blockfrost-api-key
    echo.
    echo # Payment Providers ^(Optional^)
    echo # NOWPAYMENTS_API_KEY=your-nowpayments-api-key
    echo # NOWPAYMENTS_IPN_SECRET=your-nowpayments-ipn-secret
    echo # COINBASE_API_KEY=your-coinbase-commerce-api-key
    echo # COINBASE_WEBHOOK_SECRET=your-coinbase-webhook-secret
    echo.
    echo # Telegram Bot ^(Required for Telegram functionality^)
    echo # TELEGRAM_BOT_TOKEN=your-telegram-bot-token
    echo.
    echo # Redis ^(Optional - for caching^)
    echo # REDIS_URL=redis://localhost:6379
    ) > ".env"
    
    echo ✅ .env configuration file created
    echo ⚠️ Please edit .env file to add your API keys and tokens
)

cd /d "%PROJECT_DIR%"

echo.
echo 🎉 Enhanced Deployment Completed Successfully!
echo ============================================
echo.
echo 📋 Available Commands:
echo   start_all.bat           - Start all services
echo   start_api.bat          - Start API server only
echo   start_telegram_bot.bat - Start Telegram bot only  
echo   check_status.bat       - Check system status
echo.
echo 🌐 URLs:
echo   API Docs:     http://localhost:8000/docs
echo   Health Check: http://localhost:8000/health
echo   Detailed Status: http://localhost:8000/api/v1/health/detailed
echo.
echo 📝 Next Steps:
echo   1. Edit .env file with your API keys
echo   2. Set TELEGRAM_BOT_TOKEN environment variable
echo   3. Run start_all.bat to start all services
echo   4. Visit http://localhost:8000/docs to test API
echo.
echo Press any key to continue...
pause >nul