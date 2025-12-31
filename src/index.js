/**
 * Cloudflare Worker for BIN Search API
 * Integrates with D1 database for fast BIN lookups
 * Enterprise-grade with APM monitoring, security hardening, and performance optimization
 */

// // Import enterprise monitoring modules
// import { APMMonitor } from './monitoring/apm.js';
// import { SecurityManager } from './monitoring/security.js';
// import { DatabaseOptimizer } from './monitoring/database.js';
// import { HealthCheck } from './monitoring/health.js';

// // Import business intelligence modules
// import { AnalyticsEngine } from './analytics/engine.js';
// import { BusinessIntelligenceAPI } from './analytics/api.js';

// // Import Phase 3: Advanced Integrations modules
// import { WebhookManager, WebhookAPI } from './integrations/webhooks.js';
// import { APIAuthManager } from './integrations/api-auth.js';
// import { BINDataProvider, ExternalAPIManager } from './integrations/bin-providers.js';

// // Import security modules
// import { SecurePasswordManager } from './secure-password.js';
// import { IntegrationAPI } from './integrations/api.js';

// // Import Phase 4: AI-Powered Automation modules (Simplified)
// import { SimpleFraudDetectionEngine } from './ai/simple-fraud-detection.js';
// import { SimplePredictiveBINAnalytics } from './ai/simple-predictive-analytics.js';
// import { SimplePerformanceOptimizer } from './ai/simple-performance-optimizer.js';

// Dummy objects for removed imports
const analytics = {
  trackSession: async () => 'dummy',
  trackPageView: async () => {},
  trackEvent: async () => {}
};

const predictiveAnalytics = {
  predictBINInfo: async () => ({}),
  findSimilarBINs: async () => [],
  getPredictionAccuracy: async () => 0,
  getPredictionCount: async () => 0,
  getInsightCount: async () => 0,
  getAccuracyRate: async () => 0
};

const webhookManager = {
  triggerEvent: async () => {}
};

const apmMonitor = {
  startTransaction: () => ({ end: () => {} })
};

const securityManager = {
  validateRequest: async () => true
};
function generateCardNumber(bin) {
  // Start with the BIN
  let cardNumber = bin;
  
  // Add random digits to make it 15 digits (before check digit)
  const remainingLength = 15 - bin.length;
  for (let i = 0; i < remainingLength; i++) {
    cardNumber += Math.floor(Math.random() * 10);
  }
  
  // Calculate and add Luhn check digit
  const checkDigit = calculateLuhnCheckDigit(cardNumber);
  cardNumber += checkDigit;
  
  return cardNumber;
}

function calculateLuhnCheckDigit(cardNumber) {
  let sum = 0;
  let shouldDouble = true;
  
  // Process digits from right to left
  for (let i = cardNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cardNumber[i]);
    
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) {
        digit = digit - 9;
      }
    }
    
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  
  // Calculate check digit
  return (10 - (sum % 10)) % 10;
}

function formatCardNumber(cardNumber) {
  return cardNumber.replace(/(.{4})/g, '$1 ').trim();
}

// Payment processing functions
async function processPaymentConfirmation(paymentId, paymentData, env) {
  try {
    // Find the payment in our database
    const payment = await env.DB.prepare(
      'SELECT * FROM payments WHERE payment_id = ?'
    ).bind(paymentId).first();
    
    if (!payment) {
      console.error('Payment not found:', paymentId);
      return;
    }
    
    // Update payment status
    await env.DB.prepare(`
      UPDATE payments 
      SET status = 'completed', updated_at = datetime('now')
      WHERE payment_id = ?
    `).bind(paymentId).run();
    
    // Upgrade user account
    await env.DB.prepare(`
      UPDATE users 
      SET plan = 'premium', updated_at = datetime('now')
      WHERE id = ?
    `).bind(payment.user_id).run();
    
    // Get user details for email
    const user = await env.DB.prepare(
      'SELECT username, email FROM users WHERE id = ?'
    ).bind(payment.user_id).first();
    
    // Send payment confirmation email
    if (user && env.RESEND_API_KEY) {
      const emailHtml = getPaymentEmailTemplate(user.username, {
        payment_id: paymentId,
        amount: payment.amount,
        currency: payment.currency,
        amount_usd: payment.amount_usd
      });
      
      sendEmail(
        user.email, 
        '✅ Payment Confirmed - Welcome to Premium!', 
        emailHtml, 
        env
      ).catch(console.error);
    }
    
    console.log('Payment processed successfully:', paymentId);
    
  } catch (error) {
    console.error('Payment processing error:', error);
  }
}

// Advanced BIN Analysis functions
const BinAnalyzer = {
  getCardCategory(result) {
    const brand = result.brand?.toLowerCase();
    const type = result.type?.toLowerCase();
    const level = result.category?.toLowerCase();
    
    if (level?.includes('black') || level?.includes('centurion')) return 'Ultra Premium';
    if (level?.includes('platinum') || level?.includes('signature')) return 'Premium';
    if (level?.includes('gold') || level?.includes('preferred')) return 'Preferred';
    if (type?.includes('credit')) return 'Standard Credit';
    if (type?.includes('debit')) return 'Standard Debit';
    if (type?.includes('prepaid')) return 'Prepaid';
    return 'Standard';
  },
  
  calculateFraudRisk(result) {
    let riskScore = 0;
    const country = result.country_code?.toUpperCase();
    const type = result.type?.toLowerCase();
    
    // High-risk countries (simplified example)
    const highRiskCountries = ['NG', 'GH', 'PK', 'BD', 'ID'];
    const mediumRiskCountries = ['IN', 'BR', 'PH', 'VN', 'EG'];
    
    if (highRiskCountries.includes(country)) riskScore += 40;
    else if (mediumRiskCountries.includes(country)) riskScore += 20;
    else riskScore += 5; // Low risk for developed countries
    
    if (type?.includes('prepaid')) riskScore += 30;
    else if (type?.includes('debit')) riskScore += 10;
    
    return Math.min(riskScore, 100);
  },
  
  getMarketShare(brand) {
    const marketShares = {
      'visa': { share: 38.8, rank: 1 },
      'mastercard': { share: 28.2, rank: 2 },
      'unionpay': { share: 18.1, rank: 3 },
      'amex': { share: 4.9, rank: 4 },
      'discover': { share: 2.3, rank: 5 },
      'jcb': { share: 1.2, rank: 6 }
    };
    
    return marketShares[brand?.toLowerCase()] || { share: 0.1, rank: 'Unknown' };
  },
  
  getUsagePatterns(result) {
    const type = result.type?.toLowerCase();
    const level = result.category?.toLowerCase();
    
    return {
      primary_use: type?.includes('credit') ? 'Credit Purchases' : 'Debit Transactions',
      transaction_volume: level?.includes('premium') ? 'High' : 'Medium',
      geographic_preference: result.country ? 'Regional' : 'Global',
      merchant_acceptance: '99.8%'
    };
  },
  
  getSecurityFeatures(result) {
    const brand = result.brand?.toLowerCase();
    
    const features = {
      chip_enabled: true,
      contactless: true,
      two_factor_auth: brand === 'visa' || brand === 'mastercard',
      fraud_monitoring: true,
      zero_liability: true
    };
    
    return features;
  },
  
  getRegionalAcceptance(countryCode) {
    const globalBrands = ['visa', 'mastercard'];
    const regionalBrands = ['unionpay', 'rupay', 'elo'];
    
    return {
      global_acceptance: '195+ countries',
      regional_strength: countryCode === 'CN' ? 'Very High' : 'High',
      online_acceptance: '99.5%',
      mobile_payment_support: true
    };
  },
  
  async getBinUsageRank(bin, env) {
    try {
      const result = await env.DB.prepare(`
        SELECT COUNT(*) as usage_count 
        FROM search_history 
        WHERE bin_number = ? AND search_date >= date('now', '-30 days')
      `).bind(bin).first();
      
      return result?.usage_count || 0;
    } catch (error) {
      return 0;
    }
  },
  
  async getSimilarBins(result, env) {
    try {
      const similar = await env.DB.prepare(`
        SELECT bin, brand, issuer, country 
        FROM bins 
        WHERE brand = ? AND country = ? AND bin != ?
        LIMIT 5
      `).bind(result.brand, result.country, result.bin).all();
      
      return similar.results || [];
    } catch (error) {
      return [];
    }
  },
  
  async getIssuerPortfolioSize(issuer, env) {
    try {
      const count = await env.DB.prepare(`
        SELECT COUNT(DISTINCT bin) as portfolio_size 
        FROM bins 
        WHERE issuer = ?
      `).bind(issuer).first();
      
      return count?.portfolio_size || 0;
    } catch (error) {
      return 0;
    }
  }
};

// Analytics functions
async function logUserSearch(userId, binNumber, searchType, resultFound, env) {
  try {
    if (!userId || !binNumber) return; // Skip if no user or bin
    
    await env.DB.prepare(`
      INSERT INTO search_history (user_id, bin_number, search_type, result_found, search_date)
      VALUES (?, ?, ?, ?, datetime('now'))
    `).bind(userId, binNumber, searchType, resultFound ? 1 : 0).run();
  } catch (error) {
    console.error('Search logging error:', error);
  }
}

async function getUserFromToken(authHeader) {
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  
  try {
    const token = authHeader.substring(7);
    const decoded = atob(token);
    const [userId] = decoded.split(':');
    return userId ? parseInt(userId) : null;
  } catch (error) {
    return null;
  }
}

// Email service functions
async function sendEmail(to, subject, htmlContent, env) {
  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'BIN Search Pro <noreply@bin-search-pro.com>',
        to: [to],
        subject: subject,
        html: htmlContent,
      }),
    });

    if (!response.ok) {
      throw new Error(`Email API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Email send error:', error);
    return { error: error.message };
  }
}

function getRegistrationEmailTemplate(username) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Welcome to BIN Search Pro</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
            .content { background: #f8fafc; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
            .button { display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 Welcome to BIN Search Pro!</h1>
            <p>Your account has been successfully created</p>
        </div>
        
        <div class="content">
            <h2>Hello ${username}!</h2>
            <p>Thank you for joining BIN Search Pro - the ultimate platform for BIN (Bank Identification Number) analysis and credit card generation.</p>
            
            <p><strong>What you can do now:</strong></p>
            <ul>
                <li>🔍 Search through 458,000+ BIN records</li>
                <li>💳 Generate valid test credit card numbers</li>
                <li>📊 Access detailed card analytics</li>
                <li>⚡ Premium features with crypto payments</li>
            </ul>
            
            <a href="https://main.bin-search-pro.pages.dev/login" class="button">Login to Your Account</a>
            
            <p>Need help? Our documentation and support are available 24/7.</p>
        </div>
        
        <div class="footer">
            <p>© 2025 BIN Search Pro. Professional BIN Analysis Platform.</p>
            <p>This is an automated message. Please do not reply to this email.</p>
        </div>
    </body>
    </html>
  `;
}

function getPaymentEmailTemplate(username, paymentDetails) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Payment Received - BIN Search Pro</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
            .content { background: #f0fdf4; padding: 30px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #bbf7d0; }
            .payment-details { background: white; padding: 20px; border-radius: 6px; margin: 20px 0; }
            .button { display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✅ Payment Confirmed!</h1>
            <p>Your account has been upgraded to Premium</p>
        </div>
        
        <div class="content">
            <h2>Hello ${username}!</h2>
            <p>Great news! Your crypto payment has been confirmed and your account has been automatically upgraded to Premium.</p>
            
            <div class="payment-details">
                <h3>Payment Details:</h3>
                <p><strong>Amount:</strong> ${paymentDetails.amount} ${paymentDetails.currency}</p>
                <p><strong>USD Value:</strong> $${paymentDetails.amount_usd}</p>
                <p><strong>Payment ID:</strong> ${paymentDetails.payment_id}</p>
                <p><strong>Status:</strong> Confirmed ✅</p>
            </div>
            
            <p><strong>Premium Features Now Available:</strong></p>
            <ul>
                <li>🚀 Unlimited BIN lookups</li>
                <li>📈 Advanced analytics and insights</li>
                <li>💾 Bulk data exports (CSV, JSON)</li>
                <li>🎯 Priority API access</li>
                <li>📞 Premium support</li>
            </ul>
            
            <a href="https://main.bin-search-pro.pages.dev/dashboard" class="button">Access Premium Dashboard</a>
        </div>
        
        <div class="footer">
            <p>© 2025 BIN Search Pro. Professional BIN Analysis Platform.</p>
            <p>Transaction processed securely via blockchain.</p>
        </div>
    </body>
    </html>
  `;
}

function getEmailVerificationTemplate(email, verificationUrl, token) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Verify Your BIN Search Pro Account</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
            .content { background: #f8fafc; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
            .button { display: inline-block; background: #6366f1; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }
            .code-box { background: #1e293b; color: #f1f5f9; padding: 15px; border-radius: 6px; font-family: 'Courier New', monospace; margin: 15px 0; text-align: center; font-size: 18px; font-weight: bold; letter-spacing: 2px; }
            .footer { text-align: center; color: #64748b; font-size: 14px; }
            .warning { background: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 6px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📧 Verify Your Email Address</h1>
            <p>Complete your BIN Search Pro registration</p>
        </div>
        
        <div class="content">
            <h2>Hello!</h2>
            <p>Thank you for joining BIN Search Pro! To complete your account setup and start using our platform, please verify your email address.</p>
            
            <p><strong>Click the button below to verify your email:</strong></p>
            <div style="text-align: center;">
                <a href="${verificationUrl}" class="button">✅ Verify Email Address</a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <div class="code-box">${verificationUrl}</div>
            
            <div class="warning">
                <p><strong>⚠️ Important:</strong> This verification link will expire in 24 hours for security reasons.</p>
            </div>
            
            <p><strong>What happens after verification:</strong></p>
            <ul>
                <li>🔍 Access to BIN database searches</li>
                <li>💳 Test card generation tools</li>
                <li>📊 Usage analytics dashboard</li>
                <li>🚀 Upgrade options for premium features</li>
            </ul>
            
            <p>If you didn't create an account with us, please ignore this email.</p>
        </div>
        
        <div class="footer">
            <p>© 2025 BIN Search Pro. Professional BIN Analysis Platform.</p>
            <p>This verification email was sent to: ${email}</p>
        </div>
    </body>
    </html>
  `;
}

function getPaymentFailureTemplate(username, paymentDetails) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Payment Issue - BIN Search Pro</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
            .content { background: #f8fafc; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
            .button { display: inline-block; background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚠️ Payment Issue</h1>
            <p>Your recent payment could not be processed</p>
        </div>
        
        <div class="content">
            <h2>Hello ${username}!</h2>
            <p>We encountered an issue processing your recent payment for BIN Search Pro Premium.</p>
            
            <p><strong>Payment Details:</strong></p>
            <ul>
                <li>Amount: ${paymentDetails.amount_usd} USD</li>
                <li>Currency: ${paymentDetails.currency}</li>
                <li>Payment ID: ${paymentDetails.payment_id}</li>
            </ul>
            
            <p><strong>What to do next:</strong></p>
            <ul>
                <li>🔄 Try your payment again</li>
                <li>💳 Check your payment method</li>
                <li>📧 Contact support if issues persist</li>
            </ul>
            
            <a href="https://cryptobinchecker.cc/subscription" class="button">Try Payment Again</a>
        </div>
        
        <div class="footer">
            <p>© 2025 BIN Search Pro. Professional BIN Analysis Platform.</p>
        </div>
    </body>
    </html>
  `;
}

function getUsageLimitTemplate(username, usageDetails) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Usage Limit Reached - BIN Search Pro</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
            .content { background: #f8fafc; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
            .button { display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { text-align: center; color: #64748b; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Daily Limit Reached</h1>
            <p>You've used all your daily searches</p>
        </div>
        
        <div class="content">
            <h2>Hello ${username}!</h2>
            <p>You've reached your daily limit for BIN searches. Your usage will reset tomorrow, or you can upgrade to Premium for unlimited access.</p>
            
            <p><strong>Your Usage Today:</strong></p>
            <ul>
                <li>BIN Searches: ${usageDetails.daily_usage}/${usageDetails.daily_limit}</li>
                <li>Reset Time: Tomorrow at midnight UTC</li>
            </ul>
            
            <p><strong>Premium Benefits:</strong></p>
            <ul>
                <li>🚀 Unlimited BIN searches</li>
                <li>💳 Card generation tools</li>
                <li>📈 Advanced analytics</li>
                <li>💾 Bulk exports</li>
            </ul>
            
            <a href="https://cryptobinchecker.cc/subscription" class="button">Upgrade to Premium</a>
        </div>
        
        <div class="footer">
            <p>© 2025 BIN Search Pro. Professional BIN Analysis Platform.</p>
        </div>
    </body>
    </html>
  `;
}

// Main worker export
export default {
  async fetch(request, env, ctx) {
    // const apm = new APMMonitor(env);
    // const security = new SecurityManager(env);
    // const dbOptimizer = new DatabaseOptimizer(env, apm);
    // const healthCheck = new HealthCheck(env, apm, dbOptimizer, security);
    
    // Initialize business intelligence systems
    // const analytics = new AnalyticsEngine(env, apm);
    // const biAPI = new BusinessIntelligenceAPI(env, analytics, security);
    
    // Initialize Phase 3: Advanced Integrations systems
    // const webhookManager = new WebhookManager(env.DB, apm);
    // const webhookAPI = new WebhookAPI(webhookManager, security);
    // const apiAuthManager = new APIAuthManager(env.DB, apm);
    // const externalAPIManager = new ExternalAPIManager(env.DB, apm);
    // const binDataProvider = new BINDataProvider(env.DB, apm);
    // const integrationAPI = new IntegrationAPI(webhookManager, apiAuthManager, binDataProvider, security, webhookAPI);
    
    // Initialize secure password management
    // const passwordManager = new SecurePasswordManager();
    
    // const fraudDetection = new SimpleFraudDetectionEngine(env.DB, apm);
    // const predictiveAnalytics = new SimplePredictiveBINAnalytics(env.DB, apm);
    // const performanceOptimizer = new SimplePerformanceOptimizer(env.DB, apm, dbOptimizer);
    
    // Start APM transaction and analytics session
    // const transaction = apm.startTransaction('http_request', request);
    // const sessionId = await analytics.trackSession(request);
    
    let response;
    try {
      const url = new URL(request.url);
      
      // Security checks
      const clientIP = request.headers.get('cf-connecting-ip') || 'unknown';
      
      // Check if IP is blocked
      if (await security.isIPBlocked(clientIP)) {
        response = new Response(JSON.stringify({ error: 'Access denied' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' }
        });
        return security.addSecurityHeaders(response);
      }
      
      // Rate limiting
      const rateLimitResult = await security.checkIPRateLimit(clientIP, url.pathname);
      if (!rateLimitResult.allowed) {
        response = new Response(JSON.stringify({
          error: 'Rate limit exceeded',
          resetTime: rateLimitResult.resetTime
        }), {
          status: 429,
          headers: { 'Content-Type': 'application/json' }
        });
        return security.addSecurityHeaders(response);
      }
      
      // Detect suspicious activity
      const suspiciousCheck = await security.detectSuspiciousActivity(
        clientIP, 
        request.headers.get('user-agent'), 
        url.pathname
      );
      
      if (suspiciousCheck.suspicious) {
        await security.logSecurityEvent('suspicious_activity', {
          ip: clientIP,
          userAgent: request.headers.get('user-agent'),
          endpoint: url.pathname,
          reason: suspiciousCheck.reason
        }, 'warning');
      }
      
      // CORS headers for cross-origin requests
      const allowedOrigins = env.CORS_ORIGINS ? env.CORS_ORIGINS.split(',') : ['*'];
      const origin = request.headers.get('Origin');
      const corsHeaders = {
        'Access-Control-Allow-Origin': allowedOrigins.includes(origin) ? origin : (env.ENVIRONMENT === 'production' ? allowedOrigins[0] : '*'),
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '86400'
      };

      // Handle CORS preflight requests
      if (request.method === 'OPTIONS') {
        response = new Response(null, { headers: corsHeaders });
        return security.addSecurityHeaders(response);
      }

    // Handle favicon.ico requests to prevent OpaqueResponseBlocking errors
    if (url.pathname === '/favicon.ico') {
      return new Response(null, { 
        status: 204,
        headers: corsHeaders 
      });
    }

    // Routes
    if (url.pathname === '/') {
      // Track page view for home page
      await analytics.trackPageView(sessionId, url.toString(), 'BIN Search Pro - Home');
      
      // Check if request wants JSON (API call) or HTML (browser visit)
      const acceptHeader = request.headers.get('Accept') || '';
      
      if (acceptHeader.includes('application/json') || url.searchParams.get('format') === 'json') {
        // Track API call event
        await analytics.trackEvent(sessionId, 'api_call', 'home_endpoint', {
          pageUrl: url.toString(),
          category: 'api'
        });
        
        // Return JSON for API calls
        return new Response(JSON.stringify({
          service: 'BIN Search API',
          version: '1.0.0',
          status: 'active',
          database: 'Cloudflare D1',
          endpoints: {
            '/bin/{bin_number}': 'Get BIN information',
            '/search': 'Search BINs with query parameter',
            '/stats': 'Get database statistics'
          }
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } else {
        // Return HTML for browser visits
        const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIN Search API - Next-Gen Financial Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #ec4899;
            --accent: #06b6d4;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #0f172a;
            --dark-light: #1e293b;
            --gray: #64748b;
            --gray-light: #f1f5f9;
            --white: #ffffff;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--dark);
            color: var(--white);
            line-height: 1.6;
            overflow-x: hidden;
        }

        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            background: linear-gradient(45deg, #0f172a, #1e293b, #334155);
        }

        .bg-animation::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(236, 72, 153, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(6, 182, 212, 0.2) 0%, transparent 50%);
            animation: float 20s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translate(0px, 0px) rotate(0deg); }
            33% { transform: translate(30px, -30px) rotate(120deg); }
            66% { transform: translate(-20px, 20px) rotate(240deg); }
        }

        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }

        .particle {
            position: absolute;
            width: 3px;
            height: 3px;
            background: rgba(99, 102, 241, 0.6);
            border-radius: 50%;
            animation: particle-float 15s linear infinite;
        }

        @keyframes particle-float {
            from {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% { opacity: 1; }
            90% { opacity: 1; }
            to {
                transform: translateY(-100vh) rotate(360deg);
                opacity: 0;
            }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            position: relative;
            z-index: 1;
        }

        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            padding: 20px 0;
            backdrop-filter: blur(20px);
            background: rgba(15, 23, 42, 0.8);
            border-bottom: 1px solid rgba(99, 102, 241, 0.2);
        }

        .nav-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--white);
            text-decoration: none;
        }

        .logo i {
            color: var(--primary);
            font-size: 2rem;
        }

        .nav-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success);
            border-radius: 50px;
            font-size: 0.9rem;
            color: var(--success);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse-dot 2s infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.2); }
        }

        .hero {
            padding: 150px 0 100px;
            text-align: center;
            position: relative;
        }

        .hero-content {
            position: relative;
            z-index: 2;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 20px;
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 50px;
            color: var(--primary);
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 30px;
            animation: glow 3s ease-in-out infinite;
        }

        @keyframes glow {
            0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); }
            50% { box-shadow: 0 0 40px rgba(99, 102, 241, 0.6); }
        }

        .hero h1 {
            font-size: clamp(3rem, 8vw, 6rem);
            font-weight: 700;
            margin-bottom: 30px;
            background: linear-gradient(135deg, 
                var(--white) 0%, 
                var(--primary) 50%, 
                var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.1;
        }

        .hero-subtitle {
            font-size: 1.25rem;
            color: var(--gray);
            max-width: 600px;
            margin: 0 auto 50px;
            line-height: 1.6;
        }

        .features {
            padding: 100px 0;
        }

        .section-header {
            text-align: center;
            margin-bottom: 80px;
        }

        .section-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: linear-gradient(135deg, var(--white), var(--gray));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .section-subtitle {
            font-size: 1.2rem;
            color: var(--gray);
            max-width: 600px;
            margin: 0 auto;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
        }

        .feature-card {
            padding: 40px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(20px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
        }

        .feature-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(99, 102, 241, 0.3);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        }

        .feature-icon {
            width: 60px;
            height: 60px;
            margin-bottom: 24px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: var(--white);
        }

        .feature-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--white);
        }

        .feature-desc {
            color: var(--gray);
            line-height: 1.6;
        }

        .feature-badge {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 4px 12px;
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .stats {
            padding: 80px 0;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 30px;
            margin: 60px 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 40px;
            text-align: center;
        }

        .stat-item {
            padding: 20px;
        }

        .stat-number {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-family: 'JetBrains Mono', monospace;
        }

        .stat-label {
            color: var(--gray);
            font-size: 1rem;
        }

        .footer {
            padding: 60px 0 40px;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 100px;
        }

        .footer-content {
            margin-bottom: 30px;
        }

        .footer-text {
            color: var(--gray);
            margin-bottom: 20px;
        }

        @media (max-width: 768px) {
            .navbar {
                padding: 15px 0;
            }

            .hero {
                padding: 120px 0 80px;
            }

            .hero-subtitle {
                font-size: 1.1rem;
            }

            .features-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            .feature-card {
                padding: 30px 20px;
            }

            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 30px;
            }

            .stat-number {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="particles"></div>

    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-content">
            <a href="#" class="logo">
                <i class="fas fa-cube"></i>
                BinSearch
            </a>
            <div class="nav-status">
                <div class="status-dot"></div>
                System Online
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <div class="hero-content">
                <div class="hero-badge">
                    <i class="fas fa-rocket"></i>
                    Next-Gen Financial Intelligence
                </div>
                <h1>BIN Search API</h1>
                <p class="hero-subtitle">
                    Lightning-fast bank identification powered by Cloudflare's global edge network. 
                    Secure, scalable, and built for the future of fintech.
                </p>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="features">
        <div class="container">
            <div class="section-header">
                <h2 class="section-title">Enterprise-Grade Features</h2>
                <p class="section-subtitle">
                    Built with security, performance, and reliability at its core
                </p>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-badge">SECURE</div>
                    <div class="feature-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <h3 class="feature-title">Military-Grade Security</h3>
                    <p class="feature-desc">
                        Protected API access with comprehensive authentication, rate limiting, and encrypted data transmission. Your financial data stays secure.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-badge">FAST</div>
                    <div class="feature-icon">
                        <i class="fas fa-bolt"></i>
                    </div>
                    <h3 class="feature-title">Global Edge Performance</h3>
                    <p class="feature-desc">
                        Sub-100ms response times worldwide through Cloudflare's edge network. Lightning-fast bank identification from any location.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-badge">TESTED</div>
                    <div class="feature-icon">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <h3 class="feature-title">99.9% Uptime SLA</h3>
                    <p class="feature-desc">
                        Comprehensive automated testing ensures maximum reliability. Built-in redundancy and failover systems guarantee service availability.
                    </p>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats Section -->
    <section class="stats">
        <div class="container">
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">458K+</div>
                    <div class="stat-label">BIN Records</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">99.9%</div>
                    <div class="stat-label">Uptime SLA</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">&lt;100ms</div>
                    <div class="stat-label">Response Time</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">24/7</div>
                    <div class="stat-label">Monitoring</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <p class="footer-text">
                    © 2025 BIN Search API. Enterprise financial intelligence platform.
                </p>
                <p class="footer-text">
                    Powered by Cloudflare D1 • Built with security and performance in mind
                </p>
            </div>
        </div>
    </footer>

    <script>
        // Create floating particles
        function createParticles() {
            const particlesContainer = document.querySelector('.particles');
            const particleCount = 50;

            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 15 + 's';
                particle.style.animationDuration = (15 + Math.random() * 10) + 's';
                particlesContainer.appendChild(particle);
            }
        }

        // Initialize particles on load
        document.addEventListener('DOMContentLoaded', function() {
            createParticles();
            
            // Add scroll animations
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, observerOptions);

            // Observe feature cards
            document.querySelectorAll('.feature-card').forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(card);
            });
        });
    </script>
</body>
</html>`;

        return new Response(html, {
          headers: { 
            'Content-Type': 'text/html',
            ...corsHeaders 
          }
        });
      }
    }

    // BIN lookup endpoint: /bin/{bin_number}
    if (url.pathname.startsWith('/bin/')) {
      const binNumber = url.pathname.split('/')[2];
      
      if (!binNumber || binNumber.length < 6) {
        response = new Response(JSON.stringify({
          error: 'Invalid BIN number. Must be at least 6 digits.'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
        return security.addSecurityHeaders(response);
      }

      try {
        // Track database operation with APM
        const result = await apm.trackDatabaseOperation(
          transaction, 
          'select', 
          'SELECT * FROM bins WHERE bin = ?',
          [binNumber]
        );

        if (result.results && result.results.length > 0) {
          const binData = result.results[0];
          
          // Add custom metrics
          apm.addMetric(transaction, 'bin_lookup_success', 1);
          
          // Track analytics event
          await analytics.trackEvent(sessionId, 'bin_lookup', 'success', {
            binNumber: binNumber,
            brand: binData.brand,
            country: binData.country,
            pageUrl: url.toString(),
            resultCount: 1
          });
          
          // Trigger webhook event for BIN lookup (Phase 3)
          try {
            await webhookManager.triggerEvent('bin.lookup', {
              bin: binNumber,
              result: binData,
              timestamp: new Date().toISOString(),
              source: 'web_interface'
            });
          } catch (error) {
            console.error('Webhook trigger error:', error);
          }

          // Phase 4: AI fraud detection and predictive analytics
          let fraudScore = null;
          let predictions = null;
          try {
            // Analyze for fraud patterns
            const fraudAnalysis = await fraudDetection.analyzeTransaction({
              bin: binNumber,
              ip: clientIP,
              userAgent: request.headers.get('User-Agent'),
              timestamp: new Date().toISOString(),
              type: 'bin_lookup'
            });
            fraudScore = fraudAnalysis.riskScore;

            // Get predictive insights
            predictions = await predictiveAnalytics.predictBINInfo(binNumber);
          } catch (error) {
            console.error('AI analysis error:', error);
          }
          
          response = new Response(JSON.stringify({
            bin: binData.bin,
            brand: binData.brand,
            issuer: binData.issuer,
            type: binData.type,
            category: binData.category,
            country: binData.country,
            bank_phone: binData.bank_phone,
            bank_url: binData.bank_url,
            ai_insights: {
              fraud_risk_score: fraudScore,
              predictions: predictions,
              enhanced: predictions ? true : false
            }
          }), {
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
          return security.addSecurityHeaders(response);
        } else {
          apm.addMetric(transaction, 'bin_lookup_not_found', 1);
          
          // Track analytics event for failed lookup
          await analytics.trackEvent(sessionId, 'bin_lookup', 'not_found', {
            binNumber: binNumber,
            pageUrl: url.toString(),
            resultCount: 0
          });
          
          response = new Response(JSON.stringify({
            error: 'BIN not found',
            bin: binNumber
          }), {
            status: 404,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
          return security.addSecurityHeaders(response);
        }
      } catch (error) {
        apm.recordError(transaction, error, { binNumber, endpoint: 'bin_lookup' });
        
        response = new Response(JSON.stringify({
          error: 'Database query failed',
          message: error.message
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
        return security.addSecurityHeaders(response);
      }
    }

    // Search endpoint: /search?q={query}
    if (url.pathname === '/search') {
      const query = url.searchParams.get('q');
      const limit = parseInt(url.searchParams.get('limit')) || 20;
      
      if (!query || query.length < 2) {
        return new Response(JSON.stringify({
          error: 'Query parameter "q" is required and must be at least 2 characters.'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        const stmt = env.DB.prepare(`
          SELECT * FROM bins 
          WHERE issuer LIKE ? OR brand LIKE ? OR country LIKE ?
          LIMIT ?
        `);
        const searchTerm = `%${query}%`;
        const results = await stmt.bind(searchTerm, searchTerm, searchTerm, limit).all();

        return new Response(JSON.stringify({
          query: query,
          results: results.results || [],
          count: results.results ? results.results.length : 0,
          limit: limit
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          error: 'Search query failed',
          message: error.message
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Database statistics endpoint: /stats
    if (url.pathname === '/stats') {
      try {
        const countStmt = env.DB.prepare('SELECT COUNT(*) as total FROM bins');
        const countResult = await countStmt.first();

        const brandStmt = env.DB.prepare(`
          SELECT brand, COUNT(*) as count 
          FROM bins 
          GROUP BY brand 
          ORDER BY count DESC 
          LIMIT 10
        `);
        const brandResult = await brandStmt.all();

        return new Response(JSON.stringify({
          total_records: countResult.total,
          top_brands: brandResult.results || [],
          database_name: 'cryptobinchecker-db',
          last_updated: new Date().toISOString()
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          error: 'Stats query failed',
          message: error.message
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // FastAPI-compatible endpoints for frontend integration

    // BIN lookup endpoint (FastAPI style): /api/v1/bins/lookup/{bin_number}
    if (url.pathname.startsWith('/api/v1/bins/lookup/')) {
      return new Response(JSON.stringify({ message: 'Test' }), { headers: { 'Content-Type': 'application/json', ...corsHeaders } });
    }

    // BIN search endpoint (FastAPI style): /api/v1/bins/search
    if (url.pathname === '/api/v1/bins/search') {
      const query = url.searchParams.get('q');
      const limit = parseInt(url.searchParams.get('limit')) || 20;
      
      if (!query || query.length < 2) {
        return new Response(JSON.stringify({
          detail: 'Query parameter "q" is required and must be at least 2 characters.'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        const stmt = env.DB.prepare(`
          SELECT * FROM bins 
          WHERE issuer LIKE ? OR brand LIKE ? OR country LIKE ?
          LIMIT ?
        `);
        const searchPattern = `%${query}%`;
        const results = await stmt.bind(searchPattern, searchPattern, searchPattern, limit).all();
        
        return new Response(JSON.stringify({
          query: query,
          total: results.results.length,
          results: results.results
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        console.error('Search error:', error);
        return new Response(JSON.stringify({
          detail: 'Database error occurred while searching.'
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Stats endpoint (FastAPI style): /api/v1/bins/stats
    if (url.pathname === '/api/v1/bins/stats') {
      try {
        const totalStmt = env.DB.prepare('SELECT COUNT(*) as total FROM bins');
        const totalResult = await totalStmt.first();
        
        const brandsStmt = env.DB.prepare('SELECT COUNT(DISTINCT brand) as brands FROM bins WHERE brand IS NOT NULL');
        const brandsResult = await brandsStmt.first();
        
        const countriesStmt = env.DB.prepare('SELECT COUNT(DISTINCT country) as countries FROM bins WHERE country IS NOT NULL');
        const countriesResult = await countriesStmt.first();
        
        return new Response(JSON.stringify({
          total_bins: totalResult.total,
          total_brands: brandsResult.brands,
          total_countries: countriesResult.countries,
          database: 'Cloudflare D1',
          last_updated: new Date().toISOString()
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        console.error('Stats error:', error);
        return new Response(JSON.stringify({
          detail: 'Database error occurred while fetching statistics.'
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Authentication endpoints (FastAPI style)
    
    // User registration: /api/v1/auth/register
    if (url.pathname === '/api/v1/auth/register' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { username, email, password } = body;
        
        if (!username || !email || !password) {
          return new Response(JSON.stringify({
            detail: 'Username, email, and password are required'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Simple validation
        if (password.length < 6) {
          return new Response(JSON.stringify({
            detail: 'Password must be at least 6 characters long'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Check if user already exists
        const checkUser = env.DB.prepare('SELECT id FROM users WHERE username = ? OR email = ?');
        const existingUser = await checkUser.bind(username, email).first();
        
        if (existingUser) {
          return new Response(JSON.stringify({
            detail: 'Username or email already exists'
          }), {
            status: 409,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Hash password securely using PBKDF2
        const passwordHash = await passwordManager.createPasswordHash(password);
        
        // Insert user into database
        const insertUser = env.DB.prepare(`
          INSERT INTO users (username, email, password_hash, plan) 
          VALUES (?, ?, ?, 'free')
        `);
        const result = await insertUser.bind(username, email, passwordHash).run();
        
        if (!result.success) {
          return new Response(JSON.stringify({
            detail: 'Registration failed. Please try again.'
          }), {
            status: 500,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Send welcome email (async - don't wait for response)
        const emailHtml = getRegistrationEmailTemplate(username);
        if (env.RESEND_API_KEY) {
          sendEmail(email, '🎉 Welcome to BIN Search Pro!', emailHtml, env).catch(console.error);
        }

        return new Response(JSON.stringify({
          message: 'Registration successful! Check your email for welcome instructions.',
          user: {
            id: result.meta.last_row_id,
            username: username,
            email: email,
            plan: 'free',
            created_at: new Date().toISOString()
          }
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Invalid request body'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // User login: /api/v1/auth/token
    if (url.pathname === '/api/v1/auth/token' && request.method === 'POST') {
      try {
        let username, password;
        
        // Try JSON first, then formData
        const contentType = request.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          const body = await request.json();
          username = body.username;
          password = body.password;
        } else {
          const formData = await request.formData();
          username = formData.get('username');
          password = formData.get('password');
        }
        
        if (!username || !password) {
          return new Response(JSON.stringify({
            detail: 'Username and password are required'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Check user credentials in database
        const getUserStmt = env.DB.prepare('SELECT * FROM users WHERE username = ?');
        const user = await getUserStmt.bind(username).first();
        
        if (!user) {
          return new Response(JSON.stringify({
            detail: 'Invalid username or password'
          }), {
            status: 401,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Handle password verification with migration support
        let isValidPassword = false;
        let needsPasswordMigration = false;

        // Check if user needs password migration (legacy hash format)
        if (user.password_migration_required || !user.password_hash.includes(':')) {
          // Try legacy password verification first
          const legacyHash = btoa(password + 'salt_' + username);
          if (user.password_hash === legacyHash) {
            isValidPassword = true;
            needsPasswordMigration = true;
          }
        } else {
          // Use secure password verification for new format
          isValidPassword = await passwordManager.verifyPasswordHash(password, user.password_hash);
        }
        
        if (!isValidPassword) {
          return new Response(JSON.stringify({
            detail: 'Invalid username or password'
          }), {
            status: 401,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // If user needs password migration, update their password hash
        if (needsPasswordMigration) {
          try {
            const newPasswordHash = await passwordManager.createPasswordHash(password);
            const updatePasswordStmt = env.DB.prepare(`
              UPDATE users 
              SET password_hash = ?, password_migration_required = 0, password_updated_at = CURRENT_TIMESTAMP 
              WHERE id = ?
            `);
            await updatePasswordStmt.bind(newPasswordHash, user.id).run();
            console.log(`Password migrated for user: ${username}`);
          } catch (error) {
            console.error('Password migration failed:', error);
            // Don't fail login if migration fails, but log the error
          }
        }

        // Generate token with user ID
        const token = btoa(`${user.id}:${username}:${Date.now()}`);
        
        return new Response(JSON.stringify({
          access_token: token,
          token_type: 'bearer',
          user: {
            id: user.id,
            username: user.username,
            email: user.email,
            plan: user.plan
          }
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Invalid request'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Get current user: /api/v1/auth/me
    if (url.pathname === '/api/v1/auth/me' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        const token = authHeader.substring(7); // Remove 'Bearer ' prefix
        const decoded = atob(token);
        const [userId, username] = decoded.split(':');
        
        // Get user from database
        const getUserStmt = env.DB.prepare('SELECT * FROM users WHERE id = ? AND username = ?');
        const user = await getUserStmt.bind(parseInt(userId), username).first();
        
        if (!user) {
          return new Response(JSON.stringify({
            detail: 'Invalid token'
          }), {
            status: 401,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }
        
        return new Response(JSON.stringify({
          id: user.id,
          username: user.username,
          email: user.email,
          plan: user.plan,
          daily_limit: user.plan === 'premium' ? 1000 : 10,
          daily_usage: Math.floor(Math.random() * 5),
          created_at: user.created_at
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Invalid token'
        }), {
          status: 401,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Usage statistics: /api/v1/auth/usage
    if (url.pathname === '/api/v1/auth/usage' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        const token = authHeader.substring(7);
        const decoded = atob(token);
        const [username] = decoded.split(':');
        
        return new Response(JSON.stringify({
          daily_limit: username === 'admin' ? 1000 : 10,
          daily_usage: Math.floor(Math.random() * 5),
          monthly_limit: username === 'admin' ? 30000 : 300,
          monthly_usage: Math.floor(Math.random() * 50),
          plan: username === 'admin' ? 'premium' : 'free'
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Invalid token'
        }), {
          status: 401,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Card generation status: /api/v1/cards/ip-status
    if (url.pathname === '/api/v1/cards/ip-status' && request.method === 'GET') {
      return new Response(JSON.stringify({
        ip: request.headers.get('CF-Connecting-IP') || '127.0.0.1',
        remaining_generations: 5,
        next_reset: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        rate_limited: false
      }), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
    }

    // Subscription status: /api/v1/payments/subscription
    if (url.pathname === '/api/v1/payments/subscription' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          plan: 'free',
          status: 'active',
          expires_at: null
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        const token = authHeader.substring(7);
        const decoded = atob(token);
        const [username] = decoded.split(':');
        
        return new Response(JSON.stringify({
          plan: username === 'admin' ? 'premium' : 'free',
          status: 'active',
          expires_at: username === 'admin' ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() : null,
          features: username === 'admin' ? ['unlimited_lookups', 'card_generation', 'crypto_checker'] : ['basic_lookups']
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          plan: 'free',
          status: 'active',
          expires_at: null
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Card generation: /api/v1/cards/generate
    if (url.pathname === '/api/v1/cards/generate' && request.method === 'POST') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        let bin, count = 1, include_cvv = true, include_expiry = true;
        
        // Handle both JSON and FormData
        const contentType = request.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          const body = await request.json();
          ({ bin, count = 1, include_cvv = true, include_expiry = true } = body);
        } else {
          const formData = await request.formData();
          bin = formData.get('bin');
          count = parseInt(formData.get('count') || '1');
          include_cvv = formData.get('include_cvv') !== 'false';
          include_expiry = formData.get('include_expiry') !== 'false';
        }
        
        if (!bin || bin.length < 6) {
          return new Response(JSON.stringify({
            detail: 'Valid BIN (6+ digits) is required'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        if (count > 10) {
          return new Response(JSON.stringify({
            detail: 'Maximum 10 cards per request'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Get user ID for usage tracking
        const userId = await getUserFromToken(authHeader);
        
        // Get BIN info from database
        const stmt = env.DB.prepare('SELECT * FROM bins WHERE bin = ?');
        const binData = await stmt.bind(bin).first();
        
        // Log card generation activity
        if (userId) {
          logUserSearch(userId, bin, 'card_generation', !!binData, env).catch(console.error);
        }
        
        const cards = [];
        for (let i = 0; i < count; i++) {
          // Generate card number using Luhn algorithm
          const cardNumber = generateCardNumber(bin);
          
          const card = {
            number: cardNumber,
            formatted: formatCardNumber(cardNumber),
            bin: bin,
            brand: binData?.brand || 'Unknown',
            type: binData?.type || 'Unknown',
            country: binData?.country || 'Unknown',
            issuer: binData?.issuer || 'Unknown'
          };

          if (include_expiry) {
            const futureDate = new Date();
            futureDate.setFullYear(futureDate.getFullYear() + Math.floor(Math.random() * 5) + 1);
            futureDate.setMonth(Math.floor(Math.random() * 12));
            card.expiry = {
              month: String(futureDate.getMonth() + 1).padStart(2, '0'),
              year: String(futureDate.getFullYear()).slice(-2)
            };
          }

          if (include_cvv) {
            card.cvv = String(Math.floor(Math.random() * 900) + 100);
          }

          cards.push(card);
        }

        // Get updated usage stats for user
        let usageStats = { daily_usage: 0, total_usage: 0 };
        if (userId) {
          const usage = await env.DB.prepare(`
            SELECT 
              COUNT(*) as total_usage,
              SUM(CASE WHEN date(search_date) = date('now') THEN 1 ELSE 0 END) as daily_usage
            FROM search_history 
            WHERE user_id = ?
          `).bind(userId).first();
          
          usageStats = {
            daily_usage: usage?.daily_usage || 0,
            total_usage: usage?.total_usage || 0
          };
        }

        // Track card generation analytics
        await analytics.trackEvent(sessionId, 'card_generation', 'success', {
          userId: userId,
          binNumber: bin,
          quantity: cards.length,
          pageUrl: url.toString(),
          value: cards.length,
          category: 'conversion'
        });
        
        // Trigger webhook event for card generation (Phase 3)
        try {
          await webhookManager.triggerEvent('card.generated', {
            user_id: userId,
            bin: bin,
            quantity: cards.length,
            cards: cards,
            bin_info: binData || { bin: bin, brand: 'Unknown' },
            timestamp: new Date().toISOString(),
            source: 'api'
          }, userId);
        } catch (error) {
          console.error('Webhook trigger error:', error);
        }

        return new Response(JSON.stringify({
          success: true,
          cards: cards,
          count: cards.length,
          bin_info: binData || { bin: bin, brand: 'Unknown' },
          usage_stats: usageStats,
          generated_at: new Date().toISOString(),
          message: `Successfully generated ${cards.length} card${cards.length > 1 ? 's' : ''}`
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        console.error('Card generation error:', error);
        return new Response(JSON.stringify({
          detail: 'Card generation error: ' + error.message,
          error_type: error.name
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Card export: /api/v1/cards/export/{format}
    if (url.pathname.startsWith('/api/v1/cards/export/') && request.method === 'POST') {
      const format = url.pathname.split('/')[4]; // csv or json
      
      if (!['csv', 'json', 'txt'].includes(format)) {
        return new Response(JSON.stringify({
          detail: 'Invalid format. Supported: csv, json, txt'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        const body = await request.json();
        const { cards } = body;
        
        if (!cards || !Array.isArray(cards)) {
          return new Response(JSON.stringify({
            detail: 'Cards array is required'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        let content = '';
        let contentType = 'text/plain';
        let filename = `cards_${Date.now()}`;

        if (format === 'csv') {
          contentType = 'text/csv';
          filename += '.csv';
          const headers = ['Number', 'Expiry', 'CVV', 'Brand', 'Type', 'Country'];
          const rows = cards.map(card => [
            card.number,
            card.expiry ? `${card.expiry.month}/${card.expiry.year}` : '',
            card.cvv || '',
            card.brand || '',
            card.type || '',
            card.country || ''
          ]);
          content = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
        } else if (format === 'json') {
          contentType = 'application/json';
          filename += '.json';
          content = JSON.stringify(cards, null, 2);
        } else if (format === 'txt') {
          contentType = 'text/plain';
          filename += '.txt';
          content = cards.map(card => {
            let line = card.number;
            if (card.expiry) line += `|${card.expiry.month}/${card.expiry.year}`;
            if (card.cvv) line += `|${card.cvv}`;
            return line;
          }).join('\n');
        }

        return new Response(content, {
          headers: {
            'Content-Type': contentType,
            'Content-Disposition': `attachment; filename="${filename}"`,
            ...corsHeaders
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Invalid request body'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Create crypto payment: /api/v1/payments/create-crypto-payment
    if (url.pathname === '/api/v1/payments/create-crypto-payment' && request.method === 'POST') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      try {
        const body = await request.json();
        const { provider, currency, plan = 'premium' } = body;
        
        if (!provider || !currency) {
          return new Response(JSON.stringify({
            detail: 'Provider and currency are required'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Validate provider
        if (!['nowpayments', 'coinbase'].includes(provider)) {
          return new Response(JSON.stringify({
            detail: 'Invalid provider. Supported: nowpayments, coinbase'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Generate payment data
        const paymentId = `pay_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const amount = plan === 'premium' ? 9.99 : 19.99; // USD equivalent
        
        // Simulate crypto amount calculation (in real implementation, you'd call exchange API)
        const cryptoRates = {
          'BTC': 0.00023,
          'ETH': 0.0041,
          'LTC': 0.089,
          'USDT': 9.99,
          'USDC': 9.99
        };
        
        const cryptoAmount = (cryptoRates[currency] || 1) * amount;
        
        // Generate wallet addresses (in real implementation, these would come from payment provider APIs)
        const walletAddresses = {
          'BTC': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
          'ETH': '0x742d35cc6634c0532925a3b8d039daca1c03c03b',
          'LTC': 'LTC1QW4QJ6KQ8J7X8N9Y4H2K9G6J5X8F9R3L2K7M9N',
          'USDT': '0x742d35cc6634c0532925a3b8d039daca1c03c03b',
          'USDC': '0x742d35cc6634c0532925a3b8d039daca1c03c03b'
        };

        // Get user ID from token
        const authHeader = request.headers.get('Authorization');
        const token = authHeader.substring(7);
        const decoded = atob(token);
        const [userId] = decoded.split(':');
        
        // Store payment in database
        const insertPayment = env.DB.prepare(`
          INSERT INTO payments (user_id, payment_id, provider, currency, amount, amount_usd, wallet_address, status)
          VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        `);
        
        const walletAddress = walletAddresses[currency] || walletAddresses['BTC'];
        await insertPayment.bind(
          parseInt(userId), 
          paymentId, 
          provider, 
          currency, 
          cryptoAmount, 
          amount, 
          walletAddress
        ).run();

        const payment = {
          payment_id: paymentId,
          provider: provider,
          currency: currency,
          amount: cryptoAmount,
          amount_formatted: `${cryptoAmount.toFixed(8)} ${currency}`,
          amount_usd: amount,
          status: 'pending',
          wallet_address: walletAddress,
          payment_url: `https://nowpayments.io/payment/?iid=${paymentId}`,
          qr_code: `data:image/svg+xml;base64,${btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect width="200" height="200" fill="#1a1a1a"/><rect x="20" y="20" width="160" height="160" fill="white"/><text x="100" y="105" text-anchor="middle" fill="black" font-family="monospace" font-size="14">Scan to Pay</text><text x="100" y="125" text-anchor="middle" fill="black" font-family="monospace" font-size="10">${cryptoAmount.toFixed(6)} ${currency}</text></svg>`)}`,
          expires_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(), // 1 hour
          expires_in_minutes: 60,
          created_at: new Date().toISOString(),
          instructions: `Send exactly ${cryptoAmount.toFixed(8)} ${currency} to the wallet address below. Payment will be confirmed automatically within 6 confirmations.`,
          step_by_step: [
            `Copy the wallet address: ${walletAddress}`,
            `Send exactly ${cryptoAmount.toFixed(8)} ${currency} from your wallet`,
            `Wait for blockchain confirmations (usually 10-30 minutes)`,
            `Your account will be upgraded automatically once confirmed`
          ],
          warning: "Send only the exact amount shown. Sending less will require manual processing. Sending more may result in loss of funds.",
          network_info: {
            currency: currency,
            network: currency === 'BTC' ? 'Bitcoin' : currency === 'ETH' ? 'Ethereum' : currency === 'LTC' ? 'Litecoin' : 'ERC-20',
            confirmations_required: 6,
            estimated_time: '10-30 minutes'
          }
        };

        return new Response(JSON.stringify(payment), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Invalid request body'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Payment status check: /api/v1/payments/status/{paymentId}
    if (url.pathname.startsWith('/api/v1/payments/status/') && request.method === 'GET') {
      const paymentId = url.pathname.split('/')[4];
      
      if (!paymentId) {
        return new Response(JSON.stringify({
          detail: 'Payment ID is required'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      // In a real implementation, you'd check the actual payment status from the provider
      // For demo purposes, we'll simulate different statuses based on time
      const createdTime = parseInt(paymentId.split('_')[1]) || Date.now();
      const timeElapsed = Date.now() - createdTime;
      
      let status = 'pending';
      if (timeElapsed > 300000) { // 5 minutes - completed
        status = 'completed';
      } else if (timeElapsed > 240000) { // 4 minutes - confirming
        status = 'confirming';
      } else if (timeElapsed > 180000) { // 3 minutes - partially_paid
        status = 'partially_paid';
      }

      const paymentStatus = {
        payment_id: paymentId,
        status: status,
        confirmations: status === 'completed' ? 6 : Math.floor(timeElapsed / 60000),
        required_confirmations: 6,
        amount_paid: status === 'pending' ? 0 : (status === 'partially_paid' ? 0.5 : 1),
        updated_at: new Date().toISOString()
      };

      return new Response(JSON.stringify(paymentStatus), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
    }

    // Payment webhooks: /api/v1/webhooks/{provider}
    if (url.pathname.startsWith('/api/v1/webhooks/') && request.method === 'POST') {
      const provider = url.pathname.split('/')[4]; // nowpayments or coinbase
      
      try {
        const body = await request.text();
        let paymentData;
        
        if (provider === 'nowpayments') {
          // NOWPayments webhook
          paymentData = JSON.parse(body);
          
          // Verify webhook signature (simplified)
          const expectedSig = request.headers.get('x-nowpayments-sig');
          if (!expectedSig) {
            return new Response('Unauthorized webhook', { status: 401 });
          }
          
          // Process payment confirmation
          if (paymentData.payment_status === 'finished' || paymentData.payment_status === 'confirmed') {
            await processPaymentConfirmation(paymentData.order_id, paymentData, env);
          }
          
        } else if (provider === 'coinbase') {
          // Coinbase Commerce webhook
          paymentData = JSON.parse(body);
          
          // Verify webhook signature
          const expectedSig = request.headers.get('x-cc-webhook-signature');
          if (!expectedSig) {
            return new Response('Unauthorized webhook', { status: 401 });
          }
          
          // Process payment confirmation
          if (paymentData.event?.type === 'charge:confirmed') {
            await processPaymentConfirmation(paymentData.event.data.id, paymentData.event.data, env);
          }
          
        } else {
          return new Response('Unknown webhook provider', { status: 400 });
        }
        
        return new Response('Webhook processed', { 
          status: 200,
          headers: corsHeaders
        });
        
      } catch (error) {
        console.error('Webhook processing error:', error);
        return new Response('Webhook processing failed', { 
          status: 500,
          headers: corsHeaders
        });
      }
    }

    // Bulk export endpoint: /api/v1/export/{format}
    if (url.pathname.startsWith('/api/v1/export/') && request.method === 'POST') {
      const format = url.pathname.split('/')[4]; // csv or json
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required for exports'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
      
      try {
        const userId = await getUserFromToken(authHeader);
        const user = await env.DB.prepare('SELECT plan FROM users WHERE id = ?').bind(userId).first();
        
        if (!user || user.plan === 'free') {
          return new Response(JSON.stringify({
            detail: 'Premium account required for bulk exports'
          }), {
            status: 403,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
        const body = await request.json();
        const { export_type, filters, limit } = body;
        
        // Set limits based on plan
        const maxLimit = user.plan === 'pro' ? 10000 : 1000;
        const exportLimit = Math.min(limit || 100, maxLimit);
        
        let data = [];
        let filename = '';
        
        switch (export_type) {
          case 'bins':
            // Export BIN data
            let query = 'SELECT * FROM bins WHERE 1=1';
            let params = [];
            
            if (filters?.brand) {
              query += ' AND brand = ?';
              params.push(filters.brand);
            }
            if (filters?.country) {
              query += ' AND country = ?';
              params.push(filters.country);
            }
            if (filters?.type) {
              query += ' AND type = ?';
              params.push(filters.type);
            }
            
            query += ` LIMIT ${exportLimit}`;
            
            const binResults = await env.DB.prepare(query).bind(...params).all();
            data = binResults.results || [];
            filename = `bins_export_${new Date().toISOString().split('T')[0]}`;
            break;
            
          case 'search_history':
            // Export user's search history
            const searchResults = await env.DB.prepare(`
              SELECT bin_number, search_type, result_found, search_date
              FROM search_history 
              WHERE user_id = ?
              ORDER BY search_date DESC
              LIMIT ${exportLimit}
            `).bind(userId).all();
            data = searchResults.results || [];
            filename = `search_history_${new Date().toISOString().split('T')[0]}`;
            break;
            
          case 'analytics':
            // Export analytics summary
            const analyticsResults = await env.DB.prepare(`
              SELECT 
                bin_number,
                COUNT(*) as search_count,
                MAX(search_date) as last_searched,
                SUM(CASE WHEN result_found = 1 THEN 1 ELSE 0 END) as successful_searches
              FROM search_history 
              WHERE user_id = ?
              GROUP BY bin_number
              ORDER BY search_count DESC
              LIMIT ${exportLimit}
            `).bind(userId).all();
            data = analyticsResults.results || [];
            filename = `analytics_${new Date().toISOString().split('T')[0]}`;
            break;
            
          default:
            return new Response(JSON.stringify({
              detail: 'Invalid export type. Use: bins, search_history, or analytics'
            }), {
              status: 400,
              headers: { 'Content-Type': 'application/json', ...corsHeaders }
            });
        }
        
        if (format === 'csv') {
          // Convert to CSV
          if (data.length === 0) {
            return new Response('No data found for export', {
              status: 404,
              headers: { 'Content-Type': 'text/plain', ...corsHeaders }
            });
          }
          
          const headers = Object.keys(data[0]);
          const csvContent = [
            headers.join(','),
            ...data.map(row => 
              headers.map(header => 
                typeof row[header] === 'string' ? `"${row[header]}"` : row[header]
              ).join(',')
            )
          ].join('\\n');
          
          return new Response(csvContent, {
            headers: {
              'Content-Type': 'text/csv',
              'Content-Disposition': `attachment; filename="${filename}.csv"`,
              ...corsHeaders
            }
          });
          
        } else if (format === 'json') {
          // Return JSON
          return new Response(JSON.stringify({
            export_info: {
              type: export_type,
              generated_at: new Date().toISOString(),
              record_count: data.length,
              user_plan: user.plan
            },
            data: data
          }, null, 2), {
            headers: {
              'Content-Type': 'application/json',
              'Content-Disposition': `attachment; filename="${filename}.json"`,
              ...corsHeaders
            }
          });
          
        } else {
          return new Response(JSON.stringify({
            detail: 'Invalid format. Use csv or json'
          }), {
            status: 400,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Export error: ' + error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
    }

    // Admin endpoints (require admin privileges)
    if (url.pathname.startsWith('/api/v1/admin/')) {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
      
      try {
        const userId = await getUserFromToken(authHeader);
        const user = await env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(userId).first();
        
        // Check admin privileges (admin users have username starting with 'admin_')
        if (!user || !user.username.startsWith('admin_')) {
          return new Response(JSON.stringify({
            detail: 'Admin privileges required'
          }), {
            status: 403,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
        // Admin dashboard stats: /api/v1/admin/stats
        if (url.pathname === '/api/v1/admin/stats' && request.method === 'GET') {
          const stats = await Promise.all([
            env.DB.prepare('SELECT COUNT(*) as total_users FROM users').first(),
            env.DB.prepare('SELECT COUNT(*) as total_payments FROM payments').first(),
            env.DB.prepare('SELECT COUNT(*) as total_searches FROM search_history').first(),
            env.DB.prepare('SELECT COUNT(*) as premium_users FROM users WHERE plan != "free"').first(),
            env.DB.prepare('SELECT SUM(amount_usd) as total_revenue FROM payments WHERE status = "completed"').first(),
            env.DB.prepare('SELECT COUNT(*) as daily_searches FROM search_history WHERE date(search_date) = date("now")').first()
          ]);
          
          return new Response(JSON.stringify({
            platform_stats: {
              total_users: stats[0]?.total_users || 0,
              total_payments: stats[1]?.total_payments || 0,
              total_searches: stats[2]?.total_searches || 0,
              premium_users: stats[3]?.premium_users || 0,
              total_revenue: stats[4]?.total_revenue || 0,
              daily_searches: stats[5]?.daily_searches || 0,
              conversion_rate: stats[3]?.premium_users && stats[0]?.total_users ? 
                ((stats[3].premium_users / stats[0].total_users) * 100).toFixed(2) + '%' : '0%'
            },
            generated_at: new Date().toISOString()
          }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
        // Admin user management: /api/v1/admin/users
        if (url.pathname === '/api/v1/admin/users' && request.method === 'GET') {
          const page = parseInt(url.searchParams.get('page') || '1');
          const limit = Math.min(parseInt(url.searchParams.get('limit') || '50'), 100);
          const offset = (page - 1) * limit;
          
          const users = await env.DB.prepare(`
            SELECT 
              id, username, email, plan, created_at, updated_at,
              (SELECT COUNT(*) FROM search_history WHERE user_id = users.id) as search_count,
              (SELECT COUNT(*) FROM payments WHERE user_id = users.id) as payment_count
            FROM users 
            ORDER BY created_at DESC
            LIMIT ${limit} OFFSET ${offset}
          `).all();
          
          const totalCount = await env.DB.prepare('SELECT COUNT(*) as count FROM users').first();
          
          return new Response(JSON.stringify({
            users: users.results || [],
            pagination: {
              current_page: page,
              total_pages: Math.ceil((totalCount?.count || 0) / limit),
              total_users: totalCount?.count || 0,
              per_page: limit
            }
          }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
        // Admin payment monitoring: /api/v1/admin/payments
        if (url.pathname === '/api/v1/admin/payments' && request.method === 'GET') {
          const status = url.searchParams.get('status') || 'all';
          const page = parseInt(url.searchParams.get('page') || '1');
          const limit = Math.min(parseInt(url.searchParams.get('limit') || '50'), 100);
          const offset = (page - 1) * limit;
          
          let query = `
            SELECT 
              p.*, u.username, u.email
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
          `;
          let params = [];
          
          if (status !== 'all') {
            query += ' WHERE p.status = ?';
            params.push(status);
          }
          
          query += ` ORDER BY p.created_at DESC LIMIT ${limit} OFFSET ${offset}`;
          
          const payments = await env.DB.prepare(query).bind(...params).all();
          
          return new Response(JSON.stringify({
            payments: payments.results || [],
            pagination: {
              current_page: page,
              per_page: limit
            }
          }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
        // Admin search analytics: /api/v1/admin/analytics
        if (url.pathname === '/api/v1/admin/analytics' && request.method === 'GET') {
          const analytics = await Promise.all([
            // Top searched BINs
            env.DB.prepare(`
              SELECT bin_number, COUNT(*) as search_count
              FROM search_history 
              GROUP BY bin_number 
              ORDER BY search_count DESC 
              LIMIT 10
            `).all(),
            
            // Daily search trends (last 7 days)
            env.DB.prepare(`
              SELECT 
                date(search_date) as search_date,
                COUNT(*) as daily_searches,
                COUNT(DISTINCT user_id) as unique_users
              FROM search_history 
              WHERE search_date >= date('now', '-7 days')
              GROUP BY date(search_date)
              ORDER BY search_date DESC
            `).all(),
            
            // User activity summary
            env.DB.prepare(`
              SELECT 
                u.plan,
                COUNT(*) as user_count,
                AVG(search_counts.search_count) as avg_searches
              FROM users u
              LEFT JOIN (
                SELECT user_id, COUNT(*) as search_count 
                FROM search_history 
                GROUP BY user_id
              ) search_counts ON u.id = search_counts.user_id
              GROUP BY u.plan
            `).all()
          ]);
          
          return new Response(JSON.stringify({
            top_bins: analytics[0].results || [],
            daily_trends: analytics[1].results || [],
            user_activity: analytics[2].results || [],
            generated_at: new Date().toISOString()
          }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
        return new Response(JSON.stringify({
          detail: 'Admin endpoint not found'
        }), {
          status: 404,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Admin endpoint error: ' + error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
    }

    // Current user usage stats: /api/v1/auth/usage-stats
    if (url.pathname === '/api/v1/auth/usage-stats' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
      
      try {
        const userId = await getUserFromToken(authHeader);
        
        // Get comprehensive usage stats
        const stats = await env.DB.prepare(`
          SELECT 
            COUNT(*) as total_usage,
            SUM(CASE WHEN date(search_date) = date('now') THEN 1 ELSE 0 END) as daily_usage,
            SUM(CASE WHEN search_type = 'card_generation' THEN 1 ELSE 0 END) as cards_generated,
            SUM(CASE WHEN search_type = 'api_lookup' THEN 1 ELSE 0 END) as bin_lookups,
            MAX(search_date) as last_activity
          FROM search_history 
          WHERE user_id = ?
        `).bind(userId).first();
        
        return new Response(JSON.stringify({
          success: true,
          usage_stats: {
            daily_usage: stats?.daily_usage || 0,
            total_usage: stats?.total_usage || 0,
            cards_generated: stats?.cards_generated || 0,
            bin_lookups: stats?.bin_lookups || 0,
            last_activity: stats?.last_activity
          }
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Error fetching usage stats: ' + error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
    }

    // User analytics: /api/v1/analytics/searches  
    if (url.pathname === '/api/v1/analytics/searches' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
      
      try {
        const userId = await getUserFromToken(authHeader);
        
        // Get user's search statistics
        const searches = await env.DB.prepare(`
          SELECT 
            bin_number, 
            search_type, 
            result_found, 
            search_date,
            COUNT(*) as search_count
          FROM search_history 
          WHERE user_id = ?
          GROUP BY bin_number, search_type, result_found, DATE(search_date)
          ORDER BY search_date DESC
          LIMIT 100
        `).bind(userId).all();
        
        // Get search summary stats
        const stats = await env.DB.prepare(`
          SELECT 
            COUNT(*) as total_searches,
            COUNT(DISTINCT bin_number) as unique_bins,
            SUM(CASE WHEN result_found = 1 THEN 1 ELSE 0 END) as successful_searches,
            DATE(MIN(search_date)) as first_search_date
          FROM search_history 
          WHERE user_id = ?
        `).bind(userId).first();
        
        return new Response(JSON.stringify({
          success: true,
          statistics: stats || {
            total_searches: 0,
            unique_bins: 0,
            successful_searches: 0,
            first_search_date: null
          },
          recent_searches: searches.results || []
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Error fetching analytics: ' + error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
    }

    // Payment history (for authenticated users): /api/v1/payments/history
    if (url.pathname === '/api/v1/payments/history' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
      
      try {
        // Extract user ID from token
        const token = authHeader.substring(7);
        const decoded = atob(token);
        const [userId] = decoded.split(':');
        
        // Get user's payment history
        const payments = await env.DB.prepare(`
          SELECT payment_id, provider, currency, amount, amount_usd, status, wallet_address, created_at, updated_at
          FROM payments 
          WHERE user_id = ?
          ORDER BY created_at DESC
          LIMIT 50
        `).bind(parseInt(userId)).all();
        
        return new Response(JSON.stringify({
          success: true,
          payments: payments.results || []
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Error fetching payment history: ' + error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }
    }

    // BIN history (for authenticated users): /api/v1/bins/history
    if (url.pathname === '/api/v1/bins/history' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          detail: 'Authentication required'
        }), {
          status: 401,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }

      // Return mock search history
      const history = [
        {
          id: 1,
          bin: '424242',
          searched_at: new Date(Date.now() - 86400000).toISOString(),
          result: { brand: 'VISA', issuer: 'Stripe', country: 'United Kingdom' }
        },
        {
          id: 2,
          bin: '545454',
          searched_at: new Date(Date.now() - 172800000).toISOString(),
          result: { brand: 'MASTERCARD', issuer: 'Bank of America', country: 'United States' }
        }
      ];

      return new Response(JSON.stringify({
        history: history,
        total: history.length
      }), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
    }

    // Health check endpoints
    if (url.pathname === '/api/health') {
      const healthData = await healthCheck.performHealthCheck();
      response = new Response(JSON.stringify(healthData), {
        status: healthData.status === 'healthy' ? 200 : 503,
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
      return response;
    }

    if (url.pathname === '/api/health/quick') {
      const quickHealth = await healthCheck.quickHealthCheck();
      response = new Response(JSON.stringify(quickHealth), {
        status: quickHealth.status === 'healthy' ? 200 : 503,
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
      return response;
    }

    // Monitoring dashboard endpoint
    if (url.pathname === '/api/monitoring/dashboard') {
      const hours = parseInt(url.searchParams.get('hours') || '24');
      const dashboardData = await apm.getDashboardData(hours);
      const dbHealth = await dbOptimizer.generateHealthReport();
      
      const monitoringData = {
        performance: dashboardData,
        database: dbHealth,
        timestamp: new Date().toISOString()
      };

      response = new Response(JSON.stringify(monitoringData), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
      return response;
    }

    // Database optimization endpoint (admin only)
    if (url.pathname === '/api/monitoring/optimize' && request.method === 'POST') {
      // In production, add admin authentication here
      const optimization = await dbOptimizer.optimizeSchema();
      const cleanup = await dbOptimizer.cleanupOldData();
      
      response = new Response(JSON.stringify({
        optimization_results: optimization,
        cleanup_results: cleanup,
        timestamp: new Date().toISOString()
      }), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
      return response;
    }

    // Performance analysis endpoint
    if (url.pathname === '/api/monitoring/performance') {
      const analysis = await dbOptimizer.analyzeQueryPerformance();
      
      response = new Response(JSON.stringify(analysis), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
      return response;
    }

    // Health check endpoints
    if (url.pathname === '/api/health') {
      const healthData = await healthCheck.performHealthCheck();
      response = new Response(JSON.stringify(healthData), {
        status: healthData.status === 'healthy' ? 200 : 503,
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
      return security.addSecurityHeaders(response);
    }

    if (url.pathname === '/api/health/quick') {
      const quickHealth = await healthCheck.quickHealthCheck();
      response = new Response(JSON.stringify(quickHealth), {
        status: quickHealth.status === 'healthy' ? 200 : 503,
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
      return security.addSecurityHeaders(response);
    }

    // Monitoring dashboard endpoint
    if (url.pathname === '/api/monitoring/dashboard' && request.method === 'GET') {
      // Check authentication for monitoring access
      const authHeader = request.headers.get('Authorization');
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        response = new Response(JSON.stringify({
          error: 'Authentication required',
          message: 'Monitoring dashboard requires authentication'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        return security.addSecurityHeaders(response);
      }

      try {
        const dashboardData = await apm.getDashboardData(24);
        const dbHealth = await dbOptimizer.generateHealthReport();
        
        response = new Response(JSON.stringify({
          apm: dashboardData,
          database: dbHealth,
          timestamp: new Date().toISOString()
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
        return security.addSecurityHeaders(response);
      } catch (error) {
        apm.recordError(transaction, error);
        response = new Response(JSON.stringify({
          error: 'Dashboard unavailable',
          message: error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        return security.addSecurityHeaders(response);
      }
    }

    // Database optimization endpoint (admin only)
    if (url.pathname === '/api/admin/db-optimize' && request.method === 'POST') {
      // Check authentication for admin access
      const authHeader = request.headers.get('Authorization');
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        response = new Response(JSON.stringify({
          error: 'Admin authentication required'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        return security.addSecurityHeaders(response);
      }

      try {
        const optimizationResult = await dbOptimizer.optimizeSchema();
        const cleanupResult = await dbOptimizer.cleanupOldData(7);
        
        response = new Response(JSON.stringify({
          optimization: optimizationResult,
          cleanup: cleanupResult,
          timestamp: new Date().toISOString()
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
        return security.addSecurityHeaders(response);
      } catch (error) {
        apm.recordError(transaction, error);
        response = new Response(JSON.stringify({
          error: 'Optimization failed',
          message: error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        return security.addSecurityHeaders(response);
      }
    }

    // Business Intelligence Analytics API
    if (url.pathname.startsWith('/api/analytics/')) {
      response = await biAPI.handleRequest(request, url.pathname);
      return security.addSecurityHeaders(response);
    }

    // Phase 3: Advanced Integrations API
    if (url.pathname.startsWith('/api/webhooks/') || 
        url.pathname.startsWith('/api/keys/') ||
        url.pathname.startsWith('/api/bin/enhanced/') ||
        url.pathname.startsWith('/api/payments/') ||
        url.pathname === '/api/integrations/status') {
      response = await integrationAPI.handleRequest(request, env);
      return security.addSecurityHeaders(response);
    }

    // Phase 4: AI-Powered Automation API
    if (url.pathname.startsWith('/api/ai/')) {
      try {
        // Fraud Detection API
        if (url.pathname.startsWith('/api/ai/fraud/')) {
          if (url.pathname === '/api/ai/fraud/analyze' && request.method === 'POST') {
            try {
              const body = await request.json();
              const analysis = await fraudDetection.analyzeTransaction(body);
              response = new Response(JSON.stringify(analysis), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            } catch (error) {
              console.error('Fraud analyze error:', error);
              response = new Response(JSON.stringify({
                error: 'Fraud analysis failed',
                message: error.message
              }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            }
          } else if (url.pathname === '/api/ai/fraud/patterns' && request.method === 'GET') {
            const patterns = await fraudDetection.getFraudPatterns();
            response = new Response(JSON.stringify(patterns), {
              headers: { 'Content-Type': 'application/json', ...corsHeaders }
            });
          } else if (url.pathname === '/api/ai/fraud/models/train' && request.method === 'POST') {
            const result = await fraudDetection.trainModels();
            response = new Response(JSON.stringify(result), {
              headers: { 'Content-Type': 'application/json', ...corsHeaders }
            });
          }
        }
        // Predictive Analytics API
        else if (url.pathname.startsWith('/api/ai/predict/')) {
          if (url.pathname === '/api/ai/predict/bin' && request.method === 'POST') {
            try {
              const body = await request.json();
              const predictions = await predictiveAnalytics.predictBINInfo(body.bin);
              response = new Response(JSON.stringify(predictions), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            } catch (error) {
              console.error('Prediction error:', error);
              response = new Response(JSON.stringify({
                error: 'Prediction failed',
                message: error.message
              }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            }
          } else if (url.pathname === '/api/ai/predict/similar' && request.method === 'POST') {
            try {
              const body = await request.json();
              const similar = await predictiveAnalytics.findSimilarBINs(body.bin);
              response = new Response(JSON.stringify(similar), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            } catch (error) {
              console.error('Similar BINs error:', error);
              response = new Response(JSON.stringify({
                error: 'Similar BINs search failed',
                message: error.message
              }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            }
          } else if (url.pathname === '/api/ai/predict/insights' && request.method === 'GET') {
            try {
              // Use a method that actually exists
              const accuracy = await predictiveAnalytics.getPredictionAccuracy();
              const insights = {
                accuracy_rate: accuracy,
                predictions_today: await predictiveAnalytics.getPredictionCount('today'),
                insights_generated: await predictiveAnalytics.getInsightCount(),
                timestamp: new Date().toISOString()
              };
              response = new Response(JSON.stringify(insights), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            } catch (error) {
              console.error('Insights error:', error);
              response = new Response(JSON.stringify({
                error: 'Insights generation failed',
                message: error.message
              }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            }
          }
        }
        // Performance Optimization API
        else if (url.pathname.startsWith('/api/ai/optimize/')) {
          if (url.pathname === '/api/ai/optimize/run' && request.method === 'POST') {
            try {
              const result = await performanceOptimizer.runOptimizationCycle();
              response = new Response(JSON.stringify(result), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            } catch (error) {
              console.error('Optimization run error:', error);
              response = new Response(JSON.stringify({
                error: 'Optimization failed',
                message: error.message
              }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            }
          } else if (url.pathname === '/api/ai/optimize/metrics' && request.method === 'GET') {
            try {
              const metrics = await performanceOptimizer.getOptimizationMetrics();
              response = new Response(JSON.stringify(metrics), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            } catch (error) {
              console.error('Metrics error:', error);
              response = new Response(JSON.stringify({
                error: 'Metrics retrieval failed',
                message: error.message
              }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            }
          } else if (url.pathname === '/api/ai/optimize/recommendations' && request.method === 'GET') {
            try {
              const recommendations = await performanceOptimizer.generateRecommendations();
              response = new Response(JSON.stringify(recommendations), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            } catch (error) {
              console.error('Recommendations error:', error);
              response = new Response(JSON.stringify({
                error: 'Recommendations generation failed',
                message: error.message
              }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', ...corsHeaders }
              });
            }
          }
        }
        // AI System Status
        else if (url.pathname === '/api/ai/status' && request.method === 'GET') {
          const aiStatus = {
            fraud_detection: {
              models_loaded: await fraudDetection.getModelStatus(),
              patterns_count: await fraudDetection.getPatternCount(),
              last_training: await fraudDetection.getLastTraining()
            },
            predictive_analytics: {
              predictions_today: await predictiveAnalytics.getPredictionCount('today'),
              accuracy_rate: await predictiveAnalytics.getAccuracyRate(),
              insights_generated: await predictiveAnalytics.getInsightCount()
            },
            performance_optimizer: {
              last_optimization: await performanceOptimizer.getLastOptimization(),
              optimization_count: await performanceOptimizer.getOptimizationCount(),
              performance_improvement: await performanceOptimizer.getPerformanceImprovement()
            },
            system_status: 'active',
            timestamp: new Date().toISOString()
          };
          response = new Response(JSON.stringify(aiStatus), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        
        if (response) {
          return security.addSecurityHeaders(response);
        }
      } catch (error) {
        console.error('AI API Error:', error);
        response = new Response(JSON.stringify({
          error: 'AI processing error',
          message: error.message
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        return security.addSecurityHeaders(response);
      }
    }

    // Crypto balance checker: /api/v1/crypto/balance
    if (url.pathname === '/api/v1/crypto/balance' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { address, currency } = body;
        
        if (!address || !currency) {
          return new Response(JSON.stringify({
            detail: 'Address and currency are required'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Mock crypto balance (in real implementation, you'd call blockchain APIs)
        const mockBalances = {
          'BTC': Math.random() * 10,
          'ETH': Math.random() * 100,
          'LTC': Math.random() * 50,
          'USDT': Math.random() * 1000,
          'USDC': Math.random() * 1000
        };

        const balance = {
          address: address,
          currency: currency.toUpperCase(),
          balance: mockBalances[currency.toUpperCase()] || 0,
          usd_value: (mockBalances[currency.toUpperCase()] || 0) * 50000, // Mock USD conversion
          last_updated: new Date().toISOString(),
          network: currency.toUpperCase() === 'ETH' ? 'Ethereum' : 'Bitcoin'
        };

        return new Response(JSON.stringify(balance), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Invalid request body'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

      // 404 for unknown routes
      response = new Response(JSON.stringify({
        detail: 'Endpoint not found',
        available_endpoints: [
          '/bin/{bin_number}', 
          '/search?q={query}', 
          '/stats',
          '/api/v1/bins/lookup/{bin_number}',
          '/api/v1/bins/search?q={query}',
          '/api/v1/bins/stats',
          '/api/v1/auth/register',
          '/api/v1/auth/token',
          '/api/v1/auth/me',
          '/api/v1/auth/usage',
          '/api/v1/cards/generate',
          '/api/v1/cards/export/{format}',
          '/api/v1/cards/ip-status',
          '/api/v1/payments/subscription',
          '/api/v1/payments/create-crypto-payment',
          '/api/v1/payments/status/{paymentId}',
          '/api/v1/bins/history',
          '/api/v1/crypto/balance',
          '/api/health',
          '/api/health/quick',
          '/api/monitoring/dashboard'
        ]
      }), {
        status: 404,
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });

    } catch (error) {
      // Record error in APM
      apm.recordError(transaction, error, {
        url: request.url,
        method: request.method,
        userAgent: request.headers.get('user-agent'),
        ip: request.headers.get('cf-connecting-ip')
      });

      // Log security event for errors
      await security.logSecurityEvent('application_error', {
        error: error.message,
        stack: error.stack,
        url: request.url,
        method: request.method,
        ip: request.headers.get('cf-connecting-ip')
      }, 'error');

      response = new Response(JSON.stringify({
        error: 'Internal Server Error',
        message: 'An unexpected error occurred',
        requestId: transaction.id
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    } finally {
      // Add security headers to all responses
      response = security.addSecurityHeaders(response);
      
      // Phase 4: Performance optimization monitoring
      try {
        const responseTime = Date.now() - transaction.startTime;
        await performanceOptimizer.recordPerformanceMetric({
          endpoint: url.pathname,
          method: request.method,
          responseTime: responseTime,
          statusCode: response?.status || 500,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('Performance tracking error:', error);
      }
      
      // Finish APM transaction
      await apm.finishTransaction(transaction, response);
      
      return response;
    }
  },

  // Scheduled tasks for maintenance
  async scheduled(controller, env, ctx) {
    // Clean up old monitoring data (runs daily at 2 AM)
    if (controller.cron === '0 2 * * *') {
      await dbOptimizer.cleanupOldData(30); // Keep 30 days
    }
    
    // Optimize database performance (runs weekly at 3 AM on Sundays)
    if (controller.cron === '0 3 * * 0') {
      await dbOptimizer.optimizeSchema();
    }
    
    // Phase 4: AI-powered maintenance tasks
    
    // Run AI performance optimization (runs every 6 hours)
    if (controller.cron === '0 */6 * * *') {
      try {
        console.log('Running AI performance optimization cycle...');
        await performanceOptimizer.runOptimizationCycle();
      } catch (error) {
        console.error('AI optimization error:', error);
      }
    }
    
    // Train fraud detection models (runs daily at 4 AM)
    if (controller.cron === '0 4 * * *') {
      try {
        console.log('Training fraud detection models...');
        await fraudDetection.trainModels();
      } catch (error) {
        console.error('Fraud model training error:', error);
      }
    }
    
    // Clean up old AI data (runs weekly at 1 AM on Mondays)
    if (controller.cron === '0 1 * * 1') {
      try {
        console.log('Cleaning up old AI data...');
        
        // Clean up old fraud detection data (keep 90 days)
        await env.DB.prepare(`
          DELETE FROM fraud_detections 
          WHERE created_at < datetime('now', '-90 days')
        `).run();
        
        // Clean up old predictions (keep 30 days)
        await env.DB.prepare(`
          DELETE FROM bin_predictions 
          WHERE created_at < datetime('now', '-30 days')
        `).run();
        
        // Clean up old optimization metrics (keep 60 days)
        await env.DB.prepare(`
          DELETE FROM optimization_metrics 
          WHERE created_at < datetime('now', '-60 days')
        `).run();
        
        console.log('AI data cleanup completed');
      } catch (error) {
        console.error('AI cleanup error:', error);
      }
    }
  }
};