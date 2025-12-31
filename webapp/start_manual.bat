@echo off
echo 🚀 Starting BIN Search Web Application (Manual Mode)
echo.

REM Check if Python virtual environment exists
if not exist "backend\.venv" (
    echo 📦 Creating Python virtual environment...
    cd backend
    python -m venv .venv
    cd ..
)

REM Activate virtual environment and install dependencies
echo 📥 Installing backend dependencies...
cd backend
call .venv\Scripts\activate.bat
pip install -r requirements.txt

REM Check if BIN data file exists
if not exist "merged_bin_data.csv" (
    if exist "..\merged_bin_data.csv" (
        echo 📊 Copying BIN data file...
        copy "..\merged_bin_data.csv" "merged_bin_data.csv"
    ) else (
        echo ❌ Warning: BIN data file not found. Some features may not work.
    )
)

echo 🔧 Starting backend server...
start "Backend Server" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

cd ..\frontend

REM Install frontend dependencies if needed
if not exist "node_modules" (
    echo 📥 Installing frontend dependencies...
    npm install
)

echo 🎨 Starting frontend development server...
start "Frontend Server" cmd /k "npm run dev -- --host 0.0.0.0 --port 3000"

echo.
echo ✅ Both servers are starting up!
echo.
echo 📍 Access Points:
echo    🌐 Frontend: http://localhost:3000
echo    🔧 Backend API: http://localhost:8000
echo    📖 API Docs: http://localhost:8000/docs
echo.
echo ⏳ Please wait 30-60 seconds for both servers to fully start...
echo.
echo 💡 To stop the servers:
echo    - Close both command windows that opened
echo    - Or press Ctrl+C in each window
echo.
pause