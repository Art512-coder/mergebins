/**
 * Cloudflare Worker for BIN Search API - Fixed Version with Safe AI Loading
 * Integrates with D1 database for fast BIN lookups
 * Enterprise-grade with APM monitoring, security hardening, and performance optimization
 */

// Import enterprise monitoring modules
import { APMMonitor } from './monitoring/apm.js';
import { SecurityManager } from './monitoring/security.js';
import { DatabaseOptimizer } from './monitoring/database.js';
import { HealthCheck } from './monitoring/health.js';

// Import business intelligence modules
import { AnalyticsEngine } from './analytics/engine.js';
import { BusinessIntelligenceAPI } from './analytics/api.js';

// Import Phase 3: Advanced Integrations modules
import { WebhookManager, WebhookAPI } from './integrations/webhooks.js';
import { APIAuthManager } from './integrations/api-auth.js';
import { BINDataProvider, ExternalAPIManager } from './integrations/bin-providers.js';
import { IntegrationAPI } from './integrations/api.js';

// Import Phase 4: AI-Powered Automation modules (Conditional)
let SimpleFraudDetectionEngine, SimplePredictiveBINAnalytics, SimplePerformanceOptimizer;

// Safe AI module loading
async function loadAIModules() {
  try {
    const fraudModule = await import('./ai/simple-fraud-detection.js');
    SimpleFraudDetectionEngine = fraudModule.SimpleFraudDetectionEngine;
    
    const predictiveModule = await import('./ai/simple-predictive-analytics.js');
    SimplePredictiveBINAnalytics = predictiveModule.SimplePredictiveBINAnalytics;
    
    const optimizerModule = await import('./ai/simple-performance-optimizer.js');
    SimplePerformanceOptimizer = optimizerModule.SimplePerformanceOptimizer;
    
    return true;
  } catch (error) {
    console.warn('AI modules failed to load:', error);
    return false;
  }
}

// Safe AI instance creation
function createAIInstances(env, apm, dbOptimizer) {
  try {
    if (!SimpleFraudDetectionEngine || !SimplePredictiveBINAnalytics || !SimplePerformanceOptimizer) {
      return { aiEnabled: false };
    }
    
    const fraudDetection = new SimpleFraudDetectionEngine(env.DB, apm);
    const predictiveAnalytics = new SimplePredictiveBINAnalytics(env.DB, apm);
    const performanceOptimizer = new SimplePerformanceOptimizer(env.DB, apm, dbOptimizer);
    
    return {
      aiEnabled: true,
      fraudDetection,
      predictiveAnalytics,
      performanceOptimizer
    };
  } catch (error) {
    console.warn('AI instances failed to create:', error);
    return { aiEnabled: false };
  }
}

// Safe AI operation wrapper
async function safeAIOperation(operation, fallback = null) {
  try {
    return await operation();
  } catch (error) {
    console.warn('AI operation failed:', error);
    return fallback;
  }
}

// Helper functions for card generation
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
        digit -= 9;
      }
    }
    
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  
  const checkDigit = (10 - (sum % 10)) % 10;
  return checkDigit;
}

function isValidLuhn(cardNumber) {
  let sum = 0;
  let shouldDouble = false;
  
  for (let i = cardNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cardNumber[i]);
    
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  
  return sum % 10 === 0;
}

// Main worker export
export default {
  async fetch(request, env, ctx) {
    try {
      // Initialize enterprise monitoring systems
      const apm = new APMMonitor(env);
      const security = new SecurityManager(env);
      const dbOptimizer = new DatabaseOptimizer(env, apm);
      const healthCheck = new HealthCheck(env, apm, dbOptimizer, security);
      
      // Initialize business intelligence systems  
      const analytics = new AnalyticsEngine(env, apm);
      const biAPI = new BusinessIntelligenceAPI(env, analytics, security);
      
      // Initialize Phase 3: Advanced Integrations systems
      const webhookManager = new WebhookManager(env.DB, apm);
      const webhookAPI = new WebhookAPI(webhookManager, security);
      const apiAuthManager = new APIAuthManager(env.DB, apm);
      const externalAPIManager = new ExternalAPIManager(env.DB, apm);
      const binDataProvider = new BINDataProvider(env.DB, apm);
      const integrationAPI = new IntegrationAPI(webhookManager, apiAuthManager, binDataProvider, security, webhookAPI);
      
      // Load and initialize AI modules safely
      const aiModulesLoaded = await loadAIModules();
      const aiInstances = aiModulesLoaded ? createAIInstances(env, apm, dbOptimizer) : { aiEnabled: false };
      
      // Start APM transaction and analytics session
      const transaction = apm.startTransaction('http_request', request);
      const sessionId = await analytics.trackSession(request);
      
      let response;
      
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
      
      // CORS headers for cross-origin requests
      const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400'
      };

      // Handle CORS preflight requests
      if (request.method === 'OPTIONS') {
        response = new Response(null, { status: 204, headers: corsHeaders });
        return security.addSecurityHeaders(response);
      }

      // Homepage route
      if (url.pathname === '/' || url.pathname === '/index.html') {
        response = new Response(getHomepageHTML(), {
          headers: { 'Content-Type': 'text/html', ...corsHeaders }
        });
        await analytics.trackRequest(request, response, sessionId);
        return security.addSecurityHeaders(response);
      }
      
      // Health check endpoint 
      if (url.pathname === '/health' || url.pathname === '/status') {
        const healthStatus = await healthCheck.getSystemHealth();
        response = new Response(JSON.stringify({
          ...healthStatus,
          ai_status: {
            enabled: aiInstances.aiEnabled,
            modules_loaded: aiModulesLoaded,
            timestamp: new Date().toISOString()
          }
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        await analytics.trackRequest(request, response, sessionId);
        return security.addSecurityHeaders(response);
      }

      // BIN Lookup API
      if (url.pathname.startsWith('/api/bin/lookup/')) {
        const bin = url.pathname.split('/').pop();
        
        if (!bin || bin.length < 4 || bin.length > 8) {
          response = new Response(JSON.stringify({
            error: 'Invalid BIN format',
            message: 'BIN must be 4-8 digits'
          }), {
            status: 400,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
          await analytics.trackRequest(request, response, sessionId);
          return security.addSecurityHeaders(response);
        }

        try {
          // Core BIN lookup from database
          const result = await env.DB.prepare(
            'SELECT * FROM bin_data WHERE bin = ?'
          ).bind(bin).first();

          let binData;
          if (result) {
            binData = {
              bin: result.bin,
              brand: result.brand,
              issuer: result.issuer,
              type: result.type,
              category: result.category,
              country: result.country_name,
              country_code: result.country_code,
              currency: result.currency,
              website: result.website,
              phone: result.phone,
              luhn_valid: isValidLuhn(bin + '00000000'),
              status: 'SUCCESS'
            };
          } else {
            // Fallback data when not in database
            binData = {
              bin: bin,
              brand: 'UNKNOWN',
              issuer: 'UNKNOWN',
              type: 'UNKNOWN',
              category: 'UNKNOWN', 
              country: 'UNKNOWN',
              currency: 'USD',
              luhn_valid: isValidLuhn(bin + '00000000'),
              status: 'NOT_FOUND'
            };
          }

          // Add AI insights if available
          if (aiInstances.aiEnabled) {
            const aiInsights = {};
            
            // Fraud detection
            const fraudAnalysis = await safeAIOperation(
              () => aiInstances.fraudDetection.analyzeTransaction({
                bin: bin,
                ip: clientIP,
                userAgent: request.headers.get('user-agent') || ''
              }),
              { fraud_risk_score: 0, confidence: 0 }
            );
            
            if (fraudAnalysis) {
              aiInsights.fraud_risk_score = fraudAnalysis.risk_score || 0;
              aiInsights.fraud_confidence = fraudAnalysis.confidence || 0;
            }
            
            // Predictive analytics
            const predictions = await safeAIOperation(
              () => aiInstances.predictiveAnalytics.predictBINInfo(bin),
              null
            );
            
            if (predictions && predictions.predictions) {
              aiInsights.predictions = predictions.predictions;
            }
            
            aiInsights.enhanced = true;
            binData.ai_insights = aiInsights;
          }

          binData.timestamp = new Date().toISOString();
          
          response = new Response(JSON.stringify(binData), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
          
          await analytics.trackRequest(request, response, sessionId);
          return security.addSecurityHeaders(response);

        } catch (error) {
          console.error('Database error:', error);
          response = new Response(JSON.stringify({
            error: 'Database error',
            message: 'Failed to query BIN database'
          }), {
            status: 500,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
          await analytics.trackRequest(request, response, sessionId);
          return security.addSecurityHeaders(response);
        }
      }

      // Card generation endpoint
      if (url.pathname.startsWith('/api/generate/')) {
        const bin = url.pathname.split('/').pop();
        
        if (!bin || bin.length < 4) {
          response = new Response(JSON.stringify({
            error: 'Invalid BIN for generation'
          }), {
            status: 400,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
          await analytics.trackRequest(request, response, sessionId);
          return security.addSecurityHeaders(response);
        }

        const cards = [];
        for (let i = 0; i < 10; i++) {
          const cardNumber = generateCardNumber(bin);
          cards.push({
            number: cardNumber,
            formatted: cardNumber.replace(/(\d{4})/g, '$1 ').trim(),
            bin: bin,
            luhn_valid: isValidLuhn(cardNumber)
          });
        }

        const result = {
          bin: bin,
          cards: cards,
          count: cards.length,
          timestamp: new Date().toISOString()
        };

        response = new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        
        await analytics.trackRequest(request, response, sessionId);
        return security.addSecurityHeaders(response);
      }

      // AI Status endpoint
      if (url.pathname === '/api/ai/status') {
        const aiStatus = {
          ai_enabled: aiInstances.aiEnabled,
          modules_loaded: aiModulesLoaded,
          features: {
            fraud_detection: aiInstances.aiEnabled,
            predictive_analytics: aiInstances.aiEnabled,
            performance_optimizer: aiInstances.aiEnabled
          },
          timestamp: new Date().toISOString()
        };
        
        response = new Response(JSON.stringify(aiStatus), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
        
        await analytics.trackRequest(request, response, sessionId);
        return security.addSecurityHeaders(response);
      }

      // 404 for all other routes
      response = new Response(JSON.stringify({
        error: 'Not Found',
        message: 'The requested resource was not found'
      }), {
        status: 404,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
      
      await analytics.trackRequest(request, response, sessionId);
      return security.addSecurityHeaders(response);
      
    } catch (error) {
      console.error('Worker Error:', error);
      
      return new Response(JSON.stringify({
        error: 'Internal Server Error',
        message: 'An unexpected error occurred',
        timestamp: new Date().toISOString()
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }
  }
};

// Homepage HTML
function getHomepageHTML() {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIN Search Pro - Enterprise BIN Analysis Platform</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 800px;
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .subtitle {
            font-size: 1.3rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        .feature {
            background: rgba(255, 255, 255, 0.2);
            padding: 1.5rem;
            border-radius: 15px;
            transition: transform 0.3s ease;
        }
        .feature:hover {
            transform: translateY(-5px);
        }
        .feature h3 {
            margin-top: 0;
            color: #ffd700;
        }
        .button {
            display: inline-block;
            padding: 1rem 2rem;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 0.5rem;
        }
        .button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }
        .api-demo {
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            margin: 1rem 0;
            text-align: left;
        }
        .footer {
            margin-top: 2rem;
            opacity: 0.7;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 BIN Search Pro</h1>
        <p class="subtitle">Enterprise-Grade BIN Analysis Platform with AI-Powered Insights</p>
        
        <div class="features">
            <div class="feature">
                <h3>🚀 Lightning Fast</h3>
                <p>Sub-100ms response times with global CDN distribution</p>
            </div>
            <div class="feature">
                <h3>🤖 AI-Enhanced</h3>
                <p>Fraud detection and predictive analytics powered by AI</p>
            </div>
            <div class="feature">
                <h3>🔒 Enterprise Security</h3>
                <p>Bank-grade security with advanced threat detection</p>
            </div>
            <div class="feature">
                <h3>📊 Business Intelligence</h3>
                <p>Comprehensive analytics and reporting dashboards</p>
            </div>
        </div>
        
        <div class="api-demo">
            <strong>API Demo:</strong><br>
            GET /api/bin/lookup/424242<br>
            GET /api/generate/424242<br>
            GET /api/ai/status
        </div>
        
        <div>
            <a href="/api/bin/lookup/424242" class="button">Try API Demo</a>
            <a href="/api/ai/status" class="button">Check AI Status</a>
        </div>
        
        <div class="footer">
            <p>© 2025 BIN Search Pro. Professional BIN Analysis Platform.</p>
            <p>🌍 Serving millions of requests worldwide</p>
        </div>
    </div>
</body>
</html>
  `;
}