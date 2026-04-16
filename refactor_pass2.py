#!/usr/bin/env python3
"""Second pass refactoring for Department → Module"""

import os
import re
from pathlib import Path

def refactor_pass2(filepath):
    """Apply second-pass replacements"""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original
    
    # More specific replacements
    replacements = [
        # Fix variable naming issues
        (r'(\s)department = request\.user\.module', r'\1module = request.user.module'),
        (r'(\s)department\.courses', r'\1module.courses'),
        (r'(\s)department\.members', r'\1module.members'),
        (r'(\s)department\.name', r'\1module.name'),
        
        # Comments and docstrings
        (r'"""List all departments"""', '"""List all modules"""'),
        (r'"""Module detail page"""', '"""Module detail page"""'),
        (r'# Department Views', '# Module Views'),
        (r'#.*(?i)department', '# Module'),
        
        # Variable names in module context
        (r'get_object_or_404\(Module,.*?\) as department', 'get_object_or_404(Module, ...) as module'),
        (r'\.filter\(.*?\) as department', '.filter(...) as module'),
        
        # Path changes
        (r"path\('departments/", "path('modules/"),
        (r"path\('admin-panel/departments/", "path('admin-panel/modules/"),
        
        # Admin field names  
        (r"'department',\s*'is_approved'", "'module', 'is_approved'"),
        (r"'department': department", "'module': module"),
    ]
    
    for old_pattern, new_string in replacements:
        content = re.sub(old_pattern, new_string, content, flags=re.IGNORECASE if 'comment' in old_pattern else 0)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Apply to specific files
files = [
    'lms/views.py',
    'lms/urls.py',
    'lms/admin/__init__.py',
]

for filepath in files:
    if Path(filepath).exists():
        refactor_pass2(filepath)
        print(f'✓ Pass 2: {filepath}')

print('Second pass complete')
