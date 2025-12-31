@echo off
echo 🧪 Testing JavaScript Fixes
echo.

echo 1️⃣ Building frontend with latest fixes...
cd frontend
call npm run build

echo.
echo 2️⃣ Starting frontend preview server...
start "Frontend Preview" cmd /k "npm run preview -- --host 0.0.0.0 --port 3000"

echo.
echo 3️⃣ Testing if backend can run...
cd ..\backend

REM Quick backend test
if not exist ".venv" (
    echo Creating virtual environment for backend...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install fastapi uvicorn python-dotenv

echo.
echo 4️⃣ Starting minimal backend...
start "Backend Test" cmd /k "call .venv\Scripts\activate.bat && python -c \"import uvicorn; from main import app; print('Backend starting...'); uvicorn.run(app, host='0.0.0.0', port=8000)\""

echo.
echo ✅ Test servers starting!
echo.
echo 🌐 Frontend Preview: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo.
echo 🧪 TO TEST THE JAVASCRIPT FIXES:
echo 1. Open http://localhost:3000 in your browser
echo 2. Open Developer Tools (F12)
echo 3. Go to Console tab
echo 4. Look for the previous JavaScript errors:
echo    - "currentUser already declared" ❌ Should be GONE
echo    - "openCryptoChecker not defined" ❌ Should be GONE  
echo    - "openLogin not defined" ❌ Should be GONE
echo 5. Try clicking subscription/payment buttons
echo.
echo If you still see errors, press Ctrl+F5 to hard refresh!
echo.
pause