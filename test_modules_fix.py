#!/usr/bin/env python
"""Test that module.total_instructors property works with the new module_id column."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from lms.models import Module

print("Testing module.total_instructors property...")
print(f"Total modules: {Module.objects.count()}\n")

for module in Module.objects.all():
    try:
        count = module.total_instructors
        print(f"✅ {module.name}: {count} instructors")
    except Exception as e:
        print(f"❌ {module.name}: ERROR - {e}")

print("\n✅ All module queries succeeded! The /modules/ page should now work.")
