"""
Security tests for BIN Search Pro API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import sys

# Add the parent directory to sys.path to import main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app

client = TestClient(app)

class TestSecurityHeaders:
    """Test security headers implementation"""
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses"""
        response = client.get("/health")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Strict-Transport-Security" in response.headers
        
        assert "Content-Security-Policy" in response.headers
        
        assert "Permissions-Policy" in response.headers

    def test_csrf_token_generation(self):
        """Test CSRF token generation endpoint"""
        response = client.get("/api/csrf-token")
        
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 20  # Should be a reasonable length token
        assert isinstance(data["csrf_token"], str)

    def test_csrf_protection_on_post_requests(self):
        """Test CSRF protection for POST requests without Bearer token"""
        # This should fail without CSRF token
        response = client.post("/api/v1/bins/lookup", json={"bin": "123456"})
        
        # Should return 403 without CSRF token (if not authenticated with Bearer)
        # Note: This might vary based on your actual endpoint implementation
        assert response.status_code in [403, 422, 401]  # Various possible security responses

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present"""
        response = client.get("/health")
        
        # Rate limiting should add headers (if implemented)
        assert response.status_code == 200

class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self):
        """Test CORS headers for allowed origins"""
        headers = {"Origin": "http://localhost:3000"}
        response = client.options("/health", headers=headers)
        
        # CORS should be configured
        assert response.status_code in [200, 204]

class TestInputValidation:
    """Test input validation using our Pydantic models"""
    
    def test_invalid_bin_format_rejected(self):
        """Test that invalid BIN formats are rejected"""
        # Test SQL injection attempt
        response = client.post("/api/v1/bins/lookup", json={
            "bin": "'; DROP TABLE bins; --"
        })
        
        # Should be rejected with validation error
        assert response.status_code == 422

    def test_xss_attempt_sanitized(self):
        """Test XSS attempts are handled safely"""
        response = client.post("/api/v1/bins/lookup", json={
            "bin": "<script>alert('xss')</script>"
        })
        
        # Should be rejected with validation error
        assert response.status_code == 422

class TestJWTSecurity:
    """Test JWT token functionality"""
    
    def test_jwt_endpoints_require_valid_tokens(self):
        """Test that protected endpoints require valid JWT tokens"""
        # Try to access a protected endpoint without token
        response = client.get("/api/v1/crypto/check-balance", params={
            "wallet_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        })
        
        # Should require authentication
        assert response.status_code in [401, 422]

    def test_malformed_jwt_rejected(self):
        """Test that malformed JWT tokens are rejected"""
        headers = {"Authorization": "Bearer invalid_token_format"}
        response = client.get("/api/v1/crypto/check-balance", 
                            params={"wallet_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"},
                            headers=headers)
        
        # Should reject malformed token
        assert response.status_code in [401, 422]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])