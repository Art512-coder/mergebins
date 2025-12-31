@echo off
echo 🚀 Starting D1 batch upload...
echo 📦 Uploading first 50 batches to test the process

for /L %%i in (4,1,50) do (
    if %%i LSS 10 (
        set "batch_file=migrations/batch_000%%i.sql"
    ) else if %%i LSS 100 (
        set "batch_file=migrations/batch_00%%i.sql"
    ) else (
        set "batch_file=migrations/batch_0%%i.sql"
    )
    
    echo 📤 Uploading batch %%i...
    call wrangler d1 execute bin-search-db --file=%%batch_file%%
    
    if errorlevel 1 (
        echo ❌ Batch %%i failed
        pause
        exit /b 1
    ) else (
        echo ✅ Batch %%i uploaded successfully
    )
    
    timeout /t 1 /nobreak >nul
)

echo 🎉 First 50 batches uploaded!
echo Checking record count...
wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;"
