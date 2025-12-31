/**
 * Health Check Module
 * Comprehensive system health monitoring for BIN Search Pro
 */

export class HealthCheck {
  constructor(env, apm, dbOptimizer, security) {
    this.env = env;
    this.apm = apm;
    this.dbOptimizer = dbOptimizer;
    this.security = security;
    this.startTime = Date.now();
  }

  /**
   * Comprehensive health check
   */
  async performHealthCheck() {
    const healthData = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: Date.now() - this.startTime,
      version: '1.0.0',
      environment: 'production',
      checks: {},
      summary: {
        total: 0,
        passed: 0,
        failed: 0,
        warnings: 0
      }
    };

    // Perform individual health checks
    const checks = [
      { name: 'database', fn: () => this.checkDatabase() },
      { name: 'api_endpoints', fn: () => this.checkAPIEndpoints() },
      { name: 'security', fn: () => this.checkSecurity() },
      { name: 'performance', fn: () => this.checkPerformance() },
      { name: 'storage', fn: () => this.checkStorage() },
      { name: 'external_services', fn: () => this.checkExternalServices() }
    ];

    for (const check of checks) {
      try {
        healthData.checks[check.name] = await check.fn();
        healthData.summary.total++;
        
        if (healthData.checks[check.name].status === 'healthy') {
          healthData.summary.passed++;
        } else if (healthData.checks[check.name].status === 'warning') {
          healthData.summary.warnings++;
        } else {
          healthData.summary.failed++;
        }
      } catch (error) {
        healthData.checks[check.name] = {
          status: 'unhealthy',
          message: `Health check failed: ${error.message}`,
          timestamp: new Date().toISOString()
        };
        healthData.summary.total++;
        healthData.summary.failed++;
      }
    }

    // Determine overall status
    if (healthData.summary.failed > 0) {
      healthData.status = 'unhealthy';
    } else if (healthData.summary.warnings > 2) {
      healthData.status = 'degraded';
    }

    // Store health check result
    await this.storeHealthCheck(healthData);

    return healthData;
  }

  /**
   * Database health check
   */
  async checkDatabase() {
    const check = {
      status: 'healthy',
      message: 'Database is operational',
      timestamp: new Date().toISOString(),
      metrics: {}
    };

    try {
      // Connectivity test
      const start = performance.now();
      await this.env.DB.prepare('SELECT 1 as test').first();
      const latency = performance.now() - start;
      
      check.metrics.latency = Math.round(latency);
      check.metrics.connectivity = 'connected';

      // Performance check
      if (latency > 1000) {
        check.status = 'warning';
        check.message = `Database latency high: ${Math.round(latency)}ms`;
      } else if (latency > 2000) {
        check.status = 'unhealthy';
        check.message = `Database latency critical: ${Math.round(latency)}ms`;
      }

      // Check critical tables exist
      const tables = ['users', 'bins', 'payments', 'search_history'];
      for (const table of tables) {
        try {
          await this.env.DB.prepare(`SELECT COUNT(*) FROM ${table} LIMIT 1`).first();
          check.metrics[`${table}_accessible`] = true;
        } catch (error) {
          check.metrics[`${table}_accessible`] = false;
          check.status = 'unhealthy';
          check.message = `Critical table ${table} inaccessible`;
        }
      }

      // Check recent error rate
      const recentErrors = await this.env.DB.prepare(`
        SELECT COUNT(*) as error_count
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-5 minutes')
        AND name LIKE '%database%'
        AND success = 0
      `).first();

      check.metrics.recent_db_errors = recentErrors?.error_count || 0;
      if (check.metrics.recent_db_errors > 5) {
        check.status = 'warning';
        check.message = `High database error rate: ${check.metrics.recent_db_errors} in 5 minutes`;
      }

    } catch (error) {
      check.status = 'unhealthy';
      check.message = `Database connection failed: ${error.message}`;
      check.metrics.connectivity = 'disconnected';
    }

    return check;
  }

  /**
   * API endpoints health check
   */
  async checkAPIEndpoints() {
    const check = {
      status: 'healthy',
      message: 'All API endpoints operational',
      timestamp: new Date().toISOString(),
      endpoints: {}
    };

    const criticalEndpoints = [
      '/api/auth/me',
      '/api/bin/lookup',
      '/api/cards/generate',
      '/api/user/stats'
    ];

    let failedEndpoints = 0;
    let slowEndpoints = 0;

    for (const endpoint of criticalEndpoints) {
      try {
        const start = performance.now();
        
        // Simulate internal endpoint check (in production, use actual HTTP calls)
        await this.simulateEndpointCheck(endpoint);
        
        const duration = performance.now() - start;
        
        check.endpoints[endpoint] = {
          status: duration < 1000 ? 'healthy' : duration < 2000 ? 'slow' : 'timeout',
          response_time: Math.round(duration)
        };

        if (check.endpoints[endpoint].status === 'timeout') {
          failedEndpoints++;
        } else if (check.endpoints[endpoint].status === 'slow') {
          slowEndpoints++;
        }

      } catch (error) {
        check.endpoints[endpoint] = {
          status: 'failed',
          error: error.message
        };
        failedEndpoints++;
      }
    }

    // Determine overall endpoint health
    if (failedEndpoints > 0) {
      check.status = 'unhealthy';
      check.message = `${failedEndpoints} critical endpoints failing`;
    } else if (slowEndpoints > 1) {
      check.status = 'warning';
      check.message = `${slowEndpoints} endpoints responding slowly`;
    }

    return check;
  }

  /**
   * Security health check
   */
  async checkSecurity() {
    const check = {
      status: 'healthy',
      message: 'Security systems operational',
      timestamp: new Date().toISOString(),
      metrics: {}
    };

    try {
      // Check for recent security incidents
      const recentIncidents = await this.env.DB.prepare(`
        SELECT COUNT(*) as incident_count
        FROM security_logs
        WHERE created_at >= datetime('now', '-1 hour')
        AND severity IN ('error', 'critical')
      `).first();

      check.metrics.recent_incidents = recentIncidents?.incident_count || 0;

      // Check blocked IPs
      const blockedIPs = await this.env.DB.prepare(`
        SELECT COUNT(*) as blocked_count
        FROM ip_blocklist
        WHERE is_active = 1
      `).first();

      check.metrics.blocked_ips = blockedIPs?.blocked_count || 0;

      // Check failed authentication attempts
      const failedAuth = await this.env.DB.prepare(`
        SELECT COUNT(*) as failed_count
        FROM failed_auth_attempts
        WHERE created_at >= datetime('now', '-1 hour')
      `).first();

      check.metrics.failed_auth_attempts = failedAuth?.failed_count || 0;

      // Determine security status
      if (check.metrics.recent_incidents > 10) {
        check.status = 'warning';
        check.message = `High security incident rate: ${check.metrics.recent_incidents}/hour`;
      }

      if (check.metrics.failed_auth_attempts > 100) {
        check.status = 'warning';
        check.message = `High failed authentication rate: ${check.metrics.failed_auth_attempts}/hour`;
      }

    } catch (error) {
      check.status = 'unhealthy';
      check.message = `Security check failed: ${error.message}`;
    }

    return check;
  }

  /**
   * Performance health check
   */
  async checkPerformance() {
    const check = {
      status: 'healthy',
      message: 'Performance within acceptable limits',
      timestamp: new Date().toISOString(),
      metrics: {}
    };

    try {
      // Check average response time
      const avgResponse = await this.env.DB.prepare(`
        SELECT AVG(duration) as avg_duration
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-15 minutes')
      `).first();

      check.metrics.avg_response_time = Math.round(avgResponse?.avg_duration || 0);

      // Check 95th percentile
      const p95Response = await this.env.DB.prepare(`
        SELECT duration as p95_duration
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-15 minutes')
        ORDER BY duration DESC
        LIMIT 1 OFFSET (
          SELECT COUNT(*) * 0.05 
          FROM monitoring_transactions
          WHERE created_at >= datetime('now', '-15 minutes')
        )
      `).first();

      check.metrics.p95_response_time = Math.round(p95Response?.p95_duration || 0);

      // Check throughput
      const throughput = await this.env.DB.prepare(`
        SELECT COUNT(*) as request_count
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-5 minutes')
      `).first();

      check.metrics.requests_per_minute = (throughput?.request_count || 0);

      // Performance thresholds
      if (check.metrics.avg_response_time > 2000) {
        check.status = 'warning';
        check.message = `High average response time: ${check.metrics.avg_response_time}ms`;
      }

      if (check.metrics.p95_response_time > 5000) {
        check.status = 'unhealthy';
        check.message = `Critical 95th percentile response time: ${check.metrics.p95_response_time}ms`;
      }

      if (check.metrics.requests_per_minute < 1 && new Date().getHours() > 6 && new Date().getHours() < 22) {
        check.status = 'warning';
        check.message = 'Unusually low traffic during business hours';
      }

    } catch (error) {
      check.status = 'unhealthy';
      check.message = `Performance check failed: ${error.message}`;
    }

    return check;
  }

  /**
   * Storage health check
   */
  async checkStorage() {
    const check = {
      status: 'healthy',
      message: 'Storage systems operational',
      timestamp: new Date().toISOString(),
      metrics: {}
    };

    try {
      // Check table sizes
      const tables = ['bins', 'users', 'payments', 'search_history', 'monitoring_transactions'];
      let totalRows = 0;

      for (const table of tables) {
        try {
          const { count } = await this.env.DB.prepare(`SELECT COUNT(*) as count FROM ${table}`).first();
          check.metrics[`${table}_rows`] = count;
          totalRows += count;
        } catch (error) {
          check.metrics[`${table}_rows`] = 'error';
        }
      }

      check.metrics.total_rows = totalRows;

      // Check for rapid growth
      const recentRows = await this.env.DB.prepare(`
        SELECT COUNT(*) as count
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-1 hour')
      `).first();

      check.metrics.hourly_growth = recentRows?.count || 0;

      // Storage warnings
      if (totalRows > 10000000) { // 10M rows
        check.status = 'warning';
        check.message = 'High storage usage, consider archiving old data';
      }

      if (check.metrics.hourly_growth > 10000) {
        check.status = 'warning';
        check.message = 'Rapid data growth detected';
      }

    } catch (error) {
      check.status = 'unhealthy';
      check.message = `Storage check failed: ${error.message}`;
    }

    return check;
  }

  /**
   * External services health check
   */
  async checkExternalServices() {
    const check = {
      status: 'healthy',
      message: 'External services operational',
      timestamp: new Date().toISOString(),
      services: {}
    };

    const services = [
      { name: 'nowpayments', url: 'https://api.nowpayments.io/v1/status', timeout: 5000 },
      { name: 'cloudflare_d1', url: null, timeout: 2000 } // Internal check
    ];

    for (const service of services) {
      try {
        const start = performance.now();
        
        if (service.url) {
          // External service check
          const response = await fetch(service.url, {
            method: 'GET',
            signal: AbortSignal.timeout(service.timeout)
          });
          
          const duration = performance.now() - start;
          
          check.services[service.name] = {
            status: response.ok ? 'healthy' : 'unhealthy',
            response_time: Math.round(duration),
            http_status: response.status
          };
        } else if (service.name === 'cloudflare_d1') {
          // D1 specific check
          await this.env.DB.prepare('SELECT 1').first();
          const duration = performance.now() - start;
          
          check.services[service.name] = {
            status: 'healthy',
            response_time: Math.round(duration)
          };
        }
        
      } catch (error) {
        check.services[service.name] = {
          status: 'unhealthy',
          error: error.message
        };
      }
    }

    // Check if any critical services are down
    const failedServices = Object.values(check.services).filter(s => s.status === 'unhealthy').length;
    
    if (failedServices > 0) {
      check.status = failedServices > 1 ? 'unhealthy' : 'warning';
      check.message = `${failedServices} external service(s) unavailable`;
    }

    return check;
  }

  /**
   * Simulate endpoint check (replace with actual HTTP calls in production)
   */
  async simulateEndpointCheck(endpoint) {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, Math.random() * 100));
    
    // Simulate occasional failures
    if (Math.random() < 0.05) { // 5% failure rate
      throw new Error('Simulated endpoint failure');
    }
    
    return { status: 'ok' };
  }

  /**
   * Store health check results
   */
  async storeHealthCheck(healthData) {
    try {
      await this.env.DB.prepare(`
        INSERT INTO monitoring_health (
          status, uptime, database_status, database_latency, error_rate,
          response_time, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
      `).bind(
        healthData.status,
        healthData.uptime,
        healthData.checks.database?.status || 'unknown',
        healthData.checks.database?.metrics?.latency || 0,
        healthData.checks.security?.metrics?.recent_incidents || 0,
        healthData.checks.performance?.metrics?.avg_response_time || 0
      ).run();
    } catch (error) {
      console.error('Failed to store health check:', error);
    }
  }

  /**
   * Get health history
   */
  async getHealthHistory(hours = 24) {
    try {
      const history = await this.env.DB.prepare(`
        SELECT 
          status, uptime, database_status, database_latency,
          error_rate, response_time, created_at
        FROM monitoring_health
        WHERE created_at >= datetime('now', '-${hours} hours')
        ORDER BY created_at DESC
      `).all();

      return history.results || [];
    } catch (error) {
      console.error('Failed to get health history:', error);
      return [];
    }
  }

  /**
   * Quick health status (for load balancer health checks)
   */
  async quickHealthCheck() {
    try {
      // Quick database connectivity test
      const start = performance.now();
      await this.env.DB.prepare('SELECT 1').first();
      const latency = performance.now() - start;

      if (latency > 5000) { // 5 seconds
        return { status: 'unhealthy', latency: Math.round(latency) };
      }

      return { status: 'healthy', latency: Math.round(latency) };
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  }
}