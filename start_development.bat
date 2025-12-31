@echo off
REM Quick Development Start Script for CryptoBinChecker.cc Enhanced Version
REM This script starts all components for local development

echo ========================================
echo CryptoBinChecker.cc Development Startup
echo Enhanced Version 2.0
echo ========================================

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv-1\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv-1
)

REM Check if deployment was done
if not exist "webapp\backend\.env" (
    echo [WARNING] Environment files not configured properly
    echo Please ensure .env files are set up
)

echo [INFO] Starting all services...

REM Start Backend API
echo [INFO] Starting Backend API on port 8000...
start "Backend API" cmd /k "cd webapp\backend && call ..\..\..venv-1\Scripts\activate.bat && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start Frontend
echo [INFO] Starting Frontend on port 5173...
start "Frontend" cmd /k "cd webapp\frontend && npm run dev -- --host 0.0.0.0 --port 5173"

REM Start Telegram Bot
echo [INFO] Starting Telegram Bot...
start "Telegram Bot" cmd /k "call .venv-1\Scripts\activate.bat && python telegram_bot.py"

REM Wait a moment for services to start
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Services Started Successfully!
echo ========================================
echo.
echo Frontend:      http://localhost:5173
echo Backend API:   http://localhost:8000
echo API Docs:      http://localhost:8000/docs
echo.
echo All services are running in separate windows.
echo Close those windows to stop the services.
echo.
echo To configure API keys, edit:
echo   - webapp\backend\.env
echo   - webapp\frontend\.env
echo.

REM Try to open browser
echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo [SUCCESS] CryptoBinChecker.cc is now running!
echo Press any key to exit this window...
pause >nul