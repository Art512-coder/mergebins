/**
 * Database Performance Optimizer
 * Enterprise-grade database optimization for BIN Search Pro
 */

export class DatabaseOptimizer {
  constructor(env, apm) {
    this.env = env;
    this.apm = apm;
  }

  /**
   * Analyze query performance and suggest optimizations
   */
  async analyzeQueryPerformance() {
    const analysis = {
      slowQueries: [],
      indexSuggestions: [],
      tableStats: [],
      recommendations: []
    };

    try {
      // Get slow queries from APM data
      const slowQueries = await this.env.DB.prepare(`
        SELECT 
          JSON_EXTRACT(metadata, '$.spans') as spans,
          name, duration, created_at
        FROM monitoring_transactions 
        WHERE duration > 2000 
        ORDER BY duration DESC 
        LIMIT 50
      `).all();

      for (const transaction of slowQueries.results || []) {
        try {
          const spans = JSON.parse(transaction.spans || '[]');
          const dbSpans = spans.filter(s => s.type === 'database' && s.duration > 1000);
          
          for (const span of dbSpans) {
            analysis.slowQueries.push({
              query: span.metadata?.query || 'Unknown',
              duration: span.duration,
              timestamp: transaction.created_at
            });
          }
        } catch (e) {
          console.error('Error parsing spans:', e);
        }
      }

      // Analyze table statistics
      analysis.tableStats = await this.getTableStatistics();

      // Generate index suggestions
      analysis.indexSuggestions = await this.suggestIndexes(analysis.slowQueries);

      // Generate general recommendations
      analysis.recommendations = await this.generateRecommendations(analysis);

      return analysis;
    } catch (error) {
      console.error('Query performance analysis failed:', error);
      return analysis;
    }
  }

  /**
   * Get table statistics
   */
  async getTableStatistics() {
    const tables = [
      'bins', 'users', 'payments', 'search_history', 'monitoring_transactions',
      'monitoring_spans', 'monitoring_metrics', 'rate_limits', 'security_logs'
    ];

    const stats = [];

    for (const table of tables) {
      try {
        // Get row count
        const { count } = await this.env.DB.prepare(`
          SELECT COUNT(*) as count FROM ${table}
        `).first();

        // Get table info (simplified for D1)
        stats.push({
          table,
          rowCount: count,
          status: count > 100000 ? 'large' : count > 10000 ? 'medium' : 'small'
        });
      } catch (error) {
        stats.push({
          table,
          rowCount: 0,
          status: 'error',
          error: error.message
        });
      }
    }

    return stats;
  }

  /**
   * Suggest indexes based on slow queries
   */
  async suggestIndexes(slowQueries) {
    const suggestions = [];
    const commonPatterns = {
      'WHERE user_id =': 'Consider adding index on user_id',
      'WHERE created_at >': 'Consider adding index on created_at',
      'WHERE status =': 'Consider adding index on status',
      'WHERE email =': 'Consider adding index on email',
      'WHERE bin_number =': 'Consider adding index on bin_number',
      'ORDER BY created_at': 'Consider adding index on created_at for sorting',
      'ORDER BY updated_at': 'Consider adding index on updated_at for sorting'
    };

    for (const query of slowQueries) {
      for (const [pattern, suggestion] of Object.entries(commonPatterns)) {
        if (query.query.includes(pattern)) {
          suggestions.push({
            query: query.query,
            suggestion,
            estimatedImprovement: '50-80%',
            priority: query.duration > 5000 ? 'high' : 'medium'
          });
        }
      }
    }

    // Remove duplicates
    return suggestions.filter((item, index, self) => 
      index === self.findIndex(t => t.suggestion === item.suggestion)
    );
  }

  /**
   * Generate performance recommendations
   */
  async generateRecommendations(analysis) {
    const recommendations = [];

    // Large table recommendations
    const largeTables = analysis.tableStats.filter(t => t.status === 'large');
    if (largeTables.length > 0) {
      recommendations.push({
        type: 'performance',
        priority: 'high',
        title: 'Large Table Optimization',
        description: `Tables ${largeTables.map(t => t.table).join(', ')} have grown large. Consider archiving old data.`,
        action: 'Implement data archiving strategy'
      });
    }

    // Slow query recommendations
    if (analysis.slowQueries.length > 10) {
      recommendations.push({
        type: 'performance',
        priority: 'high',
        title: 'Query Optimization Required',
        description: `${analysis.slowQueries.length} slow queries detected. Average response time exceeds 2 seconds.`,
        action: 'Optimize database queries and add missing indexes'
      });
    }

    // Index recommendations
    if (analysis.indexSuggestions.length > 0) {
      recommendations.push({
        type: 'optimization',
        priority: 'medium',
        title: 'Missing Indexes Detected',
        description: `${analysis.indexSuggestions.length} potential index optimizations found.`,
        action: 'Review and implement suggested indexes'
      });
    }

    // General recommendations
    recommendations.push({
      type: 'maintenance',
      priority: 'low',
      title: 'Regular Maintenance',
      description: 'Implement regular database maintenance tasks.',
      action: 'Schedule cleanup jobs for old monitoring data'
    });

    return recommendations;
  }

  /**
   * Optimize database schema
   */
  async optimizeSchema() {
    const optimizations = [];

    try {
      // Add missing indexes
      const indexCommands = [
        // Search history optimizations
        'CREATE INDEX IF NOT EXISTS idx_search_history_user_date ON search_history(user_id, search_date DESC)',
        'CREATE INDEX IF NOT EXISTS idx_search_history_bin_date ON search_history(bin_number, search_date DESC)',
        
        // User optimizations
        'CREATE INDEX IF NOT EXISTS idx_users_created_plan ON users(created_at, plan_type)',
        'CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active)',
        
        // Payment optimizations
        'CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_id, status)',
        'CREATE INDEX IF NOT EXISTS idx_payments_date_amount ON payments(created_at, amount)',
        
        // BIN lookup optimizations
        'CREATE INDEX IF NOT EXISTS idx_bins_range_bank ON bins(bin_start, bin_end, bank)',
        'CREATE INDEX IF NOT EXISTS idx_bins_country_type ON bins(country, type)',
        
        // Monitoring optimizations
        'CREATE INDEX IF NOT EXISTS idx_monitoring_trans_endpoint_time ON monitoring_transactions(name, start_time DESC)',
        'CREATE INDEX IF NOT EXISTS idx_monitoring_spans_trans_type ON monitoring_spans(transaction_id, type)',
      ];

      for (const command of indexCommands) {
        try {
          await this.env.DB.prepare(command).run();
          optimizations.push({
            type: 'index',
            command,
            status: 'success'
          });
        } catch (error) {
          optimizations.push({
            type: 'index',
            command,
            status: 'failed',
            error: error.message
          });
        }
      }

      return optimizations;
    } catch (error) {
      console.error('Schema optimization failed:', error);
      return [];
    }
  }

  /**
   * Clean up old monitoring data
   */
  async cleanupOldData(retentionDays = 30) {
    const cleanup = {
      transactions: 0,
      spans: 0,
      rateLimits: 0,
      securityLogs: 0
    };

    try {
      const cutoffDate = new Date(Date.now() - (retentionDays * 24 * 60 * 60 * 1000)).toISOString();

      // Clean monitoring transactions
      const transactionsResult = await this.env.DB.prepare(`
        DELETE FROM monitoring_transactions 
        WHERE created_at < ?
      `).bind(cutoffDate).run();
      cleanup.transactions = transactionsResult.changes || 0;

      // Clean spans (cascade from transactions)
      const spansResult = await this.env.DB.prepare(`
        DELETE FROM monitoring_spans 
        WHERE created_at < ?
      `).bind(cutoffDate).run();
      cleanup.spans = spansResult.changes || 0;

      // Clean old rate limits (keep last 24 hours)
      const rateLimitCutoff = Date.now() - (24 * 60 * 60 * 1000);
      const rateLimitsResult = await this.env.DB.prepare(`
        DELETE FROM rate_limits 
        WHERE timestamp < ?
      `).bind(rateLimitCutoff).run();
      cleanup.rateLimits = rateLimitsResult.changes || 0;

      // Clean old security logs
      const securityLogsResult = await this.env.DB.prepare(`
        DELETE FROM security_logs 
        WHERE created_at < ? AND resolved = 1
      `).bind(cutoffDate).run();
      cleanup.securityLogs = securityLogsResult.changes || 0;

      return cleanup;
    } catch (error) {
      console.error('Data cleanup failed:', error);
      return cleanup;
    }
  }

  /**
   * Generate database health report
   */
  async generateHealthReport() {
    const report = {
      overall: 'healthy',
      timestamp: new Date().toISOString(),
      metrics: {},
      issues: [],
      recommendations: []
    };

    try {
      // Check database connectivity
      const start = performance.now();
      await this.env.DB.prepare('SELECT 1').first();
      const latency = performance.now() - start;

      report.metrics.connectivity = {
        status: latency < 100 ? 'excellent' : latency < 500 ? 'good' : 'poor',
        latency: Math.round(latency)
      };

      // Check table sizes
      const tableStats = await this.getTableStatistics();
      report.metrics.tables = tableStats;

      // Check for large tables
      const largeTables = tableStats.filter(t => t.rowCount > 100000);
      if (largeTables.length > 0) {
        report.issues.push({
          type: 'performance',
          severity: 'medium',
          message: `Large tables detected: ${largeTables.map(t => t.table).join(', ')}`
        });
      }

      // Check recent error rate
      const recentErrors = await this.env.DB.prepare(`
        SELECT COUNT(*) as error_count
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-1 hour')
        AND success = 0
      `).first();

      const recentTotal = await this.env.DB.prepare(`
        SELECT COUNT(*) as total_count
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-1 hour')
      `).first();

      const errorRate = recentTotal.total_count > 0 ? 
        (recentErrors.error_count / recentTotal.total_count) : 0;

      report.metrics.errorRate = {
        rate: errorRate,
        status: errorRate < 0.01 ? 'excellent' : errorRate < 0.05 ? 'good' : 'poor',
        recentErrors: recentErrors.error_count,
        recentTotal: recentTotal.total_count
      };

      if (errorRate > 0.05) {
        report.issues.push({
          type: 'reliability',
          severity: 'high',
          message: `High error rate detected: ${(errorRate * 100).toFixed(2)}%`
        });
      }

      // Check average response time
      const avgResponseTime = await this.env.DB.prepare(`
        SELECT AVG(duration) as avg_duration
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-1 hour')
      `).first();

      const avgDuration = avgResponseTime.avg_duration || 0;
      report.metrics.responseTime = {
        average: Math.round(avgDuration),
        status: avgDuration < 500 ? 'excellent' : avgDuration < 1000 ? 'good' : 'poor'
      };

      if (avgDuration > 1000) {
        report.issues.push({
          type: 'performance',
          severity: 'medium',
          message: `Slow average response time: ${Math.round(avgDuration)}ms`
        });
      }

      // Set overall status
      const highSeverityIssues = report.issues.filter(i => i.severity === 'high');
      const mediumSeverityIssues = report.issues.filter(i => i.severity === 'medium');

      if (highSeverityIssues.length > 0) {
        report.overall = 'unhealthy';
      } else if (mediumSeverityIssues.length > 2) {
        report.overall = 'degraded';
      }

      // Generate recommendations
      if (report.metrics.responseTime.status === 'poor') {
        report.recommendations.push('Consider optimizing slow queries and adding database indexes');
      }

      if (largeTables.length > 0) {
        report.recommendations.push('Implement data archiving for large tables');
      }

      if (report.metrics.errorRate.rate > 0.01) {
        report.recommendations.push('Investigate and fix sources of database errors');
      }

      return report;
    } catch (error) {
      console.error('Health report generation failed:', error);
      report.overall = 'unknown';
      report.issues.push({
        type: 'system',
        severity: 'high',
        message: `Health check failed: ${error.message}`
      });
      return report;
    }
  }

  /**
   * Get database performance metrics
   */
  async getPerformanceMetrics(hours = 24) {
    try {
      const metrics = await this.env.DB.prepare(`
        SELECT 
          strftime('%Y-%m-%d %H:00:00', created_at) as hour,
          COUNT(*) as request_count,
          AVG(duration) as avg_duration,
          MIN(duration) as min_duration,
          MAX(duration) as max_duration,
          SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count,
          AVG(JSON_EXTRACT(metadata, '$.performance.dbTime')) as avg_db_time
        FROM monitoring_transactions
        WHERE created_at >= datetime('now', '-${hours} hours')
        GROUP BY strftime('%Y-%m-%d %H:00:00', created_at)
        ORDER BY hour DESC
      `).all();

      return metrics.results || [];
    } catch (error) {
      console.error('Performance metrics query failed:', error);
      return [];
    }
  }
}