# Windows PowerShell Script for BIN Search Bot Management
# Usage: .\start_bot.ps1

param(
    [string]$Action = "start"
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Stop-BotProcesses {
    Write-ColorOutput "[STOP] Stopping any running bot processes..." "Yellow"
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -eq "python" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
}

function Test-BotHealth {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 5 -ErrorAction Stop
        Write-ColorOutput "[OK] Bot is healthy: $($response.status)" "Green"
        return $true
    } catch {
        Write-ColorOutput "[ERROR] Bot health check failed" "Red"
        return $false
    }
}

function Start-Bot {
    Write-ColorOutput "[START] BIN Search Bot - Windows Launcher" "Green"
    Write-ColorOutput "=========================================" "Green"

    # Stop any existing processes
    Stop-BotProcesses

    # Check if virtual environment exists
    if (Test-Path ".venv-1") {
        Write-ColorOutput "[OK] Virtual environment found" "Green"
    } else {
        Write-ColorOutput "[SETUP] Creating virtual environment..." "Yellow"
        python -m venv .venv-1
    }

    # Activate virtual environment
    & .\.venv-1\Scripts\Activate.ps1

    # Install/upgrade dependencies
    Write-ColorOutput "[DEPS] Installing dependencies..." "Blue"
    pip install --upgrade pip | Out-Null
    pip install python-telegram-bot aiohttp python-dotenv requests PyJWT | Out-Null

    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-ColorOutput "[ERROR] .env file not found! Please create one with your bot token." "Red"
        exit 1
    }

    # Display bot information
    Write-ColorOutput ""
    Write-ColorOutput "[CONFIG] Bot Configuration:" "Cyan"
    Write-ColorOutput "  • Bot Username: @Cryptobinchecker_ccbot" "White"
    Write-ColorOutput "  • Web Platform: https://5e336a94.bin-search-pro.pages.dev" "White"
    Write-ColorOutput "  • Health Check: http://localhost:8001/health" "White"
    Write-ColorOutput ""

    # Start the bot
    Write-ColorOutput "[RUN] Starting bot..." "Green"
    Write-ColorOutput "[INFO] Press Ctrl+C to stop the bot" "Yellow"
    Write-ColorOutput ""

    try {
        # Start bot directly
        python run_windows_bot.py
            
    } catch {
        Write-ColorOutput "[ERROR] Bot failed to start: $_" "Red"
    }
    
    Write-ColorOutput "[EXIT] Bot launcher stopped" "Yellow"
}

function Show-Status {
    Write-ColorOutput "[STATUS] Bot Status Check" "Cyan"
    Write-ColorOutput "========================" "Cyan"
    
    if (Test-BotHealth) {
        Write-ColorOutput "[RUNNING] Bot is running and healthy" "Green"
    } else {
        Write-ColorOutput "[STOPPED] Bot is not running or unhealthy" "Red"
    }
}

function Stop-Bot {
    Write-ColorOutput "[STOP] Stopping bot..." "Yellow"
    Stop-BotProcesses
    Write-ColorOutput "[OK] Bot stopped" "Green"
}

# Main script logic
switch ($Action.ToLower()) {
    "start" { Start-Bot }
    "stop" { Stop-Bot }
    "status" { Show-Status }
    "restart" { 
        Stop-Bot
        Start-Sleep 3
        Start-Bot
    }
    default {
        Write-ColorOutput "Usage: .\start_bot.ps1 [start|stop|status|restart]" "Yellow"
        Write-ColorOutput "Default action is 'start'" "Gray"
    }
}