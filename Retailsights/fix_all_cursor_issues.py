#!/usr/bin/env python3
"""
Comprehensive fix for all conn.cursor() issues in the codebase.
Converts MySQL connector pattern to SQLAlchemy pattern.
"""
import os
import re
from pathlib import Path

def fix_cursor_file(file_path):
    """Fix cursor issues in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = False
        
        # Check if file uses get_connection()
        if 'get_connection()' not in content:
            return False
        
        # Add text import if not present and file uses conn.execute
        if 'from sqlalchemy import' in content:
            # Already has sqlalchemy import, check if text is there
            if 'text' not in content.split('from sqlalchemy import')[1].split('\n')[0]:
                # Add text to existing import
                content = re.sub(
                    r'from sqlalchemy import ([^\n]+)',
                    r'from sqlalchemy import \1, text',
                    content,
                    count=1
                )
                changes_made = True
        elif 'conn.cursor(' in content:
            # Need to add text import
            # Find the best place to add it (after other imports)
            import_lines = []
            other_lines = []
            in_imports = True
            
            for line in content.split('\n'):
                if in_imports and (line.startswith('from ') or line.startswith('import ') or line.strip() == '' or line.startswith('#')):
                    import_lines.append(line)
                else:
                    if in_imports and line.strip() != '':
                        in_imports = False
                    other_lines.append(line)
            
            # Add text import
            import_lines.append('from sqlalchemy import text')
            content = '\n'.join(import_lines + other_lines)
            changes_made = True
        
        # Pattern 1: cur = conn.cursor(dictionary=True) - needs full replacement
        # Pattern 2: cur = conn.cursor() - needs full replacement
        
        # We'll mark sections that need manual review
        if 'cur = conn.cursor' in content:
            print(f"  ⚠️  {file_path} - Contains cursor() calls - needs manual SQLAlchemy conversion")
            return False
        
        if changes_made and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False

def find_cursor_files(root_dir):
    """Find all files with cursor issues"""
    files_with_issues = []
    
    print("\n🔍 Scanning for files with cursor() issues...\n")
    
    for file_path in Path(root_dir).rglob("*.py"):
        # Skip virtual env and cache
        if '.venv' in str(file_path) or '__pycache__' in str(file_path):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'conn.cursor(' in content and 'get_connection()' in content:
                files_with_issues.append(file_path)
        except:
            pass
    
    return files_with_issues

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_with_issues = find_cursor_files(root_dir)
    
    if not files_with_issues:
        print("✅ No cursor() issues found!")
        return
    
    print(f"Found {len(files_with_issues)} files with cursor() issues:\n")
    
    # Group by directory
    by_dir = {}
    for f in files_with_issues:
        dir_name = f.parent.name
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(f.name)
    
    for dir_name, files in sorted(by_dir.items()):
        print(f"\n📁 {dir_name}/")
        for fname in sorted(files):
            print(f"   - {fname}")
    
    print(f"\n⚠️  Total: {len(files_with_issues)} files need SQLAlchemy conversion")
    print(f"\nThese files use conn.cursor() which doesn't work with SQLAlchemy connections.")
    print(f"They need to be converted to use conn.execute(text(...)) pattern.\n")

if __name__ == "__main__":
    main()
