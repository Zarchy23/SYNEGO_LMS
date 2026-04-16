#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')
django.setup()

from lms.models import Module

# Update the module name
module = Module.objects.get(code='CEI')
old_name = module.name
module.name = "Technical Module"
module.save()

print(f"✓ Updated module name from '{old_name}' to '{module.name}'")
