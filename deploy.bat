REM filepath: d:\mergebins\deploy.bat
@echo off
echo 🚀 BIN Search Pro - Production Deployment
echo.

echo ✅ Building Frontend...
cd webapp\frontend
npm run build
echo Frontend build complete!
echo.

echo ✅ Deploying Frontend...
npx wrangler pages deploy dist --project-name=bin-search-pro
echo.

echo ✅ Deploying Backend...
cd ..\..\deployment
npx wrangler deploy --name bin-search-api
echo.

echo 🎉 Deployment Complete!
echo Frontend: https://5e336a94.bin-search-pro.pages.dev
echo Backend:  https://bin-search-api.arturovillanueva1994.workers.dev
echo.
pause