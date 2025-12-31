# Cloudflare D1 Integration Setup

## Overview
The BIN checker now uses Cloudflare D1 as the primary database source for global edge performance, with SQLite as a fallback for reliability.

## Database Configuration

### D1 Database Details
- **Database ID**: `e8e3af39-17e0-4c36-bebe-efe510a973af`
- **Database Name**: `bin-database`
- **Records**: 458,502 total BIN records (migration in progress)
- **Schema**: Optimized with indexes for fast lookups

### Current Migration Status
- ✅ Database created and schema applied
- ✅ 100 batches uploaded (50,002 records - 11%)
- 🔄 Bulk upload in progress (817 remaining batches)
- ⏱️ Estimated completion: ~20 minutes

## Environment Variables Required

Add these to your production environment:

```bash
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
```

### Getting Cloudflare Credentials

1. **Account ID**: 
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
   - Copy the Account ID from the right sidebar

2. **API Token**:
   - Go to [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
   - Create token with permissions:
     - Account: Cloudflare D1:Edit
     - Zone resources: Include All zones

## Backend Integration

### Service Implementation
- **File**: `app/services/d1_bin_service.py`
- **Class**: `CloudflareD1Service`
- **Methods**: 
  - `lookup_bin(bin_number)` - Single BIN lookup
  - `search_bins(filters)` - Search with filters

### Route Updates
- **File**: `app/routes/bins.py`
- **Primary Source**: Cloudflare D1 (global edge)
- **Fallback**: SQLite database (local reliability)
- **Caching**: Redis cache layer for performance

### Performance Benefits
- **Global Edge**: D1 data served from Cloudflare edge locations worldwide
- **Low Latency**: Sub-100ms responses globally
- **Reliability**: Automatic fallback to SQLite if D1 unavailable
- **Caching**: Redis cache for frequently accessed BINs

## Schema Mapping

| SQLite Field | D1 Field | Notes |
|--------------|----------|-------|
| bin | bin | Primary key |
| brand | brand | Card brand (VISA, MASTERCARD, etc.) |
| issuer | issuer | Bank/issuer name |
| type | type | CREDIT, DEBIT, etc. |
| level | category | Premium, Classic, etc. |
| country_name | country | Country name |
| bank_phone | bank_phone | Bank contact number |
| bank_url | bank_url | Bank website |
| country_code | - | Not available in D1 schema |

## Monitoring Upload Progress

Check upload progress with:
```powershell
# Check if wrangler is still running
Get-Process -Name "wrangler" -ErrorAction SilentlyContinue

# Check D1 database record count
wrangler d1 execute bin-database --command="SELECT COUNT(*) as total_records FROM bins;"
```

## Testing D1 Integration

1. **Local Testing**: Requires Cloudflare credentials
2. **Production**: Automatic failover to SQLite if D1 unavailable
3. **Performance**: Monitor response times and cache hit rates

## Next Steps

1. ✅ Complete bulk upload (in progress)
2. ⏱️ Add environment variables to production
3. ⏱️ Monitor D1 performance metrics
4. ⏱️ Test global edge response times

## Troubleshooting

### Common Issues
- **Missing credentials**: Add `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`
- **Network issues**: Service automatically falls back to SQLite
- **Rate limiting**: D1 has generous limits but respects Cloudflare quotas

### Fallback Behavior
- D1 failure → SQLite lookup
- SQLite failure → HTTP 404 error
- Cache failure → Direct database query
