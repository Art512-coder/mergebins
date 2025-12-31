# 🤖 AI Assistant Context - BIN Search Pro Platform

## PROJECT OVERVIEW
You are assisting with "BIN Search Pro" - a fully deployed, professional fintech platform for BIN (Bank Identification Number) lookup services.

## CURRENT STATUS ✅
- **FULLY OPERATIONAL** and deployed to production
- **Frontend**: https://5e336a94.bin-search-pro.pages.dev (Vue.js + TypeScript)
- **Backend**: https://bin-search-api.arturovillanueva1994.workers.dev (FastAPI + Python)
- **Database**: Cloudflare D1 with 458,051 BIN records imported
- **Infrastructure**: Cloudflare Pages + Workers

## ARCHITECTURE
### Frontend (webapp/frontend/):
- Vue.js 3 + TypeScript + Tailwind CSS
- Key files: LandingPage.vue (dark pricing cards), BinSearch.vue, PaymentModal.vue
- Features: BIN lookup, card generator, crypto checker, subscriptions

### Backend (webapp/backend/):
- FastAPI with comprehensive health monitoring
- Key files: health.py (enterprise monitoring), security_service.py, d1_bin_service.py
- Features: 458K BIN database, security monitoring, payment integration

### Database:
- Cloudflare D1 with 458,051 BIN records
- Models: User, BinData, SecurityEvent, PaymentLog, UsageLog
- Status: Fully operational with global distribution

## KEY FIXES COMPLETED ✅
1. **Pricing Visibility**: Fixed LandingPage.vue pricing cards with dark backgrounds
2. **Model Imports**: Added SecurityEvent and PaymentLog models
3. **Health Monitoring**: Enterprise-grade system monitoring operational
4. **Database Import**: 458K records successfully imported
5. **Security**: Real-time threat detection and IP blocking active

## IMPORTANT NOTES FOR AI ASSISTANTS:
1. **Platform is LIVE**: All development should consider production impact
2. **Database is Populated**: 458,051 records ready for queries
3. **Payment System**: NOWPayments integration for crypto subscriptions  
4. **Security Active**: Advanced threat monitoring running
5. **Pricing Fixed**: Dark cards with perfect contrast implemented

## COMMON TASKS:
- **Development**: Use setup.bat for local environment
- **Deployment**: Use deploy.bat for production updates
- **Monitoring**: Check /health endpoint for system status
- **Database**: Import via generate_import_sql.py script

## SUBSCRIPTION TIERS:
- **Free**: 3 BIN lookups/day, basic features
- **Premium ($9.99/mo)**: Unlimited lookups, advanced features, crypto tools

## QUICK REFERENCE:
- Project root: d:\mergebins\
- Live platform: https://5e336a94.bin-search-pro.pages.dev
- API docs: https://bin-search-api.arturovillanueva1994.workers.dev/docs
- Health check: https://bin-search-api.arturovillanueva1994.workers.dev/health

This is a PRODUCTION PLATFORM serving real users with 458K+ BIN records!