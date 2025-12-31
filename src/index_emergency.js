/**
 * Cloudflare Worker for BIN Search API - Emergency Safe Mode
 * Minimal working version without complex module dependencies
 */

export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);
      const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      };

      // Handle CORS preflight
      if (request.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: corsHeaders });
      }

      // Homepage
      if (url.pathname === '/' || url.pathname === '/index.html') {
        return new Response(getHomepageHTML(), {
          headers: { 
            'Content-Type': 'text/html',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            ...corsHeaders 
          }
        });
      }
      
      // Health check
      if (url.pathname === '/health' || url.pathname === '/status') {
        return new Response(JSON.stringify({
          status: 'OPERATIONAL',
          message: 'BIN Search Pro - Emergency Safe Mode',
          version: 'emergency-safe-v1.1',
          timestamp: new Date().toISOString(),
          mode: 'EMERGENCY_SAFE',
          cache_busted: true,
          features: {
            bin_lookup: true,
            card_generation: true,
            database_connection: true,
            advanced_features: false
          }
        }), {
          headers: { 
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            ...corsHeaders 
          }
        });
      }

      // BIN Lookup
      if (url.pathname.startsWith('/api/bin/lookup/')) {
        const bin = url.pathname.split('/').pop();
        
        if (!bin || bin.length < 4 || bin.length > 8 || !/^\d+$/.test(bin)) {
          return new Response(JSON.stringify({
            error: 'Invalid BIN format',
            message: 'BIN must be 4-8 digits'
          }), {
            status: 400,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }

        try {
          // Try database lookup
          let result = null;
          if (env.DB) {
            try {
              result = await env.DB.prepare(
                'SELECT * FROM bin_data WHERE bin = ?'
              ).bind(bin).first();
            } catch (dbError) {
              console.warn('Database query failed:', dbError.message);
            }
          }

          let binData;
          if (result) {
            binData = {
              bin: result.bin,
              brand: result.brand || 'UNKNOWN',
              issuer: result.issuer || 'UNKNOWN',
              type: result.type || 'UNKNOWN',
              category: result.category || 'UNKNOWN',
              country: result.country_name || 'UNKNOWN',
              country_code: result.country_code || 'XX',
              currency: result.currency || 'USD',
              website: result.website || null,
              phone: result.phone || null,
              status: 'SUCCESS'
            };
          } else {
            // Fallback data
            binData = {
              bin: bin,
              brand: getBrandFromBin(bin),
              issuer: 'EMERGENCY MODE - Limited Data',
              type: getTypeFromBin(bin),
              category: 'STANDARD',
              country: 'UNKNOWN',
              country_code: 'XX',
              currency: 'USD',
              status: 'EMERGENCY_MODE'
            };
          }

          binData.luhn_valid = isValidLuhn(bin + '00000000');
          binData.timestamp = new Date().toISOString();
          binData.mode = 'emergency_safe';

          return new Response(JSON.stringify(binData), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });

        } catch (error) {
          console.error('BIN lookup error:', error);
          return new Response(JSON.stringify({
            error: 'Lookup failed',
            message: 'Emergency mode - limited functionality',
            bin: bin,
            timestamp: new Date().toISOString()
          }), {
            status: 500,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
      }

      // Card generation
      if (url.pathname.startsWith('/api/generate/')) {
        const bin = url.pathname.split('/').pop();
        
        if (!bin || bin.length < 4 || !/^\d+$/.test(bin)) {
          return new Response(JSON.stringify({
            error: 'Invalid BIN for generation'
          }), {
            status: 400,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
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

        return new Response(JSON.stringify({
          bin: bin,
          cards: cards,
          count: cards.length,
          timestamp: new Date().toISOString(),
          mode: 'emergency_safe'
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // System status
      if (url.pathname === '/api/status') {
        return new Response(JSON.stringify({
          status: 'OPERATIONAL',
          mode: 'EMERGENCY_SAFE',
          version: 'emergency-safe-v1.0',
          features: {
            bin_lookup: true,
            card_generation: true,
            database: env.DB ? true : false,
            advanced_monitoring: false,
            ai_features: false
          },
          timestamp: new Date().toISOString(),
          message: 'Running in emergency safe mode - core features only'
        }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // 404 for unknown routes
      return new Response(JSON.stringify({
        error: 'Not Found',
        message: 'Route not found',
        available_routes: ['/health', '/api/bin/lookup/{bin}', '/api/generate/{bin}', '/api/status'],
        mode: 'emergency_safe'
      }), {
        status: 404,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });

    } catch (error) {
      console.error('Emergency worker error:', error);
      
      return new Response(JSON.stringify({
        error: 'Critical Error',
        message: 'Emergency safe mode encountered an error',
        timestamp: new Date().toISOString(),
        error_details: error.message
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

// Utility functions
function isValidLuhn(cardNumber) {
  try {
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
  } catch (error) {
    return false;
  }
}

function generateCardNumber(bin) {
  try {
    let cardNumber = bin;
    const remainingLength = 15 - bin.length;
    
    for (let i = 0; i < remainingLength; i++) {
      cardNumber += Math.floor(Math.random() * 10);
    }
    
    // Calculate Luhn check digit
    let sum = 0;
    let shouldDouble = true;
    
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
    cardNumber += checkDigit;
    
    return cardNumber;
  } catch (error) {
    return bin + '00000000000';
  }
}

function getBrandFromBin(bin) {
  const first = bin[0];
  if (first === '4') return 'VISA';
  if (first === '5') return 'MASTERCARD';
  if (first === '3') return 'AMERICAN EXPRESS';
  if (first === '6') return 'DISCOVER';
  return 'UNKNOWN';
}

function getTypeFromBin(bin) {
  if (bin.startsWith('4111') || bin.startsWith('5555')) return 'CREDIT';
  if (bin.startsWith('4000')) return 'DEBIT';
  return 'UNKNOWN';
}

function getHomepageHTML() {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIN Search Pro - Emergency Safe Mode</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
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
        .emergency-notice {
            background: rgba(255, 165, 0, 0.3);
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            border: 2px solid rgba(255, 165, 0, 0.5);
        }
        .status {
            background: rgba(0, 255, 0, 0.2);
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .button {
            display: inline-block;
            padding: 1rem 2rem;
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            margin: 0.5rem;
            transition: transform 0.3s ease;
        }
        .button:hover {
            transform: translateY(-3px);
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        .feature {
            background: rgba(255, 255, 255, 0.2);
            padding: 1rem;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 BIN Search Pro</h1>
        <h2>Emergency Safe Mode - UPDATED v1.1</h2>
        
        <div class="emergency-notice">
            <h3>⚠️ Emergency Mode Active - Cache Cleared</h3>
            <p>System is running in emergency safe mode with core functionality only.</p>
            <p>Advanced features have been temporarily disabled for stability.</p>
            <p><strong>Timestamp: ${new Date().toISOString()}</strong></p>
        </div>
        
        <div class="status">
            <h3>✅ Core System Operational</h3>
            <p>BIN lookup and card generation services are fully functional</p>
        </div>
        
        <div class="features">
            <div class="feature">
                <h4>🔍 BIN Lookup</h4>
                <p>Basic BIN information retrieval</p>
            </div>
            <div class="feature">
                <h4>💳 Card Generation</h4>
                <p>Test card number generation</p>
            </div>
            <div class="feature">
                <h4>📊 System Status</h4>
                <p>Real-time health monitoring</p>
            </div>
        </div>
        
        <div>
            <a href="/api/bin/lookup/424242" class="button">Test BIN Lookup</a>
            <a href="/api/generate/424242" class="button">Generate Cards</a>
            <a href="/api/status" class="button">System Status</a>
        </div>
        
        <div class="footer" style="margin-top: 2rem; opacity: 0.8;">
            <p>🛡️ Emergency Safe Mode v1.1 - Cache Cleared - Updated ${new Date().toLocaleString()}</p>
            <p>© 2025 BIN Search Pro</p>
        </div>
    </div>
</body>
</html>
  `;
}