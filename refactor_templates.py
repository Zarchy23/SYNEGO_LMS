#!/usr/bin/env python3
"""Refactor all template files: Department → Module"""

import re
from pathlib import Path

def refactor_templates(template_dir='lms/templates/lms'):
    """Refactor all HTML templates recursively"""
    template_path = Path(template_dir)
    modified_count = 0
    
    # Template variable replacements (order matters!)
    replacements = [
        # URL names and context vars
        ('{% url \'lms:department_list\'', '{% url \'lms:module_list\''),
        ('{% url \'lms:department_detail\'', '{% url \'lms:module_detail\''),
        ('{% url \'lms:admin_departments\'', '{% url \'lms:admin_modules\''),
        ('{% url \'lms:admin_add_department\'', '{% url \'lms:admin_add_module\''),
        ('{% url \'lms:admin_edit_department\'', '{% url \'lms:admin_edit_module\''),
        
        # HTML form fields and selects
        ('name="department"', 'name="module"'),
        ('name="department_id"', 'name="module_id"'),
        ('id="department_id"', 'id="module_id"'),
        ('for="department_id"', 'for="module_id"'),
        ('Department', 'Module'),
        ('departments', 'modules'),
        ('department', 'module'),
        
        # CSS classes
        ('.departments-list', '.modules-list'),
        ('.department-chip', '.module-chip'),
        ('.department-hero', '.module-hero'),
        ('.department-', '.module-'),
    ]
    
    # Process all HTML files
    for html_file in template_path.rglob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        
        # Apply replacements (carefully preserve course.department field)
        for old, new in replacements:
            # Dont change course.department - that's a ForeignKey field
            if 'course.department' not in old:
                content = content.replace(old, new)
        
        # Preserve course.department field access (revert if damaged)
        content = content.replace('course.module', 'course.department')
        
        if content != original_content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            modified_count += 1
            print(f'✓ {html_file.relative_to(template_path)}')
    
    return modified_count

# Run it
count = refactor_templates()
print(f'\n✓ Modified {count} template file(s)')
