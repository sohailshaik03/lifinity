#!/usr/bin/env python3
"""
Convert MySQL DATE_SUB syntax to PostgreSQL INTERVAL syntax
"""
import os
import re
from pathlib import Path

def fix_date_sub(content: str) -> str:
    """Replace DATE_SUB(NOW(), INTERVAL X DAY/HOUR) with NOW() - INTERVAL 'X days/hours'"""
    
    # Pattern 1: DATE_SUB(NOW(), INTERVAL %s DAY) -> NOW() - INTERVAL '%s days'
    content = re.sub(
        r'DATE_SUB\(NOW\(\),\s*INTERVAL\s+%s\s+DAY\)',
        r"NOW() - INTERVAL '%s days'",
        content
    )
    
    # Pattern 2: DATE_SUB(NOW(), INTERVAL \d+ DAY) -> NOW() - INTERVAL '\d+ days'
    content = re.sub(
        r'DATE_SUB\(NOW\(\),\s*INTERVAL\s+(\d+)\s+DAY\)',
        r"NOW() - INTERVAL '\1 days'",
        content
    )
    
    # Pattern 3: DATE_SUB(NOW(), INTERVAL %s HOUR) -> NOW() - INTERVAL '%s hours'
    content = re.sub(
        r'DATE_SUB\(NOW\(\),\s*INTERVAL\s+%s\s+HOUR\)',
        r"NOW() - INTERVAL '%s hours'",
        content
    )
    
    # Pattern 4: DATE_SUB(NOW(), INTERVAL \d+ HOUR) -> NOW() - INTERVAL '\d+ hours'
    content = re.sub(
        r'DATE_SUB\(NOW\(\),\s*INTERVAL\s+(\d+)\s+HOUR\)',
        r"NOW() - INTERVAL '\1 hours'",
        content
    )
    
    return content

def process_file(filepath: Path) -> bool:
    """Process a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        if 'DATE_SUB' not in original_content:
            return False
        
        fixed_content = fix_date_sub(original_content)
        
        if original_content != fixed_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ Fixed: {filepath}")
            return True
        
        return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Process all Python files in Retailsights directory"""
    base_dir = Path(__file__).parent / 'Retailsights'
    
    if not base_dir.exists():
        print(f"Directory not found: {base_dir}")
        return
    
    fixed_count = 0
    for py_file in base_dir.rglob('*.py'):
        if process_file(py_file):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
