#!/usr/bin/env python3
"""
Comprehensive Project Health Check
Tests all major systems, APIs, databases, and configurations
"""

import os
import sys
import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from sqlalchemy import create_engine, text, inspect
    from core.config import get_settings
    from db.models import Base
    import importlib
except ImportError as e:
    print(f"Warning: Could not import backend modules: {e}")

class HealthChecker:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'unknown',
            'categories': {},
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_comprehensive_check(self):
        """Run all health checks"""
        print("🔍 Starting Comprehensive Project Health Check...")
        print("=" * 60)
        
        checks = [
            ("Environment Configuration", self.check_environment),
            ("Database Health", self.check_database),
            ("API Endpoints", self.check_api_endpoints),
            ("Frontend Build", self.check_frontend),
            ("Dependencies", self.check_dependencies),
            ("File Structure", self.check_file_structure),
            ("Security Configuration", self.check_security),
            ("Performance Indicators", self.check_performance)
        ]
        
        for category, check_func in checks:
            print(f"\n📊 Checking {category}...")
            try:
                result = await check_func()
                self.results['categories'][category] = result
                self.print_category_result(category, result)
            except Exception as e:
                error_result = {
                    'status': 'error',
                    'issues': [f"Failed to run check: {str(e)}"],
                    'score': 0
                }
                self.results['categories'][category] = error_result
                self.results['critical_issues'].append(f"{category}: {str(e)}")
        
        self.calculate_overall_health()
        self.generate_report()
    
    def print_category_result(self, category, result):
        status = result.get('status', 'unknown')
        score = result.get('score', 0)
        
        if status == 'healthy':
            print(f"  ✅ {category}: {status.upper()} (Score: {score}/100)")
        elif status == 'warning':
            print(f"  ⚠️  {category}: {status.upper()} (Score: {score}/100)")
        else:
            print(f"  ❌ {category}: {status.upper()} (Score: {score}/100)")
        
        if result.get('issues'):
            for issue in result['issues'][:3]:  # Show first 3 issues
                print(f"     • {issue}")
    
    async def check_environment(self) -> Dict[str, Any]:
        """Check environment configuration"""
        issues = []
        warnings = []
        score = 100
        
        # Check environment files
        env_files = ['.env', 'backend/.env', 'frontend/.env']
        for env_file in env_files:
            if not os.path.exists(env_file):
                warnings.append(f"Missing {env_file}")
        
        # Check critical environment variables
        critical_vars = [
            'DATABASE_URL', 'OPENAI_API_KEY', 'JWT_SECRET_KEY',
            'FRONTEND_URL', 'BACKEND_URL'
        ]
        
        try:
            settings = get_settings()
            for var in critical_vars:
                if not hasattr(settings, var.lower()) or not getattr(settings, var.lower(), None):
                    issues.append(f"Missing or empty: {var}")
                    score -= 15
        except Exception as e:
            issues.append(f"Cannot load settings: {str(e)}")
            score -= 30
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(f"Python version too old: {python_version}")
            score -= 20
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings,
            'details': {
                'python_version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                'environment_files_found': [f for f in env_files if os.path.exists(f)]
            }
        }
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connection and schema"""
        issues = []
        warnings = []
        score = 100
        
        try:
            settings = get_settings()
            engine = create_engine(settings.database_url)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Check if tables exist
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            # Expected critical tables
            critical_tables = [
                'users', 'user_settings', 'content_logs', 'social_platform_connections',
                'notifications', 'social_posts', 'milestones'
            ]
            
            missing_tables = [table for table in critical_tables if table not in existing_tables]
            if missing_tables:
                for table in missing_tables:
                    issues.append(f"Missing table: {table}")
                    score -= 10
            
            # Check table schemas for critical tables
            for table in ['users', 'user_settings']:
                if table in existing_tables:
                    try:
                        columns = [col['name'] for col in inspector.get_columns(table)]
                        if table == 'users' and 'email' not in columns:
                            issues.append(f"Users table missing email column")
                            score -= 15
                        if table == 'user_settings' and 'brand_voice' not in columns:
                            warnings.append(f"user_settings table may be incomplete")
                    except Exception as e:
                        warnings.append(f"Could not inspect {table}: {str(e)}")
            
        except Exception as e:
            issues.append(f"Database connection failed: {str(e)}")
            score = 0
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 40 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings,
            'details': {
                'tables_found': len(existing_tables) if 'existing_tables' in locals() else 0,
                'missing_critical_tables': missing_tables if 'missing_tables' in locals() else []
            }
        }
    
    async def check_api_endpoints(self) -> Dict[str, Any]:
        """Test critical API endpoints"""
        issues = []
        warnings = []
        score = 100
        
        # Critical endpoints to test
        endpoints = [
            ('GET', '/health', 'Health check'),
            ('GET', '/api/content/', 'Content API'),
            ('GET', '/api/user-settings/', 'User Settings'),
            ('GET', '/api/notifications/', 'Notifications'),
            ('GET', '/api/memory/', 'Memory API'),
            ('GET', '/api/social/connections', 'Social Connections'),
            ('POST', '/api/ai/suggestions', 'AI Suggestions')
        ]
        
        base_url = 'https://socialmedia-api-wxip.onrender.com'  # Production URL
        
        async with aiohttp.ClientSession() as session:
            for method, endpoint, description in endpoints:
                try:
                    if method == 'GET':
                        async with session.get(f"{base_url}{endpoint}", timeout=10) as response:
                            status_code = response.status
                    else:  # POST
                        payload = {'type': 'content', 'context': {}, 'limit': 4} if 'suggestions' in endpoint else {}
                        async with session.post(f"{base_url}{endpoint}", json=payload, timeout=15) as response:
                            status_code = response.status
                    
                    if status_code >= 500:
                        issues.append(f"{description} ({endpoint}): {status_code} error")
                        score -= 15
                    elif status_code >= 400:
                        warnings.append(f"{description} ({endpoint}): {status_code} client error")
                        score -= 5
                    
                except asyncio.TimeoutError:
                    issues.append(f"{description} ({endpoint}): Timeout")
                    score -= 10
                except Exception as e:
                    issues.append(f"{description} ({endpoint}): {str(e)}")
                    score -= 10
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 50 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings,
            'details': {
                'endpoints_tested': len(endpoints),
                'base_url': base_url
            }
        }
    
    async def check_frontend(self) -> Dict[str, Any]:
        """Check frontend build and configuration"""
        issues = []
        warnings = []
        score = 100
        
        frontend_path = Path('frontend')
        if not frontend_path.exists():
            issues.append("Frontend directory not found")
            return {'status': 'critical', 'score': 0, 'issues': issues}
        
        # Check package.json
        package_json_path = frontend_path / 'package.json'
        if not package_json_path.exists():
            issues.append("package.json not found")
            score -= 20
        else:
            try:
                with open(package_json_path) as f:
                    package_data = json.load(f)
                    if 'build' not in package_data.get('scripts', {}):
                        warnings.append("No build script in package.json")
            except Exception as e:
                warnings.append(f"Could not parse package.json: {str(e)}")
        
        # Check for critical files
        critical_files = [
            'src/main.jsx',
            'src/App.jsx', 
            'src/services/api.js',
            'vite.config.js',
            'index.html'
        ]
        
        for file in critical_files:
            if not (frontend_path / file).exists():
                issues.append(f"Missing critical file: {file}")
                score -= 10
        
        # Check node_modules
        if not (frontend_path / 'node_modules').exists():
            warnings.append("node_modules not found - may need npm install")
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings,
            'details': {
                'frontend_path': str(frontend_path.absolute()),
                'critical_files_found': [f for f in critical_files if (frontend_path / f).exists()]
            }
        }
    
    async def check_dependencies(self) -> Dict[str, Any]:
        """Check Python and Node dependencies"""
        issues = []
        warnings = []
        score = 100
        
        # Check Python requirements
        requirements_files = ['requirements.txt', 'backend/requirements.txt']
        python_reqs_found = any(os.path.exists(f) for f in requirements_files)
        
        if not python_reqs_found:
            issues.append("No requirements.txt found")
            score -= 20
        
        # Check if critical Python packages are importable
        critical_packages = [
            'fastapi', 'sqlalchemy', 'pydantic', 'openai', 
            'psycopg2', 'alembic', 'uvicorn'
        ]
        
        for package in critical_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                issues.append(f"Missing Python package: {package}")
                score -= 8
        
        # Check Node package.json
        if os.path.exists('frontend/package.json'):
            try:
                with open('frontend/package.json') as f:
                    package_data = json.load(f)
                    deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                    
                    critical_node_packages = ['react', 'vite', '@heroicons/react', 'tailwindcss']
                    for package in critical_node_packages:
                        if package not in deps:
                            warnings.append(f"Missing Node package: {package}")
                            score -= 5
            except Exception as e:
                warnings.append(f"Could not parse frontend package.json: {str(e)}")
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings
        }
    
    async def check_file_structure(self) -> Dict[str, Any]:
        """Check critical file structure"""
        issues = []
        warnings = []
        score = 100
        
        critical_paths = [
            'backend/',
            'backend/api/',
            'backend/db/',
            'backend/core/',
            'frontend/src/',
            'frontend/src/pages/',
            'frontend/src/components/',
            'alembic/',
            'alembic/versions/'
        ]
        
        for path in critical_paths:
            if not os.path.exists(path):
                issues.append(f"Missing critical directory: {path}")
                score -= 10
        
        # Check for configuration files
        config_files = [
            'alembic.ini',
            'frontend/vite.config.js',
            'frontend/tailwind.config.js'
        ]
        
        for file in config_files:
            if not os.path.exists(file):
                warnings.append(f"Missing config file: {file}")
                score -= 5
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings
        }
    
    async def check_security(self) -> Dict[str, Any]:
        """Check security configuration"""
        issues = []
        warnings = []
        score = 100
        
        # Check for sensitive files in repo
        sensitive_patterns = ['.env', '*.key', '*.pem', 'secrets.*']
        
        # This is a basic check - in a real scenario you'd use gitignore patterns
        if os.path.exists('.env'):
            warnings.append(".env file present - ensure it's in .gitignore")
        
        # Check gitignore
        if not os.path.exists('.gitignore'):
            issues.append("Missing .gitignore file")
            score -= 15
        else:
            with open('.gitignore') as f:
                gitignore_content = f.read()
                if '.env' not in gitignore_content:
                    issues.append(".env not in .gitignore")
                    score -= 20
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings
        }
    
    async def check_performance(self) -> Dict[str, Any]:
        """Check performance indicators"""
        issues = []
        warnings = []
        score = 100
        
        # This would include checks for:
        # - Large files in repo
        # - Database query performance
        # - API response times (partially done in API check)
        
        # Check for large files
        large_files = []
        for root, dirs, files in os.walk('.'):
            # Skip common large directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    if size > 10 * 1024 * 1024:  # 10MB
                        large_files.append(f"{filepath}: {size // 1024 // 1024}MB")
                except:
                    continue
        
        if large_files:
            for file_info in large_files[:5]:  # Show first 5
                warnings.append(f"Large file: {file_info}")
                score -= 5
        
        status = 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical'
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'warnings': warnings,
            'details': {
                'large_files_found': len(large_files)
            }
        }
    
    def calculate_overall_health(self):
        """Calculate overall project health"""
        total_score = 0
        total_weight = 0
        
        # Weighted scoring
        weights = {
            'Environment Configuration': 15,
            'Database Health': 25,
            'API Endpoints': 20,
            'Frontend Build': 15,
            'Dependencies': 10,
            'File Structure': 5,
            'Security Configuration': 5,
            'Performance Indicators': 5
        }
        
        for category, result in self.results['categories'].items():
            weight = weights.get(category, 5)
            score = result.get('score', 0)
            total_score += score * weight
            total_weight += weight
            
            # Collect critical issues
            if result.get('status') == 'critical':
                self.results['critical_issues'].extend([
                    f"{category}: {issue}" for issue in result.get('issues', [])
                ])
            elif result.get('status') == 'warning':
                self.results['warnings'].extend([
                    f"{category}: {warning}" for warning in result.get('warnings', [])
                ])
        
        overall_score = (total_score / total_weight) if total_weight > 0 else 0
        
        if overall_score >= 85:
            self.results['overall_health'] = 'excellent'
        elif overall_score >= 70:
            self.results['overall_health'] = 'good'
        elif overall_score >= 50:
            self.results['overall_health'] = 'fair'
        else:
            self.results['overall_health'] = 'poor'
        
        self.results['overall_score'] = round(overall_score, 1)
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE HEALTH CHECK REPORT")
        print("=" * 60)
        
        # Overall health
        health_emoji = {
            'excellent': '🟢',
            'good': '🟡', 
            'fair': '🟠',
            'poor': '🔴'
        }
        
        overall = self.results['overall_health']
        score = self.results['overall_score']
        
        print(f"\n{health_emoji.get(overall, '⚪')} OVERALL HEALTH: {overall.upper()} ({score}/100)")
        
        # Critical issues
        if self.results['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.results['critical_issues'])}):")
            for issue in self.results['critical_issues'][:10]:
                print(f"  ❌ {issue}")
        
        # Warnings
        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results['warnings'][:10]:
                print(f"  ⚠️  {warning}")
        
        # Generate recommendations
        self.generate_recommendations()
        
        if self.results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.results['recommendations'][:10], 1):
                print(f"  {i}. {rec}")
        
        # Save detailed report
        report_file = f"health_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print("=" * 60)
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Database recommendations
        db_result = self.results['categories'].get('Database Health', {})
        if db_result.get('status') in ['critical', 'warning']:
            if any('Missing table' in issue for issue in db_result.get('issues', [])):
                recommendations.append("Run database migrations: `alembic upgrade head`")
            if any('connection failed' in issue.lower() for issue in db_result.get('issues', [])):
                recommendations.append("Check database connection string and ensure database server is running")
        
        # API recommendations  
        api_result = self.results['categories'].get('API Endpoints', {})
        if api_result.get('status') in ['critical', 'warning']:
            recommendations.append("Investigate failing API endpoints - check logs for specific errors")
            recommendations.append("Verify all required environment variables are set")
        
        # Frontend recommendations
        frontend_result = self.results['categories'].get('Frontend Build', {})
        if frontend_result.get('status') in ['critical', 'warning']:
            recommendations.append("Run `npm install` in frontend directory")
            recommendations.append("Test frontend build with `npm run build`")
        
        # Dependencies recommendations
        deps_result = self.results['categories'].get('Dependencies', {})
        if deps_result.get('status') in ['critical', 'warning']:
            recommendations.append("Install missing Python packages: `pip install -r requirements.txt`")
            recommendations.append("Update frontend dependencies: `npm install` in frontend/")
        
        # Environment recommendations
        env_result = self.results['categories'].get('Environment Configuration', {})
        if env_result.get('status') in ['critical', 'warning']:
            recommendations.append("Create and configure .env file with all required variables")
            recommendations.append("Check environment variable documentation in README")
        
        # Security recommendations
        sec_result = self.results['categories'].get('Security Configuration', {})
        if sec_result.get('status') in ['critical', 'warning']:
            recommendations.append("Add sensitive files to .gitignore")
            recommendations.append("Review security configuration and secrets management")
        
        self.results['recommendations'] = recommendations

async def main():
    """Run comprehensive health check"""
    checker = HealthChecker()
    await checker.run_comprehensive_check()

if __name__ == "__main__":
    asyncio.run(main())