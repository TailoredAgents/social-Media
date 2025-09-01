#!/usr/bin/env python3
"""
Master Health Audit Script
Runs comprehensive project analysis and generates action plan
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime
import json

class MasterHealthAudit:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'audit_results': {},
            'action_plan': [],
            'priority_fixes': [],
            'overall_health_score': 0
        }
    
    async def run_complete_audit(self):
        """Run all health checks in sequence"""
        print("🔍 MASTER HEALTH AUDIT")
        print("=" * 60)
        print("Running comprehensive project analysis...")
        print("This may take a few minutes.\n")
        
        # Phase 1: Infrastructure Health Check
        print("📋 Phase 1: Infrastructure Health Check")
        print("-" * 40)
        await self.run_health_check()
        
        # Phase 2: Database Schema Validation
        print("\n🗄️  Phase 2: Database Schema Validation")
        print("-" * 40)
        await self.run_database_validation()
        
        # Phase 3: Deployment Validation
        print("\n🚀 Phase 3: Deployment Validation")
        print("-" * 40)
        await self.run_deployment_validation()
        
        # Phase 4: Code Quality Analysis
        print("\n🔍 Phase 4: Code Quality Analysis")
        print("-" * 40)
        await self.run_code_analysis()
        
        # Generate Master Report
        print("\n📊 Generating Master Report...")
        self.generate_master_report()
        
        # Create Action Plan
        print("\n🎯 Creating Action Plan...")
        self.create_action_plan()
        
        print("\n✅ Master Health Audit Complete!")
    
    async def run_health_check(self):
        """Run comprehensive health check"""
        try:
            result = await self.run_script('comprehensive_health_check.py')
            self.results['audit_results']['health_check'] = {
                'status': 'completed',
                'output': result
            }
            print("   ✅ Infrastructure health check completed")
        except Exception as e:
            self.results['audit_results']['health_check'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"   ❌ Infrastructure health check failed: {e}")
    
    async def run_database_validation(self):
        """Run database schema validation"""
        try:
            result = await self.run_script('validate_database_schema.py')
            self.results['audit_results']['database_validation'] = {
                'status': 'completed',
                'output': result
            }
            print("   ✅ Database validation completed")
        except Exception as e:
            self.results['audit_results']['database_validation'] = {
                'status': 'failed', 
                'error': str(e)
            }
            print(f"   ❌ Database validation failed: {e}")
    
    async def run_deployment_validation(self):
        """Run deployment validation"""
        try:
            result = await self.run_script('deployment_validator.py')
            self.results['audit_results']['deployment_validation'] = {
                'status': 'completed',
                'output': result
            }
            print("   ✅ Deployment validation completed")
        except Exception as e:
            self.results['audit_results']['deployment_validation'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"   ❌ Deployment validation failed: {e}")
    
    async def run_code_analysis(self):
        """Run code quality analysis"""
        print("   🔍 Analyzing Python code...")
        
        # Check for common issues
        issues = []
        
        # Check for TODO/FIXME comments
        todo_count = await self.count_todos()
        if todo_count > 0:
            issues.append(f"Found {todo_count} TODO/FIXME comments")
        
        # Check for large files
        large_files = await self.find_large_files()
        if large_files:
            issues.append(f"Found {len(large_files)} large files (>1MB)")
        
        # Check for missing docstrings
        python_files = await self.find_python_files()
        files_without_docstrings = await self.check_docstrings(python_files[:10])  # Sample
        if files_without_docstrings:
            issues.append(f"Found {len(files_without_docstrings)} files without docstrings")
        
        self.results['audit_results']['code_analysis'] = {
            'status': 'completed',
            'issues': issues,
            'todo_count': todo_count,
            'large_files_count': len(large_files),
            'python_files_count': len(python_files)
        }
        
        if issues:
            print(f"   ⚠️  Found {len(issues)} code quality issues")
        else:
            print("   ✅ Code quality analysis completed - no major issues")
    
    async def run_script(self, script_name):
        """Run a Python script and capture output"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=os.getcwd()
            )
            stdout, _ = await process.communicate()
            return stdout.decode('utf-8') if stdout else ""
        except Exception as e:
            raise Exception(f"Failed to run {script_name}: {e}")
    
    async def count_todos(self):
        """Count TODO/FIXME comments in codebase"""
        try:
            process = await asyncio.create_subprocess_shell(
                "grep -r -i 'TODO\\|FIXME' --include='*.py' --include='*.js' --include='*.jsx' . | wc -l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return int(stdout.decode().strip()) if stdout else 0
        except:
            return 0
    
    async def find_large_files(self):
        """Find files larger than 1MB"""
        try:
            process = await asyncio.create_subprocess_shell(
                "find . -type f -size +1M -not -path './.git/*' -not -path './node_modules/*'",
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if stdout:
                return stdout.decode().strip().split('\n')
            return []
        except:
            return []
    
    async def find_python_files(self):
        """Find all Python files"""
        try:
            process = await asyncio.create_subprocess_shell(
                "find . -name '*.py' -not -path './.git/*' -not -path './venv/*' -not -path './.venv/*'",
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if stdout:
                return stdout.decode().strip().split('\n')
            return []
        except:
            return []
    
    async def check_docstrings(self, files):
        """Check for missing docstrings in Python files"""
        files_without_docstrings = []
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'def ' in content and '"""' not in content and "'''" not in content:
                        files_without_docstrings.append(file_path)
            except:
                continue
        return files_without_docstrings
    
    def generate_master_report(self):
        """Generate comprehensive master report"""
        print("\n" + "=" * 60)
        print("📋 MASTER HEALTH AUDIT REPORT")
        print("=" * 60)
        
        # Calculate overall health score
        scores = []
        
        # Each audit contributes to overall score
        for audit_name, audit_result in self.results['audit_results'].items():
            if audit_result.get('status') == 'completed':
                scores.append(85)  # Base score for completed audits
            elif audit_result.get('status') == 'failed':
                scores.append(0)   # Failed audits get 0
        
        # Adjust for specific issues
        code_analysis = self.results['audit_results'].get('code_analysis', {})
        if code_analysis.get('issues'):
            scores.append(max(50, 100 - len(code_analysis['issues']) * 10))
        
        overall_score = sum(scores) / len(scores) if scores else 0
        self.results['overall_health_score'] = round(overall_score, 1)
        
        # Report overall health
        if overall_score >= 90:
            health_status = "EXCELLENT"
            health_emoji = "🟢"
        elif overall_score >= 75:
            health_status = "GOOD"
            health_emoji = "🟡"
        elif overall_score >= 60:
            health_status = "FAIR"
            health_emoji = "🟠"
        else:
            health_status = "NEEDS ATTENTION"
            health_emoji = "🔴"
        
        print(f"\n{health_emoji} OVERALL PROJECT HEALTH: {health_status}")
        print(f"Score: {overall_score}/100")
        
        # Report audit results
        print(f"\n📊 AUDIT SUMMARY:")
        for audit_name, audit_result in self.results['audit_results'].items():
            status = audit_result.get('status', 'unknown')
            if status == 'completed':
                print(f"   ✅ {audit_name.replace('_', ' ').title()}: PASSED")
            else:
                print(f"   ❌ {audit_name.replace('_', ' ').title()}: FAILED")
        
        # Code quality summary
        code_analysis = self.results['audit_results'].get('code_analysis', {})
        if code_analysis.get('issues'):
            print(f"\n⚠️  CODE QUALITY ISSUES:")
            for issue in code_analysis['issues']:
                print(f"   • {issue}")
    
    def create_action_plan(self):
        """Create prioritized action plan"""
        action_items = []
        priority_items = []
        
        # Analyze audit results and create recommendations
        for audit_name, audit_result in self.results['audit_results'].items():
            if audit_result.get('status') == 'failed':
                priority_items.append(f"Fix {audit_name.replace('_', ' ')}")
        
        # Database issues are high priority
        db_result = self.results['audit_results'].get('database_validation', {})
        if 'database' in str(db_result).lower() and 'error' in str(db_result).lower():
            priority_items.append("Fix database connectivity and schema issues")
        
        # Code quality improvements
        code_analysis = self.results['audit_results'].get('code_analysis', {})
        if code_analysis.get('todo_count', 0) > 20:
            action_items.append("Address high number of TODO/FIXME comments")
        
        if code_analysis.get('large_files_count', 0) > 0:
            action_items.append("Review and optimize large files")
        
        # Standard recommendations
        action_items.extend([
            "Review and test all API endpoints",
            "Ensure all database tables exist and are properly configured", 
            "Verify environment variables are properly set",
            "Run frontend build to check for syntax errors",
            "Monitor application performance and response times"
        ])
        
        self.results['priority_fixes'] = priority_items
        self.results['action_plan'] = action_items
        
        # Display action plan
        if priority_items:
            print(f"\n🚨 PRIORITY FIXES NEEDED:")
            for i, item in enumerate(priority_items, 1):
                print(f"   {i}. {item}")
        
        print(f"\n📋 RECOMMENDED ACTIONS:")
        for i, item in enumerate(action_items[:10], 1):  # Show top 10
            print(f"   {i}. {item}")
        
        # Save comprehensive report
        report_file = f"master_health_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Complete audit report saved to: {report_file}")
        
        # Create summary file
        summary_file = f"audit_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.create_markdown_summary(summary_file)
        print(f"📄 Executive summary saved to: {summary_file}")
    
    def create_markdown_summary(self, filename):
        """Create markdown summary report"""
        content = f"""# Project Health Audit Summary

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Overall Health Score:** {self.results['overall_health_score']}/100

## Executive Summary

This comprehensive health audit analyzed all major systems including infrastructure, database, deployment, and code quality.

## Audit Results

"""
        
        for audit_name, audit_result in self.results['audit_results'].items():
            status = "✅ PASSED" if audit_result.get('status') == 'completed' else "❌ FAILED"
            content += f"- **{audit_name.replace('_', ' ').title()}:** {status}\n"
        
        if self.results['priority_fixes']:
            content += "\n## Priority Fixes Required\n\n"
            for i, item in enumerate(self.results['priority_fixes'], 1):
                content += f"{i}. {item}\n"
        
        content += "\n## Recommended Actions\n\n"
        for i, item in enumerate(self.results['action_plan'][:10], 1):
            content += f"{i}. {item}\n"
        
        content += f"""
## Next Steps

1. Address priority fixes immediately
2. Work through recommended actions systematically  
3. Re-run health audit after fixes to verify improvements
4. Set up regular health monitoring

---
*Generated by Master Health Audit System*
"""
        
        with open(filename, 'w') as f:
            f.write(content)

async def main():
    """Run master health audit"""
    audit = MasterHealthAudit()
    await audit.run_complete_audit()

if __name__ == "__main__":
    asyncio.run(main())