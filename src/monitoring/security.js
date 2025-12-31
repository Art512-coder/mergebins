/**
 * Security Hardening Module
 * Enterprise-grade security features for BIN Search Pro
 */

export class SecurityManager {
  constructor(env) {
    this.env = env;
  }

  /**
   * Rate limiting with Redis-like functionality using D1
   */
  async checkRateLimit(key, limit, window) {
    const now = Date.now();
    const windowStart = now - (window * 1000);

    // Clean old entries
    await this.env.DB.prepare(`
      DELETE FROM rate_limits 
      WHERE key = ? AND timestamp < ?
    `).bind(key, windowStart).run();

    // Count current requests
    const { count } = await this.env.DB.prepare(`
      SELECT COUNT(*) as count 
      FROM rate_limits 
      WHERE key = ? AND timestamp >= ?
    `).bind(key, windowStart).first();

    if (count >= limit) {
      return {
        allowed: false,
        remaining: 0,
        resetTime: windowStart + (window * 1000)
      };
    }

    // Add current request
    await this.env.DB.prepare(`
      INSERT INTO rate_limits (key, timestamp) 
      VALUES (?, ?)
    `).bind(key, now).run();

    return {
      allowed: true,
      remaining: limit - count - 1,
      resetTime: windowStart + (window * 1000)
    };
  }

  /**
   * IP-based rate limiting
   */
  async checkIPRateLimit(ip, endpoint, limit = 100, window = 3600) {
    const key = `ip:${ip}:${endpoint}`;
    return await this.checkRateLimit(key, limit, window);
  }

  /**
   * User-based rate limiting
   */
  async checkUserRateLimit(userId, endpoint, limit = 1000, window = 3600) {
    const key = `user:${userId}:${endpoint}`;
    return await this.checkRateLimit(key, limit, window);
  }

  /**
   * Request validation and sanitization
   */
  validateRequest(request, schema) {
    const errors = [];

    // Content-Type validation
    const contentType = request.headers.get('content-type');
    if (schema.requireJSON && !contentType?.includes('application/json')) {
      errors.push('Invalid Content-Type. Expected application/json');
    }

    // Request size validation
    const contentLength = request.headers.get('content-length');
    if (contentLength && parseInt(contentLength) > (schema.maxSize || 1048576)) { // 1MB default
      errors.push('Request too large');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Input sanitization
   */
  sanitizeInput(data, rules = {}) {
    if (typeof data !== 'object' || data === null) {
      return data;
    }

    const sanitized = {};
    
    for (const [key, value] of Object.entries(data)) {
      const rule = rules[key] || {};
      
      if (typeof value === 'string') {
        let sanitizedValue = value;
        
        // XSS protection
        if (rule.escapeHtml !== false) {
          sanitizedValue = this.escapeHtml(sanitizedValue);
        }
        
        // SQL injection protection
        if (rule.escapeSql !== false) {
          sanitizedValue = this.escapeSql(sanitizedValue);
        }
        
        // Length limits
        if (rule.maxLength && sanitizedValue.length > rule.maxLength) {
          sanitizedValue = sanitizedValue.substring(0, rule.maxLength);
        }
        
        // Pattern validation
        if (rule.pattern && !rule.pattern.test(sanitizedValue)) {
          continue; // Skip invalid fields
        }
        
        sanitized[key] = sanitizedValue;
      } else if (typeof value === 'number') {
        if (rule.min !== undefined && value < rule.min) continue;
        if (rule.max !== undefined && value > rule.max) continue;
        sanitized[key] = value;
      } else if (Array.isArray(value) && rule.allowArray) {
        sanitized[key] = value.map(item => 
          typeof item === 'string' ? this.escapeHtml(item) : item
        );
      } else if (rule.allowObject) {
        sanitized[key] = this.sanitizeInput(value, rule.objectRules || {});
      }
    }
    
    return sanitized;
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  /**
   * Basic SQL escape (additional to parameterized queries)
   */
  escapeSql(text) {
    return text.replace(/'/g, "''");
  }

  /**
   * JWT token validation
   */
  async validateJWT(token, secret) {
    try {
      const [header, payload, signature] = token.split('.');
      
      // Decode header and payload
      const decodedHeader = JSON.parse(atob(header));
      const decodedPayload = JSON.parse(atob(payload));
      
      // Check expiration
      if (decodedPayload.exp && decodedPayload.exp < Date.now() / 1000) {
        return { valid: false, error: 'Token expired' };
      }
      
      // Verify signature (simplified - in production use proper crypto library)
      const expectedSignature = await this.createSignature(header + '.' + payload, secret);
      if (signature !== expectedSignature) {
        return { valid: false, error: 'Invalid signature' };
      }
      
      return { valid: true, payload: decodedPayload };
    } catch (error) {
      return { valid: false, error: 'Invalid token format' };
    }
  }

  /**
   * Create JWT signature
   */
  async createSignature(data, secret) {
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    
    const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(data));
    return btoa(String.fromCharCode(...new Uint8Array(signature)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  /**
   * Request origin validation
   */
  validateOrigin(request, allowedOrigins) {
    const origin = request.headers.get('origin');
    const referer = request.headers.get('referer');
    
    if (!origin && !referer) {
      return { valid: false, error: 'Missing origin information' };
    }
    
    const sourceOrigin = origin || new URL(referer).origin;
    
    if (!allowedOrigins.includes(sourceOrigin) && !allowedOrigins.includes('*')) {
      return { valid: false, error: 'Invalid origin' };
    }
    
    return { valid: true };
  }

  /**
   * Security headers
   */
  addSecurityHeaders(response) {
    // CORS headers
    response.headers.set('Access-Control-Allow-Origin', 'https://main.bin-search-pro.pages.dev');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key');
    response.headers.set('Access-Control-Max-Age', '86400');
    
    // Security headers
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-XSS-Protection', '1; mode=block');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    response.headers.set('Content-Security-Policy', 
      "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.nowpayments.io https://*.cloudflare.com"
    );
    
    // Cache control for sensitive endpoints
    if (response.headers.get('cache-control') === null) {
      response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, private');
    }
    
    return response;
  }

  /**
   * Log security events
   */
  async logSecurityEvent(type, details, severity = 'info') {
    try {
      await this.env.DB.prepare(`
        INSERT INTO security_logs (
          event_type, severity, details, ip_address, user_agent, created_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'))
      `).bind(
        type,
        severity,
        JSON.stringify(details),
        details.ip || 'unknown',
        details.userAgent || 'unknown'
      ).run();
    } catch (error) {
      console.error('Failed to log security event:', error);
    }
  }

  /**
   * Detect suspicious activity
   */
  async detectSuspiciousActivity(ip, userAgent, endpoint) {
    const now = Date.now();
    const hour = now - (60 * 60 * 1000); // Last hour
    
    // Check for rapid requests from same IP
    const { request_count } = await this.env.DB.prepare(`
      SELECT COUNT(*) as request_count 
      FROM rate_limits 
      WHERE key LIKE ? AND timestamp >= ?
    `).bind(`ip:${ip}:%`, hour).first();
    
    if (request_count > 1000) { // More than 1000 requests per hour
      await this.logSecurityEvent('high_request_volume', {
        ip,
        userAgent,
        endpoint,
        requestCount: request_count
      }, 'warning');
      
      return { suspicious: true, reason: 'High request volume' };
    }
    
    // Check for SQL injection patterns
    const suspiciousPatterns = [
      /union\s+select/i,
      /drop\s+table/i,
      /insert\s+into/i,
      /delete\s+from/i,
      /script\s*>/i,
      /<\s*script/i
    ];
    
    for (const pattern of suspiciousPatterns) {
      if (pattern.test(endpoint) || pattern.test(userAgent)) {
        await this.logSecurityEvent('injection_attempt', {
          ip,
          userAgent,
          endpoint,
          pattern: pattern.source
        }, 'critical');
        
        return { suspicious: true, reason: 'Injection attempt detected' };
      }
    }
    
    return { suspicious: false };
  }

  /**
   * API key validation
   */
  async validateAPIKey(apiKey) {
    if (!apiKey) {
      return { valid: false, error: 'API key required' };
    }
    
    try {
      const result = await this.env.DB.prepare(`
        SELECT id, user_id, permissions, rate_limit, is_active, expires_at
        FROM api_keys 
        WHERE key_hash = ? AND is_active = 1
      `).bind(await this.hashAPIKey(apiKey)).first();
      
      if (!result) {
        return { valid: false, error: 'Invalid API key' };
      }
      
      // Check expiration
      if (result.expires_at && new Date(result.expires_at) < new Date()) {
        return { valid: false, error: 'API key expired' };
      }
      
      return {
        valid: true,
        keyId: result.id,
        userId: result.user_id,
        permissions: JSON.parse(result.permissions || '[]'),
        rateLimit: result.rate_limit
      };
    } catch (error) {
      console.error('API key validation error:', error);
      return { valid: false, error: 'Validation failed' };
    }
  }

  /**
   * Hash API key for storage
   */
  async hashAPIKey(apiKey) {
    const encoder = new TextEncoder();
    const data = encoder.encode(apiKey);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(hash))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  /**
   * Generate secure API key
   */
  generateAPIKey() {
    const prefix = 'bsp_'; // BIN Search Pro
    const randomBytes = new Uint8Array(32);
    crypto.getRandomValues(randomBytes);
    const key = Array.from(randomBytes)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    return prefix + key;
  }

  /**
   * Check if IP is in blocklist
   */
  async isIPBlocked(ip) {
    try {
      const result = await this.env.DB.prepare(`
        SELECT id FROM ip_blocklist 
        WHERE ip_address = ? AND is_active = 1
      `).bind(ip).first();
      
      return !!result;
    } catch (error) {
      console.error('IP blocklist check error:', error);
      return false; // Fail open for availability
    }
  }

  /**
   * Block IP address
   */
  async blockIP(ip, reason, duration = null) {
    try {
      const expiresAt = duration ? 
        new Date(Date.now() + duration * 1000).toISOString() : 
        null;
      
      await this.env.DB.prepare(`
        INSERT OR REPLACE INTO ip_blocklist (
          ip_address, reason, expires_at, is_active, created_at
        ) VALUES (?, ?, ?, 1, datetime('now'))
      `).bind(ip, reason, expiresAt).run();
      
      await this.logSecurityEvent('ip_blocked', {
        ip,
        reason,
        duration
      }, 'warning');
      
      return true;
    } catch (error) {
      console.error('IP blocking error:', error);
      return false;
    }
  }
}