#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Social Media Integration Test
Tests the basic functionality of social media platform integrations
"""

import sys
import os
import importlib
from datetime import datetime

# Add the project root to sys.path
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

def test_module_imports():
    """Test if all integration modules can be imported successfully"""
    print("🧪 Testing Social Media Integration Module Imports...")
    print("=" * 60)
    
    modules_to_test = [
        ('backend.integrations.twitter_client', 'TwitterAPIClient'),
        ('backend.integrations.linkedin_client', 'LinkedInAPIClient'),
        ('backend.integrations.instagram_client', 'InstagramAPIClient'),
        ('backend.integrations.facebook_client', 'FacebookAPIClient'),
        ('backend.auth.social_oauth', 'oauth_manager')
    ]
    
    results = {}
    
    for module_path, class_name in modules_to_test:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                results[module_path] = {'status': 'SUCCESS', 'class': class_name}
                print("✅ {}: {} imported successfully".format(module_path, class_name))
            else:
                results[module_path] = {'status': 'PARTIAL', 'error': 'Class {} not found'.format(class_name)}
                print("⚠️  {}: Module imported but {} not found".format(module_path, class_name))
        except ImportError as e:
            results[module_path] = {'status': 'FAILED', 'error': str(e)}
            print("❌ {}: Import failed - {}".format(module_path, str(e)))
        except Exception as e:
            results[module_path] = {'status': 'ERROR', 'error': str(e)}
            print("❌ {}: Unexpected error - {}".format(module_path, str(e)))
    
    return results

def test_client_instantiation():
    """Test if client classes can be instantiated"""
    print("\n🏗️  Testing Client Class Instantiation...")
    print("=" * 60)
    
    clients = {}
    
    try:
        from backend.integrations.twitter_client import TwitterAPIClient
        clients['Twitter'] = TwitterAPIClient()
        print("✅ Twitter client instantiated successfully")
    except Exception as e:
        print("❌ Twitter client failed: {}".format(str(e)))
    
    try:
        from backend.integrations.linkedin_client import LinkedInAPIClient
        clients['LinkedIn'] = LinkedInAPIClient()
        print("✅ LinkedIn client instantiated successfully")
    except Exception as e:
        print("❌ LinkedIn client failed: {}".format(str(e)))
    
    try:
        from backend.integrations.instagram_client import InstagramAPIClient
        clients['Instagram'] = InstagramAPIClient()
        print("✅ Instagram client instantiated successfully") 
    except Exception as e:
        print("❌ Instagram client failed: {}".format(str(e)))
    
    try:
        from backend.integrations.facebook_client import FacebookAPIClient
        clients['Facebook'] = FacebookAPIClient()
        print("✅ Facebook client instantiated successfully")
    except Exception as e:
        print("❌ Facebook client failed: {}".format(str(e)))
    
    return clients

def test_client_methods(clients):
    """Test if required methods exist on client instances"""
    print("\n🔍 Testing Client Method Availability...")
    print("=" * 60)
    
    required_methods = {
        'Twitter': ['create_tweet', 'get_tweet', 'delete_tweet', 'get_user_timeline'],
        'LinkedIn': ['create_post', 'get_profile', 'get_post_analytics'],
        'Instagram': ['create_media_post', 'get_account_info', 'get_media_insights'],
        'Facebook': ['create_page_post', 'get_page_info', 'get_post_insights']
    }
    
    results = {}
    
    for platform, client in clients.items():
        if platform in required_methods:
            platform_results = {}
            methods = required_methods[platform]
            
            for method in methods:
                if hasattr(client, method):
                    platform_results[method] = True
                    print("✅ {}: {} method available".format(platform, method))
                else:
                    platform_results[method] = False
                    print("❌ {}: {} method missing".format(platform, method))
            
            success_rate = sum(platform_results.values()) / len(platform_results)
            results[platform] = {
                'methods': platform_results,
                'success_rate': success_rate
            }
            print("📊 {}: {}/{} methods available ({:.1%})".format(
                platform, 
                sum(platform_results.values()), 
                len(platform_results),
                success_rate
            ))
        else:
            print("⚠️  {}: No method requirements defined".format(platform))
    
    return results

def test_configuration_availability():
    """Test if required configuration is available"""
    print("\n⚙️  Testing Configuration Availability...")
    print("=" * 60)
    
    required_env_vars = {
        'Twitter': ['TWITTER_API_KEY', 'TWITTER_API_SECRET', 'TWITTER_BEARER_TOKEN'],
        'LinkedIn': ['LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET'],
        'Instagram': ['INSTAGRAM_APP_ID', 'INSTAGRAM_APP_SECRET'],
        'Facebook': ['FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET']
    }
    
    config_status = {}
    
    for platform, env_vars in required_env_vars.items():
        platform_config = {}
        for var in env_vars:
            value = os.getenv(var)
            if value:
                platform_config[var] = True
                print("✅ {}: {} configured".format(platform, var))
            else:
                platform_config[var] = False
                print("⚠️  {}: {} not configured".format(platform, var))
        
        config_rate = sum(platform_config.values()) / len(platform_config)
        config_status[platform] = {
            'variables': platform_config,
            'config_rate': config_rate
        }
        print("📊 {}: {}/{} variables configured ({:.1%})".format(
            platform,
            sum(platform_config.values()),
            len(platform_config),
            config_rate
        ))
    
    return config_status

def create_integration_report(import_results, clients, method_results, config_status):
    """Create a comprehensive integration report"""
    print("\n" + "=" * 80)
    print("📋 SOCIAL MEDIA INTEGRATION COMPREHENSIVE REPORT")
    print("=" * 80)
    print("Generated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    platforms = ['Twitter', 'LinkedIn', 'Instagram', 'Facebook']
    
    print("\n🏆 PLATFORM READINESS SUMMARY")
    print("-" * 50)
    
    overall_scores = {}
    
    for platform in platforms:
        scores = []
        
        # Import score
        import_score = 1.0 if any(platform.lower() in module.lower() for module in import_results 
                                 if import_results[module]['status'] == 'SUCCESS') else 0.0
        scores.append(import_score)
        
        # Client instantiation score  
        client_score = 1.0 if platform in clients else 0.0
        scores.append(client_score)
        
        # Method availability score
        method_score = method_results.get(platform, {}).get('success_rate', 0.0)
        scores.append(method_score)
        
        # Configuration score
        config_score = config_status.get(platform, {}).get('config_rate', 0.0)
        scores.append(config_score)
        
        overall_score = sum(scores) / len(scores)
        overall_scores[platform] = overall_score
        
        status = "🟢 READY" if overall_score >= 0.8 else "🟡 PARTIAL" if overall_score >= 0.5 else "🔴 NOT READY"
        
        print("{:<12} | Score: {:.1%} | {}".format(platform, overall_score, status))
    
    # Overall system readiness
    system_score = sum(overall_scores.values()) / len(overall_scores)
    print("-" * 50)
    print("SYSTEM       | Score: {:.1%} | {}".format(
        system_score,
        "🟢 PRODUCTION READY" if system_score >= 0.8 else 
        "🟡 DEVELOPMENT READY" if system_score >= 0.6 else 
        "🔴 NEEDS WORK"
    ))
    
    print("\n📝 RECOMMENDATIONS")
    print("-" * 50)
    
    if system_score >= 0.8:
        print("✅ All integrations are ready for production testing")
        print("✅ Proceed with live API testing and user acceptance testing")
    elif system_score >= 0.6:
        print("⚠️  Most integrations working - address configuration gaps")
        print("⚠️  Complete missing environment variable setup")
        print("⚠️  Test missing methods with mock implementations")
    else:
        print("❌ Significant integration issues need resolution")
        print("❌ Review import errors and fix module dependencies")
        print("❌ Complete client implementation for all platforms")
    
    print("\n🔧 NEXT STEPS")
    print("-" * 50)
    print("1. Configure missing environment variables")
    print("2. Test with sandbox/development API credentials")
    print("3. Implement missing client methods")
    print("4. Run live API tests with real credentials")
    print("5. Set up monitoring and error alerting")
    
    return overall_scores

def main():
    """Main test execution"""
    print("🚀 Starting Social Media Integration Testing...")
    print("📅 Test Date: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Run all tests
    import_results = test_module_imports()
    clients = test_client_instantiation()
    method_results = test_client_methods(clients)
    config_status = test_configuration_availability()
    
    # Generate comprehensive report
    scores = create_integration_report(import_results, clients, method_results, config_status)
    
    # Save results to file
    try:
        report_file = "integration_test_report_{}.txt".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        
        with open(report_file, 'w') as f:
            f.write("Social Media Integration Test Report\n")
            f.write("Generated: {}\n\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            f.write("Import Results:\n")
            for module, result in import_results.items():
                f.write("  {}: {}\n".format(module, result['status']))
            
            f.write("\nClient Instantiation:\n")
            for platform in ['Twitter', 'LinkedIn', 'Instagram', 'Facebook']:
                status = "SUCCESS" if platform in clients else "FAILED"
                f.write("  {}: {}\n".format(platform, status))
            
            f.write("\nMethod Availability:\n")
            for platform, data in method_results.items():
                f.write("  {}: {:.1%} methods available\n".format(platform, data['success_rate']))
            
            f.write("\nConfiguration Status:\n")
            for platform, data in config_status.items():
                f.write("  {}: {:.1%} configured\n".format(platform, data['config_rate']))
            
            f.write("\nOverall Scores:\n")
            for platform, score in scores.items():
                f.write("  {}: {:.1%}\n".format(platform, score))
        
        print("\n💾 Test report saved to: {}".format(report_file))
        
    except Exception as e:
        print("\n⚠️  Could not save report file: {}".format(str(e)))
    
    print("\n🎯 Integration testing complete!")
    return scores

if __name__ == "__main__":
    main()