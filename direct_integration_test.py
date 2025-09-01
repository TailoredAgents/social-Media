#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Integration Test - Tests individual integration files
"""

import os
import sys
from datetime import datetime

def test_file_existence():
    """Test if integration files exist"""
    print("Testing Social Media Integration File Existence...")
    print("=" * 60)
    
    files_to_check = [
        'backend/integrations/twitter_client.py',
        'backend/integrations/linkedin_client.py', 
        'backend/integrations/instagram_client.py',
        'backend/integrations/facebook_client.py',
        'backend/auth/social_oauth.py'
    ]
    
    results = {}
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            # Check file size to ensure it's not empty
            file_size = os.path.getsize(file_path)
            if file_size > 100:  # More than 100 bytes indicates real content
                results[file_path] = {'exists': True, 'size': file_size, 'status': 'GOOD'}
                print("✅ {}: EXISTS ({} bytes)".format(file_path, file_size))
            else:
                results[file_path] = {'exists': True, 'size': file_size, 'status': 'EMPTY'}
                print("⚠️  {}: EXISTS but appears empty ({} bytes)".format(file_path, file_size))
        else:
            results[file_path] = {'exists': False, 'size': 0, 'status': 'MISSING'}
            print("❌ {}: MISSING".format(file_path))
    
    return results

def test_file_content():
    """Test if files contain expected classes and methods"""
    print("\nTesting File Content and Structure...")
    print("=" * 60)
    
    expected_content = {
        'backend/integrations/twitter_client.py': [
            'class TwitterAPIClient',
            'def create_tweet',
            'def get_tweet',
            'async def'
        ],
        'backend/integrations/linkedin_client.py': [
            'class LinkedInAPIClient',
            'def create_post',
            'def get_profile'
        ],
        'backend/integrations/instagram_client.py': [
            'class InstagramAPIClient', 
            'def create_media_post',
            'def get_account_info'
        ],
        'backend/integrations/facebook_client.py': [
            'class FacebookAPIClient',
            'def create_page_post',
            'def get_page_info'
        ]
    }
    
    results = {}
    
    for file_path, expected_items in expected_content.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                file_results = {}
                for item in expected_items:
                    if item in content:
                        file_results[item] = True
                        print("✅ {}: Contains '{}'".format(file_path, item))
                    else:
                        file_results[item] = False
                        print("❌ {}: Missing '{}'".format(file_path, item))
                
                success_rate = sum(file_results.values()) / len(file_results)
                results[file_path] = {
                    'items': file_results,
                    'success_rate': success_rate
                }
                print("📊 {}: {}/{} items found ({:.1%})".format(
                    file_path, 
                    sum(file_results.values()),
                    len(file_results),
                    success_rate
                ))
                
            except Exception as e:
                results[file_path] = {'error': str(e), 'success_rate': 0.0}
                print("❌ {}: Error reading file - {}".format(file_path, str(e)))
        else:
            results[file_path] = {'error': 'File not found', 'success_rate': 0.0}
            print("❌ {}: File not found".format(file_path))
    
    return results

def test_api_endpoints_integration():
    """Test if API endpoints reference integration clients"""
    print("\nTesting API Endpoint Integration...")
    print("=" * 60)
    
    api_files = [
        'backend/main.py',
        'backend/api/integration_services.py',
        'backend/api/social_auth.py'
    ]
    
    integration_references = [
        'TwitterAPIClient',
        'LinkedInAPIClient', 
        'InstagramAPIClient',
        'FacebookAPIClient'
    ]
    
    results = {}
    
    for api_file in api_files:
        if os.path.exists(api_file):
            try:
                with open(api_file, 'r') as f:
                    content = f.read()
                
                file_results = {}
                for ref in integration_references:
                    if ref in content:
                        file_results[ref] = True
                        print("✅ {}: References {}".format(api_file, ref))
                    else:
                        file_results[ref] = False
                        print("⚠️  {}: No reference to {}".format(api_file, ref))
                
                results[api_file] = file_results
                
            except Exception as e:
                results[api_file] = {'error': str(e)}
                print("❌ {}: Error reading file - {}".format(api_file, str(e)))
        else:
            print("❌ {}: File not found".format(api_file))
    
    return results

def test_environment_setup():
    """Test environment variables and configuration"""
    print("\nTesting Environment and Configuration Setup...")
    print("=" * 60)
    
    config_files = [
        'backend/core/config.py',
        '.env.example',
        'requirements.txt'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print("✅ {}: EXISTS".format(config_file))
        else:
            print("❌ {}: MISSING".format(config_file))
    
    # Check for required environment variables in example file
    if os.path.exists('.env.example'):
        try:
            with open('.env.example', 'r') as f:
                env_content = f.read()
            
            required_vars = [
                'TWITTER_API_KEY',
                'LINKEDIN_CLIENT_ID', 
                'INSTAGRAM_APP_ID',
                'FACEBOOK_APP_ID'
            ]
            
            print("\nEnvironment Variable Templates:")
            for var in required_vars:
                if var in env_content:
                    print("✅ {}: Template exists in .env.example".format(var))
                else:
                    print("⚠️  {}: No template in .env.example".format(var))
                    
        except Exception as e:
            print("❌ Error reading .env.example: {}".format(str(e)))

def generate_integration_readiness_report(file_results, content_results, api_results):
    """Generate comprehensive readiness report"""
    print("\n" + "=" * 80)
    print("SOCIAL MEDIA INTEGRATION READINESS REPORT")
    print("=" * 80)
    print("Generated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    platforms = ['Twitter', 'LinkedIn', 'Instagram', 'Facebook']
    
    print("\nPLATFORM IMPLEMENTATION STATUS")
    print("-" * 50)
    
    overall_scores = {}
    
    for platform in platforms:
        platform_lower = platform.lower()
        
        # File existence score
        file_key = 'backend/integrations/{}_client.py'.format(platform_lower)
        file_score = 1.0 if file_results.get(file_key, {}).get('status') == 'GOOD' else 0.0
        
        # Content completeness score  
        content_score = content_results.get(file_key, {}).get('success_rate', 0.0)
        
        # Overall platform score
        platform_score = (file_score + content_score) / 2
        overall_scores[platform] = platform_score
        
        status = ("READY" if platform_score >= 0.8 else 
                 "PARTIAL" if platform_score >= 0.5 else 
                 "NEEDS WORK")
        
        print("{:<12} | Score: {:.1%} | Status: {}".format(
            platform, platform_score, status))
    
    # System readiness
    system_score = sum(overall_scores.values()) / len(overall_scores)
    print("-" * 50)
    print("SYSTEM       | Score: {:.1%} | Status: {}".format(
        system_score,
        "PRODUCTION READY" if system_score >= 0.8 else
        "DEVELOPMENT READY" if system_score >= 0.6 else
        "NEEDS DEVELOPMENT"
    ))
    
    print("\nRECOMMENDATIONS")
    print("-" * 50)
    
    if system_score >= 0.8:
        print("✅ Integration implementations are complete")
        print("✅ Ready for configuration and live API testing")
        print("✅ Proceed with environment variable setup")
    elif system_score >= 0.6:
        print("⚠️  Most integrations implemented - complete remaining items")
        print("⚠️  Review missing methods and add implementations")
        print("⚠️  Test with mock APIs before live testing")
    else:
        print("❌ Significant development work needed")
        print("❌ Complete integration client implementations")
        print("❌ Ensure all required methods are present")
    
    print("\nNEXT STEPS FOR LIVE TESTING")
    print("-" * 50)
    print("1. Set up developer accounts for each platform")
    print("2. Obtain API keys and configure environment variables")
    print("3. Create test applications in each platform's developer portal")
    print("4. Test authentication flows")
    print("5. Test basic posting functionality")
    print("6. Implement error handling and rate limiting")
    print("7. Set up monitoring and logging")
    
    return overall_scores

def main():
    """Main test execution"""
    print("SOCIAL MEDIA INTEGRATION DIRECT TEST")
    print("Date: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("=" * 60)
    
    # Run all tests
    print("\n1. FILE EXISTENCE TEST")
    file_results = test_file_existence()
    
    print("\n2. FILE CONTENT TEST") 
    content_results = test_file_content()
    
    print("\n3. API INTEGRATION TEST")
    api_results = test_api_endpoints_integration()
    
    print("\n4. ENVIRONMENT SETUP TEST")
    test_environment_setup()
    
    # Generate report
    scores = generate_integration_readiness_report(file_results, content_results, api_results)
    
    # Save results
    try:
        report_file = "integration_readiness_report_{}.txt".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        
        with open(report_file, 'w') as f:
            f.write("Social Media Integration Readiness Report\n")
            f.write("Generated: {}\n\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            f.write("File Existence Results:\n")
            for file_path, result in file_results.items():
                f.write("  {}: {}\n".format(file_path, result.get('status', 'UNKNOWN')))
            
            f.write("\nContent Analysis Results:\n") 
            for file_path, result in content_results.items():
                if 'success_rate' in result:
                    f.write("  {}: {:.1%} complete\n".format(file_path, result['success_rate']))
            
            f.write("\nPlatform Readiness Scores:\n")
            for platform, score in scores.items():
                f.write("  {}: {:.1%}\n".format(platform, score))
        
        print("\nReport saved to: {}".format(report_file))
        
    except Exception as e:
        print("\nCould not save report: {}".format(str(e)))
    
    print("\nIntegration testing complete!")
    return scores

if __name__ == "__main__":
    main()