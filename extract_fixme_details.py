#!/usr/bin/env python3
"""
FIXME/HACK/Priority Comments Extractor
Extracts full context of all FIXME, HACK, and priority comments for review
"""

import os
import re
from pathlib import Path

def extract_comment_details():
    """Extract detailed information about all FIXME, HACK, and priority comments"""
    
    # Patterns to search for
    patterns = {
        'FIXME': r'FIXME[\s:]*(.+)',
        'HACK': r'HACK[\s:]*(.+)', 
        'CRITICAL': r'.*(critical|urgent|important|security|bug|broken|fix|error|fail).*',
    }
    
    results = {
        'FIXME': [],
        'HACK': [],
        'PRIORITY': []
    }
    
    # File extensions to search
    extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.vue']
    
    print("🔍 Extracting FIXME/HACK/Priority Comments with Full Context")
    print("=" * 70)
    
    for root, dirs, files in os.walk('.'):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in [
            '.git', 'node_modules', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', 'coverage'
        ]]
        
        for file in files:
            if not any(file.endswith(ext) for ext in extensions):
                continue
                
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_clean = line.strip()
                    
                    # Check for FIXME
                    fixme_match = re.search(patterns['FIXME'], line_clean, re.IGNORECASE)
                    if fixme_match:
                        context = get_context(lines, line_num - 1, 2)  # 2 lines before/after
                        results['FIXME'].append({
                            'file': filepath,
                            'line': line_num,
                            'comment': fixme_match.group(1).strip(),
                            'full_line': line_clean,
                            'context': context
                        })
                    
                    # Check for HACK
                    hack_match = re.search(patterns['HACK'], line_clean, re.IGNORECASE)
                    if hack_match:
                        context = get_context(lines, line_num - 1, 2)
                        results['HACK'].append({
                            'file': filepath,
                            'line': line_num,
                            'comment': hack_match.group(1).strip(),
                            'full_line': line_clean,
                            'context': context
                        })
                    
                    # Check for priority keywords (but not if already FIXME/HACK)
                    if not fixme_match and not hack_match:
                        priority_match = re.search(patterns['CRITICAL'], line_clean, re.IGNORECASE)
                        if priority_match and ('TODO' in line_clean or 'NOTE' in line_clean):
                            context = get_context(lines, line_num - 1, 2)
                            results['PRIORITY'].append({
                                'file': filepath,
                                'line': line_num,
                                'comment': line_clean,
                                'full_line': line_clean,
                                'context': context
                            })
            
            except (UnicodeDecodeError, PermissionError, IOError):
                continue
    
    return results

def get_context(lines, center_idx, context_size):
    """Get surrounding lines for context"""
    start = max(0, center_idx - context_size)
    end = min(len(lines), center_idx + context_size + 1)
    
    context_lines = []
    for i in range(start, end):
        marker = ">>>" if i == center_idx else "   "
        context_lines.append(f"{marker} {i+1:3d}: {lines[i].rstrip()}")
    
    return "\n".join(context_lines)

def display_results(results):
    """Display all results with full context for review"""
    
    print("\n" + "="*70)
    print("🔧 FIXME COMMENTS (Real Bugs - Need Fixing)")
    print("="*70)
    
    if results['FIXME']:
        for i, item in enumerate(results['FIXME'], 1):
            print(f"\n{i}. 📍 {item['file']}:{item['line']}")
            print(f"   💬 FIXME: {item['comment']}")
            print(f"   📄 Context:")
            print(f"{item['context']}")
            print("-" * 60)
    else:
        print("   ✅ No FIXME comments found!")
    
    print("\n" + "="*70)
    print("⚠️  HACK COMMENTS (Workarounds - Should Be Proper Solutions)")
    print("="*70)
    
    if results['HACK']:
        for i, item in enumerate(results['HACK'], 1):
            print(f"\n{i}. 📍 {item['file']}:{item['line']}")
            print(f"   💬 HACK: {item['comment']}")
            print(f"   📄 Context:")
            print(f"{item['context']}")
            print("-" * 60)
    else:
        print("   ✅ No HACK comments found!")
    
    print("\n" + "="*70)
    print("🚨 PRIORITY COMMENTS (Contains Critical Keywords)")
    print("="*70)
    
    if results['PRIORITY']:
        # Show first 10 to avoid overwhelming
        for i, item in enumerate(results['PRIORITY'][:10], 1):
            print(f"\n{i}. 📍 {item['file']}:{item['line']}")
            print(f"   💬 {item['comment']}")
            print(f"   📄 Context:")
            print(f"{item['context']}")
            print("-" * 60)
        
        if len(results['PRIORITY']) > 10:
            print(f"\n... and {len(results['PRIORITY']) - 10} more priority comments")
    else:
        print("   ✅ No priority comments found!")

def generate_summary(results):
    """Generate summary and recommendations"""
    print("\n" + "="*70)
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("="*70)
    
    fixme_count = len(results['FIXME'])
    hack_count = len(results['HACK'])
    priority_count = len(results['PRIORITY'])
    
    print(f"📊 Found:")
    print(f"   🔧 {fixme_count} FIXME comments (bugs that need fixing)")
    print(f"   ⚠️  {hack_count} HACK comments (workarounds to improve)")
    print(f"   🚨 {priority_count} Priority comments (contain critical keywords)")
    
    print(f"\n🎯 Recommended Action Priority:")
    print(f"   1. Address {fixme_count} FIXME comments first (these are bugs)")
    print(f"   2. Review {hack_count} HACK comments (improve workarounds)")
    print(f"   3. Review priority comments for actual issues vs. documentation")
    
    # Risk assessment
    if fixme_count == 0 and hack_count <= 5:
        risk_level = "LOW"
        print(f"\n✅ Risk Assessment: {risk_level}")
        print("   Most issues appear to be documentation or minor improvements")
    elif fixme_count <= 3 and hack_count <= 10:
        risk_level = "MEDIUM"
        print(f"\n⚠️  Risk Assessment: {risk_level}")
        print("   Several issues need attention but manageable")
    else:
        risk_level = "HIGH"
        print(f"\n🚨 Risk Assessment: {risk_level}")
        print("   Multiple critical issues need immediate attention")
    
    return {
        'fixme_count': fixme_count,
        'hack_count': hack_count,
        'priority_count': priority_count,
        'risk_level': risk_level
    }

def main():
    """Extract and display all FIXME/HACK/Priority comments"""
    
    results = extract_comment_details()
    display_results(results)
    summary = generate_summary(results)
    
    print(f"\n📄 Review complete. Check each item above before proceeding with fixes.")

if __name__ == "__main__":
    main()