#!/usr/bin/env python3
"""
Deployment Validation Script
Tests production deployment health and readiness
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class DeploymentValidator:
    def __init__(self):
        self.backend_url = "https://socialmedia-api-wxip.onrender.com"
        self.frontend_url = "https://socialmedia-frontend-pycc.onrender.com"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'backend_health': {},
            'frontend_health': {},
            'critical_endpoints': {},
            'performance_metrics': {},
            'overall_status': 'unknown'
        }
    
    async def validate_deployment(self):
        """Run comprehensive deployment validation"""
        print("🚀 Deployment Validation")
        print("=" * 40)
        
        # Test backend
        print("\n🔧 Testing Backend Services...")
        await self.test_backend()
        
        # Test frontend
        print("\n🖥️  Testing Frontend...")
        await self.test_frontend()
        
        # Test critical user flows
        print("\n👤 Testing Critical User Flows...")
        await self.test_user_flows()
        
        # Performance testing
        print("\n⚡ Performance Testing...")
        await self.test_performance()
        
        # Generate report
        self.generate_deployment_report()
    
    async def test_backend(self):
        """Test backend API health"""
        async with aiohttp.ClientSession() as session:
            # Health check
            try:
                start_time = time.time()
                async with session.get(f"{self.backend_url}/health", timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        health_data = await response.json()
                        self.results['backend_health'] = {
                            'status': 'healthy',
                            'response_time': response_time,
                            'data': health_data
                        }
                        print(f"   ✅ Backend health check: OK ({response_time:.2f}s)")
                    else:
                        self.results['backend_health'] = {
                            'status': 'unhealthy',
                            'response_time': response_time,
                            'status_code': response.status
                        }
                        print(f"   ❌ Backend health check failed: {response.status}")
                        
            except Exception as e:
                self.results['backend_health'] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"   ❌ Backend unreachable: {e}")
            
            # Test critical endpoints
            critical_endpoints = [
                ('GET', '/api/content/', 'Content API'),
                ('GET', '/api/notifications/', 'Notifications'),
                ('GET', '/api/memory/analytics', 'Memory Analytics'),
                ('GET', '/health', 'Health Check')
            ]
            
            endpoint_results = {}
            for method, endpoint, description in critical_endpoints:
                try:
                    start_time = time.time()
                    async with session.request(method, f"{self.backend_url}{endpoint}", timeout=15) as response:
                        response_time = time.time() - start_time
                        
                        endpoint_results[endpoint] = {
                            'status_code': response.status,
                            'response_time': response_time,
                            'healthy': 200 <= response.status < 500  # 5xx is critical, 4xx might be expected
                        }
                        
                        if response.status < 500:
                            print(f"   ✅ {description}: {response.status} ({response_time:.2f}s)")
                        else:
                            print(f"   ❌ {description}: {response.status} ({response_time:.2f}s)")
                            
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'error': str(e),
                        'healthy': False
                    }
                    print(f"   ❌ {description}: {e}")
            
            self.results['critical_endpoints'] = endpoint_results
    
    async def test_frontend(self):
        """Test frontend availability"""
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.get(self.frontend_url, timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check if it's actually the React app
                        has_react_markers = any(marker in content.lower() for marker in [
                            'react', 'vite', 'root', 'social media', 'dashboard'
                        ])
                        
                        self.results['frontend_health'] = {
                            'status': 'healthy' if has_react_markers else 'warning',
                            'response_time': response_time,
                            'status_code': response.status,
                            'has_react_markers': has_react_markers
                        }
                        
                        if has_react_markers:
                            print(f"   ✅ Frontend accessible: OK ({response_time:.2f}s)")
                        else:
                            print(f"   ⚠️  Frontend accessible but may not be React app ({response_time:.2f}s)")
                    else:
                        self.results['frontend_health'] = {
                            'status': 'unhealthy',
                            'status_code': response.status,
                            'response_time': response_time
                        }
                        print(f"   ❌ Frontend check failed: {response.status}")
                        
            except Exception as e:
                self.results['frontend_health'] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"   ❌ Frontend unreachable: {e}")
    
    async def test_user_flows(self):
        """Test critical user flows"""
        async with aiohttp.ClientSession() as session:
            # Test registration flow (without actually registering)
            try:
                async with session.options(f"{self.backend_url}/api/auth/register", timeout=10) as response:
                    if response.status in [200, 204]:
                        print("   ✅ Registration endpoint accessible")
                    else:
                        print(f"   ⚠️  Registration endpoint: {response.status}")
            except Exception as e:
                print(f"   ❌ Registration endpoint error: {e}")
            
            # Test login flow (without credentials)
            try:
                async with session.options(f"{self.backend_url}/api/auth/login", timeout=10) as response:
                    if response.status in [200, 204]:
                        print("   ✅ Login endpoint accessible")
                    else:
                        print(f"   ⚠️  Login endpoint: {response.status}")
            except Exception as e:
                print(f"   ❌ Login endpoint error: {e}")
            
            # Test content generation (needs auth, expect 401)
            try:
                async with session.post(f"{self.backend_url}/api/content/generate", 
                                      json={'prompt': 'test'}, timeout=10) as response:
                    if response.status == 401:
                        print("   ✅ Content generation properly protected")
                    elif response.status == 422:
                        print("   ✅ Content generation validates input")
                    else:
                        print(f"   ⚠️  Content generation unexpected: {response.status}")
            except Exception as e:
                print(f"   ❌ Content generation error: {e}")
    
    async def test_performance(self):
        """Test performance metrics"""
        performance_tests = []
        
        # Test multiple concurrent requests
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(5):
                task = self.measure_endpoint_performance(session, f"{self.backend_url}/health")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_times = [r for r in results if isinstance(r, float)]
            if valid_times:
                avg_time = sum(valid_times) / len(valid_times)
                max_time = max(valid_times)
                min_time = min(valid_times)
                
                self.results['performance_metrics'] = {
                    'concurrent_requests': len(valid_times),
                    'average_response_time': avg_time,
                    'max_response_time': max_time,
                    'min_response_time': min_time,
                    'performance_grade': 'good' if avg_time < 1.0 else 'fair' if avg_time < 2.0 else 'poor'
                }
                
                print(f"   📊 Avg response time: {avg_time:.2f}s")
                print(f"   📊 Max response time: {max_time:.2f}s")
                print(f"   📊 Concurrent requests handled: {len(valid_times)}/5")
            else:
                print("   ❌ Performance test failed")
    
    async def measure_endpoint_performance(self, session, url):
        """Measure single endpoint performance"""
        try:
            start_time = time.time()
            async with session.get(url, timeout=10) as response:
                return time.time() - start_time
        except:
            return None
    
    def generate_deployment_report(self):
        """Generate deployment validation report"""
        print("\n" + "=" * 50)
        print("📋 DEPLOYMENT VALIDATION REPORT")
        print("=" * 50)
        
        # Calculate overall status
        issues = []
        
        # Backend health
        backend_status = self.results['backend_health'].get('status')
        if backend_status != 'healthy':
            issues.append("Backend health issues")
        
        # Frontend health  
        frontend_status = self.results['frontend_health'].get('status')
        if frontend_status not in ['healthy', 'warning']:
            issues.append("Frontend accessibility issues")
        
        # Critical endpoints
        unhealthy_endpoints = [
            endpoint for endpoint, result in self.results['critical_endpoints'].items()
            if not result.get('healthy', False)
        ]
        if unhealthy_endpoints:
            issues.extend([f"Endpoint issues: {ep}" for ep in unhealthy_endpoints[:3]])
        
        # Performance
        perf_grade = self.results.get('performance_metrics', {}).get('performance_grade')
        if perf_grade == 'poor':
            issues.append("Performance concerns")
        
        # Overall assessment
        if not issues:
            self.results['overall_status'] = 'healthy'
            status_emoji = '🟢'
            print(f"\n{status_emoji} DEPLOYMENT STATUS: HEALTHY")
            print("   All systems operational")
        elif len(issues) <= 2:
            self.results['overall_status'] = 'warning'
            status_emoji = '🟡'
            print(f"\n{status_emoji} DEPLOYMENT STATUS: WARNING")
            print("   Minor issues detected:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            self.results['overall_status'] = 'critical'
            status_emoji = '🔴'
            print(f"\n{status_emoji} DEPLOYMENT STATUS: CRITICAL")
            print("   Multiple issues require attention:")
            for issue in issues[:5]:
                print(f"   • {issue}")
        
        # Detailed breakdown
        print(f"\n📊 Service Status:")
        print(f"   Backend:  {self.results['backend_health'].get('status', 'unknown').upper()}")
        print(f"   Frontend: {self.results['frontend_health'].get('status', 'unknown').upper()}")
        
        healthy_endpoints = sum(1 for r in self.results['critical_endpoints'].values() if r.get('healthy', False))
        total_endpoints = len(self.results['critical_endpoints'])
        print(f"   Endpoints: {healthy_endpoints}/{total_endpoints} healthy")
        
        if self.results.get('performance_metrics'):
            perf = self.results['performance_metrics']
            print(f"   Performance: {perf.get('performance_grade', 'unknown').upper()} ({perf.get('average_response_time', 0):.2f}s avg)")
        
        # Save report
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Full report saved to: {report_file}")
        print("=" * 50)

async def main():
    """Run deployment validation"""
    validator = DeploymentValidator()
    await validator.validate_deployment()

if __name__ == "__main__":
    asyncio.run(main())