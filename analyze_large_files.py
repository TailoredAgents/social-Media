#!/usr/bin/env python3
"""
Large Files Analyzer
Identifies large files and categorizes them for cleanup decisions
"""

import os
import sys
from pathlib import Path

def analyze_large_files():
    """Find and categorize large files"""
    print("🔍 Analyzing Large Files (>1MB)")
    print("=" * 50)
    
    large_files = []
    total_size = 0
    
    # Walk through directory
    for root, dirs, files in os.walk('.'):
        # Skip common large directories
        dirs[:] = [d for d in dirs if d not in [
            '.git', 'node_modules', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', 'coverage'
        ]]
        
        for file in files:
            filepath = os.path.join(root, file)
            try:
                size = os.path.getsize(filepath)
                if size > 1024 * 1024:  # 1MB
                    size_mb = size / (1024 * 1024)
                    large_files.append((filepath, size_mb, size))
                    total_size += size
            except (OSError, PermissionError):
                continue
    
    # Sort by size (largest first)
    large_files.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Found {len(large_files)} files larger than 1MB")
    print(f"Total size: {total_size / (1024*1024):.1f}MB")
    print()
    
    # Categorize files
    categories = {
        'images': [],
        'data': [],
        'logs': [],
        'dependencies': [],
        'build_artifacts': [],
        'documentation': [],
        'other': []
    }
    
    for filepath, size_mb, size_bytes in large_files:
        path_lower = filepath.lower()
        
        if any(ext in path_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp']):
            categories['images'].append((filepath, size_mb))
        elif any(ext in path_lower for ext in ['.json', '.csv', '.db', '.sqlite', '.sql']):
            categories['data'].append((filepath, size_mb))
        elif any(ext in path_lower for ext in ['.log', '.logs']):
            categories['logs'].append((filepath, size_mb))
        elif any(path in path_lower for path in ['node_modules', 'venv', '.venv', 'site-packages']):
            categories['dependencies'].append((filepath, size_mb))
        elif any(ext in path_lower for ext in ['.js.map', '.min.js', '.bundle', 'dist/', 'build/']):
            categories['build_artifacts'].append((filepath, size_mb))
        elif any(ext in path_lower for ext in ['.pdf', '.md', '.txt', '.doc']):
            categories['documentation'].append((filepath, size_mb))
        else:
            categories['other'].append((filepath, size_mb))
    
    # Display categories
    for category, files in categories.items():
        if files:
            print(f"📁 {category.upper().replace('_', ' ')} ({len(files)} files)")
            total_cat_size = sum(size for _, size in files)
            print(f"   Total: {total_cat_size:.1f}MB")
            
            # Show top 5 largest in category
            for filepath, size_mb in files[:5]:
                print(f"   {size_mb:6.1f}MB  {filepath}")
            
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more")
            print()
    
    # Generate recommendations
    print("💡 RECOMMENDATIONS:")
    
    if categories['logs']:
        print("   🗑️  Consider cleaning up log files (can usually be deleted)")
    
    if categories['build_artifacts']:
        print("   🔧 Build artifacts can often be regenerated (check if needed in repo)")
    
    if categories['data']:
        print("   📊 Large data files - consider if they belong in git or should use LFS")
    
    if categories['images']:
        print("   🖼️  Large images - consider optimization or moving to CDN")
    
    if categories['dependencies']:
        print("   📦 Dependencies in repo - these usually shouldn't be committed")
    
    # Check .gitignore
    gitignore_path = Path('.gitignore')
    if gitignore_path.exists():
        print("\n📋 Checking .gitignore coverage...")
        with open(gitignore_path) as f:
            gitignore_content = f.read()
        
        # Check if common large file patterns are ignored
        patterns_to_check = [
            '*.log', '*.logs', 'logs/', 'node_modules/', 'venv/', '.venv/',
            'dist/', 'build/', '*.db', '*.sqlite'
        ]
        
        missing_patterns = []
        for pattern in patterns_to_check:
            if pattern not in gitignore_content:
                # Check if we actually have files matching this pattern
                if pattern == 'node_modules/' and categories['dependencies']:
                    missing_patterns.append(pattern)
                elif pattern == '*.log' and categories['logs']:
                    missing_patterns.append(pattern)
                elif pattern == 'dist/' and any('dist/' in f[0] for f in categories['build_artifacts']):
                    missing_patterns.append(pattern)
        
        if missing_patterns:
            print("   ⚠️  Consider adding to .gitignore:")
            for pattern in missing_patterns:
                print(f"      {pattern}")
    
    return large_files, categories

def main():
    """Run large file analysis"""
    large_files, categories = analyze_large_files()
    
    if large_files:
        print(f"\n📄 Analysis complete. Found {len(large_files)} large files.")
        print("Review recommendations above before making changes.")
    else:
        print("✅ No files larger than 1MB found!")

if __name__ == "__main__":
    main()