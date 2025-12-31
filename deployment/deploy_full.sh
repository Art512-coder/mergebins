#!/bin/bash
# Enhanced CryptoBinChecker.cc Deployment Script
# Supports multiple deployment targets: development, staging, production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Default values
ENVIRONMENT="development"
SKIP_TESTS=false
SKIP_BUILD=false
DEPLOY_FRONTEND=true
DEPLOY_BACKEND=true
DEPLOY_TELEGRAM=true

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Enhanced CryptoBinChecker.cc Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV    Set deployment environment (development|staging|production)
    -t, --skip-tests        Skip running tests
    -b, --skip-build        Skip build process
    --no-frontend           Skip frontend deployment
    --no-backend            Skip backend deployment
    --no-telegram           Skip telegram bot deployment
    -h, --help              Show this help message

Examples:
    $0                                          # Deploy to development
    $0 -e production                            # Deploy to production
    $0 -e staging --skip-tests                  # Deploy to staging without tests
    $0 --no-telegram                           # Deploy without telegram bot

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -b|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --no-frontend)
            DEPLOY_FRONTEND=false
            shift
            ;;
        --no-backend)
            DEPLOY_BACKEND=false
            shift
            ;;
        --no-telegram)
            DEPLOY_TELEGRAM=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    log_info "Valid environments: development, staging, production"
    exit 1
fi

log_info "Starting CryptoBinChecker.cc Enhanced Deployment"
log_info "Environment: $ENVIRONMENT"
log_info "Timestamp: $TIMESTAMP"

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check required tools
REQUIRED_TOOLS=("node" "npm" "python3" "pip" "git")
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        log_error "Required tool not found: $tool"
        exit 1
    fi
done

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/webapp/frontend/package.json" ]]; then
    log_error "Frontend package.json not found. Are you in the correct directory?"
    exit 1
fi

if [[ ! -f "$PROJECT_ROOT/webapp/backend/requirements.txt" ]]; then
    log_error "Backend requirements.txt not found. Are you in the correct directory?"
    exit 1
fi

# Create backup
log_info "Creating backup of current deployment..."
BACKUP_DIR="$PROJECT_ROOT/backups/deployment_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

if [[ -d "$PROJECT_ROOT/webapp" ]]; then
    cp -r "$PROJECT_ROOT/webapp" "$BACKUP_DIR/"
fi
if [[ -f "$PROJECT_ROOT/telegram_bot.py" ]]; then
    cp "$PROJECT_ROOT/telegram_bot.py" "$BACKUP_DIR/"
fi

log_success "Backup created at: $BACKUP_DIR"

# Environment setup
log_info "Setting up environment configuration..."

# Backend environment
BACKEND_ENV_FILE="$PROJECT_ROOT/webapp/backend/.env"
if [[ "$ENVIRONMENT" == "development" ]]; then
    cat > "$BACKEND_ENV_FILE" << EOF
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=$(openssl rand -hex 32)
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
EOF
elif [[ "$ENVIRONMENT" == "production" ]]; then
    cat > "$BACKEND_ENV_FILE" << EOF
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
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
EOF
fi

# Frontend environment
FRONTEND_ENV_FILE="$PROJECT_ROOT/webapp/frontend/.env"
if [[ "$ENVIRONMENT" == "development" ]]; then
    cat > "$FRONTEND_ENV_FILE" << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_DEBUG=true
VITE_VERSION=2.0-dev
VITE_TELEGRAM_BOT_USERNAME=cryptobinchecker_bot
EOF
elif [[ "$ENVIRONMENT" == "production" ]]; then
    cat > "$FRONTEND_ENV_FILE" << EOF
VITE_API_BASE_URL=https://api.cryptobinchecker.cc
VITE_ENVIRONMENT=production
VITE_DEBUG=false
VITE_VERSION=2.0
VITE_TELEGRAM_BOT_USERNAME=cryptobinchecker_bot
EOF
fi

log_success "Environment configuration created"

# Install dependencies
log_info "Installing dependencies..."

# Backend dependencies
cd "$PROJECT_ROOT/webapp/backend"
if [[ "$ENVIRONMENT" == "development" ]]; then
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
fi

pip install -r requirements.txt
log_success "Backend dependencies installed"

# Frontend dependencies
cd "$PROJECT_ROOT/webapp/frontend"
npm ci
log_success "Frontend dependencies installed"

# Run tests
if [[ "$SKIP_TESTS" == false ]]; then
    log_info "Running tests..."
    
    # Backend tests
    cd "$PROJECT_ROOT/webapp/backend"
    if [[ "$ENVIRONMENT" == "development" ]]; then
        source venv/bin/activate
    fi
    
    if [[ -f "pytest.ini" || -d "tests" ]]; then
        python -m pytest tests/ -v || {
            log_warning "Backend tests failed, continuing with deployment"
        }
    else
        log_warning "No backend tests found"
    fi
    
    # Frontend tests
    cd "$PROJECT_ROOT/webapp/frontend"
    if npm run test:unit 2>/dev/null; then
        log_success "Frontend tests passed"
    else
        log_warning "Frontend tests failed or not configured"
    fi
else
    log_warning "Skipping tests as requested"
fi

# Build applications
if [[ "$SKIP_BUILD" == false ]]; then
    log_info "Building applications..."
    
    # Build frontend
    if [[ "$DEPLOY_FRONTEND" == true ]]; then
        cd "$PROJECT_ROOT/webapp/frontend"
        npm run build
        log_success "Frontend built successfully"
    fi
    
    # Prepare backend
    if [[ "$DEPLOY_BACKEND" == true ]]; then
        cd "$PROJECT_ROOT/webapp/backend"
        if [[ "$ENVIRONMENT" == "development" ]]; then
            source venv/bin/activate
        fi
        
        # Database migrations
        if [[ -d "alembic" ]]; then
            alembic upgrade head
        else
            # Initialize database with our models
            python -c "
from app.database import engine, Base
from app import models
Base.metadata.create_all(bind=engine)
print('Database initialized')
"
        fi
        log_success "Backend prepared successfully"
    fi
else
    log_warning "Skipping build as requested"
fi

# Deploy components
log_info "Starting deployment process..."

# Deploy backend
if [[ "$DEPLOY_BACKEND" == true ]]; then
    log_info "Deploying backend..."
    
    cd "$PROJECT_ROOT/webapp/backend"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        source venv/bin/activate
        # Create development startup script
        cat > "$PROJECT_ROOT/start_backend_dev.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/webapp/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF
        chmod +x "$PROJECT_ROOT/start_backend_dev.sh"
        log_success "Backend development environment ready"
        
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        # Deploy to production server (systemd service)
        sudo cp "$PROJECT_ROOT/deployment/binsearchccgbot.service" /etc/systemd/system/cryptobinchecker-api.service
        sudo sed -i "s|/path/to/your/project|$PROJECT_ROOT|g" /etc/systemd/system/cryptobinchecker-api.service
        sudo systemctl daemon-reload
        sudo systemctl enable cryptobinchecker-api
        sudo systemctl restart cryptobinchecker-api
        log_success "Backend deployed to production"
    fi
fi

# Deploy frontend
if [[ "$DEPLOY_FRONTEND" == true ]]; then
    log_info "Deploying frontend..."
    
    cd "$PROJECT_ROOT/webapp/frontend"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        # Create development startup script
        cat > "$PROJECT_ROOT/start_frontend_dev.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/webapp/frontend"
npm run dev -- --host 0.0.0.0 --port 5173
EOF
        chmod +x "$PROJECT_ROOT/start_frontend_dev.sh"
        log_success "Frontend development environment ready"
        
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        # Deploy to Nginx
        if [[ -d "/var/www/cryptobinchecker.cc" ]]; then
            sudo cp -r dist/* /var/www/cryptobinchecker.cc/
            sudo chown -R www-data:www-data /var/www/cryptobinchecker.cc/
            sudo systemctl reload nginx
            log_success "Frontend deployed to production"
        else
            log_warning "Production web directory not found. Please configure Nginx manually."
        fi
    fi
fi

# Deploy telegram bot
if [[ "$DEPLOY_TELEGRAM" == true ]]; then
    log_info "Deploying Telegram bot..."
    
    cd "$PROJECT_ROOT"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        # Create development startup script
        cat > "start_telegram_dev.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
if [[ -d "webapp/backend/venv" ]]; then
    source webapp/backend/venv/bin/activate
fi
python telegram_bot.py
EOF
        chmod +x "start_telegram_dev.sh"
        log_success "Telegram bot development environment ready"
        
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        # Deploy telegram bot service
        sudo cp "$PROJECT_ROOT/deployment/telegram-bot.service" /etc/systemd/system/cryptobinchecker-telegram.service
        sudo sed -i "s|/path/to/your/project|$PROJECT_ROOT|g" /etc/systemd/system/cryptobinchecker-telegram.service
        sudo systemctl daemon-reload
        sudo systemctl enable cryptobinchecker-telegram
        sudo systemctl restart cryptobinchecker-telegram
        log_success "Telegram bot deployed to production"
    fi
fi

# Health checks
log_info "Running health checks..."

sleep 5  # Wait for services to start

if [[ "$DEPLOY_BACKEND" == true ]]; then
    if [[ "$ENVIRONMENT" == "development" ]]; then
        if curl -f http://localhost:8000/health 2>/dev/null; then
            log_success "Backend health check passed"
        else
            log_warning "Backend health check failed - service may still be starting"
        fi
    fi
fi

if [[ "$DEPLOY_FRONTEND" == true ]] && [[ "$ENVIRONMENT" == "development" ]]; then
    if curl -f http://localhost:5173 2>/dev/null; then
        log_success "Frontend health check passed"
    else
        log_warning "Frontend health check failed - service may still be starting"
    fi
fi

# Final status report
log_info "Deployment Summary:"
log_info "==================="
log_info "Environment: $ENVIRONMENT"
log_info "Components deployed:"
[[ "$DEPLOY_BACKEND" == true ]] && log_info "  ✅ Backend API"
[[ "$DEPLOY_FRONTEND" == true ]] && log_info "  ✅ Frontend Web App"
[[ "$DEPLOY_TELEGRAM" == true ]] && log_info "  ✅ Telegram Bot"

if [[ "$ENVIRONMENT" == "development" ]]; then
    log_info ""
    log_info "Development URLs:"
    [[ "$DEPLOY_FRONTEND" == true ]] && log_info "  Frontend: http://localhost:5173"
    [[ "$DEPLOY_BACKEND" == true ]] && log_info "  Backend:  http://localhost:8000"
    [[ "$DEPLOY_BACKEND" == true ]] && log_info "  API Docs: http://localhost:8000/docs"
    
    log_info ""
    log_info "Quick Start Commands:"
    [[ "$DEPLOY_BACKEND" == true ]] && log_info "  Backend:  ./start_backend_dev.sh"
    [[ "$DEPLOY_FRONTEND" == true ]] && log_info "  Frontend: ./start_frontend_dev.sh"
    [[ "$DEPLOY_TELEGRAM" == true ]] && log_info "  Telegram: ./start_telegram_dev.sh"
    
elif [[ "$ENVIRONMENT" == "production" ]]; then
    log_info ""
    log_info "Production URLs:"
    log_info "  Website: https://cryptobinchecker.cc"
    log_info "  API:     https://api.cryptobinchecker.cc"
    
    log_info ""
    log_info "Service Management:"
    [[ "$DEPLOY_BACKEND" == true ]] && log_info "  Backend:  sudo systemctl status cryptobinchecker-api"
    [[ "$DEPLOY_TELEGRAM" == true ]] && log_info "  Telegram: sudo systemctl status cryptobinchecker-telegram"
fi

log_info ""
log_info "Next Steps:"
log_info "1. Update API keys in .env files"
log_info "2. Configure payment webhooks"
log_info "3. Set up monitoring and alerts"
log_info "4. Configure SSL certificates (production)"
log_info "5. Test all features thoroughly"

log_success "Enhanced CryptoBinChecker.cc deployment completed!"
log_info "Backup available at: $BACKUP_DIR"
log_info "Deployment completed at: $(date)"