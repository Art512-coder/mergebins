# 🚀 BIN Search Pro - Vue.js 3 Frontend

A modern, responsive Vue.js 3 frontend for BIN lookup and crypto payment processing with enterprise-level quality standards.

## ✨ Features

### 🔍 BIN Lookup Engine
- **Real-time search** with debounced input (500ms delay)
- **Advanced filters** by brand, country, type
- **Search history** with favorites
- **Bulk lookup** with CSV import/export
- **454,303 BIN records** in database

### 💳 Card Generation Suite
- **Configurable parameters** (count, BIN, AVS)
- **Multiple export formats** (JSON, CSV, TXT)
- **Batch processing** with progress indicators
- **Visual card display** with realistic credit card designs
- **Copy functionality** for individual or bulk cards

### 💰 Payment Infrastructure
- **Multi-provider crypto payments** (NOWPayments + Coinbase Commerce)
- **Real-time price estimation** in multiple cryptocurrencies
- **Payment status tracking** with automatic polling
- **Subscription tier management** (Free/Premium)

### 🎨 User Experience
- **Dark mode first** with light mode toggle
- **Mobile responsive** design
- **Micro-interactions** and smooth animations
- **Toast notifications** system
- **Loading states** and error handling
- **WCAG 2.1 AA accessibility** compliance

## 🛠️ Tech Stack

- **Vue.js 3** with Composition API
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Pinia** for state management
- **Vue Router** for navigation
- **Axios** for HTTP requests
- **Heroicons** for icons
- **Vite** for development and building

## 📦 Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Setup Instructions

1. **Navigate to frontend directory**:
   ```bash
   cd webapp/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open in browser**:
   ```
   http://localhost:3000
   ```

### Build for Production

```bash
npm run build
npm run preview
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=BIN Search Pro
VITE_APP_VERSION=1.0.0
```

### API Integration
The frontend is configured to work with the FastAPI backend:
- **Base URL**: `http://localhost:8000`
- **Auth**: JWT tokens via `/api/v1/auth/*`
- **BIN Lookup**: `/api/v1/bins/lookup/{bin}`
- **Card Generation**: `/api/v1/cards/generate`
- **Crypto Payments**: `/api/v1/payments/create-crypto-payment`

## 🏗️ Project Structure

```
src/
├── assets/              # Static assets and styles
│   └── styles/         # Tailwind CSS and custom styles
├── components/         # Reusable UI components
│   ├── BinSearch.vue   # Real-time BIN lookup
│   ├── CardDisplay.vue # Visual credit card display
│   └── PaymentModal.vue # Crypto payment modal
├── views/              # Page-level components
│   ├── LandingPage.vue    # Hero, pricing, features
│   ├── LoginPage.vue      # Authentication
│   ├── DashboardPage.vue  # User stats and overview
│   ├── BinLookupPage.vue  # BIN search interface
│   ├── CardGeneratorPage.vue # Card generation
│   └── SubscriptionPage.vue # Subscription management
├── stores/             # Pinia state management
│   ├── auth.ts        # JWT token and user state
│   └── payment.ts     # Payment and subscription state
├── composables/        # Vue 3 composition functions
│   ├── useBinSearch.ts    # BIN lookup logic
│   ├── useCardGenerator.ts # Card generation logic
│   ├── useTheme.ts        # Dark/light mode
│   └── useDebounce.ts     # Debounced functions
├── utils/              # Helper utilities
│   ├── api.ts         # Axios API client
│   └── helpers.ts     # Formatting and validation
├── types/              # TypeScript definitions
│   ├── auth.ts        # Authentication types
│   ├── bin.ts         # BIN lookup types
│   ├── card.ts        # Card generation types
│   └── payment.ts     # Payment types
└── main.ts             # Application entry point
```

## 🎯 Key Features Implemented

### Authentication System
- **JWT token lifecycle** management
- **Auto-refresh** on token expiry
- **Protected routes** with route guards
- **Persistent sessions** across browser restarts

### BIN Search with Real-time Results
- **Debounced search** as user types
- **Input validation** (6-8 digits)
- **Favorites system** with localStorage
- **Search history** with timestamps
- **Copy functionality** for results

### Visual Card Generator
- **Realistic credit card designs** with gradients
- **Brand-specific styling** (Visa, Mastercard, Amex)
- **Hover animations** and copy-on-click
- **Bulk actions** for export and copying
- **Animated card appearance** with staggered delays

### Crypto Payment Modal
- **Provider selection** (NOWPayments/Coinbase)
- **Currency selection** with real-time pricing
- **Payment status tracking** with polling
- **Smooth animations** and transitions

### Dashboard Analytics
- **Usage statistics** with progress bars
- **Plan comparison** tables
- **Quick actions** for common tasks
- **Recent activity** summaries

## 🚀 Performance Optimizations

- **Code splitting** with dynamic imports
- **Lazy loading** of route components
- **Image optimization** with WebP support
- **Bundle analysis** and tree shaking
- **CSS optimization** with PurgeCSS
- **Lighthouse score 95+** target

## 🎨 Design System

### Color Palette
- **Primary**: Blue variants (#3b82f6)
- **Secondary**: Green variants (#10b981)
- **Gray Scale**: 50-950 variants
- **Success**: Green (#059669)
- **Warning**: Yellow (#f59e0b)
- **Error**: Red (#dc2626)

### Typography
- **Font Family**: Inter (primary), JetBrains Mono (code)
- **Font Weights**: 300, 400, 500, 600, 700
- **Line Heights**: Optimized for readability

### Components
- **Buttons**: Primary, secondary, outline, ghost variants
- **Cards**: Elevated surfaces with borders
- **Inputs**: Consistent styling with focus states
- **Modals**: Backdrop blur with animations

## 🧪 Testing

### Unit Tests
```bash
npm run test
```

### Test Coverage
```bash
npm run test:coverage
```

### E2E Tests
```bash
npm run test:e2e
```

## 📱 Mobile Responsiveness

- **Mobile-first design** approach
- **Breakpoints**: sm (640px), md (768px), lg (1024px), xl (1280px)
- **Touch-friendly** interface elements
- **Responsive navigation** with mobile menu
- **Optimized card layouts** for all screen sizes

## ♿ Accessibility

- **WCAG 2.1 AA compliance**
- **Screen reader** compatibility
- **Keyboard navigation** support
- **High contrast** mode support
- **Focus indicators** for all interactive elements
- **ARIA labels** and descriptions

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
# Upload dist/ folder to Netlify
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@binsearchpro.com or join our Slack channel.

---

**Built with ❤️ by the BIN Search Pro team**
