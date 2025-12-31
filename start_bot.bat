@echo off
REM Start BIN Search Bot - Windows

echo Starting BIN Search Bot...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "data\merged_bin_data.csv" (
    echo Error: BIN data file not found at data\merged_bin_data.csv
    pause
    exit /b 1
)

if not exist ".env" (
    echo Warning: .env file not found. Using default configuration.
    echo Please create .env file from .env.example for production use.
    echo.
)

REM Install dependencies if needed
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Start the bot
echo.
echo Starting Telegram Bot...
echo Bot will run in the background. Press Ctrl+C to stop.
echo.

python run_bot.py

pause