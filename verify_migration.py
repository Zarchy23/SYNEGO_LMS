#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synego.settings')
django.setup()

from lms.models import User, Course, Chapter, Department

print("\n** PostgreSQL Migration Verification **\n")
print("Statistics:")
print(f"  Users: {User.objects.count()}")
print(f"  Departments: {Department.objects.count()}")
print(f"  Courses: {Course.objects.count()}")
print(f"  Chapters: {Chapter.objects.count()}")

print(f"\nCourses:")
for course in Course.objects.all():
    dept = course.department.name if course.department else "No Department"
    print(f"  - {course.title}")
    print(f"    Department: {dept}")
    print(f"    Chapters: {course.chapters.count()}")
    for chapter in course.chapters.all():
        print(f"      * Ch {chapter.order}: {chapter.title}")

print(f"\nUsers:")
for user in User.objects.all():
    print(f"  - {user.username} (Role: {user.role})")

print("\n** Migration Complete! **\n")
