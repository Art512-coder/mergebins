/**
 * Analytics Engine
 * Comprehensive Business Intelligence system for BIN Search Pro
 */

export class AnalyticsEngine {
  constructor(env, apm) {
    this.env = env;
    this.apm = apm;
  }

  /**
   * Track user session and behavior
   */
  async trackSession(request, user = null) {
    try {
      const sessionId = this.generateSessionId();
      const userAgent = request.headers.get('user-agent') || '';
      const ip = request.headers.get('cf-connecting-ip') || 'unknown';
      const country = request.cf?.country || 'unknown';
      const city = request.cf?.city || 'unknown';
      const referer = request.headers.get('referer') || null;
      
      // Parse user agent for device info
      const deviceInfo = this.parseUserAgent(userAgent);
      
      // Extract UTM parameters
      const url = new URL(request.url);
      const utmParams = this.extractUtmParameters(url);

      const sessionData = {
        session_id: sessionId,
        user_id: user?.id || null,
        ip_address: ip,
        user_agent: userAgent,
        country: country,
        city: city,
        referrer: referer,
        landing_page: url.pathname,
        utm_source: utmParams.source,
        utm_medium: utmParams.medium,
        utm_campaign: utmParams.campaign,
        utm_content: utmParams.content,
        device_type: deviceInfo.device_type,
        browser_name: deviceInfo.browser_name,
        browser_version: deviceInfo.browser_version,
        os_name: deviceInfo.os_name,
        os_version: deviceInfo.os_version,
        is_mobile: deviceInfo.is_mobile ? 1 : 0,
        is_bot: deviceInfo.is_bot ? 1 : 0
      };

      await this.env.DB.prepare(`
        INSERT INTO analytics_sessions (
          session_id, user_id, ip_address, user_agent, country, city, 
          referrer, landing_page, utm_source, utm_medium, utm_campaign, 
          utm_content, device_type, browser_name, browser_version, 
          os_name, os_version, is_mobile, is_bot
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(...Object.values(sessionData)).run();

      return sessionId;
    } catch (error) {
      console.error('Session tracking failed:', error);
      return this.generateSessionId(); // Return fallback session ID
    }
  }

  /**
   * Track page view
   */
  async trackPageView(sessionId, pageUrl, pageTitle = null, timeOnPage = 0) {
    try {
      const url = new URL(pageUrl);
      const pageType = this.categorizePageType(url.pathname);

      await this.env.DB.prepare(`
        INSERT INTO analytics_page_views (
          session_id, page_url, page_title, page_type, time_on_page
        ) VALUES (?, ?, ?, ?, ?)
      `).bind(sessionId, pageUrl, pageTitle, pageType, timeOnPage).run();

      // Update session page views count
      await this.env.DB.prepare(`
        UPDATE analytics_sessions 
        SET page_views = page_views + 1, updated_at = datetime('now')
        WHERE session_id = ?
      `).bind(sessionId).run();

    } catch (error) {
      console.error('Page view tracking failed:', error);
    }
  }

  /**
   * Track user event
   */
  async trackEvent(sessionId, eventType, eventAction, options = {}) {
    try {
      const eventData = {
        session_id: sessionId,
        user_id: options.userId || null,
        event_type: eventType,
        event_category: options.category || 'engagement',
        event_action: eventAction,
        event_label: options.label || null,
        event_value: options.value || null,
        page_url: options.pageUrl || '',
        bin_number: options.binNumber || null,
        search_query: options.searchQuery || null,
        result_count: options.resultCount || null,
        error_message: options.errorMessage || null,
        conversion_funnel_step: options.funnelStep || null,
        ab_test_variant: options.abVariant || null,
        custom_properties: options.customProperties ? JSON.stringify(options.customProperties) : null
      };

      await this.env.DB.prepare(`
        INSERT INTO analytics_events (
          session_id, user_id, event_type, event_category, event_action,
          event_label, event_value, page_url, bin_number, search_query,
          result_count, error_message, conversion_funnel_step, ab_test_variant,
          custom_properties
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(...Object.values(eventData)).run();

      // Update session events count
      await this.env.DB.prepare(`
        UPDATE analytics_sessions 
        SET events_count = events_count + 1, updated_at = datetime('now')
        WHERE session_id = ?
      `).bind(sessionId).run();

      // Update real-time metrics
      await this.updateRealtimeMetric(`events.${eventType}`, 1, 'counter');

    } catch (error) {
      console.error('Event tracking failed:', error);
    }
  }

  /**
   * Track conversion event
   */
  async trackConversion(sessionId, conversionType, value = 0, properties = {}) {
    try {
      // Track as regular event
      await this.trackEvent(sessionId, 'conversion', conversionType, {
        category: 'conversion',
        value: value,
        customProperties: properties
      });

      // Update session conversion count
      await this.env.DB.prepare(`
        UPDATE analytics_sessions 
        SET conversion_events = conversion_events + 1,
            revenue_generated = revenue_generated + ?
        WHERE session_id = ?
      `).bind(value, sessionId).run();

      // Update daily business metrics
      await this.updateBusinessMetrics('conversions', 1);
      if (value > 0) {
        await this.updateBusinessMetrics('revenue', value);
      }

    } catch (error) {
      console.error('Conversion tracking failed:', error);
    }
  }

  /**
   * Track revenue transaction
   */
  async trackRevenue(transactionId, sessionId, userId, amount, currency, details = {}) {
    try {
      const amountUsd = await this.convertToUSD(amount, currency);
      const fees = details.fees || 0;
      const netAmount = amountUsd - fees;

      await this.env.DB.prepare(`
        INSERT INTO analytics_revenue (
          transaction_id, session_id, user_id, payment_method, currency,
          amount, amount_usd, transaction_type, product_type, subscription_period,
          discount_code, discount_amount, fees, net_amount, mrr_contribution
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        transactionId,
        sessionId,
        userId,
        details.paymentMethod || 'unknown',
        currency,
        amount,
        amountUsd,
        details.transactionType || 'one_time',
        details.productType || 'premium',
        details.subscriptionPeriod || null,
        details.discountCode || null,
        details.discountAmount || 0,
        fees,
        netAmount,
        this.calculateMRRContribution(details.transactionType, details.subscriptionPeriod, netAmount)
      ).run();

      // Update business metrics
      await this.updateBusinessMetrics('total_revenue', amountUsd);
      if (details.transactionType === 'subscription') {
        await this.updateBusinessMetrics('subscription_revenue', amountUsd);
      }

    } catch (error) {
      console.error('Revenue tracking failed:', error);
    }
  }

  /**
   * Update business metrics (aggregated daily metrics)
   */
  async updateBusinessMetrics(metricName, increment = 1) {
    try {
      const today = new Date().toISOString().split('T')[0];
      const column = this.getMetricColumn(metricName);
      
      if (!column) return;

      await this.env.DB.prepare(`
        INSERT OR REPLACE INTO analytics_business_metrics (
          metric_date, ${column}
        ) VALUES (
          ?, 
          COALESCE((SELECT ${column} FROM analytics_business_metrics WHERE metric_date = ?), 0) + ?
        )
      `).bind(today, today, increment).run();

    } catch (error) {
      console.error('Business metrics update failed:', error);
    }
  }

  /**
   * Update real-time metrics
   */
  async updateRealtimeMetric(metricName, value, type = 'counter', tags = {}) {
    try {
      await this.env.DB.prepare(`
        INSERT INTO analytics_realtime (
          metric_name, metric_value, metric_type, tags, timestamp
        ) VALUES (?, ?, ?, ?, ?)
      `).bind(
        metricName,
        value,
        type,
        JSON.stringify(tags),
        Date.now()
      ).run();

      // Clean up old real-time data (keep last 24 hours)
      const cutoff = Date.now() - (24 * 60 * 60 * 1000);
      await this.env.DB.prepare(`
        DELETE FROM analytics_realtime WHERE timestamp < ?
      `).bind(cutoff).run();

    } catch (error) {
      console.error('Real-time metrics update failed:', error);
    }
  }

  /**
   * Generate analytics dashboard data
   */
  async getDashboardData(timeframe = '7d') {
    try {
      const endDate = new Date();
      const startDate = new Date();
      
      // Calculate date range
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

      const dashboardData = {
        timeframe,
        overview: await this.getOverviewMetrics(startDate, endDate),
        users: await this.getUserMetrics(startDate, endDate),
        engagement: await this.getEngagementMetrics(startDate, endDate),
        conversion: await this.getConversionMetrics(startDate, endDate),
        revenue: await this.getRevenueMetrics(startDate, endDate),
        geography: await this.getGeographyMetrics(startDate, endDate),
        technology: await this.getTechnologyMetrics(startDate, endDate),
        realtime: await this.getRealtimeMetrics(),
        trends: await this.getTrendData(startDate, endDate)
      };

      return dashboardData;

    } catch (error) {
      console.error('Dashboard data generation failed:', error);
      return null;
    }
  }

  /**
   * Get overview metrics
   */
  async getOverviewMetrics(startDate, endDate) {
    const start = startDate.toISOString().split('T')[0];
    const end = endDate.toISOString().split('T')[0];

    const metrics = await this.env.DB.prepare(`
      SELECT 
        SUM(total_sessions) as total_sessions,
        SUM(daily_active_users) as total_users,
        SUM(new_users) as new_users,
        SUM(bin_lookups) as bin_lookups,
        SUM(card_generations) as card_generations,
        SUM(signups) as signups,
        SUM(total_revenue) as total_revenue,
        AVG(bounce_rate) as avg_bounce_rate,
        AVG(avg_session_duration) as avg_session_duration
      FROM analytics_business_metrics
      WHERE metric_date BETWEEN ? AND ?
    `).bind(start, end).first();

    return {
      sessions: metrics.total_sessions || 0,
      users: metrics.total_users || 0,
      new_users: metrics.new_users || 0,
      bin_lookups: metrics.bin_lookups || 0,
      card_generations: metrics.card_generations || 0,
      signups: metrics.signups || 0,
      revenue: metrics.total_revenue || 0,
      bounce_rate: metrics.avg_bounce_rate || 0,
      avg_session_duration: metrics.avg_session_duration || 0
    };
  }

  /**
   * Get real-time metrics
   */
  async getRealtimeMetrics() {
    const last5Minutes = Date.now() - (5 * 60 * 1000);
    
    const realtimeData = await this.env.DB.prepare(`
      SELECT 
        metric_name,
        SUM(metric_value) as total_value,
        COUNT(*) as count
      FROM analytics_realtime
      WHERE timestamp >= ?
      GROUP BY metric_name
      ORDER BY total_value DESC
    `).bind(last5Minutes).all();

    // Get current active users (last 5 minutes)
    const activeUsers = await this.env.DB.prepare(`
      SELECT COUNT(DISTINCT session_id) as active_users
      FROM analytics_events
      WHERE created_at >= datetime('now', '-5 minutes')
    `).first();

    return {
      active_users: activeUsers.active_users || 0,
      metrics: realtimeData.results || []
    };
  }

  /**
   * Helper functions
   */
  
  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  parseUserAgent(userAgent) {
    // Simplified user agent parsing
    const isMobile = /Mobile|Android|iPhone|iPad/i.test(userAgent);
    const isBot = /bot|crawler|spider|scraper/i.test(userAgent);
    
    let browser_name = 'Unknown';
    let os_name = 'Unknown';
    
    if (userAgent.includes('Chrome')) browser_name = 'Chrome';
    else if (userAgent.includes('Firefox')) browser_name = 'Firefox';
    else if (userAgent.includes('Safari')) browser_name = 'Safari';
    else if (userAgent.includes('Edge')) browser_name = 'Edge';
    
    if (userAgent.includes('Windows')) os_name = 'Windows';
    else if (userAgent.includes('Mac')) os_name = 'macOS';
    else if (userAgent.includes('Linux')) os_name = 'Linux';
    else if (userAgent.includes('Android')) os_name = 'Android';
    else if (userAgent.includes('iOS')) os_name = 'iOS';

    return {
      device_type: isMobile ? 'mobile' : 'desktop',
      browser_name,
      browser_version: null,
      os_name,
      os_version: null,
      is_mobile: isMobile,
      is_bot: isBot
    };
  }

  extractUtmParameters(url) {
    const searchParams = url.searchParams;
    return {
      source: searchParams.get('utm_source'),
      medium: searchParams.get('utm_medium'),
      campaign: searchParams.get('utm_campaign'),
      content: searchParams.get('utm_content')
    };
  }

  categorizePageType(pathname) {
    if (pathname === '/') return 'home';
    if (pathname.startsWith('/bin/')) return 'bin_lookup';
    if (pathname.includes('search')) return 'search';
    if (pathname.includes('pricing')) return 'pricing';
    if (pathname.includes('auth')) return 'authentication';
    if (pathname.includes('dashboard')) return 'dashboard';
    return 'other';
  }

  getMetricColumn(metricName) {
    const mapping = {
      'users': 'daily_active_users',
      'sessions': 'total_sessions',
      'conversions': 'successful_payments',
      'revenue': 'total_revenue',
      'bin_lookups': 'bin_lookups',
      'card_generations': 'card_generations',
      'signups': 'signups',
      'total_revenue': 'total_revenue',
      'subscription_revenue': 'subscription_revenue'
    };
    
    return mapping[metricName] || null;
  }

  async convertToUSD(amount, currency) {
    // Simplified currency conversion - in production use real exchange rates
    const rates = {
      'USD': 1,
      'BTC': 45000,
      'ETH': 3000,
      'LTC': 150,
      'USDT': 1,
      'USDC': 1
    };
    
    return amount * (rates[currency] || 1);
  }

  calculateMRRContribution(transactionType, period, amount) {
    if (transactionType !== 'subscription') return 0;
    
    switch (period) {
      case 'monthly': return amount;
      case 'yearly': return amount / 12;
      case 'lifetime': return 0; // One-time payment
      default: return 0;
    }
  }
}