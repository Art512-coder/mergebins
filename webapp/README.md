# 🚀 BIN Search Web Application - Crypto Payment Integration

A modern, full-stack web application for BIN (Bank Identification Number) lookup and test card generation, built with **FastAPI**, **Vue.js**, and **PostgreSQL**. Now featuring **cryptocurrency payment integration** for secure, global transactions without account freezing risks.

## 💰 **Why Crypto Payments?**

✅ **No Account Freezing** - Payment processors can't freeze your funds  
✅ **Instant Settlements** - Receive payments immediately  
✅ **No Chargebacks** - Cryptocurrency transactions are irreversible  
✅ **Global Access** - Accept payments from anywhere in the world  
✅ **Lower Fees** - Typically 1-2% vs 3-4% for traditional processors  
✅ **Privacy Focused** - Less personal data required from customers  

## 🔧 **Supported Cryptocurrencies**
- **Bitcoin (BTC)**
- **Ethereum (ETH)** 
- **Tether (USDT)**
- **USD Coin (USDC)**
- **Litecoin (LTC)**
- **Bitcoin Cash (BCH)**
- **200+ more via NOWPayments**

## 🚀 **Quick Start**

### **Windows**
```bash
cd webapp
start.bat
```

### **Linux/Mac**
```bash
cd webapp
chmod +x start.sh
./start.sh
```

The application will be available at:
- **Web App**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🏗️ **Architecture Overview**

### **Backend (FastAPI)**
- **Authentication**: JWT-based with bcrypt password hashing
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for BIN lookups and sessions
- **Payments**: Stripe integration with webhook handling
- **Rate Limiting**: Per-user and IP-based limits
- **Card Generation**: Enhanced algorithms from your existing bot

### **Frontend (Vue.js 3)**
- **Framework**: Vue.js 3 with Composition API
- **Styling**: Tailwind CSS for responsive design
- **State Management**: Pinia for reactive state
- **API Client**: Axios with authentication interceptors
- **Payment**: Stripe Elements integration

### **Database Schema**
- **users**: User accounts and tiers
- **subscriptions**: Stripe subscription management
- **bin_data**: 458K+ BIN records from your CSV
- **usage_logs**: API usage tracking and analytics
- **blocked_bins**: Test BIN blocking system

## 🔧 **Configuration**

### **Environment Variables**
Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost/bin_search_db
REDIS_URL=redis://localhost:6379

# Stripe Payments
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# App Security
SECRET_KEY=your-super-secret-key-change-in-production
```

### **Stripe Setup**
1. Create a Stripe account at https://stripe.com
2. Get your API keys from the dashboard
3. Create a webhook endpoint: `https://yourdomain.com/api/v1/payments/webhook/stripe`
4. Enable these events: `checkout.session.completed`, `invoice.payment_succeeded`, `invoice.payment_failed`, `customer.subscription.deleted`

## 📱 **Features**

### **Free Tier**
- ✅ 5 card generations per day
- ✅ Unlimited BIN lookups
- ✅ Basic card generation
- ✅ Search 458K+ BIN database

### **Premium Tier ($9.99/month)**
- ✅ Unlimited card generation
- ✅ AVS postal code generation (7 countries)
- ✅ Bulk generation (up to 1000 cards)
- ✅ Export in JSON/CSV/XML formats
- ✅ Priority support

### **Enhanced Security**
- ✅ Test BIN blocking (prevents sandbox BINs)
- ✅ Production-like card patterns
- ✅ Weighted digit distribution
- ✅ Advanced pattern filtering
- ✅ JWT authentication with refresh tokens

## 🛠️ **Development**

### **Backend Development**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### **Frontend Development**
```bash
cd frontend
npm install
npm run dev
```

### **Database Migrations**
```bash
cd backend
alembic upgrade head
```

## 🐳 **Deployment**

### **Docker Compose (Recommended)**
```bash
docker-compose up --build -d
```

### **Manual Production Setup**
1. **Database**: Set up PostgreSQL and Redis
2. **Backend**: Deploy FastAPI with Gunicorn
3. **Frontend**: Build and serve with Nginx
4. **SSL**: Use Let's Encrypt for HTTPS
5. **Monitoring**: Set up Sentry for error tracking

## 🔗 **API Endpoints**

### **Authentication**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### **BIN Lookup**
- `GET /api/v1/bins/lookup/{bin}` - Lookup specific BIN
- `GET /api/v1/bins/search` - Search BINs with filters
- `GET /api/v1/bins/stats` - Database statistics

### **Card Generation**
- `POST /api/v1/cards/generate` - Generate single card
- `POST /api/v1/cards/generate/bulk` - Bulk generation (Premium)
- `GET /api/v1/cards/usage` - User usage statistics

### **Payments**
- `POST /api/v1/payments/create-checkout-session` - Create Stripe checkout
- `POST /api/v1/payments/webhook/stripe` - Stripe webhook handler
- `GET /api/v1/payments/subscription` - Get user subscription

### **Admin**
- `GET /api/v1/admin/dashboard` - Admin dashboard data
- `GET /api/v1/admin/users` - User management
- `GET /api/v1/admin/usage-logs` - Usage analytics

## 🧪 **Testing**

### **Run Tests**
```bash
cd backend
pytest
```

### **Load Testing**
```bash
cd backend
pip install locust
locust -f tests/load_test.py
```

## 📊 **Monitoring**

### **Health Checks**
- `GET /health` - Application health status
- **Database**: Connection and query testing
- **Redis**: Cache connectivity
- **External**: Stripe API status

### **Metrics**
- **Prometheus**: Application metrics
- **Grafana**: Dashboards for monitoring
- **Sentry**: Error tracking and performance

## 🔒 **Security**

### **Best Practices Implemented**
- ✅ JWT authentication with secure cookies
- ✅ Password hashing with bcrypt
- ✅ Rate limiting per user and IP
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention
- ✅ CORS protection
- ✅ Stripe webhook signature verification

### **PCI Compliance**
- ✅ No real card data storage
- ✅ Test card generation only
- ✅ Secure payment processing via Stripe
- ✅ HTTPS enforcement in production

## 📈 **Scaling**

### **Horizontal Scaling**
- **Load Balancer**: Nginx or AWS ALB
- **Multiple Instances**: Docker Swarm or Kubernetes
- **Database**: Read replicas for scaling reads
- **Cache**: Redis Cluster for distributed caching

### **Performance Optimization**
- **Database Indexing**: Optimized BIN lookups
- **Redis Caching**: Frequent BIN data cached
- **Connection Pooling**: Database connection management
- **Background Tasks**: Celery for async processing

## 🆘 **Troubleshooting**

### **Common Issues**

**Database Connection Error**
```bash
# Check PostgreSQL status
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up db -d
```

**Frontend Not Loading**
```bash
# Check backend API
curl http://localhost:8000/health

# Rebuild frontend
docker-compose build frontend
docker-compose up frontend -d
```

**Payment Issues**
```bash
# Check Stripe webhook logs
docker-compose logs backend | grep stripe

# Verify webhook endpoint
ngrok http 8000  # For local testing
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 **License**

This project is for educational and commercial use. Please ensure compliance with all applicable laws when handling financial data.

---

**Built with ❤️ for secure financial testing and development**
