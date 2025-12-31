# Cloudflare D1 Migration Plan

## Database Schema Design

```sql
-- Create optimized BIN table for D1
CREATE TABLE bins (
    bin TEXT PRIMARY KEY,
    brand TEXT,
    type TEXT,
    category TEXT,
    issuer TEXT,
    country TEXT,
    bank_phone TEXT,
    bank_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fast lookups
CREATE INDEX idx_bin_prefix ON bins(substr(bin, 1, 6));
CREATE INDEX idx_brand ON bins(brand);
CREATE INDEX idx_country ON bins(country);
CREATE INDEX idx_issuer ON bins(issuer);
```

## Migration Steps

### 1. Create D1 Database
```bash
# Install Wrangler CLI
npm install -g wrangler

# Create D1 database
wrangler d1 create bin-search-db

# Get database ID from output and add to wrangler.toml
```

### 2. Upload Data Script
```python
# scripts/upload_to_d1.py
import csv
import requests
import json
import os
from typing import List, Dict

def batch_insert_bins(csv_file_path: str, batch_size: int = 1000):
    """Upload BIN data to D1 in batches"""
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        batch = []
        
        for row in reader:
            # Clean and format data
            bin_data = {
                'bin': row['bin'].strip(),
                'brand': row['brand'].strip() or None,
                'type': row['type'].strip() or None, 
                'category': row['category'].strip() or None,
                'issuer': row['issuer'].strip() or None,
                'country': row['country'].strip() or None,
                'bank_phone': row['bank_phone'].strip() or None,
                'bank_url': row['bank_url'].strip() or None
            }
            batch.append(bin_data)
            
            if len(batch) >= batch_size:
                upload_batch(batch)
                batch = []
        
        # Upload remaining records
        if batch:
            upload_batch(batch)

def upload_batch(batch: List[Dict]):
    """Upload a batch of BIN records to D1"""
    sql_values = []
    for record in batch:
        values = ', '.join([f"'{v}'" if v else 'NULL' for v in record.values()])
        sql_values.append(f"({values})")
    
    query = f"""
    INSERT OR REPLACE INTO bins 
    (bin, brand, type, category, issuer, country, bank_phone, bank_url)
    VALUES {', '.join(sql_values)};
    """
    
    # Execute via Wrangler D1 API or direct HTTP API
    print(f"Uploading batch of {len(batch)} records...")
    # Implementation depends on chosen upload method
```

### 3. Backend API Updates
```python
# app/services/d1_bin_service.py
import httpx
import os
from typing import Optional, Dict, Any

class D1BinService:
    def __init__(self):
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.database_id = os.getenv("D1_DATABASE_ID") 
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database/{self.database_id}"
    
    async def lookup_bin(self, bin_number: str) -> Optional[Dict[str, Any]]:
        """Lookup BIN using D1 SQL query"""
        
        # Try exact match first
        query = f"SELECT * FROM bins WHERE bin = '{bin_number[:6]}' LIMIT 1"
        result = await self._execute_query(query)
        
        if result and result.get('results'):
            return result['results'][0]
        
        # Fallback to prefix match for partial BINs
        if len(bin_number) >= 4:
            query = f"SELECT * FROM bins WHERE bin LIKE '{bin_number[:4]}%' LIMIT 1"
            result = await self._execute_query(query)
            if result and result.get('results'):
                return result['results'][0]
        
        return None
    
    async def search_bins(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search BINs by various criteria"""
        
        sql = f"""
        SELECT * FROM bins 
        WHERE bin LIKE '%{query}%' 
           OR brand LIKE '%{query.upper()}%'
           OR issuer LIKE '%{query.upper()}%'
           OR country LIKE '%{query.upper()}%'
        LIMIT {limit}
        """
        
        result = await self._execute_query(sql)
        return result.get('results', []) if result else []
    
    async def _execute_query(self, query: str) -> Optional[Dict]:
        """Execute SQL query against D1"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"sql": query}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/query",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json().get('result', [{}])[0]
            else:
                print(f"D1 query failed: {response.text}")
                return None
```

## Performance Comparison

| Feature | Current SQLite | D1 Database | KV Store |
|---------|---------------|-------------|----------|
| Data Size | 458K records | ✅ No limit | ❌ 1GB limit |
| Query Types | ✅ Complex SQL | ✅ Full SQL | ❌ Key-only |
| Global Edge | ❌ Single region | ✅ Global | ✅ Global |
| Cost (Free) | ✅ Self-hosted | ✅ 25GB/month | ❌ 1GB/month |
| Latency | ~50ms | ~10-30ms | ~5-15ms |
| Complexity | Medium | Low | High |

## Recommended Next Steps

1. **Create D1 database** using Wrangler CLI
2. **Upload your merged_bin_data.csv** in batches
3. **Update backend** to use D1 service instead of SQLite
4. **Deploy to Cloudflare Workers** for global edge performance
5. **Keep SQLite as fallback** during transition period

This approach gives you:
- ⚡ **Global edge performance** 
- 🔍 **Full SQL query capabilities**
- 💰 **Cost-effective scaling**
- 🛡️ **Built-in DDoS protection**
- 📊 **Analytics and monitoring**
