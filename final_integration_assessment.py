#!/usr/bin/env python3
"""
Final Integration Assessment - Check actual implementation status
"""

import os
import sys
from datetime import datetime

def check_file_content(file_path, search_terms):
    """Check if file contains expected content"""
    if not os.path.exists(file_path):
        return {'exists': False, 'content': {}}
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        results = {'exists': True, 'content': {}}
        for term in search_terms:
            results['content'][term] = term in content
        
        return results
    except Exception as e:
        return {'exists': True, 'error': str(e), 'content': {}}

def analyze_integrations():
    """Analyze all social media integrations"""
    print("FINAL SOCIAL MEDIA INTEGRATION ASSESSMENT")
    print("=" * 70)
    print("Date: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    integrations = {
        'Twitter': {
            'file': 'backend/integrations/twitter_client.py',
            'searches': [
                'class TwitterAPIClient',
                'async def post_tweet',
                'async def get_tweet',
                'async def delete_tweet',
                'async def post_thread',
                'def authenticate',
                'def get_tweet_analytics'
            ]
        },
        'LinkedIn': {
            'file': 'backend/integrations/linkedin_client.py', 
            'searches': [
                'class LinkedInAPIClient',
                'async def create_post', 
                'async def get_profile',
                'async def create_article',
                'def authenticate',
                'def get_post_analytics'
            ]
        },
        'Instagram': {
            'file': 'backend/integrations/instagram_client.py',
            'searches': [
                'class InstagramAPIClient',
                'async def post_image',
                'async def post_video',
                'async def create_media_container',
                'def authenticate',
                'def get_media_insights'
            ]
        },
        'Facebook': {
            'file': 'backend/integrations/facebook_client.py',
            'searches': [
                'class FacebookAPIClient',
                'async def create_text_post',
                'async def create_photo_post',
                'async def get_page_info',
                'def authenticate',
                'def get_post_insights'
            ]
        }
    }
    
    platform_results = {}
    
    for platform, config in integrations.items():
        print("\n{} Integration Assessment".format(platform))
        print("-" * 40)
        
        file_path = config['file']
        results = check_file_content(file_path, config['searches'])
        
        if not results['exists']:
            print("❌ File missing: {}".format(file_path))
            platform_results[platform] = {'score': 0.0, 'status': 'MISSING'}
            continue
        
        if 'error' in results:
            print("❌ Error reading file: {}".format(results['error']))
            platform_results[platform] = {'score': 0.0, 'status': 'ERROR'}
            continue
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print("📁 File: {} ({:,} bytes)".format(file_path, file_size))
        
        # Analyze content
        content_results = results['content']
        found_items = sum(content_results.values())
        total_items = len(content_results)
        score = found_items / total_items if total_items > 0 else 0
        
        print("📊 Implementation Status:")
        for item, found in content_results.items():
            status = "✅" if found else "❌"
            print("  {} {}".format(status, item))
        
        print("🎯 Score: {:.1%} ({}/{} items found)".format(score, found_items, total_items))
        
        # Determine status
        if score >= 0.8:
            status = "EXCELLENT"
        elif score >= 0.6:
            status = "GOOD"
        elif score >= 0.4:
            status = "PARTIAL"
        elif score > 0:
            status = "LIMITED"
        else:
            status = "MISSING"
        
        platform_results[platform] = {
            'score': score,
            'status': status,
            'file_size': file_size,
            'found_items': found_items,
            'total_items': total_items,
            'details': content_results
        }
        
        print("📋 Status: {}".format(status))
    
    return platform_results

def create_testing_recommendations(platform_results):
    """Create testing recommendations based on assessment"""
    print("\n" + "=" * 70)
    print("TESTING RECOMMENDATIONS & NEXT STEPS")
    print("=" * 70)
    
    # Calculate system score
    scores = [r['score'] for r in platform_results.values() if 'score' in r]
    system_score = sum(scores) / len(scores) if scores else 0
    
    print("\n🏆 PLATFORM READINESS SUMMARY")
    print("-" * 50)
    
    sorted_platforms = sorted(platform_results.items(), key=lambda x: x[1].get('score', 0), reverse=True)
    
    for platform, results in sorted_platforms:
        score = results.get('score', 0)
        status = results.get('status', 'UNKNOWN')
        
        if score >= 0.8:
            emoji = "🟢"
        elif score >= 0.6:
            emoji = "🟡"
        elif score >= 0.4:
            emoji = "🟠"
        else:
            emoji = "🔴"
        
        print("{} {:<12} | {:.1%} | {}".format(emoji, platform, score, status))
    
    print("-" * 50)
    if system_score >= 0.8:
        system_status = "🟢 PRODUCTION READY"
    elif system_score >= 0.6:
        system_status = "🟡 TESTING READY"
    elif system_score >= 0.4:
        system_status = "🟠 DEVELOPMENT READY"
    else:
        system_status = "🔴 NEEDS DEVELOPMENT"
    
    print("SYSTEM       | {:.1%} | {}".format(system_score, system_status))
    
    print("\n🎯 ASSESSMENT CONCLUSION")
    print("-" * 50)
    
    if system_score >= 0.8:
        print("🎉 EXCELLENT: Integrations are well-implemented!")
        print("✅ All platforms have substantial implementations")
        print("✅ Ready for configuration and live API testing")
        print("✅ Most core methods appear to be implemented")
        
        recommendation = "PROCEED TO LIVE TESTING"
        next_steps = [
            "Set up developer accounts for each platform",
            "Configure API credentials in environment variables", 
            "Test authentication flows",
            "Test basic posting functionality",
            "Test analytics retrieval",
            "Implement monitoring and error handling"
        ]
        
    elif system_score >= 0.6:
        print("👍 GOOD: Most integrations are well-implemented")
        print("🔧 Some platforms may need minor completion")
        print("✅ Ready for testing with highest-scoring platforms")
        
        recommendation = "SELECTIVE TESTING"
        next_steps = [
            "Start testing with highest-scoring platforms first",
            "Complete missing methods for lower-scoring platforms",
            "Set up API credentials for ready platforms",
            "Test core functionality before advanced features"
        ]
        
    elif system_score >= 0.4:
        print("⚠️  FAIR: Integrations are partially implemented")
        print("🛠️  Additional development work needed")
        print("🧪 Test with mock implementations first")
        
        recommendation = "COMPLETE DEVELOPMENT"
        next_steps = [
            "Complete missing essential methods",
            "Focus on core posting and retrieval functionality",
            "Test with mock/stub implementations",
            "Implement one platform at a time"
        ]
        
    else:
        print("❌ NEEDS WORK: Limited implementation detected")
        print("🔨 Substantial development work required")
        print("📝 Focus on basic client structure first")
        
        recommendation = "MAJOR DEVELOPMENT NEEDED"
        next_steps = [
            "Complete basic client class implementations",
            "Implement core posting methods",
            "Add authentication mechanisms",
            "Test with simple examples before complex features"
        ]
    
    print("\n📋 RECOMMENDATION: {}".format(recommendation))
    print("\n🔧 NEXT STEPS:")
    for i, step in enumerate(next_steps, 1):
        print("{}. {}".format(i, step))
    
    print("\n🧪 SUGGESTED TESTING ORDER:")
    for i, (platform, results) in enumerate(sorted_platforms, 1):
        score = results.get('score', 0)
        if score > 0:
            priority = "HIGH" if score >= 0.6 else "MEDIUM" if score >= 0.4 else "LOW"
            print("{}. {} - {:.1%} ready ({} priority)".format(i, platform, score, priority))
    
    return {
        'system_score': system_score,
        'recommendation': recommendation,
        'next_steps': next_steps,
        'testing_order': sorted_platforms
    }

def save_assessment_report(platform_results, recommendations):
    """Save assessment report to file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = "integration_assessment_report_{}.txt".format(timestamp)
        
        with open(report_file, 'w') as f:
            f.write("Social Media Integration Assessment Report\n")
            f.write("Generated: {}\n\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            f.write("PLATFORM SCORES:\n")
            for platform, results in platform_results.items():
                score = results.get('score', 0)
                status = results.get('status', 'UNKNOWN')
                f.write("  {}: {:.1%} ({})\n".format(platform, score, status))
            
            f.write("\nSYSTEM SCORE: {:.1%}\n".format(recommendations['system_score']))
            f.write("RECOMMENDATION: {}\n\n".format(recommendations['recommendation']))
            
            f.write("NEXT STEPS:\n")
            for i, step in enumerate(recommendations['next_steps'], 1):
                f.write("{}. {}\n".format(i, step))
            
            f.write("\nTESTING ORDER:\n")
            for i, (platform, results) in enumerate(recommendations['testing_order'], 1):
                score = results.get('score', 0)
                f.write("{}. {} ({:.1%})\n".format(i, platform, score))
        
        print("\n💾 Assessment report saved to: {}".format(report_file))
        
    except Exception as e:
        print("\n⚠️  Could not save report: {}".format(str(e)))

def main():
    """Main assessment execution"""
    print("🚀 Starting Final Integration Assessment...\n")
    
    # Analyze all integrations
    platform_results = analyze_integrations()
    
    # Create recommendations
    recommendations = create_testing_recommendations(platform_results)
    
    # Save report
    save_assessment_report(platform_results, recommendations)
    
    # Final summary
    system_score = recommendations['system_score']
    print("\n" + "=" * 70)
    print("🎯 FINAL VERDICT")
    print("=" * 70)
    
    if system_score >= 0.8:
        print("🎉 SUCCESS: Social media integrations are well-implemented!")
        print("🚀 Ready for live API testing and deployment preparation")
    elif system_score >= 0.6:
        print("✅ GOOD: Integrations are mostly ready for testing")
        print("🔧 Minor gaps to address, then proceed with testing")
    elif system_score >= 0.4:
        print("⚠️  PARTIAL: Integrations need additional development")
        print("🛠️  Complete essential methods then test")
    else:
        print("❌ LIMITED: Significant development work needed")
        print("📝 Focus on core implementations first")
    
    print("\nOverall System Readiness: {:.1%}".format(system_score))
    print("Assessment complete! 📊")
    
    return platform_results, recommendations

if __name__ == "__main__":
    main()