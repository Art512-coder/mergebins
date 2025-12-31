@echo off
echo 🚀 Starting BIN Search Web Application
echo.

echo 📍 Current Directory: %cd%
echo.

echo 🔍 Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo.
    echo ❌ Python not found! 
    echo 📦 Please install Python from Microsoft Store first
    echo � Search "Python 3.12" in Microsoft Store
    echo.
    pause
    exit /b 1
)

echo.
echo 📦 Installing/updating dependencies...
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn python-multipart python-jose[cryptography] passlib[bcrypt] sqlalchemy python-dotenv aiofiles requests aiohttp coinbase-commerce
if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo 🔧 Setting up environment...
cd webapp\backend
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
)

echo.
echo 🎯 Starting FastAPI server...
echo 📝 API docs will be at: http://localhost:8000/docs
echo 🛑 Press Ctrl+C to stop the server
echo.

python main.py
