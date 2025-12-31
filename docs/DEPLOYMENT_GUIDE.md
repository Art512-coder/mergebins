# 🚀 Deployment Guide - BIN Search Bot

This guide covers all deployment scenarios for the BIN Search Bot project.

## 📋 Pre-Deployment Checklist

### ✅ System Requirements
- [ ] **Python 3.11+** installed
- [ ] **Node.js 18+** (for webapp frontend)
- [ ] **Docker & Docker Compose** (recommended)
- [ ] **PostgreSQL 13+** (for webapp database)
- [ ] **Redis 6+** (for caching and sessions)
- [ ] **SSL Certificate** (for production HTTPS)

### ✅ Configuration Requirements
- [ ] **Telegram Bot Token** from @BotFather
- [ ] **NOWPayments API Key** (for crypto payments)
- [ ] **Coinbase Commerce API Key** (optional, for additional crypto support)
- [ ] **Domain name** configured (for production)
- [ ] **SSL certificates** installed (for HTTPS)

### ✅ Files Check
- [ ] `.env` file created from `.env.example`
- [ ] `data/merged_bin_data.csv` exists (458K+ BIN records)
- [ ] All dependencies installed (`pip install -r requirements.txt`)

## 🖥️ Local Development Deployment

### Quick Start (Windows)
```cmd
# 1. Clone and setup
git clone <repository-url>
cd mergebins
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env
# Edit .env with your settings

# 3. Start bot
start_bot.bat
```

### Quick Start (Linux/macOS)
```bash
# 1. Clone and setup
git clone <repository-url>
cd mergebins
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start bot
./start_bot.sh
```

### Web Application (Development)
```bash
# Backend
cd webapp/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd webapp/frontend
npm install
npm run dev
```

## 🐳 Docker Deployment

### Option 1: One-Command Deployment
```bash
# Complete deployment with health checks
./deployment/deploy.sh production
```

### Option 2: Manual Docker Deployment
```bash
# 1. Build and start all services
cd webapp
docker-compose up -d

# 2. Check service status
docker-compose ps

# 3. View logs
docker-compose logs -f
```

### Option 3: Custom Docker Build
```bash
# Build custom image
docker build -f deployment/Dockerfile -t bin-search-bot .

# Run with environment file
docker run -d --env-file .env -p 8000:8000 --name bot bin-search-bot

# Or run with inline environment
docker run -d \
  -e BOT_TOKEN=your_token \
  -e DATABASE_URL=your_db_url \
  -p 8000:8000 \
  --name bot bin-search-bot
```

## 🌐 Production VPS Deployment

### Server Preparation
```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Install additional tools
sudo apt install -y git nginx ufw
```

### Application Deployment
```bash
# 1. Clone repository
git clone <repository-url>
cd mergebins

# 2. Create production environment
cp .env.example .env
nano .env  # Configure all production values

# 3. Deploy application
./deployment/deploy.sh production

# 4. Setup systemd service
sudo cp deployment/binsearchccgbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable binsearchccgbot
sudo systemctl start binsearchccgbot
```

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/binbot
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Webhooks
    location /webhooks/ {
        proxy_pass http://localhost:8000/webhooks/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL Certificate Setup (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## ☁️ Cloud Platform Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)
```bash
# 1. Build and push image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker build -f deployment/Dockerfile -t bin-search-bot .
docker tag bin-search-bot:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/bin-search-bot:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/bin-search-bot:latest

# 2. Create ECS service
# Use AWS Console or CloudFormation template
```

#### Using EC2
```bash
# Same as VPS deployment, but:
# 1. Use AWS RDS for PostgreSQL
# 2. Use AWS ElastiCache for Redis
# 3. Use AWS Application Load Balancer
# 4. Use AWS Certificate Manager for SSL
```

### Google Cloud Platform (GCP)

#### Using Cloud Run
```bash
# 1. Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/bin-search-bot

# 2. Deploy to Cloud Run
gcloud run deploy bin-search-bot \
  --image gcr.io/PROJECT_ID/bin-search-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Microsoft Azure

#### Using Container Instances
```bash
# 1. Build and push to Azure Container Registry
az acr build --registry myregistry --image bin-search-bot .

# 2. Deploy container
az container create \
  --resource-group myResourceGroup \
  --name bin-search-bot \
  --image myregistry.azurecr.io/bin-search-bot:latest \
  --cpu 1 --memory 1
```

## 🔧 Environment Configuration

### Required Environment Variables
```bash
# Telegram Bot
BOT_TOKEN=7444150670:AAFDgL5_Wt7-HeTT3lT1EmbFYIzZ7wA9UHE

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bin_search_db
REDIS_URL=redis://localhost:6379

# Crypto Payments
NOWPAYMENTS_API_KEY=your_nowpayments_api_key
NOWPAYMENTS_IPN_SECRET=your_ipn_secret
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_WEBHOOK_SECRET=your_webhook_secret

# Application
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=False
BASE_URL=https://your-domain.com
CORS_ORIGINS=https://your-frontend-domain.com

# Security
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60
ENABLE_2FA=true
SESSION_TIMEOUT=3600
```

### Optional Environment Variables
```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/binbot/app.log

# Monitoring
SENTRY_DSN=your_sentry_dsn
NEW_RELIC_LICENSE_KEY=your_newrelic_key

# External APIs
BLOCKCHAIN_INFO_API_KEY=your_blockchain_api_key
ETHERSCAN_API_KEY=your_etherscan_api_key
```

## 🔍 Post-Deployment Testing

### Health Checks
```bash
# 1. Bot health
curl http://localhost:8000/health

# 2. Database connectivity
python -c "from src.bot.BINSearchCCGbot import load_bin_data; print('✅ BIN data loaded:', load_bin_data())"

# 3. Crypto integration
python tests/test_crypto_integration.py

# 4. Payment system
python tests/test_payment_system.py
```

### Telegram Bot Testing
1. **Start conversation**: Send `/start` to your bot
2. **BIN lookup**: `/binlookup 411111`
3. **Card generation**: `/generate 411111`
4. **Crypto balance**: `/walletbalance BTC 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2`

### API Testing
```bash
# Test BIN lookup endpoint
curl "http://localhost:8000/api/bins/search?query=411111"

# Test card generation endpoint
curl -X POST "http://localhost:8000/api/cards/generate" \
  -H "Content-Type: application/json" \
  -d '{"bin": "411111", "count": 1}'
```

## 📊 Monitoring & Maintenance

### Log Monitoring
```bash
# Application logs
tail -f bot.log

# Docker logs
docker-compose logs -f

# System logs
journalctl -u binsearchccgbot -f
```

### Performance Monitoring
```bash
# Check service status
systemctl status binsearchccgbot

# Monitor resource usage
htop
docker stats

# Database performance
psql -h localhost -U bin_user -d bin_search_db -c "SELECT * FROM pg_stat_activity;"
```

### Backup & Recovery
```bash
# Database backup
pg_dump -h localhost -U bin_user bin_search_db > backup_$(date +%Y%m%d).sql

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env deployment/ data/

# Automated backup script
echo "0 2 * * * /path/to/backup_script.sh" | crontab -
```

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   ```bash
   # Check bot process
   ps aux | grep python
   
   # Check logs
   tail -n 50 bot.log
   
   # Restart bot
   systemctl restart binsearchccgbot
   ```

2. **Database connection errors**
   ```bash
   # Test connection
   psql -h localhost -U bin_user -d bin_search_db -c "SELECT version();"
   
   # Check PostgreSQL status
   systemctl status postgresql
   ```

3. **Redis connection issues**
   ```bash
   # Test Redis
   redis-cli ping
   
   # Check Redis status
   systemctl status redis
   ```

4. **Docker container issues**
   ```bash
   # Check container status
   docker-compose ps
   
   # View container logs
   docker-compose logs backend
   
   # Restart containers
   docker-compose restart
   ```

### Performance Issues
```bash
# Monitor CPU/Memory
htop

# Check disk space
df -h

# Monitor database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis memory usage
redis-cli info memory
```

## 🔒 Security Hardening

### Server Security
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Install fail2ban
sudo apt install fail2ban
```

### Application Security
- Change all default passwords
- Use strong secrets for JWT tokens
- Enable HTTPS with valid SSL certificates
- Implement rate limiting
- Regular security updates
- Monitor for suspicious activities

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- [ ] **Weekly**: Check logs for errors
- [ ] **Weekly**: Monitor resource usage
- [ ] **Monthly**: Update dependencies
- [ ] **Monthly**: Database maintenance
- [ ] **Quarterly**: Security audit
- [ ] **Quarterly**: Performance optimization

### Getting Help
- **GitHub Issues**: Technical problems and bug reports
- **Documentation**: Full docs in `/docs` folder
- **Community**: Telegram support group
- **Email**: support@yourservice.com

---

**🎉 Congratulations!** Your BIN Search Bot is now deployed and ready for production use.