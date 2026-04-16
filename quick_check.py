import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'synego.settings'
django.setup()
from lms.models import User, Course
print(f'Users: {User.objects.count()}')
print(f'Courses: {Course.objects.count()}')
for c in Course.objects.all():
    print(f'  {c.title} - {c.chapters.count()} chapters')
