#!/usr/bin/env python3
"""Refactor Department → Module and dept_head → module_head across the project"""

import os
import re
from pathlib import Path

def refactor_file(filepath):
    """Apply replacements to a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original
    
    # Key replacements
    replacements = [
        (r'Department\.objects', 'Module.objects'),
        (r"'dept_head'", "'module_head'"),
        (r'"dept_head"', '"module_head"'),
        (r'def department_head_dashboard', 'def module_head_dashboard'),
        (r'def department_list', 'def module_list'),
        (r'def department_detail', 'def module_detail'),
        (r'request\.user\.department', 'request.user.module'),
        (r"'department': department", "'module': module"),
        (r"'department_head_dashboard'", "'module_head_dashboard'"),
        (r"'department_list'", "'module_list'"),
        (r"'department_detail'", "'module_detail'"),
        (r"'departments':", "'modules':"),
        (r"'selected_department'", "'selected_module'"),
        (r'department_param', 'module_param'),
        (r"'lms/departments/", "'lms/modules/"),
        (r'lms/department_', 'lms/module_'),
        (r'department_head_dashboard', 'module_head_dashboard'),
        (r'department_list', 'module_list'),
        (r'department_detail', 'module_detail'),
        (r'Department\(', 'Module('),
        (r'\bDepartment\b', 'Module'),
    ]
    
    for old_pattern, new_string in replacements:
        content = re.sub(old_pattern, new_string, content)
    
    # Only write if changed
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

files_to_refactor = [
    'lms/views.py',
    'lms/admin/__init__.py',
    'lms/urls.py',
    'lms/context_processors.py',
    'lms/permissions.py',
    'lms/role_permissions.py',
]

modified = 0
for filepath in files_to_refactor:
    full_path = Path(filepath)
    if full_path.exists():
        if refactor_file(str(full_path)):
            print(f'✓ Modified: {filepath}')
            modified += 1
        else:
            print(f'✗ No changes: {filepath}')
    else:
        print(f'✗ Not found: {filepath}')

print(f'\nModified {modified} file(s)')
