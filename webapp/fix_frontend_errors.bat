@echo off
echo 🔧 Fixing Frontend JavaScript Errors...
echo.

echo 📦 Step 1: Rebuilding frontend with fixes...
cd frontend
call npm run build
cd ..

echo 🐳 Step 2: Restarting Docker services...
docker-compose down
docker-compose up --build -d

echo ⏳ Step 3: Waiting for services to start...
timeout /t 15 /nobreak >nul

echo ✅ Step 4: Services should now be running without JavaScript errors!
echo.
echo 🌐 Access the application at:
echo    Frontend: http://localhost:3000
echo    Backend: http://localhost:8000
echo.
echo 💡 If you still see errors:
echo    1. Clear your browser cache (Ctrl+F5)
echo    2. Try in an incognito/private window
echo    3. Check browser developer console for any remaining errors
echo.
pause