/**
 * Minimal Cloudflare Worker for Error 1101 Debugging
 * Basic BIN lookup without AI features
 */

export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);
      
      // Add CORS headers for all responses
      const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
      };
      
      // Handle preflight requests
      if (request.method === 'OPTIONS') {
        return new Response(null, { 
          status: 204, 
          headers: corsHeaders 
        });
      }
      
      // Basic health check
      if (url.pathname === '/' || url.pathname === '/health') {
        return new Response(JSON.stringify({
          status: 'OPERATIONAL',
          message: 'BIN Search API - Minimal Version',
          timestamp: new Date().toISOString(),
          version: 'minimal-debug-v1.0'
        }), {
          status: 200,
          headers: corsHeaders
        });
      }
      
      // Basic BIN lookup
      if (url.pathname.startsWith('/api/bin/lookup/')) {
        const bin = url.pathname.split('/').pop();
        
        // Basic BIN validation
        if (!bin || bin.length < 4 || bin.length > 8) {
          return new Response(JSON.stringify({
            error: 'Invalid BIN format',
            message: 'BIN must be 4-8 digits',
            bin: bin
          }), {
            status: 400,
            headers: corsHeaders
          });
        }
        
        // Mock BIN data for testing
        const mockData = {
          bin: bin,
          brand: 'UNKNOWN',
          issuer: 'TEST BANK',
          type: 'UNKNOWN',
          category: 'UNKNOWN',
          country: 'UNKNOWN',
          currency: 'USD',
          luhn_valid: isValidLuhn(bin + '00000000'),
          status: 'SUCCESS',
          timestamp: new Date().toISOString(),
          version: 'minimal-debug'
        };
        
        return new Response(JSON.stringify(mockData), {
          status: 200,
          headers: corsHeaders
        });
      }
      
      // Generate test card numbers
      if (url.pathname.startsWith('/api/generate/')) {
        const bin = url.pathname.split('/').pop();
        
        if (!bin || bin.length < 4) {
          return new Response(JSON.stringify({
            error: 'Invalid BIN for generation'
          }), {
            status: 400,
            headers: corsHeaders
          });
        }
        
        const cards = [];
        for (let i = 0; i < 5; i++) {
          cards.push(generateTestCard(bin));
        }
        
        return new Response(JSON.stringify({
          bin: bin,
          cards: cards,
          count: cards.length,
          timestamp: new Date().toISOString()
        }), {
          status: 200,
          headers: corsHeaders
        });
      }
      
      // API status endpoint
      if (url.pathname === '/api/status') {
        return new Response(JSON.stringify({
          status: 'ACTIVE',
          features: {
            basic_lookup: true,
            card_generation: true,
            ai_features: false,
            database: false
          },
          endpoints: [
            '/health',
            '/api/bin/lookup/{bin}',
            '/api/generate/{bin}',
            '/api/status'
          ],
          timestamp: new Date().toISOString()
        }), {
          status: 200,
          headers: corsHeaders
        });
      }
      
      // 404 for unknown routes
      return new Response(JSON.stringify({
        error: 'Not Found',
        message: 'Route not found in minimal worker',
        available_routes: ['/health', '/api/bin/lookup/{bin}', '/api/generate/{bin}', '/api/status']
      }), {
        status: 404,
        headers: corsHeaders
      });
      
    } catch (error) {
      console.error('Worker Error:', error);
      
      return new Response(JSON.stringify({
        error: 'Internal Server Error',
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
        version: 'minimal-debug'
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

// Helper function for Luhn validation
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

// Helper function for generating test cards
function generateTestCard(bin) {
  try {
    let cardNumber = bin;
    
    // Fill to 15 digits
    const remainingLength = 15 - bin.length;
    for (let i = 0; i < remainingLength; i++) {
      cardNumber += Math.floor(Math.random() * 10);
    }
    
    // Calculate check digit
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
    
    return {
      number: cardNumber,
      formatted: cardNumber.replace(/(\d{4})/g, '$1 ').trim(),
      bin: bin,
      luhn_valid: true
    };
  } catch (error) {
    return {
      number: bin + '00000000000',
      formatted: 'Error generating card',
      bin: bin,
      luhn_valid: false,
      error: error.message
    };
  }
}