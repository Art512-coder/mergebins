# 🔧 Coinbase Commerce Setup Guide for BIN Search App

## Dashboard Configuration

### 1. **API Keys** (You already have these)
- API Key: `your_existing_api_key`
- Webhook Secret: `your_webhook_secret`

### 2. **Webhook Settings**
Configure these webhook URLs in your Coinbase Commerce dashboard:

**Webhook URL**: `https://yourdomain.com/webhook/coinbase`
**Events to Subscribe**:
- ✅ `charge:created`
- ✅ `charge:confirmed` 
- ✅ `charge:failed`
- ✅ `charge:delayed`
- ✅ `charge:pending`
- ✅ `charge:resolved`

### 3. **Settings Recommendations**
- **Auto-Cancel**: 1 hour (reasonable for subscription payments)
- **Required Confirmations**: 
  - Bitcoin: 1 confirmation
  - Ethereum: 12 confirmations  
  - Litecoin: 6 confirmations
- **Email Notifications**: Enable for successful payments

## Integration Benefits

### Why Dynamic Charges > Products:

1. **User-Specific Metadata**:
```json
{
  "metadata": {
    "user_id": "123",
    "subscription_tier": "premium", 
    "renewal_date": "2025-09-28",
    "telegram_user_id": "456789"
  }
}
```

2. **Flexible Pricing**:
- Free trial → Premium: $9.99
- Premium → API Access: $29.99
- Custom enterprise pricing

3. **Better UX**:
- Redirect to your success page
- Immediate subscription activation
- Custom confirmation emails

## Multiple Apps Strategy

Since you're using Coinbase for another app:

### Option A: **Same Coinbase Account** (Recommended)
- Use different `metadata.app_name` to distinguish
- Same API keys, different webhook handling
- Shared rate limits but easier management

### Option B: **Separate Coinbase Account**
- Complete isolation between apps
- Separate API keys and webhooks
- Independent rate limits

**Recommendation**: Use Option A with app identification in metadata.

## Implementation Example

```python
# In your BIN search app
charge_data = {
    "name": "BIN Search Premium",
    "metadata": {
        "app_name": "bin_search",  # Distinguish from other app
        "user_id": user.id,
        "tier": "premium"
    }
}

# In your webhook handler
if payload.metadata.get("app_name") == "bin_search":
    # Handle BIN search payment
    activate_premium_subscription(payload.metadata.user_id)
```
