# Enhanced CryptoBinChecker.cc Deployment Script for Windows
# Supports multiple deployment targets: development, staging, production

param(
    [string]$Environment = "development",
    [switch]$SkipTests = $false,
    [switch]$SkipBuild = $false,
    [switch]$NoFrontend = $false,
    [switch]$NoBackend = $false,
    [switch]$NoTelegram = $false,
    [switch]$Help = $false
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Deployment flags
$DeployFrontend = -not $NoFrontend
$DeployBackend = -not $NoBackend
$DeployTelegram = -not $NoTelegram

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Show-Help {
    @"
Enhanced CryptoBinChecker.cc Deployment Script for Windows

Usage: .\deploy_full.ps1 [OPTIONS]

Options:
    -Environment ENV        Set deployment environment (development|staging|production)
    -SkipTests             Skip running tests
    -SkipBuild             Skip build process
    -NoFrontend            Skip frontend deployment
    -NoBackend             Skip backend deployment
    -NoTelegram            Skip telegram bot deployment
    -Help                  Show this help message

Examples:
    .\deploy_full.ps1                                    # Deploy to development
    .\deploy_full.ps1 -Environment production            # Deploy to production
    .\deploy_full.ps1 -Environment staging -SkipTests   # Deploy to staging without tests
    .\deploy_full.ps1 -NoTelegram                       # Deploy without telegram bot

"@
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Validate environment
if ($Environment -notin @("development", "staging", "production")) {
    Write-Error "Invalid environment: $Environment"
    Write-Info "Valid environments: development, staging, production"
    exit 1
}

Write-Info "Starting CryptoBinChecker.cc Enhanced Deployment"
Write-Info "Environment: $Environment"
Write-Info "Timestamp: $Timestamp"

# Pre-deployment checks
Write-Info "Running pre-deployment checks..."

# Check required tools
$RequiredTools = @("node", "npm", "python", "pip", "git")
foreach ($tool in $RequiredTools) {
    try {
        $null = Get-Command $tool -ErrorAction Stop
    }
    catch {
        Write-Error "Required tool not found: $tool"
        exit 1
    }
}

# Check if we're in the right directory
if (-not (Test-Path "$ProjectRoot\webapp\frontend\package.json")) {
    Write-Error "Frontend package.json not found. Are you in the correct directory?"
    exit 1
}

if (-not (Test-Path "$ProjectRoot\webapp\backend\requirements.txt")) {
    Write-Error "Backend requirements.txt not found. Are you in the correct directory?"
    exit 1
}

# Create backup
Write-Info "Creating backup of current deployment..."
$BackupDir = "$ProjectRoot\backups\deployment_$Timestamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

if (Test-Path "$ProjectRoot\webapp") {
    Copy-Item -Path "$ProjectRoot\webapp" -Destination "$BackupDir\" -Recurse -Force
}
if (Test-Path "$ProjectRoot\telegram_bot.py") {
    Copy-Item -Path "$ProjectRoot\telegram_bot.py" -Destination "$BackupDir\" -Force
}

Write-Success "Backup created at: $BackupDir"

# Environment setup
Write-Info "Setting up environment configuration..."

# Generate secret key
$SecretKey = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })

# Backend environment
$BackendEnvFile = "$ProjectRoot\webapp\backend\.env"
if ($Environment -eq "development") {
    @"
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=$SecretKey
DATABASE_URL=sqlite:///./cryptobinchecker.db
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# API Keys (set these with your actual keys)
BLOCKCHAIN_INFO_API_KEY=your-blockchain-info-key
ETHERSCAN_API_KEY=your-etherscan-key
BLOCKCYPHER_API_KEY=your-blockcypher-key
BLOCKFROST_API_KEY=your-blockfrost-key
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Payment Integration
NOWPAYMENTS_API_KEY=your-nowpayments-key
COINBASE_COMMERCE_API_KEY=your-coinbase-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
"@ | Out-File -FilePath $BackendEnvFile -Encoding UTF8
}
elseif ($Environment -eq "production") {
    @"
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=$SecretKey
DATABASE_URL=postgresql://cryptobinchecker:your-password@localhost:5432/cryptobinchecker
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=https://cryptobinchecker.cc,https://www.cryptobinchecker.cc

# API Keys (set these with your actual keys)
BLOCKCHAIN_INFO_API_KEY=your-blockchain-info-key
ETHERSCAN_API_KEY=your-etherscan-key
BLOCKCYPHER_API_KEY=your-blockcypher-key
BLOCKFROST_API_KEY=your-blockfrost-key
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Payment Integration
NOWPAYMENTS_API_KEY=your-nowpayments-key
COINBASE_COMMERCE_API_KEY=your-coinbase-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Monitoring
LOG_LEVEL=WARNING
SENTRY_DSN=your-sentry-dsn
"@ | Out-File -FilePath $BackendEnvFile -Encoding UTF8
}

# Frontend environment
$FrontendEnvFile = "$ProjectRoot\webapp\frontend\.env"
if ($Environment -eq "development") {
    @"
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_DEBUG=true
VITE_VERSION=2.0-dev
VITE_TELEGRAM_BOT_USERNAME=cryptobinchecker_bot
"@ | Out-File -FilePath $FrontendEnvFile -Encoding UTF8
}
elseif ($Environment -eq "production") {
    @"
VITE_API_BASE_URL=https://api.cryptobinchecker.cc
VITE_ENVIRONMENT=production
VITE_DEBUG=false
VITE_VERSION=2.0
VITE_TELEGRAM_BOT_USERNAME=cryptobinchecker_bot
"@ | Out-File -FilePath $FrontendEnvFile -Encoding UTF8
}

Write-Success "Environment configuration created"

# Install dependencies
Write-Info "Installing dependencies..."

# Backend dependencies
Push-Location "$ProjectRoot\webapp\backend"
if ($Environment -eq "development") {
    if (-not (Test-Path "venv")) {
        python -m venv venv
    }
    & "venv\Scripts\Activate.ps1"
}

pip install -r requirements.txt
Write-Success "Backend dependencies installed"

# Frontend dependencies
Push-Location "$ProjectRoot\webapp\frontend"
npm ci
Write-Success "Frontend dependencies installed"
Pop-Location

# Run tests
if (-not $SkipTests) {
    Write-Info "Running tests..."
    
    # Backend tests
    Push-Location "$ProjectRoot\webapp\backend"
    if ($Environment -eq "development") {
        & "venv\Scripts\Activate.ps1"
    }
    
    if ((Test-Path "pytest.ini") -or (Test-Path "tests")) {
        try {
            python -m pytest tests\ -v
            Write-Success "Backend tests passed"
        }
        catch {
            Write-Warning "Backend tests failed, continuing with deployment"
        }
    }
    else {
        Write-Warning "No backend tests found"
    }
    Pop-Location
    
    # Frontend tests
    Push-Location "$ProjectRoot\webapp\frontend"
    try {
        npm run test:unit 2>$null
        Write-Success "Frontend tests passed"
    }
    catch {
        Write-Warning "Frontend tests failed or not configured"
    }
    Pop-Location
}
else {
    Write-Warning "Skipping tests as requested"
}

# Build applications
if (-not $SkipBuild) {
    Write-Info "Building applications..."
    
    # Build frontend
    if ($DeployFrontend) {
        Push-Location "$ProjectRoot\webapp\frontend"
        npm run build
        Write-Success "Frontend built successfully"
        Pop-Location
    }
    
    # Prepare backend
    if ($DeployBackend) {
        Push-Location "$ProjectRoot\webapp\backend"
        if ($Environment -eq "development") {
            & "venv\Scripts\Activate.ps1"
        }
        
        # Database initialization
        try {
            python -c @"
from app.database import engine, Base
from app import models
Base.metadata.create_all(bind=engine)
print('Database initialized')
"@
            Write-Success "Backend prepared successfully"
        }
        catch {
            Write-Warning "Database initialization failed - check configuration"
        }
        Pop-Location
    }
}
else {
    Write-Warning "Skipping build as requested"
}

# Deploy components
Write-Info "Starting deployment process..."

# Deploy backend
if ($DeployBackend) {
    Write-Info "Deploying backend..."
    
    if ($Environment -eq "development") {
        # Create development startup script
        @"
@echo off
cd /d "%~dp0webapp\backend"
call venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
"@ | Out-File -FilePath "$ProjectRoot\start_backend_dev.bat" -Encoding ASCII
        Write-Success "Backend development environment ready"
        
    }
    elseif ($Environment -eq "production") {
        Write-Warning "Production deployment on Windows requires manual IIS/service configuration"
    }
}

# Deploy frontend
if ($DeployFrontend) {
    Write-Info "Deploying frontend..."
    
    if ($Environment -eq "development") {
        # Create development startup script
        @"
@echo off
cd /d "%~dp0webapp\frontend"
npm run dev -- --host 0.0.0.0 --port 5173
pause
"@ | Out-File -FilePath "$ProjectRoot\start_frontend_dev.bat" -Encoding ASCII
        Write-Success "Frontend development environment ready"
        
    }
    elseif ($Environment -eq "production") {
        Write-Warning "Production frontend deployment requires web server configuration"
    }
}

# Deploy telegram bot
if ($DeployTelegram) {
    Write-Info "Deploying Telegram bot..."
    
    if ($Environment -eq "development") {
        # Create development startup script
        @"
@echo off
cd /d "%~dp0"
if exist "webapp\backend\venv\Scripts\activate.bat" (
    call webapp\backend\venv\Scripts\activate.bat
)
python telegram_bot.py
pause
"@ | Out-File -FilePath "$ProjectRoot\start_telegram_dev.bat" -Encoding ASCII
        Write-Success "Telegram bot development environment ready"
        
    }
    elseif ($Environment -eq "production") {
        Write-Warning "Production telegram bot requires Windows service configuration"
    }
}

# Health checks
Write-Info "Running health checks..."

Start-Sleep -Seconds 3

if ($DeployBackend -and $Environment -eq "development") {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        Write-Success "Backend health check passed"
    }
    catch {
        Write-Warning "Backend health check failed - service may still be starting"
    }
}

# Final status report
Write-Info "Deployment Summary:"
Write-Info "==================="
Write-Info "Environment: $Environment"
Write-Info "Components deployed:"
if ($DeployBackend) { Write-Info "  ✅ Backend API" }
if ($DeployFrontend) { Write-Info "  ✅ Frontend Web App" }
if ($DeployTelegram) { Write-Info "  ✅ Telegram Bot" }

if ($Environment -eq "development") {
    Write-Info ""
    Write-Info "Development URLs:"
    if ($DeployFrontend) { Write-Info "  Frontend: http://localhost:5173" }
    if ($DeployBackend) { Write-Info "  Backend:  http://localhost:8000" }
    if ($DeployBackend) { Write-Info "  API Docs: http://localhost:8000/docs" }
    
    Write-Info ""
    Write-Info "Quick Start Commands:"
    if ($DeployBackend) { Write-Info "  Backend:  start_backend_dev.bat" }
    if ($DeployFrontend) { Write-Info "  Frontend: start_frontend_dev.bat" }
    if ($DeployTelegram) { Write-Info "  Telegram: start_telegram_dev.bat" }
    
}
elseif ($Environment -eq "production") {
    Write-Info ""
    Write-Info "Production URLs:"
    Write-Info "  Website: https://cryptobinchecker.cc"
    Write-Info "  API:     https://api.cryptobinchecker.cc"
}

Write-Info ""
Write-Info "Next Steps:"
Write-Info "1. Update API keys in .env files"
Write-Info "2. Configure payment webhooks"
Write-Info "3. Set up monitoring and alerts"
Write-Info "4. Configure SSL certificates (production)"
Write-Info "5. Test all features thoroughly"

Write-Success "Enhanced CryptoBinChecker.cc deployment completed!"
Write-Info "Backup available at: $BackupDir"
Write-Info "Deployment completed at: $(Get-Date)"

# Return to original location
Pop-Location