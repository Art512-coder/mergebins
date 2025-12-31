# Windows Bot Management Commands
# Simple batch file for Windows users

@echo off
echo 🚀 BIN Search Bot - Windows Management
echo =====================================

if "%1"=="start" goto start
if "%1"=="stop" goto stop  
if "%1"=="status" goto status
if "%1"=="health" goto health
if "%1"=="logs" goto logs
if "%1"=="install" goto install

:help
echo Usage: bot.bat [command]
echo.
echo Commands:
echo   start   - Start the bot
echo   stop    - Stop the bot (Ctrl+C)
echo   status  - Show bot status
echo   health  - Check health endpoint
echo   logs    - Show recent logs
echo   install - Install dependencies
echo.
goto end

:install
echo 📦 Installing dependencies...
if not exist ".venv-1" (
    python -m venv .venv-1
)
call .venv-1\Scripts\activate.bat
pip install --upgrade pip
pip install python-telegram-bot aiohttp python-dotenv requests PyJWT
echo ✅ Dependencies installed
goto end

:start
echo 🤖 Starting BIN Search Bot...
if not exist ".venv-1" (
    echo ⚠️ Virtual environment not found. Run: bot.bat install
    goto end
)
call .venv-1\Scripts\activate.bat
python run_windows_bot.py
goto end

:status
echo 📊 Bot Status Check...
curl -s http://localhost:8001/health 2>nul || echo ❌ Bot not running or health endpoint unavailable
goto end

:health
echo 🏥 Health Check...
curl http://localhost:8001/health
goto end

:logs
echo 📝 Recent logs...
if exist "logs\bot.log" (
    powershell "Get-Content logs\bot.log -Tail 20"
) else (
    echo No log file found
)
goto end

:stop
echo ⚠️ To stop the bot, press Ctrl+C in the bot window
goto end

:end