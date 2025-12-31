# Start BIN Search Pro Server
Write-Host "🚀 Starting BIN Search Pro Server..." -ForegroundColor Cyan

# Kill any existing processes on port 8000
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2

# Navigate to backend directory
Set-Location "d:\mergebins\webapp\backend"

# Start server in background
$job = Start-Job -ScriptBlock {
    Set-Location "d:\mergebins\webapp\backend"
    & "D:/mergebins/.venv-1/Scripts/python.exe" main.py
}

Write-Host "✅ Server starting... Job ID: $($job.Id)" -ForegroundColor Green
Write-Host "⏳ Waiting for server to initialize..." -ForegroundColor Yellow

# Wait for server to start
Start-Sleep 5

# Test if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ Server is running! Status: $($response.StatusCode)" -ForegroundColor Green
    
    # Now run security tests
    Write-Host "`n🔒 Running Security Tests..." -ForegroundColor Cyan
    & ".\security-test.ps1"
    
} catch {
    Write-Host "❌ Server failed to start: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "📋 Job output:" -ForegroundColor Yellow
    Receive-Job $job
}

# Clean up
Write-Host "`n🧹 Cleaning up..." -ForegroundColor Yellow
Stop-Job $job -ErrorAction SilentlyContinue
Remove-Job $job -ErrorAction SilentlyContinue