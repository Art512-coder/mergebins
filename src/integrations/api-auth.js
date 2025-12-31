/**
 * Advanced API Authentication and Rate Limiting System
 * Handles API keys, rate limits per tier, and usage tracking
 */

export class APIAuthManager {
    constructor(database, apm) {
        this.db = database;
        this.apm = apm;
        this.rateLimitCache = new Map();
    }

    /**
     * Create API key for user
     */
    async createAPIKey(userId, keyName, tier = 'free', permissions = []) {
        const transaction = this.apm.startTransaction('api:create_key');
        
        try {
            const keyId = this.generateId();
            const apiKey = this.generateAPIKey();
            const apiSecret = this.generateAPISecret();
            
            // Get rate limits for tier
            const rateLimits = this.getTierRateLimits(tier);
            
            const keyData = {
                id: keyId,
                user_id: userId,
                key_name: keyName,
                api_key: apiKey,
                api_secret: apiSecret,
                tier: tier,
                rate_limit_per_minute: rateLimits.requests_per_minute,
                rate_limit_per_day: rateLimits.requests_per_day,
                permissions: JSON.stringify(permissions.length > 0 ? permissions : ['*']),
                is_active: true,
                created_at: new Date().toISOString(),
                expires_at: tier === 'free' ? new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString() : null,
                daily_usage_reset_at: new Date().toISOString()
            };

            await this.db.prepare(`
                INSERT INTO api_keys 
                (id, user_id, key_name, api_key, api_secret, tier, rate_limit_per_minute, 
                 rate_limit_per_day, permissions, is_active, created_at, expires_at, daily_usage_reset_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `).bind(
                keyData.id, keyData.user_id, keyData.key_name, keyData.api_key,
                keyData.api_secret, keyData.tier, keyData.rate_limit_per_minute,
                keyData.rate_limit_per_day, keyData.permissions, keyData.is_active,
                keyData.created_at, keyData.expires_at, keyData.daily_usage_reset_at
            ).run();

            transaction.setResult('success');
            
            return {
                success: true,
                api_key: apiKey,
                api_secret: apiSecret,
                tier: tier,
                rate_limits: rateLimits,
                permissions: permissions.length > 0 ? permissions : ['*']
            };

        } catch (error) {
            transaction.setResult('error');
            console.error('Error creating API key:', error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Authenticate API request
     */
    async authenticateAPIRequest(request) {
        const transaction = this.apm.startTransaction('api:authenticate_request');
        
        try {
            // Extract API key from header or query parameter
            const apiKey = this.extractAPIKey(request);
            if (!apiKey) {
                transaction.setResult('no_key');
                return { success: false, error: 'API key required' };
            }

            // Get API key details from database
            const { results } = await this.db.prepare(`
                SELECT * FROM api_keys WHERE api_key = ? AND is_active = true
            `).bind(apiKey).all();

            if (results.length === 0) {
                transaction.setResult('invalid_key');
                return { success: false, error: 'Invalid API key' };
            }

            const keyData = results[0];

            // Check if key is expired
            if (keyData.expires_at && new Date() > new Date(keyData.expires_at)) {
                transaction.setResult('expired_key');
                return { success: false, error: 'API key expired' };
            }

            // Check rate limits
            const rateLimitResult = await this.checkRateLimit(keyData, request);
            if (!rateLimitResult.allowed) {
                transaction.setResult('rate_limited');
                return { 
                    success: false, 
                    error: 'Rate limit exceeded',
                    rate_limit: rateLimitResult.limit,
                    reset_at: rateLimitResult.reset_at
                };
            }

            // Check permissions for endpoint
            const endpoint = new URL(request.url).pathname;
            const hasPermission = this.checkEndpointPermission(keyData, endpoint);
            if (!hasPermission) {
                transaction.setResult('no_permission');
                return { success: false, error: 'Insufficient permissions' };
            }

            // Update usage stats
            await this.updateUsageStats(keyData.id, endpoint, request);

            transaction.setResult('success');
            
            return {
                success: true,
                api_key_id: keyData.id,
                user_id: keyData.user_id,
                tier: keyData.tier,
                rate_limit: rateLimitResult.limit,
                remaining: rateLimitResult.remaining
            };

        } catch (error) {
            transaction.setResult('error');
            console.error('Error authenticating API request:', error);
            return { success: false, error: 'Authentication failed' };
        } finally {
            transaction.end();
        }
    }

    /**
     * Check rate limits for API key
     */
    async checkRateLimit(keyData, request) {
        const now = new Date();
        const keyId = keyData.id;
        
        // Reset daily usage if needed
        const resetTime = new Date(keyData.daily_usage_reset_at);
        const shouldResetDaily = now.getTime() - resetTime.getTime() >= 24 * 60 * 60 * 1000;
        
        if (shouldResetDaily) {
            await this.db.prepare(`
                UPDATE api_keys 
                SET daily_usage_count = 0, daily_usage_reset_at = ?
                WHERE id = ?
            `).bind(now.toISOString(), keyId).run();
            keyData.daily_usage_count = 0;
        }

        // Check daily limit (if not unlimited)
        if (keyData.rate_limit_per_day > 0 && keyData.daily_usage_count >= keyData.rate_limit_per_day) {
            return {
                allowed: false,
                limit: keyData.rate_limit_per_day,
                remaining: 0,
                reset_at: new Date(resetTime.getTime() + 24 * 60 * 60 * 1000).toISOString()
            };
        }

        // Check minute limit using in-memory cache
        const minuteKey = `${keyId}:${Math.floor(now.getTime() / 60000)}`;
        const minuteCount = this.rateLimitCache.get(minuteKey) || 0;
        
        if (minuteCount >= keyData.rate_limit_per_minute) {
            return {
                allowed: false,
                limit: keyData.rate_limit_per_minute,
                remaining: 0,
                reset_at: new Date((Math.floor(now.getTime() / 60000) + 1) * 60000).toISOString()
            };
        }

        // Update rate limit counters
        this.rateLimitCache.set(minuteKey, minuteCount + 1);
        
        // Clean up old cache entries periodically
        if (Math.random() < 0.01) { // 1% chance
            this.cleanupRateLimitCache();
        }

        return {
            allowed: true,
            limit: keyData.rate_limit_per_minute,
            remaining: keyData.rate_limit_per_minute - minuteCount - 1
        };
    }

    /**
     * Update API usage statistics
     */
    async updateUsageStats(apiKeyId, endpoint, request) {
        try {
            const logId = this.generateId();
            const now = new Date().toISOString();
            
            // Log API usage
            await this.db.prepare(`
                INSERT INTO api_usage_logs 
                (id, api_key_id, endpoint, method, request_ip, user_agent, request_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            `).bind(
                logId,
                apiKeyId,
                endpoint,
                request.method,
                request.headers.get('CF-Connecting-IP') || 'unknown',
                request.headers.get('User-Agent') || 'unknown',
                now
            ).run();

            // Update key usage counters
            await this.db.prepare(`
                UPDATE api_keys 
                SET usage_count = usage_count + 1,
                    daily_usage_count = daily_usage_count + 1,
                    last_used_at = ?
                WHERE id = ?
            `).bind(now, apiKeyId).run();

        } catch (error) {
            console.error('Error updating usage stats:', error);
        }
    }

    /**
     * Check if API key has permission for endpoint
     */
    checkEndpointPermission(keyData, endpoint) {
        try {
            const permissions = JSON.parse(keyData.permissions || '["*"]');
            
            // Wildcard permission
            if (permissions.includes('*')) {
                return true;
            }

            // Check specific endpoint permissions
            return permissions.some(permission => {
                if (permission === endpoint) return true;
                
                // Support wildcard patterns like /api/bin/*
                if (permission.endsWith('/*')) {
                    const basePath = permission.slice(0, -2);
                    return endpoint.startsWith(basePath);
                }
                
                return false;
            });

        } catch (error) {
            console.error('Error checking permissions:', error);
            return false;
        }
    }

    /**
     * Get user's API keys
     */
    async getUserAPIKeys(userId) {
        try {
            const { results } = await this.db.prepare(`
                SELECT id, key_name, api_key, tier, rate_limit_per_minute, rate_limit_per_day,
                       permissions, is_active, created_at, expires_at, last_used_at,
                       usage_count, daily_usage_count
                FROM api_keys 
                WHERE user_id = ?
                ORDER BY created_at DESC
            `).bind(userId).all();

            return {
                success: true,
                api_keys: results.map(key => ({
                    ...key,
                    permissions: JSON.parse(key.permissions || '[]'),
                    api_key: key.api_key.substring(0, 8) + '...' + key.api_key.slice(-4) // Mask API key
                }))
            };

        } catch (error) {
            console.error('Error fetching user API keys:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Update API key
     */
    async updateAPIKey(keyId, userId, updates) {
        const transaction = this.apm.startTransaction('api:update_key');
        
        try {
            const updateFields = [];
            const values = [];
            
            if (updates.key_name) {
                updateFields.push('key_name = ?');
                values.push(updates.key_name);
            }
            
            if (updates.permissions && Array.isArray(updates.permissions)) {
                updateFields.push('permissions = ?');
                values.push(JSON.stringify(updates.permissions));
            }
            
            if (typeof updates.is_active === 'boolean') {
                updateFields.push('is_active = ?');
                values.push(updates.is_active);
            }
            
            if (updates.tier && ['free', 'pro', 'enterprise'].includes(updates.tier)) {
                const rateLimits = this.getTierRateLimits(updates.tier);
                updateFields.push('tier = ?', 'rate_limit_per_minute = ?', 'rate_limit_per_day = ?');
                values.push(updates.tier, rateLimits.requests_per_minute, rateLimits.requests_per_day);
            }
            
            if (updateFields.length === 0) {
                return { success: false, error: 'No valid updates provided' };
            }
            
            values.push(keyId, userId);

            const result = await this.db.prepare(`
                UPDATE api_keys 
                SET ${updateFields.join(', ')}
                WHERE id = ? AND user_id = ?
            `).bind(...values).run();

            transaction.setResult(result.changes > 0 ? 'success' : 'not_found');
            
            return {
                success: result.changes > 0,
                updated: result.changes > 0
            };

        } catch (error) {
            transaction.setResult('error');
            console.error('Error updating API key:', error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Delete API key
     */
    async deleteAPIKey(keyId, userId) {
        const transaction = this.apm.startTransaction('api:delete_key');
        
        try {
            const result = await this.db.prepare(`
                DELETE FROM api_keys 
                WHERE id = ? AND user_id = ?
            `).bind(keyId, userId).run();

            transaction.setResult(result.changes > 0 ? 'success' : 'not_found');
            
            return {
                success: result.changes > 0,
                deleted: result.changes > 0
            };

        } catch (error) {
            transaction.setResult('error');
            console.error('Error deleting API key:', error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Get API usage analytics
     */
    async getAPIUsageAnalytics(userId, timeframe = '7d') {
        try {
            const timeframeDays = parseInt(timeframe.replace('d', '')) || 7;
            const startDate = new Date(Date.now() - timeframeDays * 24 * 60 * 60 * 1000).toISOString();
            
            // Get usage by endpoint
            const { results: endpointUsage } = await this.db.prepare(`
                SELECT aul.endpoint, COUNT(*) as request_count,
                       AVG(aul.response_time_ms) as avg_response_time
                FROM api_usage_logs aul
                JOIN api_keys ak ON aul.api_key_id = ak.id
                WHERE ak.user_id = ? AND aul.request_timestamp >= ?
                GROUP BY aul.endpoint
                ORDER BY request_count DESC
            `).bind(userId, startDate).all();

            // Get usage by day
            const { results: dailyUsage } = await this.db.prepare(`
                SELECT DATE(aul.request_timestamp) as date, COUNT(*) as request_count
                FROM api_usage_logs aul
                JOIN api_keys ak ON aul.api_key_id = ak.id
                WHERE ak.user_id = ? AND aul.request_timestamp >= ?
                GROUP BY DATE(aul.request_timestamp)
                ORDER BY date ASC
            `).bind(userId, startDate).all();

            // Get status code distribution
            const { results: statusCodes } = await this.db.prepare(`
                SELECT aul.status_code, COUNT(*) as count
                FROM api_usage_logs aul
                JOIN api_keys ak ON aul.api_key_id = ak.id
                WHERE ak.user_id = ? AND aul.request_timestamp >= ?
                GROUP BY aul.status_code
                ORDER BY count DESC
            `).bind(userId, startDate).all();

            return {
                success: true,
                analytics: {
                    endpoint_usage: endpointUsage,
                    daily_usage: dailyUsage,
                    status_codes: statusCodes,
                    timeframe: timeframe
                }
            };

        } catch (error) {
            console.error('Error fetching API usage analytics:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Extract API key from request
     */
    extractAPIKey(request) {
        // Check Authorization header (Bearer token)
        const authHeader = request.headers.get('Authorization');
        if (authHeader && authHeader.startsWith('Bearer ')) {
            return authHeader.substring(7);
        }

        // Check X-API-Key header
        const apiKeyHeader = request.headers.get('X-API-Key');
        if (apiKeyHeader) {
            return apiKeyHeader;
        }

        // Check query parameter
        const url = new URL(request.url);
        return url.searchParams.get('api_key');
    }

    /**
     * Get rate limits for tier
     */
    getTierRateLimits(tier) {
        const limits = {
            free: { requests_per_minute: 10, requests_per_day: 100 },
            pro: { requests_per_minute: 100, requests_per_day: 10000 },
            enterprise: { requests_per_minute: 1000, requests_per_day: -1 } // -1 = unlimited
        };
        
        return limits[tier] || limits.free;
    }

    /**
     * Clean up old rate limit cache entries
     */
    cleanupRateLimitCache() {
        const now = Math.floor(Date.now() / 60000);
        const keysToDelete = [];
        
        for (const [key] of this.rateLimitCache) {
            const minute = parseInt(key.split(':')[1]);
            if (now - minute > 5) { // Keep only last 5 minutes
                keysToDelete.push(key);
            }
        }
        
        keysToDelete.forEach(key => this.rateLimitCache.delete(key));
    }

    /**
     * Generate API key
     */
    generateAPIKey() {
        const prefix = 'bsp_'; // BinSearchPro prefix
        const random = crypto.randomUUID().replace(/-/g, '');
        return prefix + random;
    }

    /**
     * Generate API secret
     */
    generateAPISecret() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    /**
     * Generate unique ID
     */
    generateId() {
        return crypto.randomUUID();
    }
}