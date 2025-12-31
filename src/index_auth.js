/**
 * Simplified Cloudflare Worker for BIN Search API with Authentication
 * Focus on auth endpoints with proper CORS support
 */

// Card Generation Helper Functions
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

// Crypto helper functions
function getUsdPrice(currency) {
  const prices = {
    'BTC': 42000,
    'ETH': 2500,
    'LTC': 75,
    'USDT': 1,
    'USDC': 1,
    'BCH': 250,
    'XMR': 150,
    'ADA': 0.45,
    'DOGE': 0.08,
    'SOL': 90
  };
  return prices[currency] || 1;
}

function getAddressType(address, currency) {
  if (currency === 'BTC') {
    if (address.startsWith('1')) return 'P2PKH (Legacy)';
    if (address.startsWith('3')) return 'P2SH (Script)';
    if (address.startsWith('bc1')) return 'Bech32 (SegWit)';
  }
  if (currency === 'ETH' || currency === 'USDT' || currency === 'USDC') {
    return 'ERC-20 Address';
  }
  if (currency === 'LTC') {
    if (address.startsWith('L') || address.startsWith('M')) return 'Legacy';
    if (address.startsWith('ltc1')) return 'Bech32';
  }
  if (currency === 'DOGE') {
    return 'Dogecoin Address';
  }
  if (currency === 'SOL') {
    return 'Solana Address';
  }
  if (currency === 'ADA') {
    return 'Cardano Shelley';
  }
  if (currency === 'XMR') {
    return 'Monero Address';
  }
  if (currency === 'BCH') {
    return 'Bitcoin Cash Address';
  }
  return 'Standard Address';
}

function getNetworkInfo(currency) {
  const networks = {
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum',
    'LTC': 'Litecoin',
    'USDT': 'Ethereum (ERC-20)',
    'USDC': 'Ethereum (ERC-20)',
    'BCH': 'Bitcoin Cash',
    'XMR': 'Monero',
    'ADA': 'Cardano'
  };
  return networks[currency] || 'Unknown';
}

function getConfirmations(currency) {
  const confirmations = {
    'BTC': 6,
    'ETH': 12,
    'LTC': 6,
    'USDT': 12,
    'USDC': 12,
    'BCH': 6,
    'XMR': 10,
    'ADA': 15
  };
  return confirmations[currency] || 6;
}

// Simple password hashing using Web Crypto API
class SimplePasswordManager {
  async createPasswordHash(password, username = '') {
    const encoder = new TextEncoder();
    const data = encoder.encode(password + 'salt_' + username);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode(...new Uint8Array(hashBuffer)));
  }

  async verifyPasswordHash(password, storedHash, username = '') {
    const computedHash = await this.createPasswordHash(password, username);
    return computedHash === storedHash;
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

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
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
      return new Response(null, { headers: corsHeaders });
    }

    // Handle favicon.ico requests
    if (url.pathname === '/favicon.ico') {
      return new Response(null, { 
        status: 204,
        headers: corsHeaders
      });
    }

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

        // Hash password
        const passwordManager = new SimplePasswordManager();
        const passwordHash = await passwordManager.createPasswordHash(password, username);
        
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

        return new Response(JSON.stringify({
          message: 'Registration successful!',
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

        // Simple password verification
        const passwordManager = new SimplePasswordManager();
        const isValidPassword = await passwordManager.verifyPasswordHash(password, user.password_hash, user.username);
        
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
        const token = authHeader.substring(7);
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
          daily_usage: 0,
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
        const [userId, username] = decoded.split(':');
        
        // Get user from database for plan info
        const getUserStmt = env.DB.prepare('SELECT plan FROM users WHERE id = ? AND username = ?');
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
        
        // Calculate usage limits based on plan
        const isPremium = user.plan === 'premium';
        const dailyLimit = isPremium ? 1000 : 50;
        const monthlyLimit = isPremium ? 30000 : 1500;
        
        // For now, return mock usage data (in real implementation, query search_history table)
        const dailyUsage = Math.floor(Math.random() * (dailyLimit * 0.1));
        const monthlyUsage = Math.floor(Math.random() * (monthlyLimit * 0.1));
        const totalUsage = Math.floor(Math.random() * 500) + monthlyUsage;
        
        return new Response(JSON.stringify({
          daily_usage: dailyUsage,
          daily_limit: dailyLimit,
          monthly_usage: monthlyUsage,
          monthly_limit: monthlyLimit,
          total_usage: totalUsage,
          plan_features: {
            unlimited_lookups: isPremium,
            avs_generation: isPremium,
            bulk_export: isPremium,
            priority_support: isPremium
          }
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

    // Subscription info: /api/v1/payments/subscription
    if (url.pathname === '/api/v1/payments/subscription' && request.method === 'GET') {
      const authHeader = request.headers.get('Authorization');
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({
          id: 'guest_subscription',
          user_id: 0,
          plan: 'free',
          status: 'active',
          current_period_start: new Date().toISOString(),
          current_period_end: null,
          payment_method: null
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
        const [userId, username] = decoded.split(':');
        
        // Get user subscription info from database
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
        
        const isPremium = user.plan === 'premium';
        const subscriptionStart = user.created_at || new Date().toISOString();
        const subscriptionEnd = isPremium ? 
          new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() : null;
        
        return new Response(JSON.stringify({
          id: `sub_${user.id}`,
          user_id: user.id,
          plan: user.plan,
          status: 'active',
          current_period_start: subscriptionStart,
          current_period_end: subscriptionEnd,
          payment_method: isPremium ? 'crypto' : null
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

    // BIN lookup endpoint: /api/v1/bins/lookup/{bin_number}
    if (url.pathname.startsWith('/api/v1/bins/lookup/')) {
      const binNumber = url.pathname.split('/')[5];
      
      if (!binNumber || binNumber.length < 6) {
        return new Response(JSON.stringify({
          detail: 'Invalid BIN number. Must be at least 6 digits.'
        }), {
          status: 400,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
      
      try {
        const stmt = env.DB.prepare('SELECT * FROM bins WHERE bin = ?');
        const result = await stmt.bind(binNumber).first();
        
        if (result) {
          return new Response(JSON.stringify({
            bin: result.bin,
            brand: result.brand || 'Unknown',
            issuer: result.issuer || 'Unknown',
            type: result.type || 'Unknown',
            level: result.category || 'Unknown',
            country: result.country || 'Unknown'
          }), {
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        } else {
          return new Response(JSON.stringify({
            detail: 'BIN not found'
          }), {
            status: 404,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Database error'
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }

    // Card generation status: /api/ip-status
    if (url.pathname === '/api/ip-status' && request.method === 'GET') {
      const clientIP = request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for') || '127.0.0.1';
      
      return new Response(JSON.stringify({
        ip: clientIP,
        remaining_generations: 5,
        next_reset: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        rate_limited: false,
        daily_limit: 10,
        reset_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
      }), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
    }

    // Card generation: /api/generate
    if (url.pathname === '/api/generate' && request.method === 'POST') {
      try {
        let bin, count = 1, format = 'json', include_avs = false;
        
        // Handle both JSON and FormData
        const contentType = request.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          const body = await request.json();
          ({ bin, count = 1, format = 'json', include_avs = false } = body);
        } else {
          const formData = await request.formData();
          bin = formData.get('bin');
          count = parseInt(formData.get('count') || '1');
          format = formData.get('format') || 'json';
          include_avs = formData.get('include_avs') === 'true';
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

        // Get BIN info from database
        const stmt = env.DB.prepare('SELECT * FROM bins WHERE bin = ?');
        const binData = await stmt.bind(bin).first();
        
        const cards = [];
        for (let i = 0; i < count; i++) {
          // Generate card number using Luhn algorithm
          const cardNumber = generateCardNumber(bin);
          
          // Generate expiry date
          const futureDate = new Date();
          futureDate.setFullYear(futureDate.getFullYear() + Math.floor(Math.random() * 5) + 1);
          futureDate.setMonth(Math.floor(Math.random() * 12));
          const expiryMonth = String(futureDate.getMonth() + 1).padStart(2, '0');
          const expiryYear = String(futureDate.getFullYear()).slice(-2);
          
          const card = {
            number: cardNumber,
            cvv: String(Math.floor(Math.random() * 900) + 100),
            expiry_month: expiryMonth,
            expiry_year: expiryYear,
            expiry: `${expiryMonth}/${expiryYear}`,
            brand: binData?.brand || 'Unknown',
            type: binData?.type || 'Unknown',
            country: binData?.country || 'Unknown',
            bank: binData?.issuer || 'Unknown',
            generated_at: new Date().toISOString()
          };

          if (include_avs) {
            card.avs_address = `${Math.floor(Math.random() * 9999) + 1} Main St`;
            card.avs_postal = String(Math.floor(Math.random() * 90000) + 10000);
          }

          cards.push(card);
        }

        return new Response(JSON.stringify({
          cards: cards,
          total: cards.length,
          format: format,
          generated_at: new Date().toISOString()
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Card generation error: ' + error.message
        }), {
          status: 500,
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
        const token = authHeader.substring(7);
        const decoded = atob(token);
        const [userId] = decoded.split(':');
        
        const walletAddress = walletAddresses[currency] || walletAddresses['BTC'];

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

    // Crypto balance checker: /crypto/check-balance
    if (url.pathname === '/crypto/check-balance' && request.method === 'POST') {
      try {
        const body = await request.json();
        let { address, currency, crypto_type } = body;
        
        // Handle both currency and crypto_type formats
        if (!currency && crypto_type) {
          // Map frontend crypto_type to currency symbols
          const cryptoTypeMap = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH', 
            'litecoin': 'LTC',
            'dogecoin': 'DOGE',
            'cardano': 'ADA',
            'solana': 'SOL',
            'usdt': 'USDT',
            'usdc': 'USDC',
            'bch': 'BCH',
            'monero': 'XMR'
          };
          currency = cryptoTypeMap[crypto_type.toLowerCase()] || crypto_type.toUpperCase();
        }
        
        if (!address || !currency) {
          return new Response(JSON.stringify({
            detail: 'Address and currency (or crypto_type) are required'
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Validate currency
        const supportedCurrencies = ['BTC', 'ETH', 'LTC', 'USDT', 'USDC', 'BCH', 'XMR', 'ADA', 'DOGE', 'SOL'];
        if (!supportedCurrencies.includes(currency.toUpperCase())) {
          return new Response(JSON.stringify({
            detail: `Unsupported currency. Supported: ${supportedCurrencies.join(', ')}`
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Basic address validation (simplified - in real implementation, use proper validation)
        const addressPatterns = {
          'BTC': /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$/,
          'ETH': /^0x[a-fA-F0-9]{40}$/,
          'LTC': /^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$|^ltc1[a-z0-9]{39,59}$/,
          'USDT': /^0x[a-fA-F0-9]{40}$/, // ERC-20
          'USDC': /^0x[a-fA-F0-9]{40}$/, // ERC-20
          'BCH': /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^q[a-z0-9]{41}$/,
          'XMR': /^4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}$/,
          'ADA': /^addr1[a-z0-9]{58}$/,
          'DOGE': /^D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}$/,
          'SOL': /^[1-9A-HJ-NP-Za-km-z]{32,44}$/
        };

        const pattern = addressPatterns[currency.toUpperCase()];
        if (pattern && !pattern.test(address)) {
          return new Response(JSON.stringify({
            detail: `Invalid ${currency.toUpperCase()} address format`
          }), {
            status: 400,
            headers: { 
              'Content-Type': 'application/json',
              ...corsHeaders 
            }
          });
        }

        // Simulate balance checking (in real implementation, call actual blockchain APIs)
        const mockBalance = Math.random() * 10; // Random balance for demo
        const mockTransactions = Math.floor(Math.random() * 100) + 1;
        const mockUsdValue = mockBalance * getUsdPrice(currency.toUpperCase());

        // Simulate different balance states
        const balanceStates = ['active', 'empty', 'new', 'suspicious'];
        const randomState = balanceStates[Math.floor(Math.random() * balanceStates.length)];

        const currentPrice = getUsdPrice(currency.toUpperCase());
        
        const balanceInfo = {
          address: address,
          currency: currency.toUpperCase(),
          balance: parseFloat(mockBalance.toFixed(8)),
          balance_usd: parseFloat(mockUsdValue.toFixed(2)),
          usd_value: parseFloat(mockUsdValue.toFixed(2)), // Frontend compatibility
          price: currentPrice, // Current price per token/coin
          transactions_count: mockTransactions,
          last_activity: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
          timestamp: new Date().toISOString(), // Frontend compatibility
          address_type: getAddressType(address, currency.toUpperCase()),
          status: randomState,
          risk_score: Math.floor(Math.random() * 100),
          network_info: {
            network: getNetworkInfo(currency.toUpperCase()),
            confirmations_required: getConfirmations(currency.toUpperCase()),
            block_height: Math.floor(Math.random() * 1000000) + 700000
          },
          analysis: {
            is_exchange: Math.random() > 0.8,
            is_mixer: Math.random() > 0.95,
            is_gambling: Math.random() > 0.9,
            is_defi: Math.random() > 0.7,
            activity_score: Math.floor(Math.random() * 100)
          },
          checked_at: new Date().toISOString()
        };

        return new Response(JSON.stringify(balanceInfo), {
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

    // Health check endpoint
    if (url.pathname === '/api/health') {
      return new Response(JSON.stringify({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: env.VERSION || '1.0',
        environment: env.ENVIRONMENT || 'development'
      }), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
    }

    // Root endpoint with basic info
    if (url.pathname === '/') {
      return new Response(JSON.stringify({
        name: 'BIN Search API',
        version: env.VERSION || '1.0',
        environment: env.ENVIRONMENT || 'development',
        endpoints: [
          '/api/v1/auth/register',
          '/api/v1/auth/token',
          '/api/v1/auth/me',
          '/api/v1/auth/usage',
          '/api/v1/payments/subscription',
          '/api/v1/payments/create-crypto-payment',
          '/api/v1/payments/status/{paymentId}',
          '/api/v1/bins/lookup/{bin}',
          '/api/ip-status',
          '/api/generate',
          '/crypto/check-balance',
          '/api/health'
        ]
      }), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
    }

    // 404 for unknown routes
    return new Response(JSON.stringify({
      detail: 'Endpoint not found'
    }), {
      status: 404,
      headers: { 
        'Content-Type': 'application/json',
        ...corsHeaders 
      }
    });
  }
};