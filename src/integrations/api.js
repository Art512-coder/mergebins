/**
 * Integration API Handler
 * Manages webhooks, API keys, and third-party integrations
 */

export class IntegrationAPI {
    constructor(webhookManager, apiAuthManager, binProvider, securityManager, webhookAPI) {
        this.webhooks = webhookManager;
        this.apiAuth = apiAuthManager;
        this.binProvider = binProvider;
        this.security = securityManager;
        this.webhookAPI = webhookAPI;
    }

    async handleRequest(request, env) {
        const url = new URL(request.url);
        const path = url.pathname;
        const method = request.method;

        try {
            // API Key Management endpoints
            if (path.startsWith('/api/keys')) {
                return await this.handleAPIKeyRequests(request, path, method);
            }

            // Webhook Management endpoints
            if (path.startsWith('/api/webhooks')) {
                return await this.handleWebhookRequests(request, path, method);
            }

            // Enhanced BIN API endpoints
            if (path.startsWith('/api/bin/enhanced')) {
                return await this.handleEnhancedBINRequests(request, path, method);
            }

            // Payment endpoints
            if (path.startsWith('/api/payments')) {
                return await this.handlePaymentRequests(request, path, method);
            }

            // Integration status endpoint
            if (path === '/api/integrations/status' && method === 'GET') {
                return await this.getIntegrationStatus();
            }

            return new Response(JSON.stringify({ error: 'Not found' }), {
                status: 404,
                headers: { 'Content-Type': 'application/json' }
            });

        } catch (error) {
            console.error('Integration API error:', error);
            return new Response(JSON.stringify({ error: 'Internal server error' }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }

    /**
     * Handle API Key management requests
     */
    async handleAPIKeyRequests(request, path, method) {
        // Authenticate user
        const authResult = await this.security.authenticateRequest(request);
        if (!authResult.success) {
            return new Response(JSON.stringify({ error: 'Authentication required' }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const userId = authResult.user_id;

        if (path === '/api/keys' && method === 'POST') {
            return await this.createAPIKey(request, userId);
        }

        if (path === '/api/keys' && method === 'GET') {
            return await this.listAPIKeys(userId);
        }

        if (path.match(/^\/api\/keys\/([^\/]+)$/) && method === 'PUT') {
            const keyId = path.split('/')[3];
            return await this.updateAPIKey(request, keyId, userId);
        }

        if (path.match(/^\/api\/keys\/([^\/]+)$/) && method === 'DELETE') {
            const keyId = path.split('/')[3];
            return await this.deleteAPIKey(keyId, userId);
        }

        if (path.match(/^\/api\/keys\/([^\/]+)\/analytics$/) && method === 'GET') {
            const keyId = path.split('/')[3];
            return await this.getAPIKeyAnalytics(keyId, userId, request);
        }

        return new Response(JSON.stringify({ error: 'Not found' }), {
            status: 404,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    /**
     * Handle Webhook management requests
     */
    async handleWebhookRequests(request, path, method) {
        // Use webhook API directly
        return await this.webhookAPI.handleRequest(request);
    }

    /**
     * Handle Enhanced BIN API requests
     */
    async handleEnhancedBINRequests(request, path, method) {
        // Authenticate API request
        const authResult = await this.apiAuth.authenticateAPIRequest(request);
        if (!authResult.success) {
            return new Response(JSON.stringify({ 
                error: authResult.error,
                rate_limit: authResult.rate_limit 
            }), {
                status: 401,
                headers: { 
                    'Content-Type': 'application/json',
                    'X-RateLimit-Limit': authResult.rate_limit?.toString() || '0',
                    'X-RateLimit-Remaining': authResult.remaining?.toString() || '0'
                }
            });
        }

        if (path.match(/^\/api\/bin\/enhanced\/([0-9]+)$/) && method === 'GET') {
            const binNumber = path.split('/')[4];
            return await this.getEnhancedBINData(binNumber, request, authResult);
        }

        return new Response(JSON.stringify({ error: 'Not found' }), {
            status: 404,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    /**
     * Create API Key
     */
    async createAPIKey(request, userId) {
        try {
            const data = await request.json();
            
            if (!data.key_name) {
                return new Response(JSON.stringify({ error: 'key_name is required' }), {
                    status: 400,
                    headers: { 'Content-Type': 'application/json' }
                });
            }

            const result = await this.apiAuth.createAPIKey(
                userId, 
                data.key_name, 
                data.tier || 'free',
                data.permissions || []
            );

            return new Response(JSON.stringify(result), {
                status: result.success ? 201 : 400,
                headers: { 'Content-Type': 'application/json' }
            });

        } catch (error) {
            console.error('Error creating API key:', error);
            return new Response(JSON.stringify({ error: 'Invalid request data' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }

    /**
     * List user's API Keys
     */
    async listAPIKeys(userId) {
        const result = await this.apiAuth.getUserAPIKeys(userId);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 200 : 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    /**
     * Update API Key
     */
    async updateAPIKey(request, keyId, userId) {
        try {
            const data = await request.json();
            const result = await this.apiAuth.updateAPIKey(keyId, userId, data);
            
            return new Response(JSON.stringify(result), {
                status: result.success ? 200 : 400,
                headers: { 'Content-Type': 'application/json' }
            });

        } catch (error) {
            return new Response(JSON.stringify({ error: 'Invalid request data' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }

    /**
     * Delete API Key
     */
    async deleteAPIKey(keyId, userId) {
        const result = await this.apiAuth.deleteAPIKey(keyId, userId);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 200 : 404,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    /**
     * Get API Key Analytics
     */
    async getAPIKeyAnalytics(keyId, userId, request) {
        const url = new URL(request.url);
        const timeframe = url.searchParams.get('timeframe') || '7d';
        
        const result = await this.apiAuth.getAPIUsageAnalytics(userId, timeframe);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 200 : 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    /**
     * Get Enhanced BIN Data
     */
    async getEnhancedBINData(binNumber, request, authResult) {
        try {
            // Validate BIN number
            if (!binNumber || binNumber.length < 6) {
                return new Response(JSON.stringify({ error: 'Invalid BIN number' }), {
                    status: 400,
                    headers: { 'Content-Type': 'application/json' }
                });
            }

            const result = await this.binProvider.getBINData(binNumber);

            // Trigger webhook event for BIN lookup
            await this.webhooks.triggerEvent('bin.lookup.enhanced', {
                bin: binNumber.substring(0, 6),
                user_id: authResult.user_id,
                api_key_id: authResult.api_key_id,
                result: result,
                timestamp: new Date().toISOString()
            }, authResult.user_id);

            return new Response(JSON.stringify({
                success: true,
                data: result,
                metadata: {
                    api_tier: authResult.tier,
                    rate_limit: {
                        limit: authResult.rate_limit,
                        remaining: authResult.remaining
                    }
                }
            }), {
                status: 200,
                headers: { 
                    'Content-Type': 'application/json',
                    'X-RateLimit-Limit': authResult.rate_limit?.toString() || '0',
                    'X-RateLimit-Remaining': authResult.remaining?.toString() || '0'
                }
            });

        } catch (error) {
            console.error('Error fetching enhanced BIN data:', error);
            return new Response(JSON.stringify({ error: 'Internal server error' }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }

    /**
     * Handle Payment requests
     */
    async handlePaymentRequests(request, path, method) {
        // Authenticate user
        const authResult = await this.security.authenticateRequest(request);
        if (!authResult.success) {
            return new Response(JSON.stringify({ error: 'Authentication required' }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        if (path === '/api/payments/plans' && method === 'GET') {
            return await this.getPaymentPlans();
        }

        if (path === '/api/payments/subscription' && method === 'POST') {
            return await this.createSubscription(request, authResult.user_id);
        }

        if (path === '/api/payments/subscription' && method === 'GET') {
            return await this.getUserSubscription(authResult.user_id);
        }

        return new Response(JSON.stringify({ error: 'Not found' }), {
            status: 404,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    /**
     * Get Payment Plans
     */
    async getPaymentPlans() {
        try {
            const { results } = await this.apiAuth.db.prepare(`
                SELECT id, plan_name, plan_type, price_cents, currency, billing_interval,
                       features, rate_limits, is_active
                FROM payment_plans 
                WHERE is_active = true
                ORDER BY price_cents ASC
            `).all();

            const plans = results.map(plan => ({
                ...plan,
                features: JSON.parse(plan.features || '[]'),
                rate_limits: JSON.parse(plan.rate_limits || '{}'),
                price_display: plan.price_cents === 0 ? 'Free' : `$${(plan.price_cents / 100).toFixed(2)}`
            }));

            return new Response(JSON.stringify({
                success: true,
                plans: plans
            }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });

        } catch (error) {
            console.error('Error fetching payment plans:', error);
            return new Response(JSON.stringify({ error: 'Internal server error' }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }

    /**
     * Get Integration Status
     */
    async getIntegrationStatus() {
        try {
            return new Response(JSON.stringify({
                success: true,
                status: {
                    webhooks: {
                        total_subscriptions: 0,
                        active_subscriptions: 0,
                        total_deliveries: 0,
                        successful_deliveries: 0
                    },
                    api_keys: {
                        total_keys: 0,
                        active_keys: 0,
                        total_requests: 0
                    },
                    external_apis: {
                        total_providers: 3,
                        active_providers: 3,
                        total_successes: 0,
                        total_errors: 0
                    },
                    integration_health: 'healthy',
                    phase: 'Phase 3: Advanced Integrations',
                    last_updated: new Date().toISOString()
                }
            }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });

        } catch (error) {
            console.error('Error getting integration status:', error);
            return new Response(JSON.stringify({ error: 'Internal server error' }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }
}