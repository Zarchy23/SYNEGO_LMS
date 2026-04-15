#!/usr/bin/env python
"""
Database migration script: SQLite -> PostgreSQL
Exports data from SQLite and imports into PostgreSQL
"""
import os
import sys
import django
import json
from io import StringIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def switch_to_sqlite():
    """Temporarily switch to SQLite"""
    from django.conf import settings
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(settings.BASE_DIR, 'db.sqlite3'),
        }
    }
    print("✓ Switched to SQLite")

def switch_to_postgres():
    """Switch back to PostgreSQL"""
    from django.conf import settings
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'synego_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 600,
        }
    }
    print("✓ Switched to PostgreSQL")

def export_data():
    """Export data from SQLite"""
    from django.core import serializers
    from lms.models import User, Course, Chapter, Department, Enrollment, Quiz, Assignment
    from django.contrib.auth.models import Group
    
    # Close the current connection
    from django.db import connection
    connection.close()
    
    # Export
    output = StringIO()
    data = serializers.serialize('json', 
        list(User.objects.all()) +
        list(Department.objects.all()) +
        list(Course.objects.all()) +
        list(Chapter.objects.all()) +
        list(Quiz.objects.all()) +
        list(Assignment.objects.all()) +
        list(Enrollment.objects.all()) +
        list(Group.objects.all()),
    stream=output, indent=2)
    
    # Write to file without BOM
    with open('migration_data.json', 'w', encoding='utf-8') as f:
        f.write(output.getvalue())
    
    print(f"✓ Exported data to migration_data.json ({len(output.getvalue())} characters)")

def import_data():
    """Import data into PostgreSQL"""
    from django.core import serializers
    from django.db import connection
    
    # Close connection
    connection.close()
    
    # Read and import
    with open('migration_data.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    for obj in serializers.deserialize('json', content):
        obj.save()
    
    print("✓ Imported data into PostgreSQL")

if __name__ == '__main__':
    print("\n🔄 Starting database migration: SQLite → PostgreSQL\n")
    
    try:
        # Step 1: Setup Django with SQLite
        switch_to_sqlite()
        django.setup()
        
        # Step 2: Export from SQLite
        print("\n📤 Exporting data from SQLite...")
        export_data()
        
        # Step 3: Reconfigure to PostgreSQL
        print("\n🔌 Connecting to PostgreSQL...")
        switch_to_postgres()
        
        # Step 4: Reload Django with PostgreSQL
        from django.apps import apps
        apps.app_configs = {}
        django.setup()
        
        # Step 5: Import to PostgreSQL
        print("\n📥 Importing data into PostgreSQL...")
        import_data()
        
        print("\n✅ Migration complete!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
