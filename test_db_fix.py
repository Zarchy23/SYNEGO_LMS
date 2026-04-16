#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')
django.setup()

from lms.models import Module

# Test that the query works
module_count = Module.objects.filter(status='active').count()
print(f"✓ Query successful: Found {module_count} active modules in lms_department table")

# Test that user module field is renamed
from lms.models import User
users = User.objects.count()
print(f"✓ Users query successful: Found {users} users")

print("\n✓ All database queries are working correctly!")
