# CryptoBinChecker.cc Enhanced Deployment Guide

## 🚀 Quick Start

### Windows Development (Recommended)
```powershell
# 1. Quick start (auto-deploys if needed)
.\start_development.bat

# 2. Or manual deployment
.\deployment\deploy_full.ps1 -Environment development
```

### Linux Production
```bash
# Make scripts executable
chmod +x deployment/*.sh

# Deploy to production
./deployment/deploy_full.sh -e production

# Check deployment status
./deployment/check_status.sh
```

## 📁 Project Structure

```
d:\mergebins\
├── 📱 telegram_bot.py              # Enhanced Telegram bot with payments
├── 🌐 webapp/
│   ├── backend/                    # FastAPI + Python backend
│   │   ├── app/
│   │   │   ├── main.py            # API server
│   │   │   ├── routes/            # API endpoints
│   │   │   │   ├── bin.py         # BIN checking
│   │   │   │   ├── crypto.py      # 6 crypto wallets
│   │   │   │   ├── payment.py     # Payment processing
│   │   │   │   └── webhook.py     # Payment webhooks
│   │   │   ├── models/            # Database models
│   │   │   ├── database.py        # Database connection
│   │   │   └── enhanced_monitoring.py
│   │   ├── .env                   # Backend configuration
│   │   ├── requirements.txt       # Python dependencies
│   │   └── venv/                  # Virtual environment
│   └── frontend/                  # Vue.js 3 + TypeScript frontend
│       ├── src/
│       │   ├── views/
│       │   │   ├── BinCheckerPage.vue
│       │   │   ├── CryptoCheckerPage.vue
│       │   │   └── PaymentPage.vue
│       │   ├── stores/            # Pinia state management
│       │   └── components/
│       ├── .env                   # Frontend configuration
│       ├── package.json           # Node.js dependencies
│       └── dist/                  # Built frontend
├── 🚀 deployment/
│   ├── deploy_full.ps1            # Windows deployment
│   ├── deploy_full.sh             # Linux deployment
│   ├── check_status.sh            # Health checker
│   ├── wrangler.toml              # Cloudflare Workers
│   └── pages-deploy.toml          # Cloudflare Pages
└── 📋 start_development.bat       # Quick development start
```

## 🔧 Features Implemented

### ✅ Core Features
- **BIN Checker**: Credit card BIN validation and information
- **Crypto Wallet Checker**: 6 cryptocurrencies (BTC, ETH, LTC, DOGE, ADA, SOL)
- **Payment System**: NOWPayments + Coinbase Commerce integration
- **Telegram Bot**: Full payment processing with premium features
- **Database**: User management, subscriptions, payment logs
- **Security**: Rate limiting, input validation, secure headers

### ✅ Technical Stack
- **Frontend**: Vue.js 3, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, Python 3.11, SQLAlchemy, Redis
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Payment**: NOWPayments, Coinbase Commerce
- **Deployment**: Cloudflare Workers/Pages, Docker, systemd
- **Monitoring**: Enhanced logging, health checks, error tracking

## 🔑 Configuration Required

### Backend (.env)
```bash
# Required API Keys (replace with actual values)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
BLOCKCHAIN_INFO_API_KEY=your-blockchain-info-key
ETHERSCAN_API_KEY=your-etherscan-key
BLOCKCYPHER_API_KEY=your-blockcypher-key
BLOCKFROST_API_KEY=your-blockfrost-key
NOWPAYMENTS_API_KEY=your-nowpayments-key
COINBASE_COMMERCE_API_KEY=your-coinbase-key

# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./cryptobinchecker.db

# Security
SECRET_KEY=auto-generated-secure-key
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_TELEGRAM_BOT_USERNAME=cryptobinchecker_bot
```

## 🌍 Deployment Options

### 1. Development (Windows)
```powershell
# Quick start - everything automated
.\start_development.bat

# Manual start services
start_backend_dev.bat    # Port 8000
start_frontend_dev.bat   # Port 5173
start_telegram_dev.bat   # Telegram bot
```

**URLs:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 2. Production (Linux)
```bash
# Full deployment with services
./deployment/deploy_full.sh -e production

# Individual services
sudo systemctl status cryptobinchecker-api
sudo systemctl status cryptobinchecker-telegram
```

**URLs:**
- Website: https://cryptobinchecker.cc
- API: https://api.cryptobinchecker.cc

### 3. Cloudflare (Global CDN)
```bash
# Deploy frontend to Pages
npx wrangler pages deploy webapp/frontend/dist

# Deploy backend to Workers
npx wrangler deploy
```

## 🔍 Testing

### Health Checks
```bash
# Backend API
curl http://localhost:8000/health

# BIN Check
curl -X POST http://localhost:8000/api/v1/bin/check \
  -H "Content-Type: application/json" \
  -d '{"bin":"450678"}'

# Crypto Balance
curl -X POST http://localhost:8000/api/v1/crypto/balance \
  -H "Content-Type: application/json" \
  -d '{"cryptocurrency":"btc","address":"1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"}'
```

### Telegram Bot Testing
1. Message: `/start` - Welcome message
2. Message: `/check 450678` - BIN check
3. Message: `/crypto btc 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` - Crypto balance
4. Message: `/premium` - Payment options

## 🔒 Security Features

- **Rate Limiting**: API endpoints protected
- **Input Validation**: All user inputs sanitized
- **CORS**: Properly configured origins
- **Headers**: Security headers implemented
- **Authentication**: JWT tokens for premium features
- **Database**: SQL injection protection
- **Environment**: Sensitive data in .env files

## 📊 Monitoring

### Logs
- Backend: `logs/backend.log`
- Telegram: `logs/telegram.log`
- System: `logs/system.log`

### Health Endpoints
- `/health` - Overall system status
- `/api/v1/health` - API health
- `/metrics` - Prometheus metrics

### Error Tracking
- Structured logging with levels
- Error aggregation and alerts
- Performance monitoring

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```powershell
   # Windows - find and kill process
   netstat -ano | findstr :8000
   taskkill /PID <process_id> /F
   ```

2. **Python Virtual Environment Issues**
   ```powershell
   # Recreate virtual environment
   cd webapp\backend
   rmdir /s venv
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Node Modules Issues**
   ```powershell
   # Clear and reinstall
   cd webapp\frontend
   rmdir /s node_modules
   del package-lock.json
   npm install
   ```

4. **Database Connection Issues**
   ```bash
   # Reinitialize database
   cd webapp/backend
   rm cryptobinchecker.db
   python -c "from app.database import init_db; init_db()"
   ```

### Support Commands

```powershell
# Check deployment status
.\deployment\check_status.sh  # Linux
# Or manually verify Windows installation

# View logs
Get-Content logs\backend.log -Tail 50
Get-Content logs\telegram.log -Tail 50

# Restart services (development)
# Close terminal windows and run start scripts again
```

## 📈 Next Steps

1. **API Keys**: Update all API keys in .env files
2. **Webhooks**: Configure payment webhook URLs
3. **Domain**: Point cryptobinchecker.cc to your server
4. **SSL**: Set up SSL certificates for HTTPS
5. **Monitoring**: Configure alerts and notifications
6. **Backups**: Set up automated database backups
7. **Scaling**: Consider load balancing for high traffic

## 🎯 Version Information

**Current Version**: 2.0 Enhanced
**Features**: 6 crypto currencies, full payment system, comprehensive monitoring
**Deployment**: Multi-platform support (Windows dev, Linux prod, Cloudflare)
**Status**: Production-ready with all core features implemented

---

**🚀 Ready to Deploy!**

The enhanced CryptoBinChecker.cc is now fully functional with all features implemented. Simply run the appropriate deployment script for your environment and update the API keys to go live.