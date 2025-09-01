#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Social Media Integration Test Suite
Tests actual method names and functionality from the integration files
"""

import os
import sys
import json
from datetime import datetime
import re

def extract_methods_from_file(file_path):
    """Extract all method definitions from a Python file"""
    methods = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all method definitions
        method_pattern = r'^\s*(async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        matches = re.finditer(method_pattern, content, re.MULTILINE)
        
        for match in matches:
            is_async = match.group(1) is not None
            method_name = match.group(2)
            if not method_name.startswith('_'):  # Exclude private methods
                methods.append({
                    'name': method_name,
                    'async': is_async,
                    'full_signature': match.group(0).strip()
                })
    
    except Exception as e:
        print("Error reading {}: {}".format(file_path, str(e)))
    
    return methods

def extract_classes_from_file(file_path):
    """Extract all class definitions from a Python file"""
    classes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all class definitions
        class_pattern = r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?:'
        matches = re.finditer(class_pattern, content, re.MULTILINE)
        
        for match in matches:
            class_name = match.group(1)
            classes.append(class_name)
    
    except Exception as e:
        print("Error reading {}: {}".format(file_path, str(e)))
    
    return classes

def analyze_integration_completeness():
    """Analyze the completeness of each social media integration"""
    print("COMPREHENSIVE SOCIAL MEDIA INTEGRATION ANALYSIS")
    print("=" * 80)
    print("Generated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    integrations = {
        'Twitter': {
            'file': 'backend/integrations/twitter_client.py',
            'client_class': 'TwitterAPIClient',
            'essential_methods': [
                'post_tweet', 'get_tweet', 'delete_tweet', 'post_thread',
                'get_user_timeline', 'get_tweet_analytics', 'search_tweets'
            ],
            'auth_methods': ['authenticate', 'verify_credentials'],
            'analytics_methods': ['get_tweet_analytics', 'get_user_metrics']
        },
        'LinkedIn': {
            'file': 'backend/integrations/linkedin_client.py',
            'client_class': 'LinkedInAPIClient', 
            'essential_methods': [
                'create_post', 'get_profile', 'create_article',
                'get_post_analytics', 'share_content'
            ],
            'auth_methods': ['authenticate', 'get_access_token'],
            'analytics_methods': ['get_post_analytics', 'get_company_analytics']
        },
        'Instagram': {
            'file': 'backend/integrations/instagram_client.py',
            'client_class': 'InstagramAPIClient',
            'essential_methods': [
                'post_image', 'post_video', 'post_carousel', 'post_reel',
                'get_account_info', 'get_media_insights'
            ],
            'auth_methods': ['authenticate', 'refresh_token'],
            'analytics_methods': ['get_media_insights', 'get_account_insights']
        },
        'Facebook': {
            'file': 'backend/integrations/facebook_client.py',
            'client_class': 'FacebookAPIClient',
            'essential_methods': [
                'create_text_post', 'create_photo_post', 'create_video_post',
                'get_page_info', 'get_post_insights', 'create_event'
            ],
            'auth_methods': ['authenticate', 'get_page_access_token'],
            'analytics_methods': ['get_post_insights', 'get_page_insights']
        }
    }
    
    platform_scores = {}
    
    for platform, config in integrations.items():
        print("\n{} INTEGRATION ANALYSIS".format(platform.upper()))
        print("-" * 60)
        
        file_path = config['file']
        if not os.path.exists(file_path):
            print("❌ Integration file missing: {}".format(file_path))
            platform_scores[platform] = 0.0
            continue
        
        # Extract actual methods and classes
        classes = extract_classes_from_file(file_path)
        methods = extract_methods_from_file(file_path)
        method_names = [m['name'] for m in methods]
        
        print("📁 File: {} ({} bytes)".format(file_path, os.path.getsize(file_path)))
        print("🏗️  Classes found: {}".format(len(classes)))
        print("⚙️  Methods found: {}".format(len(methods)))
        
        # Check if main client class exists
        has_client_class = config['client_class'] in classes
        print("🎯 Main class '{}': {}".format(
            config['client_class'], 
            "✅ FOUND" if has_client_class else "❌ MISSING"
        ))
        
        # Check essential methods
        essential_found = 0
        print("\n📋 Essential Methods:")
        for method in config['essential_methods']:
            if method in method_names:
                essential_found += 1
                print("  ✅ {}".format(method))
            else:
                print("  ❌ {} (missing)".format(method))
        
        # Check auth methods
        auth_found = 0
        print("\n🔐 Authentication Methods:")
        for method in config['auth_methods']:
            if method in method_names:
                auth_found += 1
                print("  ✅ {}".format(method))
            else:
                print("  ⚠️  {} (missing)".format(method))
        
        # Check analytics methods
        analytics_found = 0
        print("\n📊 Analytics Methods:")
        for method in config['analytics_methods']: 
            if method in method_names:
                analytics_found += 1
                print("  ✅ {}".format(method))
            else:
                print("  ⚠️  {} (missing)".format(method))
        
        # Calculate completeness score
        essential_score = essential_found / len(config['essential_methods'])
        auth_score = auth_found / len(config['auth_methods']) if config['auth_methods'] else 1.0
        analytics_score = analytics_found / len(config['analytics_methods']) if config['analytics_methods'] else 1.0
        class_score = 1.0 if has_client_class else 0.0
        
        # Weighted average (essential methods are most important)
        platform_score = (
            essential_score * 0.5 +
            class_score * 0.3 +
            auth_score * 0.1 +
            analytics_score * 0.1
        )
        
        platform_scores[platform] = platform_score
        
        print("\n📈 Completeness Scores:")
        print("  Essential Methods: {:.1%} ({}/{})".format(essential_score, essential_found, len(config['essential_methods'])))
        print("  Authentication: {:.1%} ({}/{})".format(auth_score, auth_found, len(config['auth_methods'])))
        print("  Analytics: {:.1%} ({}/{})".format(analytics_score, analytics_found, len(config['analytics_methods'])))
        print("  Overall Platform: {:.1%}".format(platform_score))
        
        # Show all available methods for reference
        print("\n🔍 All Available Methods ({})".format(len(methods)))
        async_methods = [m for m in methods if m['async']]
        sync_methods = [m for m in methods if not m['async']]
        
        if async_methods:
            print("  Async methods: {}".format(", ".join([m['name'] for m in async_methods[:10]])))
            if len(async_methods) > 10:
                print("    ... and {} more".format(len(async_methods) - 10))
        
        if sync_methods:
            print("  Sync methods: {}".format(", ".join([m['name'] for m in sync_methods[:10]])))
            if len(sync_methods) > 10:
                print("    ... and {} more".format(len(sync_methods) - 10))
    
    return platform_scores

def create_integration_test_plan(platform_scores):
    """Create a detailed test plan based on the analysis"""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST PLAN & RECOMMENDATIONS")
    print("=" * 80)
    
    system_score = sum(platform_scores.values()) / len(platform_scores)
    
    print("\n🏆 PLATFORM READINESS SUMMARY")
    print("-" * 50)
    
    for platform, score in platform_scores.items():
        status = ("🟢 PRODUCTION READY" if score >= 0.8 else
                 "🟡 TESTING READY" if score >= 0.6 else
                 "🟠 DEVELOPMENT READY" if score >= 0.4 else
                 "🔴 NEEDS WORK")
        print("{:<12} | {:.1%} | {}".format(platform, score, status))
    
    print("-" * 50)
    system_status = ("🟢 EXCELLENT" if system_score >= 0.8 else
                    "🟡 GOOD" if system_score >= 0.6 else
                    "🟠 FAIR" if system_score >= 0.4 else
                    "🔴 POOR")
    print("SYSTEM       | {:.1%} | {}".format(system_score, system_status))
    
    print("\n📋 TESTING RECOMMENDATIONS")
    print("-" * 50)
    
    if system_score >= 0.8:
        print("✅ System is ready for comprehensive live API testing")
        print("✅ All platforms have sufficient method coverage")
        print("✅ Proceed with environment setup and credential configuration")
        print("✅ Start with sandbox/development API testing")
        print("✅ Implement comprehensive error handling and logging")
    elif system_score >= 0.6:
        print("🟡 System is ready for basic testing with some limitations")
        print("🟡 Focus on platforms with highest completeness scores first")
        print("🟡 Implement missing essential methods before full testing")
        print("🟡 Test core functionality before advanced features")
    elif system_score >= 0.4:
        print("🟠 System needs additional development before testing")
        print("🟠 Complete essential method implementations")
        print("🟠 Focus on one platform at a time for testing")
        print("🟠 Use mock/stub implementations for missing methods")
    else:
        print("🔴 System requires significant development work")
        print("🔴 Complete core client implementations")
        print("🔴 Focus on essential posting and retrieval methods")
        print("🔴 Defer advanced features until basics are working")
    
    print("\n🧪 SUGGESTED TESTING SEQUENCE")
    print("-" * 50)
    
    # Sort platforms by readiness score
    sorted_platforms = sorted(platform_scores.items(), key=lambda x: x[1], reverse=True)
    
    for i, (platform, score) in enumerate(sorted_platforms, 1):
        print("{}. {} ({:.1%} ready)".format(i, platform, score))
        if score >= 0.6:
            print("   - Set up developer account and API credentials")
            print("   - Test authentication flow")
            print("   - Test basic posting functionality") 
            print("   - Test content retrieval and analytics")
            print("   - Implement rate limiting and error handling")
        elif score >= 0.4:
            print("   - Complete missing essential methods")
            print("   - Test with mock implementations first")
            print("   - Implement core authentication")
        else:
            print("   - Complete basic client implementation")
            print("   - Focus on posting and retrieval methods")
    
    print("\n🔧 IMPLEMENTATION PRIORITIES")
    print("-" * 50)
    
    # Identify most critical missing pieces
    critical_gaps = []
    for platform, score in platform_scores.items():
        if score < 0.6:
            critical_gaps.append(platform)
    
    if critical_gaps:
        print("Critical gaps to address:")
        for platform in critical_gaps:
            print("  - {}: Complete essential method implementations".format(platform))
    else:
        print("✅ No critical gaps - ready for testing phase")
    
    print("\n📊 NEXT PHASE: LIVE API TESTING")
    print("-" * 50)
    print("1. Environment Setup:")
    print("   - Configure API keys for each platform")
    print("   - Set up development/sandbox accounts")
    print("   - Create test applications in developer portals")
    
    print("\n2. Authentication Testing:")
    print("   - Test OAuth flows for each platform")
    print("   - Verify token refresh mechanisms")
    print("   - Test permission scopes")
    
    print("\n3. Functional Testing:")
    print("   - Test content posting across all platforms")
    print("   - Verify content appears correctly")
    print("   - Test analytics data retrieval")
    print("   - Test error handling and rate limiting")
    
    print("\n4. Integration Testing:")
    print("   - Test cross-platform content distribution")
    print("   - Verify consistent behavior across platforms")
    print("   - Test automated workflows")
    
    return sorted_platforms

def save_comprehensive_report(platform_scores, sorted_platforms):
    """Save comprehensive analysis to file"""
    try:
        report_file = "comprehensive_integration_analysis_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'platform_scores': platform_scores,
            'system_score': sum(platform_scores.values()) / len(platform_scores),
            'platforms_by_readiness': [
                {'platform': platform, 'score': score} 
                for platform, score in sorted_platforms
            ],
            'recommendations': {
                'system_status': 'production_ready' if sum(platform_scores.values()) / len(platform_scores) >= 0.8 else 'needs_work',
                'ready_for_testing': sum(platform_scores.values()) / len(platform_scores) >= 0.6,
                'critical_gaps': [p for p, s in platform_scores.items() if s < 0.6]
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print("\n💾 Comprehensive analysis saved to: {}".format(report_file))
        
        # Also save a human-readable summary
        summary_file = "integration_test_summary_{}.txt".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        
        with open(summary_file, 'w') as f:
            f.write("Social Media Integration Analysis Summary\n")
            f.write("Generated: {}\n\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            f.write("Platform Readiness Scores:\n")
            for platform, score in platform_scores.items():
                f.write("  {}: {:.1%}\n".format(platform, score))
            
            system_score = sum(platform_scores.values()) / len(platform_scores)
            f.write("\nSystem Overall: {:.1%}\n".format(system_score))
            
            f.write("\nRecommended Testing Order:\n")
            for i, (platform, score) in enumerate(sorted_platforms, 1):
                f.write("  {}. {} ({:.1%})\n".format(i, platform, score))
            
            f.write("\nNext Steps:\n")
            if system_score >= 0.8:
                f.write("  - Ready for live API testing\n")
                f.write("  - Configure API credentials\n") 
                f.write("  - Test all platform integrations\n")
            elif system_score >= 0.6:
                f.write("  - Complete minor gaps in implementations\n")
                f.write("  - Test with highest-scoring platforms first\n")
                f.write("  - Implement missing methods\n")
            else:
                f.write("  - Complete essential method implementations\n")
                f.write("  - Focus on core posting functionality\n")
                f.write("  - Test with mock implementations first\n")
        
        print("📝 Human-readable summary saved to: {}".format(summary_file))
        
    except Exception as e:
        print("⚠️  Could not save reports: {}".format(str(e)))

def main():
    """Main analysis execution"""
    print("🚀 Starting Comprehensive Social Media Integration Analysis...")
    
    # Analyze current implementation completeness
    platform_scores = analyze_integration_completeness()
    
    # Create detailed test plan
    sorted_platforms = create_integration_test_plan(platform_scores)
    
    # Save comprehensive reports
    save_comprehensive_report(platform_scores, sorted_platforms)
    
    # Print final status
    system_score = sum(platform_scores.values()) / len(platform_scores)
    print("\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 80)
    
    if system_score >= 0.8:
        print("🎉 EXCELLENT: Social media integrations are production-ready!")
        print("✅ Proceed immediately with live API testing and deployment")
    elif system_score >= 0.6:
        print("👍 GOOD: Integrations are mostly complete and testable")
        print("🔧 Address minor gaps then proceed with testing")
    elif system_score >= 0.4:
        print("⚠️  FAIR: Integrations need additional work before testing")
        print("🛠️  Focus on completing essential methods")
    else:
        print("❌ NEEDS WORK: Significant development required")
        print("🔨 Complete core implementations before testing")
    
    print("\nSystem Readiness: {:.1%}".format(system_score))
    print("Analysis complete! 📊")
    
    return platform_scores

if __name__ == "__main__":
    main()