# PHASE 2A IMPLEMENTATION GUIDE

## Step 1: Update lms/models/__init__.py

Add imports for new models:

```python
# lms/models/__init__.py

# Existing imports
from .base import User, Department

# PHASE 2 MODELS - HIERARCHY
from .phase2_hierarchy import (
    Module,
    Section,
    Lesson,
    LessonResource,
    Prerequisite,
    LearningPath,
    LearningPathEnrollment,
    ModuleProgress,
    LessonProgress,
    LessonNote,
)

# PHASE 2 MODELS - ADAPTIVE LEARNING
from .phase2_adaptive import (
    KnowledgeConcept,
    ConceptLessonMapping,
    StudentMastery,
    ItemResponseTheory,
    AdaptivePath,
    ConceptQuizSequence,
    ContentRecommendation,
    RelatedContent,
    LearningGoal,
)

__all__ = [
    'User', 'Department',
    # Phase 2 Hierarchy
    'Module', 'Section', 'Lesson', 'LessonResource',
    'Prerequisite', 'LearningPath', 'LearningPathEnrollment',
    'ModuleProgress', 'LessonProgress', 'LessonNote',
    # Phase 2 Adaptive
    'KnowledgeConcept', 'ConceptLessonMapping', 'StudentMastery',
    'ItemResponseTheory', 'AdaptivePath', 'ConceptQuizSequence',
    'ContentRecommendation', 'RelatedContent', 'LearningGoal',
]
```

---

## Step 2: Create Migrations

```bash
# Create migration file for Phase 2 hierarchy
python manage.py makemigrations lms --name add_module_section_lesson

# Create migration file for Phase 2 adaptive learning
python manage.py makemigrations lms --name add_adaptive_learning_models

# Verify migrations look correct
python manage.py migrate --plan
```

---

## Step 3: DATA MIGRATION - Chapters to Lessons

Create a data migration:

```bash
python manage.py makemigrations lms --empty --name migrate_chapters_to_lessons
```

Edit the generated migration file (`lms/migrations/00XX_migrate_chapters_to_lessons.py`):

```python
# lms/migrations/XXXX_migrate_chapters_to_lessons.py

from django.db import migrations

def migrate_chapters_to_lessons(apps, schema_editor):
    """
    Migrate existing Chapter model data to new Module->Section->Lesson hierarchy
    """
    Chapter = apps.get_model('lms', 'Chapter')
    Course = apps.get_model('lms', 'Course')
    Module = apps.get_model('lms', 'Module')
    Section = apps.get_model('lms', 'Section')
    Lesson = apps.get_model('lms', 'Lesson')
    User = apps.get_model('auth', 'User')
    
    # Track created entities
    migration_log = {
        'modules_created': 0,
        'sections_created': 0,
        'lessons_created': 0,
    }
    
    # For each course, group chapters into modules
    for course in Course.objects.all():
        print(f"\nMigrating course: {course.title}")
        
        chapters = course.chapters.all().order_by('order')
        if not chapters.exists():
            print(f"  → No chapters found")
            continue
        
        # Create a single default module for this course
        module = Module.objects.create(
            course=course,
            title="Main Content",
            description=f"Auto-migrated from {course.chapters.count()} chapters",
            order=1,
            is_locked=False,
        )
        migration_log['modules_created'] += 1
        print(f"  ✓ Created module: {module.title}")
        
        # Create a single default section within the module
        section = Section.objects.create(
            module=module,
            title="Learning Materials",
            description="Auto-migrated course materials",
            order=1,
            estimated_minutes=sum(ch.estimated_minutes or 30 for ch in chapters),
        )
        migration_log['sections_created'] += 1
        print(f"  ✓ Created section: {section.title}")
        
        # Migrate each chapter to a lesson
        for chapter in chapters:
            lesson = Lesson.objects.create(
                section=section,
                title=chapter.title,
                lesson_type='video' if chapter.video_url else 'text',
                order=chapter.order,
                content=chapter.content or '',
                video_url=chapter.video_url or '',
                duration_minutes=chapter.estimated_minutes or 30,
                is_free_preview=chapter.is_free_preview,
                requires_previous=chapter.requires_previous_quiz_pass,
            )
            
            # Migrate document_file if it exists
            if hasattr(chapter, 'document_file') and chapter.document_file:
                lesson.document_file = chapter.document_file
                lesson.save()
            
            migration_log['lessons_created'] += 1
        
        print(f"  ✓ Migrated {chapters.count()} chapters to lessons")
    
    print(f"\n{'='*50}")
    print(f"MIGRATION SUMMARY:")
    print(f"  Modules created: {migration_log['modules_created']}")
    print(f"  Sections created: {migration_log['sections_created']}")
    print(f"  Lessons created: {migration_log['lessons_created']}")
    print(f"{'='*50}")

def reverse_migration(apps, schema_editor):
    """Rollback - delete all migrated lessons, sections, modules"""
    Lesson = apps.get_model('lms', 'Lesson')
    Section = apps.get_model('lms', 'Section')
    Module = apps.get_model('lms', 'Module')
    
    # Only delete auto-migrated items (description contains "Auto-migrated")
    Module.objects.filter(description__contains="Auto-migrated").delete()
    print("Reversed migration - deleted auto-migrated hierarchy")

class Migration(migrations.Migration):
    dependencies = [
        ('lms', '0004_chapter_document_file_alter_chapter_chapter_type_and_more'),  # Adjust to your last migration
    ]
    
    operations = [
        migrations.RunPython(migrate_chapters_to_lessons, reverse_migration),
    ]
```

Run the migrations:

```bash
python manage.py migrate
```

---

## Step 4: Update Django Admin

Create `lms/admin/phase2_admin.py`:

```python
# lms/admin/phase2_admin.py

from django.contrib import admin
from django.utils.html import format_html
from lms.models import (
    Module, Section, Lesson, LessonResource,
    ModuleProgress, LessonProgress, LessonNote,
    KnowledgeConcept, StudentMastery, AdaptivePath,
    LearningGoal,
)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'lesson_count', 'is_locked')
    list_filter = ('course', 'is_locked', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('course', 'order')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Access Control', {
            'fields': ('is_locked', 'unlock_condition'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'estimated_minutes')
    list_filter = ('module__course', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('module', 'order')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_display', 'lesson_type', 'order', 'duration_minutes')
    list_filter = ('lesson_type', 'is_free_preview', 'requires_previous', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('section', 'title', 'lesson_type', 'order', 'duration_minutes')
        }),
        ('Content', {
            'fields': ('content', 'video_url', 'document_file', 'downloadable_resources')
        }),
        ('Access Control', {
            'fields': ('is_free_preview', 'requires_previous')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def course_display(self, obj):
        return obj.course.title
    course_display.short_description = 'Course'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'module', 'status', 'completion_percentage')
    list_filter = ('status', 'created_at')
    search_fields = ('student__username', 'module__title')
    readonly_fields = ('completion_percentage',)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'status', 'completion_percentage')
    list_filter = ('status', 'created_at')
    search_fields = ('student__username', 'lesson__title')


@admin.register(StudentMastery)
class StudentMasteryAdmin(admin.ModelAdmin):
    list_display = ('student', 'concept', 'mastery_score', 'is_mastered')
    list_filter = ('concept__course', 'is_mastered')
    search_fields = ('student__username', 'concept__name')
    readonly_fields = ('knowledge_state', 'slip_probability', 'guess_probability')


@admin.register(AdaptivePath)
class AdaptivePathAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'current_lesson', 'adaptive_difficulty')
    list_filter = ('course', 'adaptive_difficulty')
    search_fields = ('student__username', 'course__title')


@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ('student', 'goal_title', 'target_grade', 'is_achieved', 'is_on_track')
    list_filter = ('is_achieved', 'created_at')
    search_fields = ('student__username', 'goal_title')
    readonly_fields = ('is_on_track',)
```

Update `lms/admin/__init__.py` to include the new admin classes:

```python
# lms/admin/__init__.py
from .phase2_admin import (
    ModuleAdmin, SectionAdmin, LessonAdmin,
    ModuleProgressAdmin, LessonProgressAdmin,
    StudentMasteryAdmin, AdaptivePathAdmin,
    LearningGoalAdmin,
)
```

---

## Step 5: Create API Endpoints

Create `lms/api/v2/hierarchy.py`:

```python
# lms/api/v2/hierarchy.py

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from lms.models import (
    Module, Section, Lesson, ModuleProgress, LessonProgress
)

class LessonSerializer(serializers.ModelSerializer):
    resources = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'lesson_type', 'order',
            'content', 'video_url', 'document_file',
            'duration_minutes', 'is_free_preview',
            'downloadable_resources', 'resources'
        )
    
    def get_resources(self, obj):
        return [{
            'name': r.name,
            'file': r.file.url,
            'size_mb': r.file_size_mb,
        } for r in obj.resources.all()]


class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = Section
        fields = ('id', 'title', 'order', 'estimated_minutes', 'lessons')


class ModuleSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = ('id', 'title', 'description', 'order', 'is_locked', 'sections')


class CourseHierarchySerializer(serializers.Serializer):
    """Full course structure"""
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    modules = ModuleSerializer(many=True)


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = (
            'id', 'lesson', 'status', 'video_progress_percentage',
            'time_spent_minutes', 'completed_at'
        )


# ViewSets

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [...]  # Add permissions
    
    @action(detail=True, methods=['get'])
    def module_progress(self, request, pk=None):
        """Get student's progress in this lesson"""
        lesson = self.get_object()
        progress = lesson.lesson_progress.filter(
            student=request.user
        ).first()
        
        if not progress:
            return Response(
                {'detail': 'No progress found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark lesson as complete"""
        lesson = self.get_object()
        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )
        progress.status = 'completed'
        progress.completed_at = timezone.now()
        progress.save()
        
        return Response(
            {'status': 'lesson completed'},
            status=status.HTTP_200_OK
        )


class CourseHierarchyViewSet(viewsets.ViewSet):
    """API to fetch full course structure"""
    
    @action(detail=False, methods=['get'])
    def structure(self, request):
        """Get course structure by slug"""
        course_slug = request.query_params.get('course')
        from lms.models import Course
        
        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        modules = course.modules.all()
        serializer = CourseHierarchySerializer({
            'course_id': course.id,
            'course_title': course.title,
            'modules': modules,
        })
        
        return Response(serializer.data)
```

Add to `lms/urls.py`:

```python
# In lms/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from lms.api.v2 import hierarchy

router = DefaultRouter()
router.register(r'lessons', hierarchy.LessonViewSet)
router.register(r'courses', hierarchy.CourseHierarchyViewSet, basename='course')

urlpatterns += [
    path('api/v2/', include(router.urls)),
]
```

---

## Step 6: Frontend Views - Course Structure Template

Create `lms/templates/lms/courses/course_structure.html`:

```html
{% extends "lms/base.html" %}
{% block title %}{{ course.title }} - Course Structure{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <h1>{{ course.title }}</h1>
    <p class="text-muted">{{ course.description }}</p>
    
    <div class="course-modules">
        {% for module in course.modules.all %}
        <div class="module-card card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    Module {{ module.order }}: {{ module.title }}
                </h5>
            </div>
            
            <div class="card-body">
                <p>{{ module.description }}</p>
                
                <div class="sections mt-3">
                    {% for section in module.sections.all %}
                    <div class="section-block mb-3 p-2 border rounded">
                        <h6>{{ section.title }}</h6>
                        <small class="text-muted">
                            {{ section.lessons.count }} lessons
                            • {{ section.total_estimated_time }} minutes
                        </small>
                        
                        <ul class="lesson-list mt-2">
                            {% for lesson in section.lessons.all %}
                            <li>
                                <a href="{% url 'lms:lesson_detail' course.slug lesson.id %}">
                                    <span class="badge badge-{{ lesson.lesson_type }}">
                                        {{ lesson.get_lesson_type_display|slice:":1" }}
                                    </span>
                                    {{ lesson.title }}
                                </a>
                                <span class="lesson-time">{{ lesson.duration_minutes }}min</span>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>

<style>
    .module-card { margin-bottom: 20px; }
    .section-block { background-color: #f9f9f9; }
    .lesson-list { list-style: none; padding-left: 0; }
    .lesson-list li { padding: 8px 0; }
    .lesson-time { float: right; font-size: 0.85em; color: #999; }
</style>
{% endblock %}
```

---

## Step 7: Testing Checklist

```bash
# Test migrations
python manage.py test lms.tests.test_migrations

# Test data migration
python manage.py migrate lms 00XX_migrate_chapters_to_lessons

# Verify data
python manage.py shell << EOF
from lms.models import Module, Section, Lesson, Course

course_count = Course.objects.count()
module_count = Module.objects.count()
lesson_count = Lesson.objects.count()

print(f"Courses: {course_count}")
print(f"Modules: {module_count}")
print(f"Lessons: {lesson_count}")

# Expected: Each course should have 1 module with lessons
for course in Course.objects.all():
    print(f"\n{course.title}:")
    print(f"  Modules: {course.modules.count()}")
    for module in course.modules.all():
        print(f"    Sections: {module.sections.count()}")
        for section in module.sections.all():
            print(f"      Lessons: {section.lessons.count()}")
EOF
```

---

## Step 8: Backward Compatibility

Keep `Chapter` model but deprecate it:

```python
# In lms/models/base.py

class Chapter(models.Model):
    """DEPRECATED: Use Lesson model instead"""
    # ... existing fields ...
    
    class Meta:
        # Mark as deprecated in Django admin
        verbose_name = "Chapter (DEPRECATED - Use Lesson)"
        verbose_name_plural = "Chapters (DEPRECATED - Use Lesson)"
```

---

## Next Steps

- ✅ Phase 2A: Course Hierarchy (above)
- ⏳ Phase 2B: Adaptive Learning (models created, need admin + views)
- ⏳ Phase 2C: Advanced Assessments
- ⏳ Phase 2D: Analytics Engine
- ⏳ Phase 2E: UI/UX Refinements

estimated timeline: **8-10 weeks** for full Phase 2

Ready to start implementation?
