#!/bin/bash
"""
Enhanced Production Deployment Script for CryptoBinChecker.cc
Deploys the complete system with all new features
Version: 2.0 - November 2025
"""

set -e  # Exit on any error

echo "🚀 CryptoBinChecker.cc - Enhanced Production Deployment"
echo "======================================================"

# Configuration
PROJECT_DIR="/var/www/cryptobinchecker"
SERVICE_USER="www-data"
PYTHON_PATH="/usr/bin/python3"
NODE_PATH="/usr/bin/node"
SYSTEMCTL="sudo systemctl"
NGINX_SITES="/etc/nginx/sites-available"
BACKUP_DIR="/var/backups/cryptobinchecker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create backup
create_backup() {
    log_info "Creating backup..."
    sudo mkdir -p "$BACKUP_DIR"
    
    if [ -d "$PROJECT_DIR" ]; then
        sudo tar -czf "$BACKUP_DIR/cryptobinchecker-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$PROJECT_DIR" .
        log_success "Backup created"
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    sudo apt-get update
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        nginx \
        postgresql \
        postgresql-contrib \
        redis-server \
        supervisor \
        certbot \
        python3-certbot-nginx \
        htop \
        fail2ban
    
    log_success "System dependencies installed"
}

# Setup project directory
setup_project() {
    log_info "Setting up project directory..."
    
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    
    # Copy project files
    sudo cp -r /tmp/mergebins/* "$PROJECT_DIR/"
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    
    log_success "Project directory setup complete"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    cd "$PROJECT_DIR"
    sudo -u "$SERVICE_USER" python3 -m venv venv
    sudo -u "$SERVICE_USER" ./venv/bin/pip install --upgrade pip
    sudo -u "$SERVICE_USER" ./venv/bin/pip install -r requirements.txt
    
    log_success "Python environment ready"
}

# Setup Node.js environment  
setup_node_env() {
    log_info "Setting up Node.js environment..."
    
    cd "$PROJECT_DIR/webapp/frontend"
    sudo -u "$SERVICE_USER" npm install
    sudo -u "$SERVICE_USER" npm run build
    
    log_success "Frontend built successfully"
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    # Create PostgreSQL database and user
    sudo -u postgres psql -c "CREATE DATABASE cryptobinchecker;"
    sudo -u postgres psql -c "CREATE USER ccg_user WITH PASSWORD 'secure_password_here';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cryptobinchecker TO ccg_user;"
    
    # Run database migrations
    cd "$PROJECT_DIR/webapp/backend"
    sudo -u "$SERVICE_USER" ../../venv/bin/python init_db.py
    
    # Import BIN data if available
    if [ -f "$PROJECT_DIR/data/merged_bin_data.csv" ]; then
        sudo -u "$SERVICE_USER" ../../venv/bin/python populate_bin_data.py
        log_success "BIN data imported"
    fi
    
    log_success "Database setup complete"
}

# Setup systemd services
setup_services() {
    log_info "Setting up systemd services..."
    
    # FastAPI Backend Service
    sudo tee /etc/systemd/system/cryptobinchecker-api.service > /dev/null << EOF
[Unit]
Description=CryptoBinChecker FastAPI Backend
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR/webapp/backend
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=DATABASE_URL=postgresql://ccg_user:secure_password_here@localhost/cryptobinchecker
Environment=REDIS_URL=redis://localhost:6379
Environment=DEBUG=false
Environment=ENVIRONMENT=production
ExecStart=$PROJECT_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Telegram Bot Service
    sudo tee /etc/systemd/system/cryptobinchecker-telegram.service > /dev/null << EOF
[Unit]
Description=CryptoBinChecker Telegram Bot
After=network.target cryptobinchecker-api.service
Wants=cryptobinchecker-api.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
Environment=API_BASE_URL=http://localhost:8000/api/v1
ExecStart=$PROJECT_DIR/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # System Monitoring Service
    sudo tee /etc/systemd/system/cryptobinchecker-monitor.service > /dev/null << EOF
[Unit]
Description=CryptoBinChecker System Monitor
After=network.target cryptobinchecker-api.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python -c "
import time
import requests
import logging
from system_status import StatusDashboard

logging.basicConfig(level=logging.INFO)
dashboard = StatusDashboard()

while True:
    try:
        report = dashboard.generate_report()
        if report['overall_status'] != 'healthy':
            logging.warning(f'System unhealthy: {report}')
        time.sleep(300)  # Check every 5 minutes
    except Exception as e:
        logging.error(f'Monitor error: {e}')
        time.sleep(60)
"
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    log_success "Systemd services configured"
}

# Setup Nginx
setup_nginx() {
    log_info "Setting up Nginx..."
    
    sudo tee "$NGINX_SITES/cryptobinchecker.cc" > /dev/null << 'EOF'
server {
    listen 80;
    server_name cryptobinchecker.cc www.cryptobinchecker.cc;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=60r/m;
    
    # Frontend (Vue.js build)
    location / {
        root /var/www/cryptobinchecker/webapp/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API routes
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        limit_req zone=general burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Block sensitive files
    location ~ /\.(env|git|htaccess) {
        deny all;
        return 404;
    }
    
    # Logs
    access_log /var/log/nginx/cryptobinchecker.access.log;
    error_log /var/log/nginx/cryptobinchecker.error.log;
}
EOF

    sudo ln -sf "$NGINX_SITES/cryptobinchecker.cc" /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx
    
    log_success "Nginx configured"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    sudo certbot --nginx -d cryptobinchecker.cc -d www.cryptobinchecker.cc --non-interactive --agree-tos --email admin@cryptobinchecker.cc
    
    # Setup auto-renewal
    sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
    
    log_success "SSL certificates configured"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    sudo systemctl enable redis-server postgresql nginx
    sudo systemctl start redis-server postgresql nginx
    
    sudo systemctl enable cryptobinchecker-api cryptobinchecker-telegram cryptobinchecker-monitor
    sudo systemctl start cryptobinchecker-api
    sleep 5  # Wait for API to be ready
    sudo systemctl start cryptobinchecker-telegram
    sudo systemctl start cryptobinchecker-monitor
    
    log_success "All services started"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check services
    services=("cryptobinchecker-api" "cryptobinchecker-telegram" "cryptobinchecker-monitor" "nginx" "postgresql" "redis-server")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            sudo systemctl status "$service"
        fi
    done
    
    # Test API endpoints
    sleep 10  # Allow services to fully start
    
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
    fi
    
    # Check system status
    cd "$PROJECT_DIR"
    sudo -u "$SERVICE_USER" ./venv/bin/python system_status.py
}

# Main deployment function
main() {
    log_info "Starting CryptoBinChecker.cc deployment..."
    
    create_backup
    install_dependencies
    setup_project
    setup_python_env
    setup_node_env
    setup_database
    setup_services
    setup_nginx
    setup_ssl
    start_services
    verify_deployment
    
    log_success "🎉 Deployment completed successfully!"
    log_info "🌐 Website: https://cryptobinchecker.cc"
    log_info "📊 Status: https://cryptobinchecker.cc/api/v1/health/detailed"
    log_info "🤖 Telegram: @YourBotUsername"
    
    echo
    echo "📋 Next Steps:"
    echo "1. Update environment variables in service files"
    echo "2. Configure your Telegram bot token"
    echo "3. Set up payment provider API keys"
    echo "4. Configure monitoring alerts"
    echo "5. Import your BIN database"
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"