@echo off
echo Starting CryptoBinChecker Backend...
cd /d "%~dp0"

REM Activate virtual environment
call .venv-1\Scripts\activate.bat

REM Go to backend directory
cd webapp\backend

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the server
echo Starting FastAPI server on http://localhost:8000
echo API documentation will be at http://localhost:8000/docs
echo Using simplified main application
uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload

pause
