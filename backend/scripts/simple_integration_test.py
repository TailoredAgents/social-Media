#!/usr/bin/env python3
"""
Simple Platform Integration Test
Basic validation of integration client structure and methods

This script performs structural validation without requiring API credentials:
1. Verifies all required methods exist
2. Checks method signatures
3. Validates error handling structure
4. Tests import capabilities
5. Verifies OAuth integration points
"""
import sys
import os
import importlib
import inspect
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

class IntegrationStructureValidator:
    """Validates the structure and interface of integration clients"""
    
    def __init__(self):
        self.results = []
        self.required_methods = {
            'get_user_token': {'args': ['user_id'], 'async': True},
            'create_post': {'args': ['access_token', 'text'], 'async': True},
        }
        
        # Platform-specific required methods
        self.platform_specific_methods = {
            'twitter': ['post_tweet', 'get_user_profile', 'delete_tweet'],
            'instagram': ['get_user_profile', 'upload_media'],
            'linkedin': ['get_user_profile', 'get_company_profile'],
            'facebook': ['get_user_profile', 'get_page_info'],
            'tiktok': ['get_user_profile', 'upload_video']
        }
    
    def validate_all_integrations(self) -> Dict[str, Any]:
        """Validate all platform integrations"""
        print("🔍 Starting Integration Structure Validation")
        print("=" * 60)
        
        platforms = ['twitter', 'instagram', 'linkedin', 'facebook', 'tiktok']
        overall_results = {
            'total_platforms': len(platforms),
            'successful_validations': 0,
            'failed_validations': 0,
            'platform_results': {},
            'summary': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for platform in platforms:
            print(f"\n📱 Validating {platform.upper()} integration...")
            
            result = self._validate_platform_integration(platform)
            overall_results['platform_results'][platform] = result
            
            if result['validation_passed']:
                overall_results['successful_validations'] += 1
                print(f"   ✅ {platform.upper()}: Structure validation passed")
            else:
                overall_results['failed_validations'] += 1
                print(f"   ❌ {platform.upper()}: Structure validation failed")
                for issue in result['issues'][:3]:  # Show first 3 issues
                    print(f"      • {issue}")
        
        # Generate summary
        success_rate = (overall_results['successful_validations'] / overall_results['total_platforms']) * 100
        overall_results['summary'] = {
            'success_rate': round(success_rate, 1),
            'total_issues': sum(len(r['issues']) for r in overall_results['platform_results'].values()),
            'ready_for_testing': overall_results['successful_validations'] >= 3  # At least 3 platforms ready
        }
        
        print(f"\n📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"🎯 Success Rate: {success_rate:.1f}% ({overall_results['successful_validations']}/{overall_results['total_platforms']})")
        print(f"🔧 Total Issues: {overall_results['summary']['total_issues']}")
        print(f"🚀 Ready for Live Testing: {'Yes' if overall_results['summary']['ready_for_testing'] else 'No'}")
        
        return overall_results
    
    def _validate_platform_integration(self, platform: str) -> Dict[str, Any]:
        """Validate a specific platform integration"""
        result = {
            'platform': platform,
            'validation_passed': True,
            'issues': [],
            'warnings': [],
            'methods_found': [],
            'methods_missing': [],
            'import_status': 'failed',
            'client_instance': None,
            'structure_score': 0
        }
        
        try:
            # Test 1: Import the client module
            module_name = f"backend.integrations.{platform}_client"
            try:
                module = importlib.import_module(module_name)
                result['import_status'] = 'success'
                print(f"   ✅ Module import successful")
            except ImportError as e:
                result['issues'].append(f"Failed to import {module_name}: {str(e)}")
                result['validation_passed'] = False
                return result
            
            # Test 2: Find the client class
            client_class_name = f"{platform.title()}APIClient"
            client_instance_name = f"{platform}_client"
            
            client_class = None
            client_instance = None
            
            # Look for class
            if hasattr(module, client_class_name):
                client_class = getattr(module, client_class_name)
                print(f"   ✅ Found client class: {client_class_name}")
            else:
                # Try alternative naming
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if inspect.isclass(attr) and 'client' in attr_name.lower():
                        client_class = attr
                        print(f"   ⚠️  Found alternative client class: {attr_name}")
                        result['warnings'].append(f"Using alternative class name: {attr_name}")
                        break
            
            # Look for instance
            if hasattr(module, client_instance_name):
                client_instance = getattr(module, client_instance_name)
                result['client_instance'] = client_instance_name
                print(f"   ✅ Found client instance: {client_instance_name}")
            
            if not client_class and not client_instance:
                result['issues'].append(f"No client class or instance found for {platform}")
                result['validation_passed'] = False
                return result
            
            # Test 3: Validate required methods
            target = client_instance if client_instance else client_class
            
            for method_name, method_spec in self.required_methods.items():
                if hasattr(target, method_name):
                    method = getattr(target, method_name)
                    result['methods_found'].append(method_name)
                    
                    # Check if method is async
                    if method_spec.get('async', False):
                        if not inspect.iscoroutinefunction(method):
                            result['warnings'].append(f"{method_name} should be async")
                    
                    print(f"   ✅ Required method found: {method_name}")
                else:
                    result['methods_missing'].append(method_name)
                    result['issues'].append(f"Missing required method: {method_name}")
                    print(f"   ❌ Missing required method: {method_name}")
            
            # Test 4: Validate platform-specific methods
            platform_methods = self.platform_specific_methods.get(platform, [])
            for method_name in platform_methods:
                if hasattr(target, method_name):
                    result['methods_found'].append(method_name)
                    print(f"   ✅ Platform method found: {method_name}")
                else:
                    result['warnings'].append(f"Missing platform-specific method: {method_name}")
            
            # Test 5: Check error handling integration
            if hasattr(target, '_make_request') or hasattr(target, 'handle_error'):
                print(f"   ✅ Error handling methods present")
            else:
                result['warnings'].append("No obvious error handling methods found")
            
            # Test 6: Check OAuth integration
            oauth_methods = ['get_user_token', 'refresh_token', 'validate_token']
            oauth_found = sum(1 for method in oauth_methods if hasattr(target, method))
            if oauth_found > 0:
                print(f"   ✅ OAuth methods found: {oauth_found}/{len(oauth_methods)}")
            else:
                result['warnings'].append("No OAuth methods found")
            
            # Calculate structure score
            total_possible_score = len(self.required_methods) + len(platform_methods) + 3  # +3 for error handling, oauth, etc.
            methods_score = len(result['methods_found'])
            result['structure_score'] = round((methods_score / total_possible_score) * 100, 1)
            
            # Determine if validation passed
            critical_issues = len(result['methods_missing'])
            if critical_issues > 0:
                result['validation_passed'] = False
            
        except Exception as e:
            result['issues'].append(f"Validation error: {str(e)}")
            result['validation_passed'] = False
        
        return result
    
    def validate_oauth_integration(self) -> Dict[str, Any]:
        """Validate OAuth manager integration"""
        print(f"\n🔐 Validating OAuth Integration...")
        
        oauth_result = {
            'validation_passed': True,
            'issues': [],
            'warnings': [],
            'methods_found': [],
            'import_status': 'failed'
        }
        
        try:
            # Try to import OAuth manager
            try:
                from backend.auth.social_oauth import oauth_manager
                oauth_result['import_status'] = 'success'
                print(f"   ✅ OAuth manager import successful")
                
                # Check required methods
                required_oauth_methods = [
                    'get_user_access_token',
                    'store_user_access_token',
                    'refresh_user_token',
                    'revoke_user_token'
                ]
                
                for method_name in required_oauth_methods:
                    if hasattr(oauth_manager, method_name):
                        oauth_result['methods_found'].append(method_name)
                        print(f"   ✅ OAuth method found: {method_name}")
                    else:
                        oauth_result['warnings'].append(f"Missing OAuth method: {method_name}")
                
            except ImportError as e:
                oauth_result['issues'].append(f"Failed to import OAuth manager: {str(e)}")
                oauth_result['validation_passed'] = False
                
        except Exception as e:
            oauth_result['issues'].append(f"OAuth validation error: {str(e)}")
            oauth_result['validation_passed'] = False
        
        return oauth_result
    
    def validate_error_handling(self) -> Dict[str, Any]:
        """Validate error handling integration"""
        print(f"\n🚨 Validating Error Handling...")
        
        error_result = {
            'validation_passed': True,
            'issues': [],
            'warnings': [],
            'features_found': [],
            'import_status': 'failed'
        }
        
        try:
            # Try to import error handler
            try:
                from backend.integrations.integration_error_handler import integration_error_handler
                error_result['import_status'] = 'success'
                print(f"   ✅ Error handler import successful")
                
                # Check features
                error_features = [
                    'handle_error_with_retry',
                    'classify_error',
                    'should_retry',
                    'record_failure',
                    'record_success',
                    'get_health_status'
                ]
                
                for feature_name in error_features:
                    if hasattr(integration_error_handler, feature_name):
                        error_result['features_found'].append(feature_name)
                        print(f"   ✅ Error handling feature: {feature_name}")
                    else:
                        error_result['warnings'].append(f"Missing error feature: {feature_name}")
                
            except ImportError as e:
                error_result['issues'].append(f"Failed to import error handler: {str(e)}")
                error_result['validation_passed'] = False
                
        except Exception as e:
            error_result['issues'].append(f"Error handling validation error: {str(e)}")
            error_result['validation_passed'] = False
        
        return error_result

def main():
    """Main validation function"""
    try:
        validator = IntegrationStructureValidator()
        
        # Validate main integrations
        integration_results = validator.validate_all_integrations()
        
        # Validate supporting systems
        oauth_results = validator.validate_oauth_integration()
        error_results = validator.validate_error_handling()
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT")
        print("=" * 60)
        
        total_systems = 3  # integrations, oauth, error handling
        working_systems = 0
        
        if integration_results['summary']['ready_for_testing']:
            working_systems += 1
            print("✅ Platform Integrations: Ready for live testing")
        else:
            print("❌ Platform Integrations: Need fixes before testing")
        
        if oauth_results['validation_passed']:
            working_systems += 1
            print("✅ OAuth System: Ready")
        else:
            print("❌ OAuth System: Issues found")
        
        if error_results['validation_passed']:
            working_systems += 1
            print("✅ Error Handling: Ready")
        else:
            print("❌ Error Handling: Issues found")
        
        system_health = (working_systems / total_systems) * 100
        print(f"\n🏥 System Health: {system_health:.1f}%")
        
        if system_health >= 80:
            print("🚀 RECOMMENDATION: Proceed with live API testing")
            return 0
        elif system_health >= 60:
            print("⚠️  RECOMMENDATION: Fix critical issues then proceed with testing")
            return 1
        else:
            print("🚨 RECOMMENDATION: Address major structural issues before testing")
            return 2
            
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)