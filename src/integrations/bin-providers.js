/**
 * Third-party BIN API Integration System
 * Handles multiple BIN data providers with fallback and caching
 */

export class BINDataProvider {
    constructor(database, apm) {
        this.db = database;
        this.apm = apm;
        this.cache = new Map();
        this.cacheTimeout = 24 * 60 * 60 * 1000; // 24 hours
        
        // Initialize providers
        this.providers = {
            binlist: new BinListProvider(),
            local: new LocalBINProvider(database),
            enhanced: new EnhancedBINProvider()
        };
    }

    /**
     * Get comprehensive BIN data using multiple providers
     */
    async getBINData(binNumber, options = {}) {
        const transaction = this.apm.startTransaction('bin:get_enhanced_data');
        
        try {
            const bin = binNumber.substring(0, 6);
            
            // Check cache first
            const cacheKey = `bin:${bin}`;
            const cachedData = this.cache.get(cacheKey);
            if (cachedData && Date.now() - cachedData.timestamp < this.cacheTimeout) {
                transaction.setResult('cache_hit');
                return cachedData.data;
            }

            // Check database cache
            const { results: cachedResults } = await this.db.prepare(`
                SELECT * FROM enhanced_bin_data 
                WHERE bin_number = ? AND cache_expires_at > datetime('now')
            `).bind(bin).all();

            if (cachedResults.length > 0) {
                const data = this.formatBINData(cachedResults[0]);
                this.cache.set(cacheKey, { data, timestamp: Date.now() });
                transaction.setResult('db_cache_hit');
                return data;
            }

            // Fetch from multiple providers
            const results = await Promise.allSettled([
                this.providers.binlist.lookup(bin),
                this.providers.local.lookup(bin),
                this.providers.enhanced.lookup(bin)
            ]);

            // Merge results from all providers
            const mergedData = this.mergeProviderResults(bin, results);
            
            // Store in database cache
            await this.storeBINData(bin, mergedData);
            
            // Store in memory cache
            this.cache.set(cacheKey, { data: mergedData, timestamp: Date.now() });

            transaction.setResult('success');
            return mergedData;

        } catch (error) {
            transaction.setResult('error');
            console.error('Error fetching BIN data:', error);
            return this.getBasicBINData(binNumber);
        } finally {
            transaction.end();
        }
    }

    /**
     * Merge results from multiple BIN data providers
     */
    mergeProviderResults(bin, results) {
        const merged = {
            bin: bin,
            issuer: {},
            card: {},
            country: {},
            bank: {},
            features: {},
            risk: {},
            metadata: {
                sources: [],
                last_updated: new Date().toISOString(),
                confidence_score: 0
            }
        };

        let totalConfidence = 0;
        let sourceCount = 0;

        results.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value.success) {
                const data = result.value.data;
                const provider = ['binlist', 'local', 'enhanced'][index];
                
                merged.metadata.sources.push(provider);
                sourceCount++;

                // Merge issuer data
                if (data.issuer) {
                    merged.issuer = { ...merged.issuer, ...data.issuer };
                }

                // Merge card data
                if (data.card) {
                    merged.card = { ...merged.card, ...data.card };
                }

                // Merge country data
                if (data.country) {
                    merged.country = { ...merged.country, ...data.country };
                }

                // Merge bank data
                if (data.bank) {
                    merged.bank = { ...merged.bank, ...data.bank };
                }

                // Merge features
                if (data.features) {
                    merged.features = { ...merged.features, ...data.features };
                }

                // Merge risk data
                if (data.risk) {
                    merged.risk = { ...merged.risk, ...data.risk };
                }

                // Add to confidence score
                totalConfidence += data.confidence_score || 50;
            }
        });

        // Calculate average confidence
        merged.metadata.confidence_score = sourceCount > 0 ? Math.round(totalConfidence / sourceCount) : 0;

        return merged;
    }

    /**
     * Store BIN data in database cache
     */
    async storeBINData(bin, data) {
        try {
            const expiresAt = new Date(Date.now() + this.cacheTimeout).toISOString();
            
            await this.db.prepare(`
                INSERT OR REPLACE INTO enhanced_bin_data
                (bin_number, issuer_name, issuer_website, issuer_phone, card_brand, card_type,
                 card_category, country_code, country_name, bank_name, bank_website, bank_phone,
                 supported_currencies, card_features, fraud_score, is_commercial, is_prepaid,
                 data_source, last_updated, cache_expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `).bind(
                bin,
                data.issuer?.name || null,
                data.issuer?.website || null,
                data.issuer?.phone || null,
                data.card?.brand || null,
                data.card?.type || null,
                data.card?.category || null,
                data.country?.code || null,
                data.country?.name || null,
                data.bank?.name || null,
                data.bank?.website || null,
                data.bank?.phone || null,
                JSON.stringify(data.features?.supported_currencies || []),
                JSON.stringify(data.features || {}),
                data.risk?.fraud_score || 0,
                data.card?.is_commercial || false,
                data.card?.is_prepaid || false,
                data.metadata?.sources?.join(',') || 'unknown',
                new Date().toISOString(),
                expiresAt
            ).run();

        } catch (error) {
            console.error('Error storing BIN data:', error);
        }
    }

    /**
     * Format BIN data from database
     */
    formatBINData(dbData) {
        return {
            bin: dbData.bin_number,
            issuer: {
                name: dbData.issuer_name,
                website: dbData.issuer_website,
                phone: dbData.issuer_phone
            },
            card: {
                brand: dbData.card_brand,
                type: dbData.card_type,
                category: dbData.card_category,
                is_commercial: dbData.is_commercial,
                is_prepaid: dbData.is_prepaid
            },
            country: {
                code: dbData.country_code,
                name: dbData.country_name
            },
            bank: {
                name: dbData.bank_name,
                website: dbData.bank_website,
                phone: dbData.bank_phone
            },
            features: JSON.parse(dbData.card_features || '{}'),
            risk: {
                fraud_score: dbData.fraud_score
            },
            metadata: {
                sources: dbData.data_source?.split(',') || [],
                last_updated: dbData.last_updated,
                confidence_score: 85 // Database data has high confidence
            }
        };
    }

    /**
     * Get basic BIN data (fallback)
     */
    getBasicBINData(binNumber) {
        const bin = binNumber.substring(0, 6);
        
        return {
            bin: bin,
            issuer: { name: 'Unknown' },
            card: { brand: 'Unknown', type: 'Unknown' },
            country: { code: 'XX', name: 'Unknown' },
            bank: {},
            features: {},
            risk: { fraud_score: 50 },
            metadata: {
                sources: ['fallback'],
                last_updated: new Date().toISOString(),
                confidence_score: 10
            }
        };
    }
}

/**
 * BinList.net API Provider
 */
class BinListProvider {
    constructor() {
        this.baseUrl = 'https://lookup.binlist.net';
        this.rateLimit = 60; // requests per minute
        this.lastRequest = 0;
    }

    async lookup(bin) {
        try {
            // Rate limiting
            const now = Date.now();
            if (now - this.lastRequest < 1000) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            this.lastRequest = Date.now();

            const response = await fetch(`${this.baseUrl}/${bin}`, {
                headers: {
                    'Accept-Version': '3'
                },
                timeout: 5000
            });

            if (!response.ok) {
                return { success: false, error: 'API request failed' };
            }

            const data = await response.json();
            
            return {
                success: true,
                data: {
                    issuer: {
                        name: data.bank?.name || data.brand,
                        website: data.bank?.url,
                        phone: data.bank?.phone
                    },
                    card: {
                        brand: data.brand,
                        type: data.type,
                        category: data.category,
                        is_prepaid: data.prepaid === true
                    },
                    country: {
                        code: data.country?.alpha2,
                        name: data.country?.name
                    },
                    bank: {
                        name: data.bank?.name,
                        website: data.bank?.url,
                        phone: data.bank?.phone
                    },
                    confidence_score: 80
                }
            };

        } catch (error) {
            console.error('BinList API error:', error);
            return { success: false, error: error.message };
        }
    }
}

/**
 * Local BIN Database Provider
 */
class LocalBINProvider {
    constructor(database) {
        this.db = database;
    }

    async lookup(bin) {
        try {
            const { results } = await this.db.prepare(`
                SELECT * FROM bin_data WHERE bin_start <= ? AND bin_end >= ?
                ORDER BY bin_start DESC LIMIT 1
            `).bind(bin, bin).all();

            if (results.length === 0) {
                return { success: false, error: 'BIN not found in local database' };
            }

            const data = results[0];
            
            return {
                success: true,
                data: {
                    issuer: {
                        name: data.issuer_name
                    },
                    card: {
                        brand: data.card_brand,
                        type: data.card_type
                    },
                    country: {
                        code: data.country_code,
                        name: data.country_name
                    },
                    confidence_score: 90 // Local data has high confidence
                }
            };

        } catch (error) {
            console.error('Local BIN database error:', error);
            return { success: false, error: error.message };
        }
    }
}

/**
 * Enhanced BIN Provider (Custom algorithms and data)
 */
class EnhancedBINProvider {
    constructor() {
        this.cardPatterns = {
            visa: /^4[0-9]/,
            mastercard: /^5[1-5]|^2[2-7]/,
            amex: /^3[47]/,
            discover: /^6(?:011|5)/,
            dinersclub: /^3[0689]/,
            jcb: /^35/
        };
        
        this.typePatterns = {
            debit: [/^4000/, /^4111/, /^5200/],
            credit: [/^4[2-6]/, /^5[1-5]/],
            prepaid: [/^4847/, /^4514/]
        };
    }

    async lookup(bin) {
        try {
            const analysis = {
                issuer: {},
                card: {},
                country: {},
                features: {},
                risk: {},
                confidence_score: 60
            };

            // Analyze card brand
            for (const [brand, pattern] of Object.entries(this.cardPatterns)) {
                if (pattern.test(bin)) {
                    analysis.card.brand = brand.charAt(0).toUpperCase() + brand.slice(1);
                    analysis.confidence_score += 10;
                    break;
                }
            }

            // Analyze card type
            for (const [type, patterns] of Object.entries(this.typePatterns)) {
                if (patterns.some(pattern => pattern.test(bin))) {
                    analysis.card.type = type;
                    analysis.confidence_score += 10;
                    break;
                }
            }

            // Calculate fraud risk score based on BIN patterns
            analysis.risk.fraud_score = this.calculateFraudRisk(bin);

            // Add enhanced features
            analysis.features = {
                luhn_valid: this.validateLuhn(bin + '0000000000'),
                bin_length: bin.length,
                industry_identifier: this.getIndustryIdentifier(bin[0])
            };

            return {
                success: true,
                data: analysis
            };

        } catch (error) {
            console.error('Enhanced BIN provider error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Calculate fraud risk score (0-100, higher = riskier)
     */
    calculateFraudRisk(bin) {
        let riskScore = 30; // Base risk

        // Known high-risk patterns
        const highRiskPatterns = [
            /^4000/, // Test cards
            /^5555/, // Test cards
            /^4111/ // Common test BIN
        ];

        if (highRiskPatterns.some(pattern => pattern.test(bin))) {
            riskScore += 40;
        }

        // Prepaid cards have higher risk
        if (this.typePatterns.prepaid.some(pattern => pattern.test(bin))) {
            riskScore += 20;
        }

        // Sequential patterns increase risk
        if (this.hasSequentialPattern(bin)) {
            riskScore += 15;
        }

        return Math.min(100, riskScore);
    }

    /**
     * Check for sequential patterns in BIN
     */
    hasSequentialPattern(bin) {
        const digits = bin.split('').map(Number);
        let sequential = 0;
        
        for (let i = 1; i < digits.length; i++) {
            if (digits[i] === digits[i-1] + 1) {
                sequential++;
            }
        }
        
        return sequential >= 3;
    }

    /**
     * Validate Luhn algorithm
     */
    validateLuhn(number) {
        const digits = number.split('').map(Number);
        let sum = 0;
        let isEven = false;
        
        for (let i = digits.length - 1; i >= 0; i--) {
            let digit = digits[i];
            
            if (isEven) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            
            sum += digit;
            isEven = !isEven;
        }
        
        return sum % 10 === 0;
    }

    /**
     * Get industry identifier meaning
     */
    getIndustryIdentifier(firstDigit) {
        const identifiers = {
            '0': 'ISO/TC 68 and other industry assignments',
            '1': 'Airlines',
            '2': 'Airlines and other future industry assignments',
            '3': 'Travel and entertainment',
            '4': 'Banking and financial',
            '5': 'Banking and financial',
            '6': 'Merchandising and banking/financial',
            '7': 'Petroleum and other future industry assignments',
            '8': 'Healthcare, telecommunications and other future industry assignments',
            '9': 'For assignment by national standards bodies'
        };
        
        return identifiers[firstDigit] || 'Unknown';
    }
}

/**
 * External API Manager
 */
export class ExternalAPIManager {
    constructor(database, apm) {
        this.db = database;
        this.apm = apm;
        this.providers = new Map();
        
        // Initialize providers
        this.initializeProviders();
    }

    async initializeProviders() {
        try {
            const { results } = await this.db.prepare(`
                SELECT * FROM external_apis WHERE is_active = true
            `).all();

            results.forEach(api => {
                this.providers.set(api.provider_name, {
                    config: api,
                    lastUsed: 0,
                    errorCount: 0,
                    successCount: 0
                });
            });

        } catch (error) {
            console.error('Error initializing external API providers:', error);
        }
    }

    /**
     * Make API request with monitoring and fallback
     */
    async makeRequest(providerName, endpoint, options = {}) {
        const transaction = this.apm.startTransaction(`external_api:${providerName}`);
        
        try {
            const provider = this.providers.get(providerName);
            if (!provider) {
                throw new Error(`Unknown provider: ${providerName}`);
            }

            // Rate limiting check
            const now = Date.now();
            if (now - provider.lastUsed < (60000 / provider.config.rate_limit_per_minute)) {
                const delay = (60000 / provider.config.rate_limit_per_minute) - (now - provider.lastUsed);
                await new Promise(resolve => setTimeout(resolve, delay));
            }

            provider.lastUsed = Date.now();

            // Make request
            const url = `${provider.config.base_url}${endpoint}`;
            const requestOptions = {
                ...options,
                timeout: provider.config.timeout_seconds * 1000,
                headers: {
                    ...options.headers,
                    'Authorization': provider.config.api_key ? `Bearer ${provider.config.api_key}` : undefined,
                    'User-Agent': 'BinSearch-Pro/1.0'
                }
            };

            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            
            // Update success stats
            provider.successCount++;
            await this.updateProviderStats(provider.config.id, true, response.headers.get('x-response-time'));

            transaction.setResult('success');
            return { success: true, data };

        } catch (error) {
            const provider = this.providers.get(providerName);
            if (provider) {
                provider.errorCount++;
                await this.updateProviderStats(provider.config.id, false);
            }

            transaction.setResult('error');
            console.error(`External API error (${providerName}):`, error);
            return { success: false, error: error.message };
        } finally {
            transaction.end();
        }
    }

    /**
     * Update provider statistics
     */
    async updateProviderStats(providerId, success, responseTime = null) {
        try {
            const updateQuery = success 
                ? `UPDATE external_apis 
                   SET success_count = success_count + 1, 
                       last_used_at = ?,
                       avg_response_time_ms = CASE 
                           WHEN avg_response_time_ms = 0 THEN ?
                           ELSE (avg_response_time_ms + ?) / 2
                       END
                   WHERE id = ?`
                : `UPDATE external_apis 
                   SET error_count = error_count + 1
                   WHERE id = ?`;

            const params = success 
                ? [new Date().toISOString(), responseTime || 0, responseTime || 0, providerId]
                : [providerId];

            await this.db.prepare(updateQuery).bind(...params).run();

        } catch (error) {
            console.error('Error updating provider stats:', error);
        }
    }

    /**
     * Get provider health status
     */
    async getProviderHealth() {
        try {
            const { results } = await this.db.prepare(`
                SELECT provider_name, success_count, error_count, avg_response_time_ms,
                       last_used_at, is_active,
                       CASE 
                           WHEN (success_count + error_count) = 0 THEN 'unknown'
                           WHEN (success_count * 100.0 / (success_count + error_count)) >= 95 THEN 'healthy'
                           WHEN (success_count * 100.0 / (success_count + error_count)) >= 80 THEN 'degraded'
                           ELSE 'unhealthy'
                       END as health_status
                FROM external_apis
                ORDER BY provider_name
            `).all();

            return {
                success: true,
                providers: results
            };

        } catch (error) {
            console.error('Error getting provider health:', error);
            return { success: false, error: error.message };
        }
    }
}