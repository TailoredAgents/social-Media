#!/usr/bin/env python3
"""
Infrastructure Code Validation Test
Validates that all infrastructure code is properly structured
"""
import os
import re

def test_health_check_endpoints():
    """Test health check endpoints are defined in main.py"""
    print("🔍 Testing Health Check Endpoints...")
    
    with open('backend/main.py', 'r') as f:
        content = f.read()
    
    # Check for required endpoints
    endpoints = [
        r'@app\.get\(["\']\/api\/v1\/health["\']',
        r'@app\.get\(["\']\/api\/v1\/ready["\']', 
        r'@app\.get\(["\']\/api\/v1\/live["\']',
        r'@app\.get\(["\']\/api\/v1\/metrics["\']',
        r'@app\.get\(["\']\/api\/v1\/environment["\']'
    ]
    
    results = {}
    for i, pattern in enumerate(endpoints):
        endpoint_names = ['/api/v1/health', '/api/v1/ready', '/api/v1/live', '/api/v1/metrics', '/api/v1/environment']
        found = bool(re.search(pattern, content))
        results[endpoint_names[i]] = found
        status = "✅" if found else "❌"
        print(f"  {status} {endpoint_names[i]}")
    
    return all(results.values())

def test_apm_integration():
    """Test APM service integration"""
    print("\n📊 Testing APM Service Integration...")
    
    with open('backend/main.py', 'r') as f:
        main_content = f.read()
    
    # Check APM middleware integration
    apm_checks = [
        ('APM middleware definition', r'async def apm_monitoring_middleware'),
        ('APM service startup', r'apm_service\.start_monitoring'),
        ('APM middleware import', r'from backend\.services\.apm_service import create_apm_middleware')
    ]
    
    amp_results = {}
    for name, pattern in apm_checks:
        found = bool(re.search(pattern, main_content))
        amp_results[name] = found
        status = "✅" if found else "❌"
        print(f"  {status} {name}")
    
    # Check APM service file
    apm_file_exists = os.path.exists('backend/services/apm_service.py')
    print(f"  {'✅' if apm_file_exists else '❌'} APM service file exists")
    
    if apm_file_exists:
        with open('backend/services/apm_service.py', 'r') as f:
            apm_content = f.read()
        
        prometheus_found = 'class PrometheusMetrics' in apm_content
        print(f"  {'✅' if prometheus_found else '❌'} Prometheus metrics class defined")
        amp_results['prometheus'] = prometheus_found
    
    return all(amp_results.values()) and apm_file_exists

def test_environment_validation():
    """Test environment validation system"""
    print("\n🔧 Testing Environment Validation...")
    
    # Check environment validator file
    env_file = 'backend/core/env_validator_simple.py'
    env_exists = os.path.exists(env_file)
    print(f"  {'✅' if env_exists else '❌'} Environment validator exists")
    
    if env_exists:
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        functions = [
            'def validate_environment',
            'def validate_on_startup'
        ]
        
        for func in functions:
            found = func in env_content
            print(f"  {'✅' if found else '❌'} {func}() defined")
    
    return env_exists

def test_security_infrastructure():
    """Test security infrastructure"""
    print("\n🔒 Testing Security Infrastructure...")
    
    # Check GitHub Actions workflows
    workflows_dir = '.github/workflows'
    security_workflows = []
    
    if os.path.exists(workflows_dir):
        for file in os.listdir(workflows_dir):
            if file.endswith('.yml') and any(x in file.lower() for x in ['security', 'audit', 'scan']):
                security_workflows.append(file)
    
    print(f"  ✅ Security workflows: {len(security_workflows)} found")
    for workflow in security_workflows:
        print(f"    - {workflow}")
    
    # Check security documentation
    security_md = os.path.exists('SECURITY.md')
    print(f"  {'✅' if security_md else '❌'} SECURITY.md exists")
    
    # Check CodeQL configuration
    codeql_config = os.path.exists('.github/codeql/codeql-config.yml')
    print(f"  {'✅' if codeql_config else '❌'} CodeQL configuration exists")
    
    return len(security_workflows) >= 3 and security_md

def test_bundle_monitoring():
    """Test bundle monitoring setup"""
    print("\n📦 Testing Bundle Monitoring...")
    
    scripts_dir = 'frontend/scripts'
    bundle_scripts = []
    
    if os.path.exists(scripts_dir):
        for file in os.listdir(scripts_dir):
            if 'bundle' in file.lower() and file.endswith('.js'):
                bundle_scripts.append(file)
    
    print(f"  ✅ Bundle monitoring scripts: {len(bundle_scripts)} found")
    for script in bundle_scripts:
        print(f"    - {script}")
    
    # Check vite.config.js for rollup-plugin-visualizer
    vite_config = 'frontend/vite.config.js'
    vite_has_visualizer = False
    
    if os.path.exists(vite_config):
        with open(vite_config, 'r') as f:
            vite_content = f.read()
        vite_has_visualizer = 'rollup-plugin-visualizer' in vite_content or 'visualizer' in vite_content
    
    print(f"  {'✅' if vite_has_visualizer else '❌'} Vite visualizer plugin configured")
    
    return len(bundle_scripts) >= 2 and vite_has_visualizer

if __name__ == "__main__":
    print("🚀 AI Social Media Content Agent - Infrastructure Code Validation")
    print("=" * 70)
    
    tests = [
        ("Health Check Endpoints", test_health_check_endpoints),
        ("APM Integration", test_apm_integration), 
        ("Environment Validation", test_environment_validation),
        ("Security Infrastructure", test_security_infrastructure),
        ("Bundle Monitoring", test_bundle_monitoring)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name} test failed: {e}")
            results[name] = False
    
    print("\n" + "=" * 70)
    print("📊 Infrastructure Validation Results:")
    print("-" * 35)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {name}")
        all_passed &= passed
    
    print("-" * 35)
    if all_passed:
        print("🎉 ALL INFRASTRUCTURE TESTS PASSED!")
        print("✅ Production infrastructure is properly configured")
        print("🚀 Ready for deployment!")
    else:
        print("⚠️ Some infrastructure components need attention")
        print("📋 Review failed tests before deployment")
    
    print("\n💡 Next Steps:")
    print("  1. Run security audit pipeline")
    print("  2. Test with actual FastAPI dependencies")
    print("  3. Deploy to staging environment")
    print("  4. Verify monitoring and alerts")