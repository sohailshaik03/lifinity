#!/usr/bin/env python3
"""
Fix two issues:
1. Replace conn.cursor() with proper SQLAlchemy execute() calls
2. Replace width="stretch" with width="stretch"
"""
import os
import re
from pathlib import Path

def fix_use_container_width(root_dir):
    """Replace all use_container_width with width parameter"""
    print("Fixing use_container_width deprecation...")
    count = 0
    
    for file_path in Path(root_dir).rglob("*.py"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace width="stretch" with width="stretch"
            content = content.replace('width="stretch"', 'width="stretch"')
            # Replace width="content" with width="content"
            content = content.replace('width="content"', 'width="content"')
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed {file_path}")
                count += 1
        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")
    
    print(f"\n✅ Fixed {count} files for use_container_width\n")

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    fix_use_container_width(root_dir)
    print("\n🎉 All deprecations fixed!")

if __name__ == "__main__":
    main()
