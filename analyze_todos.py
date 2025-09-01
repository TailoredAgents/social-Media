#!/usr/bin/env python3
"""
TODO/FIXME Comments Analyzer
Analyzes and categorizes TODO comments to prioritize cleanup
"""

import os
import re
from collections import defaultdict, Counter

def analyze_todos():
    """Analyze TODO and FIXME comments in the codebase"""
    print("📝 Analyzing TODO/FIXME Comments")
    print("=" * 40)
    
    todo_patterns = [
        (r'TODO[\s:]*(.+)', 'TODO'),
        (r'FIXME[\s:]*(.+)', 'FIXME'),
        (r'HACK[\s:]*(.+)', 'HACK'),
        (r'XXX[\s:]*(.+)', 'XXX'),
        (r'NOTE[\s:]*(.+)', 'NOTE'),
        (r'BUG[\s:]*(.+)', 'BUG')
    ]
    
    todos_by_type = defaultdict(list)
    todos_by_file = defaultdict(list)
    priority_todos = []
    
    # File extensions to search
    extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.vue', '.md', '.txt']
    
    total_count = 0
    
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
                    
                    for pattern, todo_type in todo_patterns:
                        matches = re.findall(pattern, line_clean, re.IGNORECASE)
                        if matches:
                            comment = matches[0].strip()
                            
                            todo_entry = {
                                'file': filepath,
                                'line': line_num,
                                'type': todo_type,
                                'comment': comment,
                                'full_line': line_clean
                            }
                            
                            todos_by_type[todo_type].append(todo_entry)
                            todos_by_file[filepath].append(todo_entry)
                            total_count += 1
                            
                            # Check for priority indicators
                            comment_lower = comment.lower()
                            if any(word in comment_lower for word in [
                                'critical', 'urgent', 'important', 'security', 
                                'bug', 'broken', 'fix', 'error', 'fail'
                            ]):
                                priority_todos.append(todo_entry)
            
            except (UnicodeDecodeError, PermissionError, IOError):
                continue
    
    print(f"📊 SUMMARY:")
    print(f"Total comments found: {total_count}")
    print(f"Files with comments: {len(todos_by_file)}")
    print(f"Priority comments: {len(priority_todos)}")
    print()
    
    # Show breakdown by type
    print("📋 BY TYPE:")
    for todo_type, todos in sorted(todos_by_type.items()):
        print(f"   {todo_type}: {len(todos)} comments")
    print()
    
    # Show files with most TODOs
    print("📁 TOP FILES WITH MOST COMMENTS:")
    file_counts = [(filepath, len(todos)) for filepath, todos in todos_by_file.items()]
    file_counts.sort(key=lambda x: x[1], reverse=True)
    
    for filepath, count in file_counts[:10]:
        print(f"   {count:3d} comments  {filepath}")
    print()
    
    # Show priority TODOs
    if priority_todos:
        print("🚨 PRIORITY COMMENTS (contain urgent keywords):")
        for todo in priority_todos[:10]:  # Show first 10
            print(f"   {todo['file']}:{todo['line']}")
            print(f"   {todo['type']}: {todo['comment']}")
            print()
    
    # Sample some regular TODOs
    print("💡 SAMPLE REGULAR COMMENTS:")
    regular_todos = [t for t in todos_by_type.get('TODO', []) if t not in priority_todos]
    for todo in regular_todos[:5]:
        print(f"   {todo['file']}:{todo['line']}")
        print(f"   TODO: {todo['comment']}")
        print()
    
    # Generate recommendations
    print("💡 RECOMMENDATIONS:")
    
    if priority_todos:
        print(f"   🚨 Address {len(priority_todos)} priority comments first")
    
    if len(todos_by_type.get('FIXME', [])) > 0:
        print(f"   🔧 {len(todos_by_type['FIXME'])} FIXME comments likely indicate bugs")
    
    if len(todos_by_type.get('HACK', [])) > 0:
        print(f"   ⚠️  {len(todos_by_type['HACK'])} HACK comments should be reviewed")
    
    # Check if there are files with excessive TODOs
    excessive_files = [f for f, c in file_counts if c > 50]
    if excessive_files:
        print(f"   📂 {len(excessive_files)} files have >50 comments each - consider refactoring")
    
    if total_count > 1000:
        print("   📝 Consider implementing a TODO cleanup sprint")
        print("   📋 Focus on one module/component at a time")
    
    return todos_by_type, todos_by_file, priority_todos

def main():
    """Run TODO analysis"""
    todos_by_type, todos_by_file, priority_todos = analyze_todos()
    
    print("\n📄 Analysis complete.")
    print("Focus on priority comments and FIXME items first.")

if __name__ == "__main__":
    main()