# lms/models/phase2_hierarchy.py
"""
Phase 2: Multi-level Course Hierarchy Models
Replaces Chapter with Module → Section → Lesson structure
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class CourseModule(models.Model):
    """Top-level course grouping"""
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='course_modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    
    # Access control
    is_locked = models.BooleanField(default=False)
    unlock_condition = models.CharField(
        max_length=100, 
        blank=True,
        help_text="e.g., 'previous_module:score:80' or 'course:quiz:pass'"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = [['course', 'order']]
        db_table = 'lms_module'
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} > Module {self.order}: {self.title}"
    
    @property
    def lesson_count(self):
        return self.sections.aggregate(
            count=models.Count('lessons')
        )['count'] or 0
    
    @property
    def is_accessible_by(self, user):
        """Check if user can access this module"""
        if not self.is_locked:
            return True
        
        if self.unlock_condition and user.is_authenticated:
            # Parse unlock condition
            # Format: "previous_module:score:80" or "course:quiz:1:pass"
            return self._check_unlock_condition(user)
        
        return False
    
    def _check_unlock_condition(self, user):
        """Evaluate unlock conditions"""
        try:
            parts = self.unlock_condition.split(':')
            condition_type = parts[0]
            
            if condition_type == 'previous_module':
                module_order = int(parts[1])
                required_score = int(parts[2]) if len(parts) > 2 else 80
                
                # Check if user completed previous module with required score
                prev_module = Module.objects.get(
                    course=self.course,
                    order=module_order
                )
                # TODO: Check ModuleProgress
                return True
        except:
            return False
        
        return False


class Section(models.Model):
    """Group of lessons within a module"""
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    
    # Optional: estimated time
    estimated_minutes = models.PositiveIntegerField(default=30)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['module', 'order']
        indexes = [
            models.Index(fields=['module', 'order']),
        ]
    
    def __str__(self):
        return f"{self.module.title} > {self.title}"
    
    @property
    def total_estimated_time(self):
        """Sum of all lesson durations"""
        return self.lessons.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0


class Lesson(models.Model):
    """Individual learning unit (replaces Chapter)"""
    LESSON_TYPES = (
        ('video', 'Video Lesson'),
        ('text', 'Text Lesson'),
        ('rich_media', 'Rich Media (Interactive)'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('discussion', 'Discussion Forum'),
        ('project', 'Project'),
        ('resource', 'Resource Download'),
        ('external', 'External Content (SCORM/LTI)'),
    )
    
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES)
    order = models.PositiveIntegerField(default=1)
    
    # Content
    content = models.TextField(
        blank=True,
        help_text="HTML or rich text content for lesson"
    )
    video_url = models.URLField(blank=True, help_text="YouTube, Vimeo, etc.")
    document_file = models.FileField(
        upload_to='lesson_documents/%Y/%m/',
        blank=True,
        help_text="PDF, PowerPoint, Excel files"
    )
    
    # Learning duration
    duration_minutes = models.PositiveIntegerField(default=30)
    
    # Access control
    is_free_preview = models.BooleanField(
        default=False,
        help_text="Accessible without enrollment"
    )
    requires_previous = models.BooleanField(
        default=True,
        help_text="Must complete previous lesson first"
    )
    
    # Resources
    downloadable_resources = models.JSONField(
        default=list,
        help_text="List of downloadable file URLs or file paths"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'User',
        null=True,
        on_delete=models.SET_NULL,
        related_name='created_lessons'
    )
    
    class Meta:
        ordering = ['section', 'order']
        indexes = [
            models.Index(fields=['section', 'order']),
            models.Index(fields=['lesson_type']),
        ]
    
    def __str__(self):
        return f"Lesson {self.order}: {self.title}"
    
    @property
    def course(self):
        """Get parent course"""
        return self.section.module.course
    
    def get_next_lesson(self):
        """Get next lesson in course"""
        try:
            return self.section.lessons.get(order=self.order + 1)
        except:
            # Try next section
            next_section = self.section.module.sections.filter(
                order__gt=self.section.order
            ).first()
            if next_section:
                return next_section.lessons.first()
        return None
    
    def get_previous_lesson(self):
        """Get previous lesson"""
        if self.order > 1:
            return self.section.lessons.filter(order=self.order - 1).first()
        
        # Try previous section
        prev_section = self.section.module.sections.filter(
            order__lt=self.section.order
        ).last()
        if prev_section:
            return prev_section.lessons.last()
        
        return None


class LessonResource(models.Model):
    """Structured resource list for lessons"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='lesson_resources/%Y/%m/')
    file_type = models.CharField(max_length=20)  # pdf, doc, video, etc.
    file_size_mb = models.FloatField()
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['lesson', 'order']
    
    def __str__(self):
        return f"{self.lesson.title} - {self.name}"


class Prerequisite(models.Model):
    """Course or lesson prerequisites"""
    PREREQ_TYPES = (
        ('course', 'Complete Course'),
        ('lesson', 'Complete Lesson'),
        ('quiz', 'Pass Quiz'),
        ('grade', 'Minimum Grade'),
    )
    
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='prerequisite_rules')
    prereq_type = models.CharField(max_length=20, choices=PREREQ_TYPES)
    prereq_id = models.PositiveIntegerField()
    required_value = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., '70' for grade out of 100"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['course', 'prereq_type', 'prereq_id']]
    
    def __str__(self):
        return f"{self.course.title} - {self.get_prereq_type_display()}"


class LearningPath(models.Model):
    """Customized learning sequence for different student groups"""
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='learning_paths')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Sequence as JSON list of lesson IDs
    lesson_sequence = models.JSONField(
        default=list,
        help_text="Ordered list of lesson IDs"
    )
    
    # Target audience
    target_audience = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., 'Beginners', 'Advanced', 'Management'"
    )
    
    # Is default path
    is_default = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey('User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', '-is_default', 'name']
    
    def __str__(self):
        return f"{self.course.title} - {self.name}"


class LearningPathEnrollment(models.Model):
    """Track which path a student is following"""
    student = models.ForeignKey('User', on_delete=models.CASCADE)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    
    # Progress
    current_lesson_index = models.IntegerField(default=0)
    completed_lessons = models.JSONField(default=list)
    
    # Metadata
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = [['student', 'learning_path']]
    
    def __str__(self):
        return f"{self.student.username} - {self.learning_path.name}"
    
    def get_current_lesson(self):
        """Get current lesson from path"""
        if self.current_lesson_index < len(self.learning_path.lesson_sequence):
            lesson_id = self.learning_path.lesson_sequence[self.current_lesson_index]
            return Lesson.objects.get(id=lesson_id)
        return None
    
    def complete_current_lesson(self):
        """Mark current lesson as complete"""
        if self.current_lesson_index < len(self.learning_path.lesson_sequence):
            lesson_id = self.learning_path.lesson_sequence[self.current_lesson_index]
            if lesson_id not in self.completed_lessons:
                self.completed_lessons.append(lesson_id)
            self.current_lesson_index += 1
            self.save()


# Progress Tracking Models

class ModuleProgress(models.Model):
    """Student progress through a module"""
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('paused', 'Paused'),
        ],
        default='not_started'
    )
    
    # Progress metrics
    sections_completed = models.IntegerField(default=0)
    total_sections = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    
    # Dates
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Time tracking
    time_spent_minutes = models.IntegerField(default=0)
    
    # Performance
    average_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = [['student', 'module']]
        indexes = [
            models.Index(fields=['student', 'module']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.module.title}"


class LessonProgress(models.Model):
    """Student progress through individual lessons"""
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('reviewing', 'Reviewing'),
            ('mastered', 'Mastered'),
        ],
        default='not_started'
    )
    
    # Video progress
    video_progress_percentage = models.FloatField(default=0.0)
    last_video_timestamp_seconds = models.IntegerField(default=0)
    
    # Time tracking
    time_spent_minutes = models.IntegerField(default=0)
    
    # Performance metrics
    quiz_score = models.FloatField(null=True, blank=True)
    assignment_score = models.FloatField(null=True, blank=True)
    
    # Completion tracking
    completed_at = models.DateTimeField(null=True, blank=True)
    first_accessed = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # Notes and resources
    student_notes = models.TextField(blank=True)
    bookmarked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = [['student', 'lesson']]
        indexes = [
            models.Index(fields=['student', 'lesson']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title} ({self.status})"
    
    @property
    def completion_percentage(self):
        """Calculate completion based on lesson type"""
        if self.lesson.lesson_type == 'video':
            return self.video_progress_percentage
        elif self.lesson.lesson_type == 'quiz':
            return 100.0 if self.quiz_score is not None else 0.0
        elif self.lesson.lesson_type == 'assignment':
            return 100.0 if self.assignment_score is not None else 0.0
        else:
            return 100.0 if self.status == 'completed' else 0.0


class LessonNote(models.Model):
    """Student notes on specific lesson parts"""
    student = models.ForeignKey('User', on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_notes')
    
    content = models.TextField()
    timestamp_seconds = models.IntegerField(null=True, blank=True)  # For videos
    
    # Highlighting
    highlighted_text = models.TextField(blank=True)
    highlight_color = models.CharField(max_length=7, default='#FFFF00')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note by {self.student.username} on {self.lesson.title}"
