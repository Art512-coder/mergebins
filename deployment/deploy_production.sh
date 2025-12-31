#!/bin/bash
"""
Production Deployment and Monitoring Setup Script
Deploys BIN Search Bot with comprehensive monitoring
"""

set -e  # Exit on any error

echo "🚀 BIN Search Bot - Production Deployment with Monitoring"
echo "=========================================================="

# Configuration
PROJECT_DIR="/home/ubuntu/mergebins"
SERVICE_USER="ubuntu"
PYTHON_PATH="/usr/bin/python3"
SYSTEMCTL="sudo systemctl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as correct user
    if [ "$USER" != "$SERVICE_USER" ]; then
        log_error "Please run this script as user: $SERVICE_USER"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3."
        exit 1
    fi
    
    # Check systemctl
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. This script requires systemd."
        exit 1
    fi
    
    # Check project directory
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        log_info "Installing from requirements.txt..."
        pip install -r requirements.txt
    fi
    
    # Install monitoring dependencies
    log_info "Installing monitoring dependencies..."
    pip install psutil aiohttp
    
    log_success "Python dependencies installed"
}

setup_monitoring_database() {
    log_info "Setting up monitoring database..."
    
    # Create data directory if it doesn't exist
    mkdir -p "$PROJECT_DIR/data"
    
    # Initialize monitoring database
    cd "$PROJECT_DIR"
    source venv/bin/activate
    python3 -c "
from monitoring.production_monitor import ProductionMonitor
monitor = ProductionMonitor()
print('Monitoring database initialized')
"
    
    log_success "Monitoring database setup complete"
}

configure_systemd_services() {
    log_info "Configuring systemd services..."
    
    # Copy service files
    sudo cp "$PROJECT_DIR/deployment/binsearchccgbot.service" /etc/systemd/system/
    sudo cp "$PROJECT_DIR/deployment/binsearch-monitor.service" /etc/systemd/system/
    
    # Update service files with correct paths
    sudo sed -i "s|/home/ubuntu/mergebins|$PROJECT_DIR|g" /etc/systemd/system/binsearchccgbot.service
    sudo sed -i "s|/home/ubuntu/mergebins|$PROJECT_DIR|g" /etc/systemd/system/binsearch-monitor.service
    
    # Set correct user
    sudo sed -i "s|User=ubuntu|User=$SERVICE_USER|g" /etc/systemd/system/binsearchccgbot.service
    sudo sed -i "s|User=ubuntu|User=$SERVICE_USER|g" /etc/systemd/system/binsearch-monitor.service
    sudo sed -i "s|Group=ubuntu|Group=$SERVICE_USER|g" /etc/systemd/system/binsearchccgbot.service
    sudo sed -i "s|Group=ubuntu|Group=$SERVICE_USER|g" /etc/systemd/system/binsearch-monitor.service
    
    # Reload systemd
    $SYSTEMCTL daemon-reload
    
    # Enable services
    $SYSTEMCTL enable binsearchccgbot.service
    $SYSTEMCTL enable binsearch-monitor.service
    
    log_success "Systemd services configured"
}

setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/binsearch-bot > /dev/null <<EOF
$PROJECT_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 $SERVICE_USER $SERVICE_USER
}

$PROJECT_DIR/monitoring/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 $SERVICE_USER $SERVICE_USER
}
EOF
    
    log_success "Log rotation configured"
}

check_environment_variables() {
    log_info "Checking environment variables..."
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_warning ".env file not found. Creating template..."
        cat > "$PROJECT_DIR/.env" << EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Web API Configuration
WEB_API_BASE_URL=https://bin-search-api.arturovillanueva1994.workers.dev

# Monitoring Configuration
MONITOR_INTERVAL_SECONDS=60
ALERT_COOLDOWN_MINUTES=15
MAX_RESPONSE_TIME_SECONDS=5.0
HEALTH_CHECK_PORT=8001

# Alert Configuration
ENABLE_EMAIL_ALERTS=false
ENABLE_WEBHOOK_ALERTS=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Database Configuration
DB_PATH=data/merged_bin_data.csv
EOF
        log_warning "Please update the .env file with your actual configuration"
    fi
    
    # Load environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
    fi
    
    # Check critical variables
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
        log_error "TELEGRAM_BOT_TOKEN not set in .env file"
        exit 1
    fi
    
    log_success "Environment variables checked"
}

run_health_check() {
    log_info "Running initial health check..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Run single health check
    python3 monitoring/production_monitor.py --check
    
    log_success "Initial health check completed"
}

start_services() {
    log_info "Starting services..."
    
    # Stop services if running
    $SYSTEMCTL stop binsearchccgbot.service 2>/dev/null || true
    $SYSTEMCTL stop binsearch-monitor.service 2>/dev/null || true
    
    # Start bot service
    log_info "Starting BIN Search Bot service..."
    $SYSTEMCTL start binsearchccgbot.service
    sleep 5
    
    # Check bot service status
    if $SYSTEMCTL is-active --quiet binsearchccgbot.service; then
        log_success "BIN Search Bot service started successfully"
    else
        log_error "Failed to start BIN Search Bot service"
        $SYSTEMCTL status binsearchccgbot.service
        exit 1
    fi
    
    # Start monitoring service
    log_info "Starting monitoring service..."
    $SYSTEMCTL start binsearch-monitor.service
    sleep 5
    
    # Check monitoring service status
    if $SYSTEMCTL is-active --quiet binsearch-monitor.service; then
        log_success "Monitoring service started successfully"
    else
        log_error "Failed to start monitoring service"
        $SYSTEMCTL status binsearch-monitor.service
        exit 1
    fi
    
    log_success "All services started successfully"
}

show_service_status() {
    log_info "Service Status Summary:"
    echo "======================="
    
    # Bot service status
    echo -n "🤖 BIN Search Bot: "
    if $SYSTEMCTL is-active --quiet binsearchccgbot.service; then
        echo -e "${GREEN}RUNNING${NC}"
    else
        echo -e "${RED}STOPPED${NC}"
    fi
    
    # Monitoring service status
    echo -n "🔍 Monitoring:     "
    if $SYSTEMCTL is-active --quiet binsearch-monitor.service; then
        echo -e "${GREEN}RUNNING${NC}"
    else
        echo -e "${RED}STOPPED${NC}"
    fi
    
    echo ""
    log_info "Health Check Endpoints:"
    echo "  • http://localhost:8001/health"
    echo "  • http://localhost:8001/ready"
    echo "  • http://localhost:8001/metrics"
    echo ""
    
    log_info "Service Management Commands:"
    echo "  • View logs: sudo journalctl -f -u binsearchccgbot.service"
    echo "  • Monitor logs: sudo journalctl -f -u binsearch-monitor.service"
    echo "  • Restart bot: sudo systemctl restart binsearchccgbot.service"
    echo "  • Check status: sudo systemctl status binsearchccgbot.service"
    echo ""
}

cleanup_old_deployments() {
    log_info "Cleaning up old deployment files..."
    
    # Remove old service files if they exist with different names
    sudo rm -f /etc/systemd/system/binbot.service 2>/dev/null || true
    sudo rm -f /etc/systemd/system/telegram-bot.service 2>/dev/null || true
    
    # Clean up old logs
    find "$PROJECT_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    # Clean up old monitoring data
    if [ -f "$PROJECT_DIR/data/monitoring.db" ]; then
        cd "$PROJECT_DIR"
        source venv/bin/activate
        python3 -c "
import sqlite3
from datetime import datetime, timedelta
conn = sqlite3.connect('data/monitoring.db')
cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
conn.execute('DELETE FROM service_health WHERE timestamp < ?', (cutoff,))
conn.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff,))
conn.commit()
conn.close()
print('Old monitoring data cleaned')
" 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
}

# Main deployment process
main() {
    echo -e "${BLUE}"
    echo "BIN Search Bot Production Deployment"
    echo "====================================="
    echo -e "${NC}"
    
    check_prerequisites
    install_python_dependencies
    setup_monitoring_database
    check_environment_variables
    configure_systemd_services
    setup_log_rotation
    cleanup_old_deployments
    run_health_check
    start_services
    show_service_status
    
    echo -e "${GREEN}"
    echo "🎉 Deployment completed successfully!"
    echo "======================================"
    echo -e "${NC}"
    
    log_info "The BIN Search Bot is now running in production with full monitoring."
    log_info "Check the service status with: sudo systemctl status binsearchccgbot.service"
    log_info "View live logs with: sudo journalctl -f -u binsearchccgbot.service"
    
    # Show next steps
    echo ""
    log_info "Next Steps:"
    echo "1. Update webhook URL in @BotFather if needed"
    echo "2. Test bot functionality with /start command" 
    echo "3. Monitor service health at http://localhost:8001/health"
    echo "4. Set up external monitoring alerts if desired"
    echo ""
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_service_status
        ;;
    "health")
        cd "$PROJECT_DIR"
        source venv/bin/activate 2>/dev/null || true
        python3 monitoring/production_monitor.py --status
        ;;
    "restart")
        log_info "Restarting services..."
        $SYSTEMCTL restart binsearchccgbot.service
        $SYSTEMCTL restart binsearch-monitor.service
        show_service_status
        ;;
    "stop")
        log_info "Stopping services..."
        $SYSTEMCTL stop binsearchccgbot.service
        $SYSTEMCTL stop binsearch-monitor.service
        log_success "Services stopped"
        ;;
    "logs")
        log_info "Showing recent logs..."
        sudo journalctl -n 50 -u binsearchccgbot.service
        ;;
    *)
        echo "Usage: $0 [deploy|status|health|restart|stop|logs]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full production deployment (default)"
        echo "  status  - Show service status"
        echo "  health  - Run health check"
        echo "  restart - Restart all services"
        echo "  stop    - Stop all services"
        echo "  logs    - Show recent service logs"
        exit 1
        ;;
esac