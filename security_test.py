#!/usr/bin/env python3
"""Security testing script for LNBits Subscriptions extension."""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List


class SecurityTester:
    """Test security fixes implementation."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = None
        self.results = []
    
    async def setup(self):
        """Initialize test session."""
        self.session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Clean up test session."""
        if self.session:
            await self.session.close()
    
    async def test_rate_limiting(self) -> Dict:
        """Test rate limiting on public API."""
        print("🔒 Testing rate limiting...")
        
        url = f"{self.base_url}/api/v1/public/subscribe/test_plan"
        data = {"plan_id": "test_plan", "subscriber_email": "test@example.com"}
        
        success_count = 0
        blocked_count = 0
        
        # Send 10 requests rapidly
        for i in range(10):
            try:
                async with self.session.post(url, json=data) as resp:
                    if resp.status == 429:  # Too Many Requests
                        blocked_count += 1
                    elif resp.status in [200, 201, 404]:  # Success or expected errors
                        success_count += 1
                    print(f"Request {i+1}: Status {resp.status}")
            except Exception as e:
                print(f"Request {i+1}: Error {e}")
            
            await asyncio.sleep(0.1)  # Small delay
        
        result = {
            "test": "rate_limiting",
            "passed": blocked_count > 0,
            "details": f"Blocked: {blocked_count}, Success: {success_count}",
            "expected": "Should block some requests after limit exceeded"
        }
        self.results.append(result)
        return result
    
    async def test_input_validation(self) -> Dict:
        """Test input validation for XSS and injection."""
        print("🔒 Testing input validation...")
        
        test_cases = [
            # XSS attempts
            {"plan_id": "<script>alert('xss')</script>"},
            {"plan_id": "javascript:alert(1)"},
            {"plan_id": "'; DROP TABLE plans; --"},
            
            # SQL injection attempts
            {"plan_id": "1' OR '1'='1"},
            {"plan_id": "1; DELETE FROM plans; --"},
            
            # Invalid formats
            {"plan_id": ""},
            {"plan_id": "a" * 100},  # Too long
            {"plan_id": "valid_plan", "metadata": {"key": "x" * 1000}},  # Large metadata
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for i, test_data in enumerate(test_cases):
            url = f"{self.base_url}/api/v1/public/subscribe/{test_data.get('plan_id', 'test')}"
            
            try:
                async with self.session.post(url, json=test_data) as resp:
                    # Should return 400 (Bad Request) for invalid input
                    if resp.status in [400, 422]:  # Validation error
                        passed_tests += 1
                        print(f"✅ Test {i+1}: Correctly rejected (Status: {resp.status})")
                    else:
                        print(f"❌ Test {i+1}: Unexpectedly accepted (Status: {resp.status})")
            except Exception as e:
                print(f"Test {i+1}: Network error - {e}")
        
        result = {
            "test": "input_validation",
            "passed": passed_tests >= total_tests * 0.8,  # 80% should pass
            "details": f"Passed: {passed_tests}/{total_tests}",
            "expected": "Should reject malicious input with 400/422 status"
        }
        self.results.append(result)
        return result
    
    async def test_security_headers(self) -> Dict:
        """Test security headers presence."""
        print("🔒 Testing security headers...")
        
        url = f"{self.base_url}/subscriptions/"
        required_headers = [
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy"
        ]
        
        found_headers = []
        
        try:
            async with self.session.get(url) as resp:
                for header in required_headers:
                    if header.lower() in [h.lower() for h in resp.headers.keys()]:
                        found_headers.append(header)
                        print(f"✅ Found: {header}")
                    else:
                        print(f"❌ Missing: {header}")
        except Exception as e:
            print(f"Error testing headers: {e}")
        
        result = {
            "test": "security_headers",
            "passed": len(found_headers) >= len(required_headers) * 0.8,
            "details": f"Found: {len(found_headers)}/{len(required_headers)} headers",
            "expected": "Should have security headers in responses"
        }
        self.results.append(result)
        return result
    
    async def test_url_validation(self) -> Dict:
        """Test URL validation for webhooks and redirects."""
        print("🔒 Testing URL validation...")
        
        malicious_urls = [
            "http://localhost:8080/evil",  # Local network
            "http://127.0.0.1/malicious",  # Localhost
            "http://192.168.1.1/internal",  # Private network
            "file:///etc/passwd",  # File protocol
            "javascript:alert(1)",  # JavaScript protocol
            "ftp://evil.com/",  # Non-HTTP protocol
        ]
        
        passed_tests = 0
        
        for url in malicious_urls:
            test_data = {
                "name": "Test Plan",
                "amount": 1000,
                "interval": "monthly",
                "webhook_url": url
            }
            
            api_url = f"{self.base_url}/api/v1/plans"
            
            try:
                async with self.session.post(api_url, json=test_data) as resp:
                    if resp.status in [400, 422]:  # Should reject
                        passed_tests += 1
                        print(f"✅ Correctly rejected: {url}")
                    else:
                        print(f"❌ Incorrectly accepted: {url}")
            except Exception as e:
                print(f"Error testing URL {url}: {e}")
        
        result = {
            "test": "url_validation",
            "passed": passed_tests >= len(malicious_urls) * 0.8,
            "details": f"Rejected: {passed_tests}/{len(malicious_urls)} malicious URLs",
            "expected": "Should reject malicious URLs"
        }
        self.results.append(result)
        return result
    
    async def run_all_tests(self) -> Dict:
        """Run all security tests."""
        print("🚀 Starting Security Testing Suite...")
        print("=" * 50)
        
        await self.setup()
        
        try:
            # Run all test methods
            await self.test_rate_limiting()
            await self.test_input_validation() 
            await self.test_security_headers()
            await self.test_url_validation()
            
        finally:
            await self.cleanup()
        
        # Calculate overall results
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["passed"])
        
        print("\n" + "=" * 50)
        print("📊 SECURITY TEST RESULTS")
        print("=" * 50)
        
        for result in self.results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status} - {result['test']}: {result['details']}")
        
        overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Security Score: {overall_score:.1f}% ({passed_tests}/{total_tests})")
        
        if overall_score >= 80:
            print("🎉 EXCELLENT: Security implementation meets requirements!")
        elif overall_score >= 60:
            print("⚠️  GOOD: Most security measures in place, minor issues to address")
        else:
            print("🚨 NEEDS WORK: Significant security issues remain")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "score": overall_score,
            "results": self.results
        }


async def main():
    """Main testing function."""
    tester = SecurityTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("security_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: security_test_results.json")
    
    # Return exit code based on results
    return 0 if results["score"] >= 80 else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 