/**
 * Webhook Management System
 * Handles webhook subscriptions, event delivery, and retry logic
 */

export class WebhookManager {
    constructor(database, apm) {
        this.db = database;
        this.apm = apm;
        this.retryIntervals = [1000, 5000, 15000, 60000, 300000]; // 1s, 5s, 15s, 1m, 5m
    }

    /**
     * Create webhook subscription
     */
    async createSubscription(userId, config) {
        const transaction = this.apm.startTransaction('webhook:create_subscription');
        
        try {
            const subscriptionId = this.generateId();
            const secretKey = this.generateSecretKey();
            
            const subscription = {
                id: subscriptionId,
                user_id: userId,
                endpoint_url: config.endpoint_url,
                secret_key: secretKey,
                event_types: JSON.stringify(config.event_types || []),
                is_active: true,
                retry_config: JSON.stringify({
                    max_retries: config.max_retries || 5,
                    retry_intervals: this.retryIntervals
                }),
                headers: JSON.stringify(config.headers || {}),
                created_at: new Date().toISOString()
            };

            const result = await this.db.prepare(`
                INSERT INTO webhook_subscriptions 
                (id, user_id, endpoint_url, secret_key, event_types, is_active, retry_config, headers, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            `).bind(
                subscription.id,
                subscription.user_id,
                subscription.endpoint_url,
                subscription.secret_key,
                subscription.event_types,
                subscription.is_active,
                subscription.retry_config,
                subscription.headers,
                subscription.created_at
            ).run();

            transaction.setResult('success');
            
            return {
                success: true,
                subscription_id: subscriptionId,
                secret_key: secretKey,
                endpoint_url: config.endpoint_url,
                event_types: config.event_types
            };

        } catch (error) {
            transaction.setResult('error');
            console.error('Error creating webhook subscription:', error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Get user's webhook subscriptions
     */
    async getUserSubscriptions(userId) {
        try {
            const { results } = await this.db.prepare(`
                SELECT id, endpoint_url, event_types, is_active, created_at,
                       last_delivery_at, total_deliveries, successful_deliveries, failed_deliveries
                FROM webhook_subscriptions 
                WHERE user_id = ?
                ORDER BY created_at DESC
            `).bind(userId).all();

            return {
                success: true,
                subscriptions: results.map(sub => ({
                    ...sub,
                    event_types: JSON.parse(sub.event_types || '[]'),
                    success_rate: sub.total_deliveries > 0 
                        ? (sub.successful_deliveries / sub.total_deliveries * 100).toFixed(2) 
                        : 0
                }))
            };

        } catch (error) {
            console.error('Error fetching user subscriptions:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Update webhook subscription
     */
    async updateSubscription(subscriptionId, userId, updates) {
        const transaction = this.apm.startTransaction('webhook:update_subscription');
        
        try {
            const updateFields = [];
            const values = [];
            
            if (updates.endpoint_url) {
                updateFields.push('endpoint_url = ?');
                values.push(updates.endpoint_url);
            }
            
            if (updates.event_types) {
                updateFields.push('event_types = ?');
                values.push(JSON.stringify(updates.event_types));
            }
            
            if (updates.headers) {
                updateFields.push('headers = ?');
                values.push(JSON.stringify(updates.headers));
            }
            
            if (typeof updates.is_active === 'boolean') {
                updateFields.push('is_active = ?');
                values.push(updates.is_active);
            }
            
            updateFields.push('updated_at = ?');
            values.push(new Date().toISOString());
            
            values.push(subscriptionId, userId);

            const result = await this.db.prepare(`
                UPDATE webhook_subscriptions 
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
            console.error('Error updating webhook subscription:', error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Delete webhook subscription
     */
    async deleteSubscription(subscriptionId, userId) {
        const transaction = this.apm.startTransaction('webhook:delete_subscription');
        
        try {
            const result = await this.db.prepare(`
                DELETE FROM webhook_subscriptions 
                WHERE id = ? AND user_id = ?
            `).bind(subscriptionId, userId).run();

            transaction.setResult(result.changes > 0 ? 'success' : 'not_found');
            
            return {
                success: result.changes > 0,
                deleted: result.changes > 0
            };

        } catch (error) {
            transaction.setResult('error');
            console.error('Error deleting webhook subscription:', error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Trigger webhook event
     */
    async triggerEvent(eventType, eventData, userId = null) {
        const transaction = this.apm.startTransaction('webhook:trigger_event');
        
        try {
            const eventId = this.generateId();
            
            // Store the event
            await this.db.prepare(`
                INSERT INTO webhook_events (id, event_type, event_data, user_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            `).bind(
                eventId,
                eventType,
                JSON.stringify(eventData),
                userId,
                new Date().toISOString()
            ).run();

            // Find matching subscriptions
            const { results: subscriptions } = await this.db.prepare(`
                SELECT * FROM webhook_subscriptions 
                WHERE is_active = true 
                AND (user_id = ? OR user_id IS NULL)
            `).bind(userId || '').all();

            // Filter subscriptions by event type
            const matchingSubscriptions = subscriptions.filter(sub => {
                const eventTypes = JSON.parse(sub.event_types || '[]');
                return eventTypes.includes(eventType) || eventTypes.includes('*');
            });

            // Schedule deliveries
            const deliveries = await Promise.all(
                matchingSubscriptions.map(subscription => 
                    this.scheduleDelivery(subscription, eventId, eventType, eventData)
                )
            );

            transaction.setResult('success');
            
            return {
                success: true,
                event_id: eventId,
                deliveries_scheduled: deliveries.length
            };

        } catch (error) {
            transaction.setResult('error');
            console.error('Error triggering webhook event:', error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Schedule webhook delivery
     */
    async scheduleDelivery(subscription, eventId, eventType, eventData) {
        const deliveryId = this.generateId();
        
        try {
            // Create delivery record
            await this.db.prepare(`
                INSERT INTO webhook_deliveries 
                (id, subscription_id, event_id, attempt_number, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            `).bind(
                deliveryId,
                subscription.id,
                eventId,
                1,
                'pending',
                new Date().toISOString()
            ).run();

            // Attempt immediate delivery
            const delivered = await this.attemptDelivery(subscription, eventId, eventType, eventData, deliveryId, 1);
            
            return { delivery_id: deliveryId, delivered };

        } catch (error) {
            console.error('Error scheduling webhook delivery:', error);
            return { delivery_id: deliveryId, delivered: false };
        }
    }

    /**
     * Attempt webhook delivery
     */
    async attemptDelivery(subscription, eventId, eventType, eventData, deliveryId, attemptNumber) {
        try {
            const payload = {
                event_id: eventId,
                event_type: eventType,
                timestamp: new Date().toISOString(),
                data: eventData
            };

            const signature = this.generateSignature(JSON.stringify(payload), subscription.secret_key);
            
            const headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'BinSearch-Webhook/1.0',
                'X-BinSearch-Event': eventType,
                'X-BinSearch-Signature': signature,
                'X-BinSearch-Delivery': deliveryId,
                'X-BinSearch-Attempt': attemptNumber.toString(),
                ...JSON.parse(subscription.headers || '{}')
            };

            const startTime = Date.now();
            
            const response = await fetch(subscription.endpoint_url, {
                method: 'POST',
                headers,
                body: JSON.stringify(payload),
                timeout: 30000
            });

            const responseTime = Date.now() - startTime;
            const responseBody = await response.text();

            // Update delivery record
            const status = response.ok ? 'success' : 'failed';
            
            await this.db.prepare(`
                UPDATE webhook_deliveries 
                SET status = ?, response_code = ?, response_body = ?, 
                    response_headers = ?, delivered_at = ?
                WHERE id = ?
            `).bind(
                status,
                response.status,
                responseBody.substring(0, 1000), // Limit response body size
                JSON.stringify(Object.fromEntries(response.headers.entries())),
                new Date().toISOString(),
                deliveryId
            ).run();

            // Update subscription stats
            if (response.ok) {
                await this.db.prepare(`
                    UPDATE webhook_subscriptions 
                    SET total_deliveries = total_deliveries + 1,
                        successful_deliveries = successful_deliveries + 1,
                        last_delivery_at = ?
                    WHERE id = ?
                `).bind(new Date().toISOString(), subscription.id).run();
            } else {
                await this.db.prepare(`
                    UPDATE webhook_subscriptions 
                    SET total_deliveries = total_deliveries + 1,
                        failed_deliveries = failed_deliveries + 1
                    WHERE id = ?
                `).bind(subscription.id).run();
                
                // Schedule retry if needed
                const retryConfig = JSON.parse(subscription.retry_config || '{}');
                if (attemptNumber < (retryConfig.max_retries || 5)) {
                    await this.scheduleRetry(subscription, eventId, eventType, eventData, deliveryId, attemptNumber + 1);
                }
            }

            return response.ok;

        } catch (error) {
            console.error('Webhook delivery failed:', error);
            
            // Update delivery record with error
            await this.db.prepare(`
                UPDATE webhook_deliveries 
                SET status = ?, error_message = ?, delivered_at = ?
                WHERE id = ?
            `).bind(
                'failed',
                error.message,
                new Date().toISOString(),
                deliveryId
            ).run();

            // Update subscription stats
            await this.db.prepare(`
                UPDATE webhook_subscriptions 
                SET total_deliveries = total_deliveries + 1,
                    failed_deliveries = failed_deliveries + 1
                WHERE id = ?
            `).bind(subscription.id).run();

            return false;
        }
    }

    /**
     * Schedule delivery retry
     */
    async scheduleRetry(subscription, eventId, eventType, eventData, originalDeliveryId, attemptNumber) {
        try {
            const retryDeliveryId = this.generateId();
            const retryConfig = JSON.parse(subscription.retry_config || '{}');
            const retryDelay = retryConfig.retry_intervals?.[attemptNumber - 2] || 60000;

            // Create retry delivery record
            await this.db.prepare(`
                INSERT INTO webhook_deliveries 
                (id, subscription_id, event_id, attempt_number, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            `).bind(
                retryDeliveryId,
                subscription.id,
                eventId,
                attemptNumber,
                'pending',
                new Date(Date.now() + retryDelay).toISOString()
            ).run();

            // In a real implementation, you would use a queue system like Cloudflare Queues
            // For now, we'll use setTimeout for demonstration
            setTimeout(() => {
                this.attemptDelivery(subscription, eventId, eventType, eventData, retryDeliveryId, attemptNumber);
            }, retryDelay);

        } catch (error) {
            console.error('Error scheduling webhook retry:', error);
        }
    }

    /**
     * Get webhook delivery logs
     */
    async getDeliveryLogs(subscriptionId, userId, limit = 50) {
        try {
            const { results } = await this.db.prepare(`
                SELECT wd.*, we.event_type, we.created_at as event_created_at
                FROM webhook_deliveries wd
                JOIN webhook_events we ON wd.event_id = we.id
                JOIN webhook_subscriptions ws ON wd.subscription_id = ws.id
                WHERE ws.id = ? AND ws.user_id = ?
                ORDER BY wd.created_at DESC
                LIMIT ?
            `).bind(subscriptionId, userId, limit).all();

            return {
                success: true,
                logs: results
            };

        } catch (error) {
            console.error('Error fetching delivery logs:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Verify webhook signature
     */
    verifySignature(payload, signature, secret) {
        const expectedSignature = this.generateSignature(payload, secret);
        return signature === expectedSignature;
    }

    /**
     * Generate webhook signature
     */
    generateSignature(payload, secret) {
        return `sha256=${this.hmacSha256(payload, secret)}`;
    }

    /**
     * HMAC SHA256 implementation
     */
    async hmacSha256(message, secret) {
        const encoder = new TextEncoder();
        const key = await crypto.subtle.importKey(
            'raw',
            encoder.encode(secret),
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );
        
        const signature = await crypto.subtle.sign(
            'HMAC',
            key,
            encoder.encode(message)
        );
        
        return Array.from(new Uint8Array(signature))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    /**
     * Generate unique ID
     */
    generateId() {
        return crypto.randomUUID();
    }

    /**
     * Generate secret key
     */
    generateSecretKey() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
}

/**
 * Webhook API endpoints
 */
export class WebhookAPI {
    constructor(webhookManager, securityManager) {
        this.webhookManager = webhookManager;
        this.security = securityManager;
    }

    async handleRequest(request) {
        const url = new URL(request.url);
        const path = url.pathname;
        const method = request.method;

        // Authenticate user
        const authResult = await this.security.authenticateRequest(request);
        if (!authResult.success) {
            return new Response(JSON.stringify({ error: 'Authentication required' }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const userId = authResult.user_id;

        try {
            // Route webhook requests
            if (path === '/api/webhooks' && method === 'POST') {
                return await this.createWebhook(request, userId);
            }
            
            if (path === '/api/webhooks' && method === 'GET') {
                return await this.listWebhooks(userId);
            }
            
            if (path.match(/^\/api\/webhooks\/([^\/]+)$/) && method === 'PUT') {
                const subscriptionId = path.split('/')[3];
                return await this.updateWebhook(request, subscriptionId, userId);
            }
            
            if (path.match(/^\/api\/webhooks\/([^\/]+)$/) && method === 'DELETE') {
                const subscriptionId = path.split('/')[3];
                return await this.deleteWebhook(subscriptionId, userId);
            }
            
            if (path.match(/^\/api\/webhooks\/([^\/]+)\/logs$/) && method === 'GET') {
                const subscriptionId = path.split('/')[3];
                return await this.getWebhookLogs(subscriptionId, userId);
            }

            return new Response(JSON.stringify({ error: 'Not found' }), {
                status: 404,
                headers: { 'Content-Type': 'application/json' }
            });

        } catch (error) {
            console.error('Webhook API error:', error);
            return new Response(JSON.stringify({ error: 'Internal server error' }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }

    async createWebhook(request, userId) {
        const data = await request.json();
        
        // Validate required fields
        if (!data.endpoint_url || !data.event_types || !Array.isArray(data.event_types)) {
            return new Response(JSON.stringify({ 
                error: 'endpoint_url and event_types are required' 
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // Validate URL
        try {
            new URL(data.endpoint_url);
        } catch {
            return new Response(JSON.stringify({ 
                error: 'Invalid endpoint_url' 
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const result = await this.webhookManager.createSubscription(userId, data);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 201 : 400,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    async listWebhooks(userId) {
        const result = await this.webhookManager.getUserSubscriptions(userId);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 200 : 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    async updateWebhook(request, subscriptionId, userId) {
        const data = await request.json();
        const result = await this.webhookManager.updateSubscription(subscriptionId, userId, data);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 200 : 400,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    async deleteWebhook(subscriptionId, userId) {
        const result = await this.webhookManager.deleteSubscription(subscriptionId, userId);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 200 : 404,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    async getWebhookLogs(subscriptionId, userId) {
        const result = await this.webhookManager.getDeliveryLogs(subscriptionId, userId);
        
        return new Response(JSON.stringify(result), {
            status: result.success ? 200 : 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}