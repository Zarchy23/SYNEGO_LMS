#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')
django.setup()

from lms.models import Module, Course
from django.utils import timezone

# Setup 3 modules
print("Setting up modules...")
tech = Module.objects.filter(code='TECH').first() or Module.objects.filter(name='Technical Module').first()
if tech is None:
    tech = Module.objects.create(
        name='Technical Module',
        code='TECH',
        slug='technical-module',
        status='active',
        infrastructure='Workshop facilities, labs, training equipment',
        resources='Tools, machinery, safety equipment'
    )
print(f"✓ Technical Module")

nontech = Module.objects.filter(code='NONTECH').first()
if nontech is None:
    nontech = Module.objects.create(
        name='Non-Technical Module',
        code='NONTECH',
        slug='non-technical-module',
        status='active',
        infrastructure='Classroom facilities, computer labs',
        resources='Software, business tools, training materials'
    )
print(f"✓ Non-Technical Module")

lead = Module.objects.filter(code='LEAD').first()
if lead is None:
    lead = Module.objects.create(
        name='Leadership Module',
        code='LEAD',
        slug='leadership-module',
        status='active',
        infrastructure='Conference facilities, seminar rooms',
        resources='Leadership frameworks, case studies, coaching tools'
    )
print(f"✓ Leadership Module")

mods = {'TECH': tech, 'NONTECH': nontech, 'LEAD': lead}

# All 61 courses
courses_data = [
    ('Bricklaying and Blockwork', 'BT-001', 'beginner', 'technical', 'TECH'),
    ('Carpentry and Joinery', 'BT-002', 'intermediate', 'technical', 'TECH'),
    ('Plastering and Rendering', 'BT-003', 'beginner', 'technical', 'TECH'),
    ('Wall and Floor Tiling', 'BT-004', 'beginner', 'technical', 'TECH'),
    ('Painting and Decorating', 'BT-005', 'beginner', 'technical', 'TECH'),
    ('Scaffolding and Formwork', 'BT-006', 'beginner', 'technical', 'TECH'),
    ('Electrical Installation', 'EME-001', 'intermediate', 'technical', 'TECH'),
    ('Solar PV System Design', 'EME-002', 'intermediate', 'technical', 'TECH'),
    ('Solar Battery Storage', 'EME-003', 'intermediate', 'technical', 'TECH'),
    ('Plumbing and Pipe-fitting', 'EME-004', 'intermediate', 'technical', 'TECH'),
    ('Basic Mechanical Maintenance', 'EME-005', 'beginner', 'technical', 'TECH'),
    ('Electrical Safety and Compliance', 'EME-006', 'beginner', 'technical', 'TECH'),
    ('Engineering Surveying', 'CEI-001', 'intermediate', 'technical', 'TECH'),
    ('Road Construction and Maintenance', 'CEI-002', 'intermediate', 'technical', 'TECH'),
    ('Concrete Technology and Testing', 'CEI-003', 'beginner', 'technical', 'TECH'),
    ('Structural Design Fundamentals', 'CEI-004', 'intermediate', 'technical', 'TECH'),
    ('Materials Testing Laboratory', 'CEI-005', 'beginner', 'technical', 'TECH'),
    ('Environmental Compliance in Construction', 'CEI-006', 'beginner', 'technical', 'TECH'),
    ('Heavy Motor Vehicle Licensing', 'DPO-001', 'intermediate', 'technical', 'TECH'),
    ('Excavator Operation', 'DPO-002', 'beginner', 'technical', 'TECH'),
    ('Crane Operation', 'DPO-003', 'beginner', 'technical', 'TECH'),
    ('Grader and Bulldozer Operation', 'DPO-004', 'beginner', 'technical', 'TECH'),
    ('Forklift Operation', 'DPO-005', 'beginner', 'technical', 'TECH'),
    ('Defensive Driving Course', 'DPO-006', 'beginner', 'technical', 'TECH'),
    ('Road Craft and Professional Driver Development', 'DPO-007', 'intermediate', 'technical', 'TECH'),
    ('HAZCHEM Dangerous Goods Transportation', 'DPO-008', 'intermediate', 'technical', 'TECH'),
    ('Cross-Border Transportation Compliance', 'DPO-009', 'beginner', 'technical', 'TECH'),
    ('Mechanical Theory for Operators', 'DPO-010', 'intermediate', 'technical', 'TECH'),
    ('Agricultural Business Management', 'AMI-001', 'intermediate', 'technical', 'TECH'),
    ('Irrigation Systems Installation', 'AMI-002', 'intermediate', 'technical', 'TECH'),
    ('Mining Safety and Compliance', 'AMI-003', 'intermediate', 'technical', 'TECH'),
    ('Blasting and Explosives Safety', 'AMI-004', 'intermediate', 'technical', 'TECH'),
    ('Loading, Hauling, and Stockpile Management', 'AMI-005', 'intermediate', 'technical', 'TECH'),
    ('Plastics Processing and Recycling', 'AMI-006', 'intermediate', 'technical', 'TECH'),
    ('Waste Management and Environmental Awareness', 'AMI-007', 'beginner', 'technical', 'TECH'),
    ('Construction Supervision', 'CPM-001', 'intermediate', 'technical', 'TECH'),
    ('Quantity Surveying', 'CPM-002', 'advanced', 'technical', 'TECH'),
    ('Contract Administration', 'CPM-003', 'intermediate', 'technical', 'TECH'),
    ('IT Fundamentals and Digital Literacy', 'BFT-001', 'beginner', 'technical', 'TECH'),
    ('Network Administration and Cybersecurity Basics', 'BFT-002', 'intermediate', 'technical', 'TECH'),
    ('Business Planning and Enterprise Development', 'BE-001', 'intermediate', 'non_technical', 'NONTECH'),
    ('Marketing and Customer Relationship Management', 'BE-002', 'intermediate', 'non_technical', 'NONTECH'),
    ('Microfinance Operations and Credit Management', 'BE-003', 'intermediate', 'non_technical', 'NONTECH'),
    ('Financial Management and Accounting Fundamentals', 'FA-001', 'intermediate', 'non_technical', 'NONTECH'),
    ('Human Resources Management Fundamentals', 'HRA-001', 'intermediate', 'non_technical', 'NONTECH'),
    ('Health, Safety and Environment Management', 'HSC-001', 'intermediate', 'non_technical', 'NONTECH'),
    ('Transport Safety Management', 'HSC-002', 'beginner', 'non_technical', 'NONTECH'),
    ('Advanced Executive Driver Training', 'PD-001', 'advanced', 'non_technical', 'NONTECH'),
    ('Workplace Communication and Professionalism', 'WCP-001', 'beginner', 'non_technical', 'NONTECH'),
    ('Customer Service Excellence', 'CSE-001', 'beginner', 'non_technical', 'NONTECH'),
    ('Project Management', 'PPM-001', 'advanced', 'leadership', 'LEAD'),
    ('Construction Law and Ethics', 'LC-001', 'advanced', 'leadership', 'LEAD'),
    ('Management Development 1: Strategic Planning', 'MD-001', 'advanced', 'leadership', 'LEAD'),
    ('Management Development 2: Organizational Excellence', 'MD-002', 'advanced', 'leadership', 'LEAD'),
    ('Supervisory and Team Leadership Skills', 'STL-001', 'intermediate', 'leadership', 'LEAD'),
    ('Motivation and Performance Excellence', 'PD-001L', 'beginner', 'leadership', 'LEAD'),
    ('Emotional Intelligence for Leaders', 'PD-002L', 'intermediate', 'leadership', 'LEAD'),
    ('Disciplinary Handling and Conflict Resolution', 'PM-001', 'intermediate', 'leadership', 'LEAD'),
    ('Strategic Thinking and Business Acumen', 'PM-002', 'advanced', 'leadership', 'LEAD'),
]

print(f"\nSeeding {len(courses_data)} courses...")
created = updated = 0

for title, code, difficulty, module_type, mod_code in courses_data:
    module = mods[mod_code]
    defaults = {
        'department': module,
        'title': title,
        'description': f'{title} - Professional development course',
        'learning_objectives': f'Master the competencies of {title.lower()}',
        'estimated_hours': 40,
        'status': 'published',
        'is_active': True,
        'module_type': module_type,
        'published_at': timezone.now(),
        'duration': '3-6 months',
        'difficulty': difficulty,
    }
    course, is_created = Course.objects.get_or_create(code=code, defaults=defaults)
    if is_created:
        created += 1
    else:
        updated += 1

print(f"\n{'='*50}")
print(f"Seeding Complete!")
print(f"{'='*50}")
print(f"Created: {created} courses")
print(f"Updated: {updated} courses")

tech_count = Course.objects.filter(module_type='technical').count()
nontech_count = Course.objects.filter(module_type='non_technical').count()
lead_count = Course.objects.filter(module_type='leadership').count()

print(f"\nCourse Distribution:")
print(f"  Technical:      {tech_count}")
print(f"  Non-Technical:  {nontech_count}")
print(f"  Leadership:     {lead_count}")
print(f"  TOTAL:          {tech_count + nontech_count + lead_count}")
