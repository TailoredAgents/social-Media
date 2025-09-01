"""
Load Testing Suite for Social Media Integration APIs
Production-ready load testing with realistic traffic patterns
"""
import asyncio
import aiohttp
import time
import statistics
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import random

logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    """Result of a load test"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[str]
    test_duration: float
    timestamp: str

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    base_url: str = "http://localhost:8000"
    concurrent_users: int = 50
    requests_per_user: int = 10
    ramp_up_time: int = 10  # seconds
    test_duration: int = 60  # seconds
    target_response_time: float = 200.0  # milliseconds
    acceptable_error_rate: float = 1.0  # percentage

class LoadTester:
    """
    Comprehensive load testing for the social media platform
    
    Features:
    - Realistic traffic patterns
    - Performance validation
    - Concurrent user simulation
    - Response time analysis
    - Error rate monitoring
    - Production-ready scenarios
    """
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[LoadTestResult] = []
        
        # Test scenarios with realistic endpoints
        self.test_scenarios = [
            {
                "name": "Health Check",
                "endpoint": "/health",
                "method": "GET",
                "weight": 5  # 5% of traffic
            },
            {
                "name": "User Profile",
                "endpoint": "/api/users/me",
                "method": "GET",
                "weight": 15  # 15% of traffic
            },
            {
                "name": "Content List",
                "endpoint": "/api/content/",
                "method": "GET",
                "weight": 20  # 20% of traffic
            },
            {
                "name": "Analytics Data",
                "endpoint": "/api/analytics/summary",
                "method": "GET",
                "weight": 15  # 15% of traffic
            },
            {
                "name": "Goals List",
                "endpoint": "/api/goals/",
                "method": "GET",
                "weight": 10  # 10% of traffic
            },
            {
                "name": "Memory Search",
                "endpoint": "/api/memory/search",
                "method": "POST",
                "weight": 10,  # 10% of traffic
                "payload": {"query": "test content", "limit": 10}
            },
            {
                "name": "Metrics Collection Status",
                "endpoint": "/api/integrations/metrics/collection",
                "method": "GET",
                "weight": 10  # 10% of traffic
            },
            {
                "name": "Content Creation",
                "endpoint": "/api/content/",
                "method": "POST",
                "weight": 10,  # 10% of traffic
                "payload": {
                    "content": "Test content for load testing",
                    "platform": "twitter",
                    "content_type": "post"
                }
            },
            {
                "name": "Instagram Integration",
                "endpoint": "/api/integrations/instagram/post",  
                "method": "POST",
                "weight": 3,  # 3% of traffic
                "payload": {
                    "caption": "Load test post",
                    "media_urls": ["https://example.com/test.jpg"],
                    "media_type": "IMAGE"
                }
            },
            {
                "name": "Facebook Integration",
                "endpoint": "/api/integrations/facebook/post",
                "method": "POST", 
                "weight": 2,  # 2% of traffic
                "payload": {
                    "message": "Load test Facebook post"
                }
            }
        ]
        
        # Normalize weights
        total_weight = sum(scenario["weight"] for scenario in self.test_scenarios)
        for scenario in self.test_scenarios:
            scenario["weight"] = scenario["weight"] / total_weight
        
        logger.info(f"Load tester initialized: {config.concurrent_users} users, {config.requests_per_user} req/user")
    
    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        scenario: Dict[str, Any]
    ) -> Tuple[float, bool, Optional[str]]:
        """
        Make a single HTTP request and measure response time
        
        Returns:
            Tuple of (response_time_ms, success, error_message)
        """
        start_time = time.time()
        
        try:
            url = f"{self.config.base_url}{scenario['endpoint']}"
            method = scenario.get("method", "GET")
            payload = scenario.get("payload")
            
            if method == "GET":
                async with session.get(url) as response:
                    await response.text()  # Consume response
                    success = response.status < 400
            elif method == "POST":
                async with session.post(url, json=payload) as response:
                    await response.text()  # Consume response
                    success = response.status < 400
            else:
                return 0.0, False, f"Unsupported method: {method}"
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return response_time, success, None if success else f"HTTP {response.status}"
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return response_time, False, "Timeout"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return response_time, False, str(e)
    
    async def _user_simulation(
        self,
        user_id: int,
        session: aiohttp.ClientSession
    ) -> List[Tuple[str, float, bool, Optional[str]]]:
        """
        Simulate a single user's behavior
        
        Returns:
            List of (endpoint, response_time, success, error) tuples
        """
        results = []
        
        for _ in range(self.config.requests_per_user):
            # Select scenario based on weights
            scenario = random.choices(
                self.test_scenarios,
                weights=[s["weight"] for s in self.test_scenarios]
            )[0]
            
            response_time, success, error = await self._make_request(session, scenario)
            results.append((scenario["endpoint"], response_time, success, error))
            
            # Random delay between requests (0.1 to 2 seconds)
            await asyncio.sleep(random.uniform(0.1, 2.0))
        
        return results
    
    async def _run_load_test_scenario(
        self,
        scenario_name: str
    ) -> LoadTestResult:
        """
        Run load test for a specific scenario
        
        Args:
            scenario_name: Name of the test scenario
            
        Returns:
            Load test results
        """
        logger.info(f"Starting load test: {scenario_name}")
        
        # Configure session with timeouts
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        
        all_results = []
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Create tasks for concurrent users
            tasks = []
            
            for user_id in range(self.config.concurrent_users):
                # Stagger user start times for realistic ramp-up
                delay = (user_id / self.config.concurrent_users) * self.config.ramp_up_time
                
                task = asyncio.create_task(
                    self._delayed_user_simulation(user_id, session, delay)
                )
                tasks.append(task)
            
            # Wait for all users to complete
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for result in user_results:
                if isinstance(result, list):
                    all_results.extend(result)
                else:
                    logger.error(f"User simulation error: {result}")
        
        test_duration = time.time() - start_time
        
        # Analyze results
        return self._analyze_results(scenario_name, all_results, test_duration)
    
    async def _delayed_user_simulation(
        self,
        user_id: int,
        session: aiohttp.ClientSession,
        delay: float
    ) -> List[Tuple[str, float, bool, Optional[str]]]:
        """Simulate user with initial delay"""
        await asyncio.sleep(delay)
        return await self._user_simulation(user_id, session)
    
    def _analyze_results(
        self,
        scenario_name: str,
        results: List[Tuple[str, float, bool, Optional[str]]],
        test_duration: float
    ) -> LoadTestResult:
        """
        Analyze load test results
        
        Args:
            scenario_name: Name of test scenario
            results: List of (endpoint, response_time, success, error) tuples
            test_duration: Total test duration in seconds
            
        Returns:
            Analyzed load test results
        """
        if not results:
            return LoadTestResult(
                endpoint=scenario_name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0.0,
                median_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                requests_per_second=0.0,
                error_rate=0.0,
                errors=[],
                test_duration=test_duration,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Separate successful and failed requests
        successful_requests = [r for r in results if r[2]]  # r[2] is success
        failed_requests = [r for r in results if not r[2]]
        
        # Response time analysis (only successful requests)
        response_times = [r[1] for r in successful_requests]  # r[1] is response_time
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0.0
            min_response_time = max_response_time = 0.0
        
        # Calculate metrics
        total_requests = len(results)
        successful_count = len(successful_requests)
        failed_count = len(failed_requests)
        error_rate = (failed_count / total_requests) * 100 if total_requests > 0 else 0
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        
        # Collect unique errors
        errors = list(set([r[3] for r in failed_requests if r[3]]))
        
        return LoadTestResult(
            endpoint=scenario_name,
            total_requests=total_requests,
            successful_requests=successful_count,
            failed_requests=failed_count,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors,
            test_duration=test_duration,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    async def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """
        Run comprehensive load test suite
        
        Returns:
            Complete test results and analysis
        """
        logger.info("Starting comprehensive load test suite")
        
        # Run load test
        result = await self._run_load_test_scenario("Comprehensive Load Test")
        self.results.append(result)
        
        # Analyze performance against targets
        performance_analysis = self._analyze_performance_targets(result)
        
        # Generate report
        report = {
            "test_config": asdict(self.config),
            "results": asdict(result),
            "performance_analysis": performance_analysis,
            "recommendations": self._generate_recommendations(result),
            "summary": {
                "passed": performance_analysis["response_time_target_met"] and performance_analysis["error_rate_acceptable"],
                "test_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Load test completed: {result.total_requests} requests, {result.avg_response_time:.1f}ms avg")
        
        return report
    
    def _analyze_performance_targets(self, result: LoadTestResult) -> Dict[str, Any]:
        """Analyze results against performance targets"""
        return {
            "response_time_target_met": result.avg_response_time <= self.config.target_response_time,
            "response_time_target": self.config.target_response_time,
            "actual_avg_response_time": result.avg_response_time,
            "response_time_deviation": result.avg_response_time - self.config.target_response_time,
            "error_rate_acceptable": result.error_rate <= self.config.acceptable_error_rate,
            "error_rate_target": self.config.acceptable_error_rate,
            "actual_error_rate": result.error_rate,
            "p95_response_time_acceptable": result.p95_response_time <= (self.config.target_response_time * 1.5),
            "throughput_analysis": {
                "requests_per_second": result.requests_per_second,
                "concurrent_users": self.config.concurrent_users,
                "avg_requests_per_user_per_second": result.requests_per_second / self.config.concurrent_users
            }
        }
    
    def _generate_recommendations(self, result: LoadTestResult) -> List[str]:
        """Generate performance recommendations based on results"""
        recommendations = []
        
        if result.avg_response_time > self.config.target_response_time:
            recommendations.append(f"Average response time ({result.avg_response_time:.1f}ms) exceeds target ({self.config.target_response_time}ms). Consider optimizing database queries and adding caching.")
        
        if result.p95_response_time > (self.config.target_response_time * 2):
            recommendations.append(f"95th percentile response time ({result.p95_response_time:.1f}ms) is very high. Investigate slow queries and consider connection pool optimization.")
        
        if result.error_rate > self.config.acceptable_error_rate:
            recommendations.append(f"Error rate ({result.error_rate:.1f}%) exceeds acceptable threshold ({self.config.acceptable_error_rate}%). Review error logs and improve error handling.")
        
        if result.requests_per_second < (self.config.concurrent_users * 0.5):
            recommendations.append("Low throughput detected. Consider scaling infrastructure or optimizing application performance.")
        
        if not recommendations:
            recommendations.append("Performance targets met! System is ready for production load.")
        
        return recommendations

async def run_production_load_test():
    """Run production-ready load test"""
    
    # Production-like configuration
    config = LoadTestConfig(
        base_url="http://localhost:8000",
        concurrent_users=25,  # Moderate load for initial testing
        requests_per_user=20,
        ramp_up_time=10,
        test_duration=60,
        target_response_time=200.0,  # 200ms target
        acceptable_error_rate=1.0   # 1% error rate
    )
    
    load_tester = LoadTester(config)
    
    try:
        results = await load_tester.run_comprehensive_load_test()
        
        # Print summary
        print("\n" + "="*80)
        print("LOAD TEST RESULTS SUMMARY")
        print("="*80)
        
        result = results["results"]
        analysis = results["performance_analysis"]
        
        print(f"Total Requests: {result['total_requests']}")
        print(f"Successful Requests: {result['successful_requests']}")
        print(f"Failed Requests: {result['failed_requests']}")
        print(f"Error Rate: {result['error_rate']:.2f}%")
        print(f"Average Response Time: {result['avg_response_time']:.1f}ms")
        print(f"95th Percentile Response Time: {result['p95_response_time']:.1f}ms")
        print(f"Requests per Second: {result['requests_per_second']:.1f}")
        
        print(f"\nPerformance Target Analysis:")
        print(f"Response Time Target Met: {'✅' if analysis['response_time_target_met'] else '❌'}")
        print(f"Error Rate Acceptable: {'✅' if analysis['error_rate_acceptable'] else '❌'}")
        
        print(f"\nRecommendations:")
        for rec in results["recommendations"]:
            print(f"• {rec}")
        
        print(f"\nOverall: {'✅ PASSED' if results['summary']['passed'] else '❌ FAILED'}")
        print("="*80)
        
        return results
        
    except Exception as e:
        logger.error(f"Load test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Run the load test
    results = asyncio.run(run_production_load_test())