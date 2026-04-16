#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')
django.setup()

from django.db import connection

print("\n=== lms_module columns ===")
with connection.cursor() as cursor:
    cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'lms_module'
    ORDER BY ordinal_position
    """)
    for row in cursor.fetchall():
        print(f'{row[0]:30} {row[1]}')

print("\n=== lms_department columns ===")
with connection.cursor() as cursor:
    cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'lms_department'
    ORDER BY ordinal_position
    """)
    for row in cursor.fetchall():
        print(f'{row[0]:30} {row[1]}')
