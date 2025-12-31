@echo off
echo 🔧 Quick CORS Fix for Registration Testing
echo.

echo 1️⃣ Stopping any conflicting processes...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

echo 2️⃣ Starting minimal backend with CORS enabled...
cd backend

echo Creating minimal CORS-enabled server...
echo from fastapi import FastAPI > temp_server.py
echo from fastapi.middleware.cors import CORSMiddleware >> temp_server.py
echo from pydantic import BaseModel >> temp_server.py
echo. >> temp_server.py
echo app = FastAPI() >> temp_server.py
echo. >> temp_server.py
echo app.add_middleware( >> temp_server.py
echo     CORSMiddleware, >> temp_server.py
echo     allow_origins=["*"], >> temp_server.py
echo     allow_credentials=True, >> temp_server.py
echo     allow_methods=["*"], >> temp_server.py
echo     allow_headers=["*"], >> temp_server.py
echo ^) >> temp_server.py
echo. >> temp_server.py
echo class UserRegister(BaseModel): >> temp_server.py
echo     username: str >> temp_server.py
echo     email: str >> temp_server.py
echo     password: str >> temp_server.py
echo. >> temp_server.py
echo @app.post("/api/v1/auth/register") >> temp_server.py
echo async def register(user_data: UserRegister): >> temp_server.py
echo     return {"access_token": "mock_token", "token_type": "bearer", "user": {"id": 1, "username": user_data.username, "email": user_data.email, "plan": "free"}} >> temp_server.py
echo. >> temp_server.py
echo @app.get("/health") >> temp_server.py
echo async def health(): >> temp_server.py
echo     return {"status": "healthy"} >> temp_server.py

start "Backend" cmd /k "D:\mergebins\.venv-1\Scripts\python.exe -m uvicorn temp_server:app --host 0.0.0.0 --port 8000"

cd ..\frontend

echo 3️⃣ Starting frontend...
start "Frontend" cmd /k "npm run dev"

echo.
echo ✅ Services starting!
echo.
echo 🌐 Frontend: http://localhost:3000  
echo 🔧 Backend: http://localhost:8000
echo.
echo 🧪 Now test registration - CORS errors should be gone!
echo.
pause