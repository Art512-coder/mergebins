@echo off
echo Starting CryptoBinChecker Frontend...
cd /d "%~dp0"

REM Go to frontend directory
cd webapp\frontend

REM Install dependencies if needed
echo Installing/updating frontend dependencies...
npm install

REM Start development server
echo Starting Vue.js development server on http://localhost:5173
npm run dev

pause
