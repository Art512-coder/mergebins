#!/usr/bin/env python3
"""
BIN Search API Test Suite
Tests the Cloudflare Worker API endpoints securely from the terminal
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class BINSearchAPITester:
    def __init__(self, base_url: str = "https://bin-search-api.arturovillanueva1994.workers.dev"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BIN-Search-Test-Suite/1.0',
            'Accept': 'application/json'
        })

    def test_endpoint(self, endpoint: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Test an API endpoint and return results"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            response = self.session.request(method, url, **kwargs)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time_ms': round((end_time - start_time) * 1000, 2),
                'success': response.status_code == 200,
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'headers': dict(response.headers)
            }
        except Exception as e:
            return {
                'status_code': None,
                'response_time_ms': None,
                'success': False,
                'error': str(e),
                'data': None
            }

    def test_bin_lookup(self, bin_number: str) -> Dict[str, Any]:
        """Test BIN lookup endpoint"""
        print(f"🔍 Testing BIN lookup for: {bin_number}")
        result = self.test_endpoint(f"/bin/{bin_number}")
        
        if result['success']:
            print(f"✅ Success ({result['response_time_ms']}ms)")
            if 'bin' in result['data']:
                print(f"   Found: {result['data'].get('issuer', 'Unknown')} - {result['data'].get('brand', 'Unknown')}")
        else:
            print(f"❌ Failed: {result.get('error', f'HTTP {result['status_code']}')}") 
            
        return result

    def test_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Test search endpoint"""
        print(f"🔍 Testing search for: '{query}'")
        result = self.test_endpoint(f"/search", params={'q': query, 'limit': limit})
        
        if result['success']:
            count = result['data'].get('count', 0)
            print(f"✅ Success ({result['response_time_ms']}ms) - Found {count} results")
        else:
            print(f"❌ Failed: {result.get('error', f'HTTP {result['status_code']}')}") 
            
        return result

    def test_stats(self) -> Dict[str, Any]:
        """Test stats endpoint"""
        print("📊 Testing stats endpoint")
        result = self.test_endpoint("/stats")
        
        if result['success']:
            total = result['data'].get('total_records', 'Unknown')
            print(f"✅ Success ({result['response_time_ms']}ms) - {total} total records")
        else:
            print(f"❌ Failed: {result.get('error', f'HTTP {result['status_code']}')}") 
            
        return result

    def test_cors(self) -> Dict[str, Any]:
        """Test CORS headers"""
        print("🌐 Testing CORS headers")
        result = self.test_endpoint("/", method='OPTIONS')
        
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        has_cors = all(header in result.get('headers', {}) for header in cors_headers)
        
        if has_cors:
            print(f"✅ CORS properly configured")
        else:
            print(f"⚠️  CORS headers missing or incomplete")
            
        return result

    def run_comprehensive_test(self):
        """Run all tests and provide summary"""
        print("🚀 Starting BIN Search API Test Suite")
        print("=" * 50)
        
        results = {}
        
        # Test cases
        test_cases = [
            ('stats', lambda: self.test_stats()),
            ('cors', lambda: self.test_cors()),
            ('bin_valid', lambda: self.test_bin_lookup('424242')),
            ('bin_invalid', lambda: self.test_bin_lookup('000000')),
            ('bin_short', lambda: self.test_bin_lookup('123')),
            ('search_visa', lambda: self.test_search('visa')),
            ('search_empty', lambda: self.test_search('')),
            ('search_bank', lambda: self.test_search('bank'))
        ]
        
        for test_name, test_func in test_cases:
            try:
                results[test_name] = test_func()
                print()  # Add spacing between tests
            except Exception as e:
                print(f"💥 Test '{test_name}' crashed: {e}")
                results[test_name] = {'success': False, 'error': str(e)}
                print()
        
        # Summary
        print("📋 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for r in results.values() if r.get('success', False))
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            timing = f"({result.get('response_time_ms', 0)}ms)" if result.get('response_time_ms') else ""
            print(f"{status} {test_name} {timing}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API is working perfectly.")
        else:
            print(f"⚠️  {total - passed} tests failed. Check the API configuration.")
            
        return results

def main():
    """Main test runner"""
    tester = BINSearchAPITester()
    results = tester.run_comprehensive_test()
    
    # Optional: Save results to file
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to test_results.json")

if __name__ == "__main__":
    main()