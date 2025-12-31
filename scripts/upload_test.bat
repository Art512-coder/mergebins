@echo off
echo 🚀 Starting D1 batch upload...
echo 📦 Uploading batches 4-20 to test process

for /L %%i in (4,1,20) do (
    echo 📤 Uploading batch %%i...
    wrangler d1 execute bin-search-db --file=migrations/batch_00%%i.sql
    if errorlevel 1 (
        echo ❌ Batch %%i failed
        pause
        exit /b 1
    ) else (
        echo ✅ Batch %%i uploaded successfully
    )
    timeout /t 1 /nobreak >nul
)

echo 🎉 Test upload completed!
echo Checking record count...
wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;"
