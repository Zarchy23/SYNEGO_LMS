#!/usr/bin/env python
"""
Seed the database with Synego Training Institute's three-module course structure.
Implements 61 courses across Technical, Non-Technical, and Leadership categories.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')
django.setup()

from lms.models import Module, Course
from django.utils import timezone

# First, ensure we have the three main modules
modules_data = [
    {
        'name': 'Technical Module',
        'code': 'TECH',
        'description': 'Hands-on skills, practical training, and trade-specific competencies',
        'mission': 'Deliver world-class technical training for immediate job readiness',
        'infrastructure': 'Workshop facilities, labs, training equipment',
        'resources': 'Tools, machinery, safety equipment',
        'min_instructors': 2,
        'max_capacity': 100,
    },
    {
        'name': 'Non-Technical Module',
        'code': 'NONTECH',
        'description': 'Business operations, soft skills, and administrative competencies',
        'mission': 'Develop business acumen and operational excellence',
        'infrastructure': 'Classroom facilities, computer labs',
        'resources': 'Software, business tools, training materials',
        'min_instructors': 1,
        'max_capacity': 80,
    },
    {
        'name': 'Leadership Module',
        'code': 'LEAD',
        'description': 'Strategic thinking, people management, and organizational development',
        'mission': 'Build visionary leaders for organizational excellence',
        'infrastructure': 'Conference facilities, seminar rooms',
        'resources': 'Leadership frameworks, case studies, coaching tools',
        'min_instructors': 1,
        'max_capacity': 60,
    },
]

print("Creating/updating three-module structure...")
modules_map = {}
for mod_data in modules_data:
    module, created = Module.objects.get_or_create(
        code=mod_data['code'],
        defaults={
            'name': mod_data['name'],
            'slug': mod_data['code'].lower(),
            'description': mod_data['description'],
            'mission': mod_data['mission'],
            'infrastructure': mod_data['infrastructure'],
            'resources': mod_data['resources'],
            'min_instructors': mod_data['min_instructors'],
            'max_capacity': mod_data['max_capacity'],
            'status': 'active',
        }
    )
    modules_map[mod_data['code']] = module
    status = "Created" if created else "Updated"
    print(f"  ✓ {status}: {module.name} (ID: {module.id})")

# Now create all 61 courses
courses_data = [
    # ============================================
    # MODULE 1: TECHNICAL COURSES (42)
    # ============================================
    
    # 1.1 Building Trades (6)
    {'title': 'Bricklaying and Blockwork', 'code': 'BT-001', 'duration': '3 – 6 months', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Carpentry and Joinery', 'code': 'BT-002', 'duration': '6 – 12 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Plastering and Rendering', 'code': 'BT-003', 'duration': '3 months', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Wall and Floor Tiling', 'code': 'BT-004', 'duration': '3 months', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Painting and Decorating', 'code': 'BT-005', 'duration': '3 months', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Scaffolding and Formwork', 'code': 'BT-006', 'duration': '2 – 4 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    
    # 1.2 Electrical, Mechanical & Energy Engineering (6)
    {'title': 'Electrical Installation (Domestic & Commercial)', 'code': 'EME-001', 'duration': '6 – 12 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Solar PV System Design and Installation', 'code': 'EME-002', 'duration': '3 – 6 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Solar Battery Storage and Maintenance', 'code': 'EME-003', 'duration': '4 – 8 weeks', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    {'title': 'Plumbing and Pipe-fitting', 'code': 'EME-004', 'duration': '6 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Basic Mechanical Maintenance', 'code': 'EME-005', 'duration': '3 months', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Electrical Safety and Compliance', 'code': 'EME-006', 'duration': '2 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    
    # 1.3 Civil Engineering & Infrastructure (6)
    {'title': 'Engineering Surveying', 'code': 'CEI-001', 'duration': '6 – 12 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Road Construction and Maintenance', 'code': 'CEI-002', 'duration': '6 – 12 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Concrete Technology and Testing', 'code': 'CEI-003', 'duration': '3 months', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Short Course'},
    {'title': 'Structural Design Fundamentals', 'code': 'CEI-004', 'duration': '6 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Materials Testing Laboratory Practice', 'code': 'CEI-005', 'duration': '4 – 8 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    {'title': 'Environmental Compliance in Construction', 'code': 'CEI-006', 'duration': '2 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    
    # 1.4 Driver & Plant Operator Training (10)
    {'title': 'Heavy Motor Vehicle (HMV) Licensing', 'code': 'DPO-001', 'duration': '4 – 8 weeks', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Licence Training'},
    {'title': 'Excavator Operation', 'code': 'DPO-002', 'duration': '4 – 6 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Crane Operation', 'code': 'DPO-003', 'duration': '4 – 6 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Grader and Bulldozer Operation', 'code': 'DPO-004', 'duration': '4 – 6 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Forklift Operation', 'code': 'DPO-005', 'duration': '1 – 2 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Defensive Driving Course', 'code': 'DPO-006', 'duration': '3 – 5 days', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Road Craft and Professional Driver Development', 'code': 'DPO-007', 'duration': '2 – 3 weeks', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'HAZCHEM — Dangerous Goods Transportation', 'code': 'DPO-008', 'duration': '3 – 5 days', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Cross-Border Transportation Compliance', 'code': 'DPO-009', 'duration': '3 days', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    {'title': 'Mechanical Theory for Operators', 'code': 'DPO-010', 'duration': '2 – 4 weeks', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    
    # 1.5 Agribusiness, Mining & Industrial (7)
    {'title': 'Agricultural Business Management', 'code': 'AMI-001', 'duration': '6 – 12 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Irrigation Systems Installation and Management', 'code': 'AMI-002', 'duration': '3 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Mining Safety and Compliance', 'code': 'AMI-003', 'duration': '6 – 8 weeks', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Blasting and Explosives Safety Awareness', 'code': 'AMI-004', 'duration': '2 – 3 days', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    {'title': 'Loading, Hauling, and Stockpile Management', 'code': 'AMI-005', 'duration': '2 – 3 weeks', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    {'title': 'Plastics Processing and Recycling Technology', 'code': 'AMI-006', 'duration': '3 – 6 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Waste Management and Environmental Awareness', 'code': 'AMI-007', 'duration': '1 – 2 weeks', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    
    # 1.6 Construction & Project Management (Technical Track) (3)
    {'title': 'Construction Supervision', 'code': 'CPM-001', 'duration': '6 – 12 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Quantity Surveying', 'code': 'CPM-002', 'duration': '12 months', 'difficulty': 'advanced', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate/Diploma'},
    {'title': 'Contract Administration', 'code': 'CPM-003', 'duration': '4 – 6 weeks', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Short Course'},
    
    # 1.7 Business, Finance & Technology (Technical Track) (2)
    {'title': 'IT Fundamentals and Digital Literacy', 'code': 'BFT-001', 'duration': '3 months', 'difficulty': 'beginner', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    {'title': 'Network Administration and Cybersecurity Basics', 'code': 'BFT-002', 'duration': '3 – 6 months', 'difficulty': 'intermediate', 'module_type': 'technical', 'module': 'TECH', 'level': 'Certificate'},
    
    # ============================================
    # MODULE 2: NON-TECHNICAL COURSES (10)
    # ============================================
    
    # 2.1 Business & Entrepreneurship (3)
    {'title': 'Business Planning and Enterprise Development', 'code': 'BE-001', 'duration': '3 months', 'difficulty': 'intermediate', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Certificate'},
    {'title': 'Marketing and Customer Relationship Management', 'code': 'BE-002', 'duration': '3 months', 'difficulty': 'intermediate', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Certificate'},
    {'title': 'Microfinance Operations and Credit Management', 'code': 'BE-003', 'duration': '6 months', 'difficulty': 'intermediate', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Certificate/Diploma'},
    
    # 2.2 Finance & Accounting (1)
    {'title': 'Financial Management and Accounting Fundamentals', 'code': 'FA-001', 'duration': '3 – 6 months', 'difficulty': 'intermediate', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Certificate'},
    
    # 2.3 Human Resources & Administration (1)
    {'title': 'Human Resources Management Fundamentals', 'code': 'HRA-001', 'duration': '3 months', 'difficulty': 'intermediate', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Certificate'},
    
    # 2.4 Health, Safety & Compliance (2)
    {'title': 'Health, Safety and Environment (HSE) Management', 'code': 'HSC-001', 'duration': '3 months', 'difficulty': 'intermediate', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Certificate'},
    {'title': 'Transport Safety Management', 'code': 'HSC-002', 'duration': '3 days', 'difficulty': 'beginner', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Short Course'},
    
    # 2.5 Professional Driving (Non-Technical Track) (1)
    {'title': 'Advanced Executive Driver Training', 'code': 'PD-001', 'duration': '5 days', 'difficulty': 'advanced', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Certificate'},
    
    # Additional Non-Technical Courses (2)
    {'title': 'Workplace Communication and Professionalism', 'code': 'WCP-001', 'duration': '2 weeks', 'difficulty': 'beginner', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Short Course'},
    {'title': 'Customer Service Excellence', 'code': 'CSE-001', 'duration': '2 weeks', 'difficulty': 'beginner', 'module_type': 'non_technical', 'module': 'NONTECH', 'level': 'Short Course'},
    
    # ============================================
    # MODULE 3: LEADERSHIP & MANAGEMENT (9)
    # ============================================
    
    # 3.1 Project & Program Management (1)
    {'title': 'Project Management', 'code': 'PPM-001', 'duration': '6 – 12 months', 'difficulty': 'advanced', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Certificate/Diploma'},
    
    # 3.2 Legal & Compliance (1)
    {'title': 'Construction Law and Ethics', 'code': 'LC-001', 'duration': '2 – 4 weeks', 'difficulty': 'advanced', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Short Course'},
    
    # 3.3 Management Development (2)
    {'title': 'Management Development 1: Strategic Planning', 'code': 'MD-001', 'duration': '3 weeks', 'difficulty': 'advanced', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Short Course'},
    {'title': 'Management Development 2: Organizational Excellence', 'code': 'MD-002', 'duration': '3 weeks', 'difficulty': 'advanced', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Short Course'},
    
    # 3.4 Supervisory & Team Leadership (1)
    {'title': 'Supervisory and Team Leadership Skills', 'code': 'STL-001', 'duration': '2 – 4 weeks', 'difficulty': 'intermediate', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Short Course'},
    
    # 3.5 Personal Development & Soft Skills (2)
    {'title': 'Motivation and Performance Excellence', 'code': 'PD-001L', 'duration': '1 week', 'difficulty': 'beginner', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Short Course'},
    {'title': 'Emotional Intelligence for Leaders', 'code': 'PD-002L', 'duration': '2 weeks', 'difficulty': 'intermediate', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Short Course'},
    
    # 3.6 People Management (1)
    {'title': 'Disciplinary Handling and Conflict Resolution', 'code': 'PM-001', 'duration': '1 week', 'difficulty': 'intermediate', 'module_type': 'leadership', 'module': 'LEAD', 'level': 'Short Course'},
]

print(f"\nCreating {len(courses_data)} courses...")
created_count = 0
updated_count = 0
error_count = 0

for idx, course_data in enumerate(courses_data, 1):
    try:
        module_code = course_data.pop('module')
        module_type = course_data.pop('module_type')
        level = course_data.pop('level')
        
        module = modules_map[module_code]
        
        defaults = {
            'description': f"{course_data['title']} - {level} level course designed to develop practical competencies.",
            'learning_objectives': f"Upon completion, participants will have mastered the key competencies of {course_data['title'].lower()}.",
            'prerequisites': 'Basic education or equivalent experience',
            'estimated_hours': 40,
            'status': 'published',
            'is_active': True,
            'module_type': module_type,
            'published_at': timezone.now(),
            **course_data
        }
        
        course, created = Course.objects.get_or_create(
            code=course_data['code'],
            defaults={'department': module, **defaults}
        )
        
        if created:
            created_count += 1
        else:
            # Update existing course
            Course.objects.filter(pk=course.pk).update(**defaults)
            updated_count += 1
        
        if idx % 10 == 0:
            print(f"  [{idx}/{len(courses_data)}] Progress...")
    
    except Exception as e:
        error_count += 1
        print(f"  ✗ Error creating course {idx}: {str(e)}")

print(f"\n✓ Course Seeding Complete!")
print(f"  - Created: {created_count} new courses")
print(f"  - Updated: {updated_count} existing courses")
print(f"  - Errors: {error_count}")

# Print category summary
print("\n=== Course Distribution by Module Type ===")
tech_count = Course.objects.filter(module_type='technical').count()
nontech_count = Course.objects.filter(module_type='non_technical').count()
lead_count = Course.objects.filter(module_type='leadership').count()

print(f"Technical Courses: {tech_count}")
print(f"Non-Technical Courses: {nontech_count}")
print(f"Leadership Courses: {lead_count}")
print(f"TOTAL: {tech_count + nontech_count + lead_count} courses")

print("\n=== Module Summary ===")
for mod in Module.objects.all():
    course_count = mod.courses.count()
    print(f"{mod.name}: {course_count} courses")
