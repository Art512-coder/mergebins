"""
Cloudflare D1 Database Service for BIN Lookup
Provides high-performance BIN lookup using Cloudflare D1 global database
"""

import httpx
import os
import json
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
import asyncio
from datetime import datetime

class CloudflareD1Service:
    """Service for interacting with Cloudflare D1 database"""
    
    def __init__(self):
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.database_id = os.getenv("CLOUDFLARE_D1_DATABASE_ID", "e8e3af39-17e0-4c36-bebe-efe510a973af")
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        
        if not self.account_id or not self.api_token:
            print("⚠️ Warning: Cloudflare D1 credentials not configured. Using fallback SQLite.")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database/{self.database_id}"
            
    async def _execute_query(self, sql: str) -> Optional[Dict]:
        """Execute SQL query against D1 database"""
        if not self.enabled:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"sql": sql}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/query",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('result', [{}])[0] if result.get('result') else None
                else:
                    print(f"D1 query failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"D1 connection error: {e}")
            return None
    
    async def lookup_bin(self, bin_number: str) -> Optional[Dict[str, Any]]:
        """
        Lookup BIN information from D1 database
        
        Args:
            bin_number: BIN number to lookup (6-8 digits)
            
        Returns:
            Dict with BIN information or None if not found
        """
        if not self.enabled:
            return None
            
        # Clean input
        bin_clean = ''.join(filter(str.isdigit, bin_number))[:8]
        if len(bin_clean) < 4:
            return None
        
        # Try exact match first (6-digit BIN)
        bin_prefix = bin_clean[:6]
        sql = f"SELECT * FROM bins WHERE bin = '{bin_prefix}' LIMIT 1;"
        
        result = await self._execute_query(sql)
        if result and result.get('results'):
            return self._format_bin_result(result['results'][0])
        
        # Fallback to 4-digit prefix match
        if len(bin_clean) >= 4:
            bin_4digit = bin_clean[:4]
            sql = f"SELECT * FROM bins WHERE bin LIKE '{bin_4digit}%' ORDER BY bin LIMIT 1;"
            
            result = await self._execute_query(sql)
            if result and result.get('results'):
                return self._format_bin_result(result['results'][0])
        
        return None
    
    async def search_bins(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search BINs by various criteria
        
        Args:
            query: Search query (can be BIN, brand, issuer, country)
            limit: Maximum number of results
            
        Returns:
            List of matching BIN records
        """
        if not self.enabled:
            return []
            
        query_clean = query.strip().upper()
        
        # Build search SQL
        sql = f"""
        SELECT * FROM bins 
        WHERE bin LIKE '%{query_clean}%' 
           OR UPPER(brand) LIKE '%{query_clean}%'
           OR UPPER(issuer) LIKE '%{query_clean}%'
           OR UPPER(country) LIKE '%{query_clean}%'
           OR UPPER(type) LIKE '%{query_clean}%'
        ORDER BY bin 
        LIMIT {min(limit, 50)};
        """
        
        result = await self._execute_query(sql)
        if result and result.get('results'):
            return [self._format_bin_result(row) for row in result['results']]
        
        return []
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.enabled:
            return {"error": "D1 not enabled"}
            
        stats_sql = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT brand) as unique_brands,
            COUNT(DISTINCT country) as unique_countries,
            COUNT(DISTINCT issuer) as unique_issuers,
            COUNT(DISTINCT type) as card_types
        FROM bins;
        """
        
        result = await self._execute_query(stats_sql)
        if result and result.get('results'):
            return result['results'][0]
        
        return {"error": "Failed to get stats"}
    
    async def get_popular_brands(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular card brands"""
        if not self.enabled:
            return []
            
        sql = f"""
        SELECT brand, COUNT(*) as count
        FROM bins 
        WHERE brand IS NOT NULL AND brand != ''
        GROUP BY brand 
        ORDER BY count DESC 
        LIMIT {limit};
        """
        
        result = await self._execute_query(sql)
        if result and result.get('results'):
            return result['results']
        
        return []
    
    def _format_bin_result(self, row: Dict) -> Dict[str, Any]:
        """Format database row to standard BIN result format"""
        return {
            "bin": row.get("bin", ""),
            "brand": row.get("brand", "Unknown").title() if row.get("brand") else "Unknown",
            "type": row.get("type", "Unknown").title() if row.get("type") else "Unknown",
            "category": row.get("category", "Standard").title() if row.get("category") else "Standard",
            "issuer": row.get("issuer", "Unknown").title() if row.get("issuer") else "Unknown",
            "country": row.get("country", "Unknown").title() if row.get("country") else "Unknown",
            "country_name": row.get("country", "Unknown").title() if row.get("country") else "Unknown",
            "bank_phone": row.get("bank_phone", "") or "",
            "bank_url": row.get("bank_url", "") or "",
            "source": "cloudflare_d1",
            "updated_at": datetime.utcnow().isoformat()
        }

# Global instance
d1_service = CloudflareD1Service()

async def get_bin_from_d1(bin_number: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get BIN from D1
    Falls back gracefully if D1 is not available
    """
    try:
        return await d1_service.lookup_bin(bin_number)
    except Exception as e:
        print(f"D1 lookup failed: {e}")
        return None
