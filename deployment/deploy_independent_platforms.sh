#!/bin/bash

# Independent Platform Deployment Script
# Deploys both web and Telegram platforms with shared backend

echo "🚀 Deploying Independent BIN Checker Platforms..."

# Configuration
PROJECT_DIR="/opt/mergebins"
SERVICE_NAME="telegram-bot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Phase 1: Deploy Web Platform (Cloudflare Workers)
print_status "Phase 1: Deploying Web Platform..."

cd $PROJECT_DIR/deployment

if ! command -v npx &> /dev/null; then
    print_error "Node.js/npm not installed. Please install Node.js first."
    exit 1
fi

print_status "Installing dependencies..."
npm install

print_status "Deploying to Cloudflare Workers..."
npx wrangler deploy

if [ $? -eq 0 ]; then
    print_success "✅ Web platform deployed successfully!"
    print_status "🌐 Web URL: https://cryptobinchecker.cc"
else
    print_error "❌ Web platform deployment failed"
    exit 1
fi

# Phase 2: Deploy Telegram Bot
print_status "Phase 2: Deploying Telegram Bot..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    print_warning "Telegram bot deployment requires sudo privileges"
    SUDO_PREFIX="sudo"
else
    SUDO_PREFIX=""
fi

# Copy bot files
print_status "Setting up bot files..."
$SUDO_PREFIX cp telegram_bot.py $PROJECT_DIR/
$SUDO_PREFIX chmod +x $PROJECT_DIR/telegram_bot.py

# Create logs directory
$SUDO_PREFIX mkdir -p $PROJECT_DIR/logs
$SUDO_PREFIX chmod 755 $PROJECT_DIR/logs

# Install Python dependencies
print_status "Installing Python dependencies..."
$SUDO_PREFIX pip3 install python-telegram-bot requests

# Set up systemd service
print_status "Configuring systemd service..."
$SUDO_PREFIX cp deployment/telegram-bot.service /etc/systemd/system/

# Reload systemd and enable service
$SUDO_PREFIX systemctl daemon-reload
$SUDO_PREFIX systemctl enable $SERVICE_NAME

# Start the service
print_status "Starting Telegram bot service..."
$SUDO_PREFIX systemctl stop $SERVICE_NAME 2>/dev/null || true
$SUDO_PREFIX systemctl start $SERVICE_NAME

# Check service status
if $SUDO_PREFIX systemctl is-active --quiet $SERVICE_NAME; then
    print_success "✅ Telegram bot deployed and running!"
else
    print_error "❌ Telegram bot failed to start"
    print_status "Checking service logs..."
    $SUDO_PREFIX systemctl status $SERVICE_NAME --no-pager -l
    exit 1
fi

# Phase 3: Verification
print_status "Phase 3: Platform Verification..."

# Check web platform
print_status "Testing web platform API..."
if curl -s "https://cryptobinchecker.cc/api/v1/bins/stats" > /dev/null; then
    print_success "✅ Web API responding"
else
    print_warning "⚠️ Web API not responding"
fi

# Check Telegram bot
print_status "Checking Telegram bot status..."
if $SUDO_PREFIX systemctl is-active --quiet $SERVICE_NAME; then
    print_success "✅ Telegram bot active"
    
    # Show bot logs
    print_status "Recent bot logs:"
    $SUDO_PREFIX journalctl -u $SERVICE_NAME --lines=5 --no-pager
else
    print_error "❌ Telegram bot not active"
fi

# Final summary
echo ""
print_success "🎉 Independent Platform Deployment Complete!"
echo ""
echo -e "${BLUE}📊 Platform Status:${NC}"
echo "• 🌐 Web Platform: https://cryptobinchecker.cc"
echo "• 🤖 Telegram Bot: $($SUDO_PREFIX systemctl is-active $SERVICE_NAME)"
echo "• 💾 Database: Shared D1 database"
echo "• 🔗 Cross-platform: User linking enabled"
echo ""
echo -e "${BLUE}📋 Management Commands:${NC}"
echo "• Web: cd $PROJECT_DIR/deployment && npx wrangler deploy"
echo "• Bot: $SUDO_PREFIX systemctl restart $SERVICE_NAME"
echo "• Logs: $SUDO_PREFIX journalctl -u $SERVICE_NAME -f"
echo ""
print_success "Both platforms are now running independently with shared backend!"