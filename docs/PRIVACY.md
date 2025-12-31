# Privacy Policy for @BINSearchCCGBot

**Last Updated**: August 19, 2025

## Overview
@BINSearchCCGBot is committed to protecting your privacy. This policy outlines how we handle data for BIN lookups, test card generation, and crypto wallet balance checks.

## Data Collection
- **Public Data**: We process publicly available BINs (458,051+ records) and crypto wallet addresses (ETH/BTC) for informational purposes.
- **User Data**: Telegram user IDs are used to track free-tier limits (3/day) and premium subscriptions ($9.99/month via NOWPayments or $5/check). No personal data is stored unless you opt into premium.
- **Premium Subscriptions**: User IDs are stored in Redis (`DBCWcheck`) with a 30-day expiry for subscription status.

## Data Usage
- **Purpose**: Provide BIN lookup, test card generation, and wallet balance checks for ethical testing and fintech research.
- **Storage**: Data is cached in Redis (5-minute expiry for balances, 30-day for premium status). No sensitive payment data is stored.
- **Third Parties**: We use Etherscan, Blockchain.com, CoinGecko, and NOWPayments APIs. Their privacy policies apply.

## GDPR Compliance
- We only process public data or user-consented IDs.
- You can request deletion of premium status by contacting @BINSearchCCGBot support.
- No sensitive personal data is collected.

## Contact
- Telegram: @BINSearchCCGBot
- GitHub: Create an issue at [your-repo-url]

**Disclaimer**: This bot is for ethical testing only. Do not use for unauthorized activities.
