/**
 * Business Intelligence API
 * REST endpoints for analytics and business metrics
 */

export class BusinessIntelligenceAPI {
  constructor(env, analytics, security) {
    this.env = env;
    this.analytics = analytics;
    this.security = security;
  }

  /**
   * Handle analytics API requests
   */
  async handleRequest(request, pathname) {
    const url = new URL(request.url);
    
    // Authentication check for analytics endpoints
    const authResult = await this.authenticateRequest(request);
    if (!authResult.success) {
      return new Response(JSON.stringify({
        error: 'Authentication required',
        message: authResult.message
      }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    try {
      // Route to appropriate handler
      if (pathname === '/api/analytics/dashboard') {
        return await this.getDashboard(request);
      } else if (pathname === '/api/analytics/overview') {
        return await this.getOverview(request);
      } else if (pathname === '/api/analytics/users') {
        return await this.getUserAnalytics(request);
      } else if (pathname === '/api/analytics/events') {
        return await this.getEventAnalytics(request);
      } else if (pathname === '/api/analytics/revenue') {
        return await this.getRevenueAnalytics(request);
      } else if (pathname === '/api/analytics/geography') {
        return await this.getGeographyAnalytics(request);
      } else if (pathname === '/api/analytics/technology') {
        return await this.getTechnologyAnalytics(request);
      } else if (pathname === '/api/analytics/realtime') {
        return await this.getRealtimeAnalytics(request);
      } else if (pathname === '/api/analytics/funnels') {
        return await this.getFunnelAnalytics(request);
      } else if (pathname === '/api/analytics/cohorts') {
        return await this.getCohortAnalytics(request);
      } else if (pathname === '/api/analytics/export') {
        return await this.exportData(request);
      } else if (pathname === '/api/analytics/track' && request.method === 'POST') {
        return await this.trackEvent(request);
      } else {
        return new Response(JSON.stringify({
          error: 'Endpoint not found',
          available_endpoints: [
            '/api/analytics/dashboard',
            '/api/analytics/overview',
            '/api/analytics/users',
            '/api/analytics/events',
            '/api/analytics/revenue',
            '/api/analytics/geography',
            '/api/analytics/technology',
            '/api/analytics/realtime',
            '/api/analytics/funnels',
            '/api/analytics/cohorts',
            '/api/analytics/export',
            '/api/analytics/track'
          ]
        }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    } catch (error) {
      console.error('Analytics API error:', error);
      return new Response(JSON.stringify({
        error: 'Internal server error',
        message: error.message
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  /**
   * Get comprehensive dashboard data
   */
  async getDashboard(request) {
    const url = new URL(request.url);
    const timeframe = url.searchParams.get('timeframe') || '7d';
    
    const dashboardData = await this.analytics.getDashboardData(timeframe);
    
    return new Response(JSON.stringify({
      success: true,
      data: dashboardData,
      generated_at: new Date().toISOString()
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Get overview metrics
   */
  async getOverview(request) {
    const url = new URL(request.url);
    const timeframe = url.searchParams.get('timeframe') || '7d';
    const compare = url.searchParams.get('compare') === 'true';
    
    const endDate = new Date();
    const startDate = this.calculateStartDate(endDate, timeframe);
    
    const currentMetrics = await this.analytics.getOverviewMetrics(startDate, endDate);
    
    let comparison = null;
    if (compare) {
      const compareEndDate = new Date(startDate);
      const compareStartDate = this.calculateStartDate(compareEndDate, timeframe);
      comparison = await this.analytics.getOverviewMetrics(compareStartDate, compareEndDate);
    }

    return new Response(JSON.stringify({
      success: true,
      data: {
        current: currentMetrics,
        comparison: comparison,
        timeframe: timeframe
      }
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Get user analytics
   */
  async getUserAnalytics(request) {
    const url = new URL(request.url);
    const timeframe = url.searchParams.get('timeframe') || '7d';
    const groupBy = url.searchParams.get('group_by') || 'day';
    
    const { startDate, endDate } = this.getDateRange(timeframe);
    
    let dateFormat;
    switch (groupBy) {
      case 'hour':
        dateFormat = "strftime('%Y-%m-%d %H:00:00', created_at)";
        break;
      case 'day':
        dateFormat = "date(created_at)";
        break;
      case 'week':
        dateFormat = "strftime('%Y-W%W', created_at)";
        break;
      case 'month':
        dateFormat = "strftime('%Y-%m', created_at)";
        break;
      default:
        dateFormat = "date(created_at)";
    }

    const userMetrics = await this.env.DB.prepare(`
      SELECT 
        ${dateFormat} as date,
        COUNT(DISTINCT session_id) as sessions,
        COUNT(DISTINCT CASE WHEN user_id IS NOT NULL THEN session_id END) as authenticated_sessions,
        COUNT(DISTINCT CASE WHEN user_id IS NULL THEN session_id END) as anonymous_sessions,
        AVG(session_duration) as avg_duration,
        AVG(page_views) as avg_page_views,
        COUNT(DISTINCT country) as countries,
        SUM(CASE WHEN page_views = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as bounce_rate
      FROM analytics_sessions
      WHERE created_at BETWEEN ? AND ?
      GROUP BY ${dateFormat}
      ORDER BY date DESC
    `).bind(startDate.toISOString(), endDate.toISOString()).all();

    // Get top countries and devices
    const topCountries = await this.env.DB.prepare(`
      SELECT country, COUNT(*) as sessions
      FROM analytics_sessions
      WHERE created_at BETWEEN ? AND ?
      GROUP BY country
      ORDER BY sessions DESC
      LIMIT 10
    `).bind(startDate.toISOString(), endDate.toISOString()).all();

    const deviceBreakdown = await this.env.DB.prepare(`
      SELECT device_type, COUNT(*) as sessions
      FROM analytics_sessions
      WHERE created_at BETWEEN ? AND ?
      GROUP BY device_type
      ORDER BY sessions DESC
    `).bind(startDate.toISOString(), endDate.toISOString()).all();

    return new Response(JSON.stringify({
      success: true,
      data: {
        metrics: userMetrics.results || [],
        top_countries: topCountries.results || [],
        device_breakdown: deviceBreakdown.results || [],
        timeframe: timeframe,
        group_by: groupBy
      }
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Get event analytics
   */
  async getEventAnalytics(request) {
    const url = new URL(request.url);
    const timeframe = url.searchParams.get('timeframe') || '7d';
    const eventType = url.searchParams.get('event_type');
    const groupBy = url.searchParams.get('group_by') || 'day';
    
    const { startDate, endDate } = this.getDateRange(timeframe);
    
    let whereClause = 'WHERE created_at BETWEEN ? AND ?';
    let params = [startDate.toISOString(), endDate.toISOString()];
    
    if (eventType) {
      whereClause += ' AND event_type = ?';
      params.push(eventType);
    }

    const dateFormat = this.getDateFormat(groupBy);

    // Event counts over time
    const eventTrends = await this.env.DB.prepare(`
      SELECT 
        ${dateFormat} as date,
        event_type,
        COUNT(*) as event_count,
        COUNT(DISTINCT session_id) as unique_sessions,
        AVG(CASE WHEN event_value IS NOT NULL THEN event_value END) as avg_value
      FROM analytics_events
      ${whereClause}
      GROUP BY ${dateFormat}, event_type
      ORDER BY date DESC, event_count DESC
    `).bind(...params).all();

    // Top events
    const topEvents = await this.env.DB.prepare(`
      SELECT 
        event_type,
        event_action,
        COUNT(*) as event_count,
        COUNT(DISTINCT session_id) as unique_sessions,
        SUM(CASE WHEN event_value IS NOT NULL THEN event_value ELSE 0 END) as total_value
      FROM analytics_events
      ${whereClause}
      GROUP BY event_type, event_action
      ORDER BY event_count DESC
      LIMIT 20
    `).bind(...params).all();

    return new Response(JSON.stringify({
      success: true,
      data: {
        trends: eventTrends.results || [],
        top_events: topEvents.results || [],
        timeframe: timeframe,
        event_type: eventType || 'all',
        group_by: groupBy
      }
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Get revenue analytics
   */
  async getRevenueAnalytics(request) {
    const url = new URL(request.url);
    const timeframe = url.searchParams.get('timeframe') || '30d';
    const currency = url.searchParams.get('currency') || 'USD';
    
    const { startDate, endDate } = this.getDateRange(timeframe);

    // Revenue over time
    const revenueMetrics = await this.env.DB.prepare(`
      SELECT 
        date(created_at) as date,
        COUNT(*) as transactions,
        SUM(amount_usd) as total_revenue,
        AVG(amount_usd) as avg_transaction_value,
        SUM(CASE WHEN transaction_type = 'subscription' THEN amount_usd ELSE 0 END) as subscription_revenue,
        SUM(CASE WHEN transaction_type = 'one_time' THEN amount_usd ELSE 0 END) as one_time_revenue,
        COUNT(DISTINCT user_id) as paying_users
      FROM analytics_revenue
      WHERE created_at BETWEEN ? AND ?
      GROUP BY date(created_at)
      ORDER BY date DESC
    `).bind(startDate.toISOString(), endDate.toISOString()).all();

    // Revenue by product
    const productRevenue = await this.env.DB.prepare(`
      SELECT 
        product_type,
        COUNT(*) as transactions,
        SUM(amount_usd) as revenue,
        AVG(amount_usd) as avg_value
      FROM analytics_revenue
      WHERE created_at BETWEEN ? AND ?
      GROUP BY product_type
      ORDER BY revenue DESC
    `).bind(startDate.toISOString(), endDate.toISOString()).all();

    // MRR calculation
    const mrr = await this.env.DB.prepare(`
      SELECT SUM(mrr_contribution) as monthly_recurring_revenue
      FROM analytics_revenue
      WHERE created_at BETWEEN ? AND ?
    `).bind(startDate.toISOString(), endDate.toISOString()).first();

    return new Response(JSON.stringify({
      success: true,
      data: {
        revenue_metrics: revenueMetrics.results || [],
        product_breakdown: productRevenue.results || [],
        mrr: mrr.monthly_recurring_revenue || 0,
        currency: currency,
        timeframe: timeframe
      }
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Get real-time analytics
   */
  async getRealtimeAnalytics(request) {
    const realtimeData = await this.analytics.getRealtimeMetrics();
    
    // Get current sessions (last 30 minutes)
    const currentSessions = await this.env.DB.prepare(`
      SELECT 
        COUNT(DISTINCT session_id) as active_sessions,
        COUNT(DISTINCT country) as active_countries,
        COUNT(*) as active_events
      FROM analytics_events
      WHERE created_at >= datetime('now', '-30 minutes')
    `).first();

    // Get top pages being viewed now
    const topPages = await this.env.DB.prepare(`
      SELECT 
        page_url,
        COUNT(*) as views
      FROM analytics_page_views
      WHERE created_at >= datetime('now', '-5 minutes')
      GROUP BY page_url
      ORDER BY views DESC
      LIMIT 10
    `).all();

    return new Response(JSON.stringify({
      success: true,
      data: {
        active_users: realtimeData.active_users,
        active_sessions: currentSessions.active_sessions || 0,
        active_countries: currentSessions.active_countries || 0,
        recent_events: currentSessions.active_events || 0,
        top_pages: topPages.results || [],
        metrics: realtimeData.metrics,
        timestamp: new Date().toISOString()
      }
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  /**
   * Track custom event (public endpoint)
   */
  async trackEvent(request) {
    try {
      const body = await request.json();
      const { session_id, event_type, event_action, ...options } = body;
      
      if (!session_id || !event_type || !event_action) {
        return new Response(JSON.stringify({
          error: 'Missing required fields',
          required: ['session_id', 'event_type', 'event_action']
        }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      await this.analytics.trackEvent(session_id, event_type, event_action, options);

      return new Response(JSON.stringify({
        success: true,
        message: 'Event tracked successfully'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: 'Failed to track event',
        message: error.message
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  /**
   * Export analytics data
   */
  async exportData(request) {
    const url = new URL(request.url);
    const format = url.searchParams.get('format') || 'json';
    const type = url.searchParams.get('type') || 'overview';
    const timeframe = url.searchParams.get('timeframe') || '30d';
    
    const { startDate, endDate } = this.getDateRange(timeframe);
    
    let data;
    let filename;
    
    switch (type) {
      case 'sessions':
        data = await this.exportSessions(startDate, endDate);
        filename = `sessions_export_${timeframe}.${format}`;
        break;
      case 'events':
        data = await this.exportEvents(startDate, endDate);
        filename = `events_export_${timeframe}.${format}`;
        break;
      case 'revenue':
        data = await this.exportRevenue(startDate, endDate);
        filename = `revenue_export_${timeframe}.${format}`;
        break;
      default:
        data = await this.analytics.getOverviewMetrics(startDate, endDate);
        filename = `overview_export_${timeframe}.${format}`;
    }

    const responseData = {
      export_type: type,
      timeframe: timeframe,
      generated_at: new Date().toISOString(),
      data: data
    };

    if (format === 'csv') {
      const csv = this.convertToCSV(data);
      return new Response(csv, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="${filename}"`
        }
      });
    } else {
      return new Response(JSON.stringify(responseData, null, 2), {
        headers: {
          'Content-Type': 'application/json',
          'Content-Disposition': `attachment; filename="${filename}"`
        }
      });
    }
  }

  /**
   * Helper methods
   */
  
  async authenticateRequest(request) {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return { success: false, message: 'Missing or invalid authorization header' };
    }

    // In production, validate JWT token or API key here
    // For now, accept any Bearer token for analytics access
    return { success: true };
  }

  getDateRange(timeframe) {
    const endDate = new Date();
    const startDate = new Date();
    
    switch (timeframe) {
      case '1h':
        startDate.setHours(startDate.getHours() - 1);
        break;
      case '24h':
        startDate.setDate(startDate.getDate() - 1);
        break;
      case '7d':
        startDate.setDate(startDate.getDate() - 7);
        break;
      case '30d':
        startDate.setDate(startDate.getDate() - 30);
        break;
      case '90d':
        startDate.setDate(startDate.getDate() - 90);
        break;
      default:
        startDate.setDate(startDate.getDate() - 7);
    }
    
    return { startDate, endDate };
  }

  calculateStartDate(endDate, timeframe) {
    const startDate = new Date(endDate);
    
    switch (timeframe) {
      case '24h':
        startDate.setDate(startDate.getDate() - 1);
        break;
      case '7d':
        startDate.setDate(startDate.getDate() - 7);
        break;
      case '30d':
        startDate.setDate(startDate.getDate() - 30);
        break;
      case '90d':
        startDate.setDate(startDate.getDate() - 90);
        break;
      default:
        startDate.setDate(startDate.getDate() - 7);
    }
    
    return startDate;
  }

  getDateFormat(groupBy) {
    switch (groupBy) {
      case 'hour':
        return "strftime('%Y-%m-%d %H:00:00', created_at)";
      case 'day':
        return "date(created_at)";
      case 'week':
        return "strftime('%Y-W%W', created_at)";
      case 'month':
        return "strftime('%Y-%m', created_at)";
      default:
        return "date(created_at)";
    }
  }

  convertToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) {
      return 'No data available';
    }
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        return typeof value === 'string' ? `"${value}"` : value;
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  }
}