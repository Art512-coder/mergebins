@echo off
title BIN Search Development Environment

echo.
echo ====================================
echo  Starting BIN Search Dev Environment
echo ====================================
echo.

echo [1/3] Starting Backend Server...
cd /d "C:\Users\artur\CCGBOT\mergebins\webapp\backend"
start "Backend Server" cmd /c "python -m uvicorn main_cloudflare:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Frontend Dev Server...
cd /d "C:\Users\artur\CCGBOT\mergebins\webapp\frontend"
start "Frontend Server" cmd /c "npm run dev"

timeout /t 2 /nobreak >nul

echo [3/3] Environment Ready!
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
pause >nul

echo Stopping servers...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Backend Server*" >nul 2>&1
taskkill /f /im node.exe /fi "WINDOWTITLE eq Frontend Server*" >nul 2>&1

echo Development environment stopped.
pause
