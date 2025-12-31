/**
 * Application Performance Monitoring (APM) System
 * Enterprise-grade monitoring for BIN Search Pro
 */

export class APMMonitor {
  constructor(env) {
    this.env = env;
    this.startTime = Date.now();
  }

  /**
   * Start performance tracking for a request
   */
  startTransaction(transactionName, request) {
    const transactionId = this.generateTransactionId();
    return {
      id: transactionId,
      name: transactionName,
      startTime: Date.now(),
      url: request.url,
      method: request.method,
      userAgent: request.headers.get('user-agent'),
      ip: request.headers.get('cf-connecting-ip') || 'unknown',
      country: request.cf?.country || 'unknown',
      spans: [],
      errors: [],
      metadata: {}
    };
  }

  /**
   * Track database operations
   */
  async trackDatabaseOperation(transaction, operation, query, params = []) {
    const span = {
      id: this.generateSpanId(),
      name: `db.${operation}`,
      startTime: Date.now(),
      type: 'database'
    };

    try {
      let result;
      const startTime = performance.now();
      
      if (operation === 'select') {
        result = await this.env.DB.prepare(query).bind(...params).all();
      } else if (operation === 'insert' || operation === 'update' || operation === 'delete') {
        result = await this.env.DB.prepare(query).bind(...params).run();
      } else {
        result = await this.env.DB.prepare(query).bind(...params).first();
      }

      const duration = performance.now() - startTime;
      
      span.duration = duration;
      span.endTime = Date.now();
      span.success = true;
      span.metadata = {
        query: this.sanitizeQuery(query),
        paramCount: params.length,
        rowsAffected: result?.changes || 0,
        rowsReturned: result?.results?.length || (result ? 1 : 0)
      };

      transaction.spans.push(span);
      return result;
    } catch (error) {
      span.duration = performance.now() - span.startTime;
      span.endTime = Date.now();
      span.success = false;
      span.error = error.message;
      
      transaction.spans.push(span);
      transaction.errors.push({
        type: 'DatabaseError',
        message: error.message,
        timestamp: Date.now(),
        span: span.id
      });
      
      throw error;
    }
  }

  /**
   * Track external API calls
   */
  async trackExternalAPI(transaction, apiName, url, options = {}) {
    const span = {
      id: this.generateSpanId(),
      name: `api.${apiName}`,
      startTime: Date.now(),
      type: 'http'
    };

    try {
      const startTime = performance.now();
      const response = await fetch(url, options);
      const duration = performance.now() - startTime;

      span.duration = duration;
      span.endTime = Date.now();
      span.success = response.ok;
      span.metadata = {
        url,
        method: options.method || 'GET',
        status: response.status,
        statusText: response.statusText
      };

      transaction.spans.push(span);
      return response;
    } catch (error) {
      span.duration = performance.now() - span.startTime;
      span.endTime = Date.now();
      span.success = false;
      span.error = error.message;
      
      transaction.spans.push(span);
      transaction.errors.push({
        type: 'NetworkError',
        message: error.message,
        timestamp: Date.now(),
        span: span.id
      });
      
      throw error;
    }
  }

  /**
   * Add custom metrics to transaction
   */
  addMetric(transaction, name, value, unit = 'count') {
    if (!transaction.metadata.metrics) {
      transaction.metadata.metrics = [];
    }
    
    transaction.metadata.metrics.push({
      name,
      value,
      unit,
      timestamp: Date.now()
    });
  }

  /**
   * Record error in transaction
   */
  recordError(transaction, error, context = {}) {
    transaction.errors.push({
      type: error.constructor.name,
      message: error.message,
      stack: error.stack,
      timestamp: Date.now(),
      context
    });
  }

  /**
   * Complete transaction and store metrics
   */
  async finishTransaction(transaction, response) {
    transaction.endTime = Date.now();
    transaction.duration = transaction.endTime - transaction.startTime;
    transaction.status = response?.status || 500;
    transaction.success = !transaction.errors.length && (response?.status < 400);

    // Calculate performance metrics
    const metrics = this.calculateMetrics(transaction);
    transaction.metadata.performance = metrics;

    // Store in monitoring database
    await this.storeTransaction(transaction);

    // Check for alerts
    await this.checkAlerts(transaction, metrics);

    return transaction;
  }

  /**
   * Calculate performance metrics
   */
  calculateMetrics(transaction) {
    const totalDuration = transaction.duration;
    const dbTime = transaction.spans
      .filter(s => s.type === 'database')
      .reduce((sum, s) => sum + (s.duration || 0), 0);
    const apiTime = transaction.spans
      .filter(s => s.type === 'http')
      .reduce((sum, s) => sum + (s.duration || 0), 0);

    return {
      totalDuration,
      dbTime,
      apiTime,
      applicationTime: totalDuration - dbTime - apiTime,
      dbQueryCount: transaction.spans.filter(s => s.type === 'database').length,
      apiCallCount: transaction.spans.filter(s => s.type === 'http').length,
      errorCount: transaction.errors.length
    };
  }

  /**
   * Store transaction data
   */
  async storeTransaction(transaction) {
    try {
      const query = `
        INSERT INTO monitoring_transactions (
          transaction_id, name, start_time, end_time, duration, status, success,
          method, url, user_agent, ip, country, error_count, db_query_count,
          api_call_count, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
      `;

      await this.env.DB.prepare(query).bind(
        transaction.id,
        transaction.name,
        transaction.startTime,
        transaction.endTime,
        transaction.duration,
        transaction.status,
        transaction.success ? 1 : 0,
        transaction.method,
        transaction.url,
        transaction.userAgent,
        transaction.ip,
        transaction.country,
        transaction.errors.length,
        transaction.metadata.performance?.dbQueryCount || 0,
        transaction.metadata.performance?.apiCallCount || 0,
        JSON.stringify({
          spans: transaction.spans,
          errors: transaction.errors,
          metrics: transaction.metadata.metrics || [],
          performance: transaction.metadata.performance
        })
      ).run();

      // Store individual spans for detailed analysis
      for (const span of transaction.spans) {
        await this.storeSpan(transaction.id, span);
      }

      // Update aggregate metrics
      await this.updateAggregateMetrics(transaction);
    } catch (error) {
      console.error('Failed to store APM transaction:', error);
    }
  }

  /**
   * Store span data
   */
  async storeSpan(transactionId, span) {
    const query = `
      INSERT INTO monitoring_spans (
        span_id, transaction_id, name, type, start_time, end_time, duration,
        success, error_message, metadata, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `;

    await this.env.DB.prepare(query).bind(
      span.id,
      transactionId,
      span.name,
      span.type,
      span.startTime,
      span.endTime,
      span.duration || 0,
      span.success ? 1 : 0,
      span.error || null,
      JSON.stringify(span.metadata || {})
    ).run();
  }

  /**
   * Update aggregate metrics
   */
  async updateAggregateMetrics(transaction) {
    const hour = new Date(transaction.startTime).toISOString().slice(0, 13) + ':00:00';
    
    const query = `
      INSERT OR REPLACE INTO monitoring_metrics (
        metric_hour, endpoint, total_requests, successful_requests, failed_requests,
        avg_response_time, p95_response_time, error_rate, throughput,
        avg_db_time, total_db_queries, updated_at
      ) VALUES (
        ?, ?, 
        COALESCE((SELECT total_requests FROM monitoring_metrics WHERE metric_hour = ? AND endpoint = ?), 0) + 1,
        COALESCE((SELECT successful_requests FROM monitoring_metrics WHERE metric_hour = ? AND endpoint = ?), 0) + ?,
        COALESCE((SELECT failed_requests FROM monitoring_metrics WHERE metric_hour = ? AND endpoint = ?), 0) + ?,
        ?, ?, ?, ?, ?, ?, datetime('now')
      )
    `;

    await this.env.DB.prepare(query).bind(
      hour,
      transaction.name,
      hour, transaction.name,
      hour, transaction.name, transaction.success ? 1 : 0,
      hour, transaction.name, transaction.success ? 0 : 1,
      transaction.duration,
      0, // P95 will be calculated separately
      transaction.errors.length > 0 ? 1 : 0,
      1, // throughput
      transaction.metadata.performance?.dbTime || 0,
      transaction.metadata.performance?.dbQueryCount || 0
    ).run();
  }

  /**
   * Check for performance alerts
   */
  async checkAlerts(transaction, metrics) {
    const alerts = [];

    // High response time alert
    if (metrics.totalDuration > 5000) { // 5 seconds
      alerts.push({
        type: 'high_response_time',
        severity: 'warning',
        message: `High response time: ${metrics.totalDuration}ms`,
        transaction: transaction.id
      });
    }

    // High database time alert
    if (metrics.dbTime > 3000) { // 3 seconds
      alerts.push({
        type: 'high_database_time',
        severity: 'warning',
        message: `High database time: ${metrics.dbTime}ms`,
        transaction: transaction.id
      });
    }

    // Error alert
    if (transaction.errors.length > 0) {
      alerts.push({
        type: 'error',
        severity: 'error',
        message: `Transaction failed: ${transaction.errors[0].message}`,
        transaction: transaction.id
      });
    }

    // Store alerts
    for (const alert of alerts) {
      await this.storeAlert(alert);
    }
  }

  /**
   * Store alert
   */
  async storeAlert(alert) {
    const query = `
      INSERT INTO monitoring_alerts (
        type, severity, message, transaction_id, created_at
      ) VALUES (?, ?, ?, ?, datetime('now'))
    `;

    await this.env.DB.prepare(query).bind(
      alert.type,
      alert.severity,
      alert.message,
      alert.transaction
    ).run();
  }

  /**
   * Generate transaction ID
   */
  generateTransactionId() {
    return `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate span ID
   */
  generateSpanId() {
    return `span_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Sanitize SQL query for storage
   */
  sanitizeQuery(query) {
    return query.replace(/\s+/g, ' ').trim().substring(0, 500);
  }

  /**
   * Get health check data
   */
  async getHealthCheck() {
    const uptime = Date.now() - this.startTime;
    
    // Database connectivity check
    let dbStatus = 'unknown';
    let dbLatency = 0;
    try {
      const start = performance.now();
      await this.env.DB.prepare('SELECT 1').first();
      dbLatency = performance.now() - start;
      dbStatus = 'healthy';
    } catch (error) {
      dbStatus = 'unhealthy';
    }

    // Get recent metrics
    const recentMetrics = await this.getRecentMetrics();

    return {
      status: dbStatus === 'healthy' ? 'healthy' : 'unhealthy',
      uptime,
      timestamp: Date.now(),
      database: {
        status: dbStatus,
        latency: dbLatency
      },
      metrics: recentMetrics
    };
  }

  /**
   * Get recent performance metrics
   */
  async getRecentMetrics() {
    try {
      const query = `
        SELECT 
          SUM(total_requests) as total_requests,
          SUM(successful_requests) as successful_requests,
          SUM(failed_requests) as failed_requests,
          AVG(avg_response_time) as avg_response_time,
          AVG(error_rate) as error_rate
        FROM monitoring_metrics 
        WHERE metric_hour >= datetime('now', '-1 hour')
      `;

      const result = await this.env.DB.prepare(query).first();
      return result || {
        total_requests: 0,
        successful_requests: 0,
        failed_requests: 0,
        avg_response_time: 0,
        error_rate: 0
      };
    } catch (error) {
      console.error('Failed to get recent metrics:', error);
      return null;
    }
  }

  /**
   * Get performance dashboard data
   */
  async getDashboardData(hours = 24) {
    try {
      const metricsQuery = `
        SELECT 
          metric_hour,
          endpoint,
          total_requests,
          successful_requests,
          failed_requests,
          avg_response_time,
          error_rate,
          throughput
        FROM monitoring_metrics 
        WHERE metric_hour >= datetime('now', '-${hours} hours')
        ORDER BY metric_hour DESC
      `;

      const alertsQuery = `
        SELECT type, severity, message, created_at
        FROM monitoring_alerts 
        WHERE created_at >= datetime('now', '-${hours} hours')
        ORDER BY created_at DESC
        LIMIT 50
      `;

      const [metrics, alerts] = await Promise.all([
        this.env.DB.prepare(metricsQuery).all(),
        this.env.DB.prepare(alertsQuery).all()
      ]);

      return {
        metrics: metrics.results || [],
        alerts: alerts.results || [],
        summary: await this.getRecentMetrics()
      };
    } catch (error) {
      console.error('Failed to get dashboard data:', error);
      return { metrics: [], alerts: [], summary: null };
    }
  }
}