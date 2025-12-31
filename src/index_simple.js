export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': env.ENVIRONMENT === 'production' 
        ? 'https://dd0e40f5.cryptobinchecker-cc.pages.dev'
        : '*',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    };
    
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }
    
    // BIN lookup endpoint
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
    
    // Stats endpoint
    if (url.pathname === '/api/v1/bins/stats') {
      try {
        const totalStmt = env.DB.prepare('SELECT COUNT(*) as total FROM bins');
        const totalResult = await totalStmt.first();
        
        return new Response(JSON.stringify({
          total_bins: totalResult.total,
          database: 'Cloudflare D1'
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
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

    // Health endpoint
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'healthy',
        version: env.VERSION || '2.0',
        environment: env.ENVIRONMENT || 'production',
        database: 'connected'
      }), {
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders 
        }
      });
    }

    // Search endpoint
    if (url.pathname === '/api/v1/bins/search' && request.method === 'POST') {
      try {
        const body = await request.json();
        let query = 'SELECT * FROM bins WHERE 1=1';
        const params = [];
        
        if (body.brand) {
          query += ' AND brand = ?';
          params.push(body.brand.toUpperCase());
        }
        if (body.country) {
          query += ' AND country LIKE ?';
          params.push(`%${body.country}%`);
        }
        if (body.issuer) {
          query += ' AND issuer LIKE ?';
          params.push(`%${body.issuer}%`);
        }
        if (body.type) {
          query += ' AND type = ?';
          params.push(body.type.toUpperCase());
        }
        
        query += ' LIMIT 50';
        
        const stmt = env.DB.prepare(query);
        const results = await stmt.bind(...params).all();
        
        return new Response(JSON.stringify({
          results: results.results || [],
          count: results.results?.length || 0
        }), {
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          detail: 'Search error'
        }), {
          status: 500,
          headers: { 
            'Content-Type': 'application/json',
            ...corsHeaders 
          }
        });
      }
    }
    
    return new Response('Not found', { status: 404 });
  }
};