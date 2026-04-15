# lms/models.py
import uuid
import hashlib
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.urls import reverse
from django.utils.text import slugify
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import json

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def generate_certificate_id():
    """Generate a unique certificate ID with timestamp and random component"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_part = uuid.uuid4().hex[:8].upper()
    return f"SYN-{timestamp}-{random_part}"

def validate_json_structure(value):
    """Validate that JSON field has expected structure"""
    if not isinstance(value, dict):
        raise ValidationError("Must be a valid JSON object")

# -------------------------------------------------------------------
# Custom User Model with Enhanced Functionality
# -------------------------------------------------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('instructor', 'Instructor'),
        ('learner', 'Learner'),
        ('dept_head', 'Department Head'),
        ('approver', 'Approver'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='learner')
    department = models.ForeignKey(
        'Department', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='members'
    )
    
    # Personal Information
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    # Approval workflow for self‑registered users
    is_approved = models.BooleanField(default=False)
    approval_token = models.UUIDField(unique=True, null=True, blank=True)
    approval_token_created_at = models.DateTimeField(null=True, blank=True)
    temp_password = models.CharField(max_length=128, blank=True)
    temp_password_created_at = models.DateTimeField(null=True, blank=True)
    
    # Google OAuth2 tokens
    google_access_token = models.TextField(blank=True)
    google_refresh_token = models.TextField(blank=True)
    google_token_expiry = models.DateTimeField(null=True, blank=True)
    
    # Activity tracking
    last_active = models.DateTimeField(auto_now=True)
    login_count = models.PositiveIntegerField(default=0)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(unique=True, null=True, blank=True)
    
    # Preferences
    receive_notifications = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_approved']),
            models.Index(fields=['username']),
            models.Index(fields=['last_active']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until and timezone.now() < self.account_locked_until:
            return True
        return False
    
    def lock_account(self, minutes=30):
        """Lock account for specified minutes"""
        self.account_locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock account"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def record_login_attempt(self, success):
        """Record login attempt for security tracking"""
        if success:
            self.login_count += 1
            self.failed_login_attempts = 0
            self.unlock_account()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.lock_account(30)
        self.save()
    
    def generate_approval_token(self):
        """Generate a new approval token"""
        self.approval_token = uuid.uuid4()
        self.approval_token_created_at = timezone.now()
        self.save()
        return self.approval_token
    
    def is_approval_token_valid(self):
        """Check if approval token is still valid (48 hours)"""
        if not self.approval_token_created_at:
            return False
        expiry = self.approval_token_created_at + timedelta(hours=48)
        return timezone.now() < expiry
    
    def get_enrolled_courses(self):
        """Get all active courses the user is enrolled in"""
        return Course.objects.filter(
            enrollments__student=self,
            enrollments__status='active'
        )
    
    def get_completion_rate(self):
        """Calculate overall completion rate across all courses"""
        enrollments = self.enrollments.filter(status='active')
        if not enrollments:
            return 0.0
        total_percent = sum(e.get_progress_percent() for e in enrollments)
        return total_percent / enrollments.count()
    
    def get_pending_assignments(self):
        """Get all assignments that are due and not yet submitted"""
        return Assignment.objects.filter(
            course__in=self.get_enrolled_courses(),
            due_date__gte=timezone.now(),
            submissions__student=self,
            submissions__status__in=['draft', 'returned']
        ).distinct()


# -------------------------------------------------------------------
# Department with Enhanced Features
# -------------------------------------------------------------------
class Department(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    code = models.CharField(max_length=20, unique=True, help_text="Department code (e.g., BT, EME, CE)")
    description = models.TextField()
    mission = models.TextField(blank=True, help_text="Department mission statement")
    vision = models.TextField(blank=True, help_text="Department vision statement")
    
    # Infrastructure and resources
    infrastructure = models.TextField(help_text="Required infrastructure (workshops, labs, etc.)")
    resources = models.TextField(help_text="Tools, equipment, software needed")
    min_instructors = models.PositiveIntegerField(default=1, help_text="Minimum instructors required")
    max_capacity = models.PositiveIntegerField(default=100, help_text="Maximum student capacity")
    
    # Staffing
    head = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'role__in': ['dept_head', 'admin']},
        related_name='headed_depts'
    )
    
    # Contact information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    office_location = models.CharField(max_length=200, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        indexes = [
            models.Index(fields=['code', 'status']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Department.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def total_instructors(self):
        """Get total number of instructors in this department"""
        return self.members.filter(role='instructor').count()
    
    @property
    def total_students(self):
        """Get total number of active students in this department"""
        return self.members.filter(role='learner', is_approved=True).count()
    
    @property
    def total_courses(self):
        """Get total number of active courses in this department"""
        return self.courses.filter(is_active=True).count()
    
    @property
    def is_adequately_staffed(self):
        """Check if department has enough instructors"""
        return self.total_instructors >= self.min_instructors
    
    def can_enroll(self):
        """Check if department can accept more students"""
        return self.total_students < self.max_capacity


# -------------------------------------------------------------------
# Course with Enhanced Features
# -------------------------------------------------------------------
class Course(models.Model):
    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    code = models.CharField(max_length=20, unique=True, help_text="Course code (e.g., BLCK-101)")
    description = models.TextField()
    learning_objectives = models.TextField(help_text="What students will learn")
    prerequisites = models.TextField(blank=True, help_text="Required prior knowledge")
    
    # Duration and schedule
    duration = models.CharField(max_length=50, help_text="e.g., '3 months', '6 weeks'")
    estimated_hours = models.PositiveIntegerField(default=40, help_text="Total estimated study hours")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    
    # Pricing (if applicable)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    
    # Grading weights (quizzes are 0% – excluded)
    assignment_weight = models.PositiveIntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    project_weight = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Quiz progression (non‑graded)
    require_quiz_pass = models.BooleanField(default=True)
    quiz_pass_score = models.PositiveIntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Media
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    promo_video_url = models.URLField(blank=True)
    
    # Google Classroom integration
    google_classroom_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    
    # Certificate template
    certificate_template = models.FileField(
        upload_to='cert_templates/',
        null=True, blank=True,
        validators=[FileExtensionValidator(['pdf'])]
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['department', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['code']),
            models.Index(fields=['difficulty']),
        ]
    
    def __str__(self):
        return f"{self.code}: {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.code:
            # Auto-generate course code from department and title
            dept_code = self.department.code if self.department else "GEN"
            self.code = f"{dept_code}-{uuid.uuid4().hex[:6].upper()}"
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def total_chapters(self):
        return self.chapters.count()
    
    @property
    def total_assignments(self):
        return self.assignments.count()
    
    @property
    def total_students_enrolled(self):
        return self.enrollments.filter(status='active').count()
    
    @property
    def completion_rate(self):
        total = self.enrollments.filter(status='active').count()
        if total == 0:
            return 0.0
        completed = self.enrollments.filter(status='completed').count()
        return (completed / total) * 100
    
    @property
    def avg_rating(self):
        """Average rating from course reviews"""
        reviews = self.reviews.all()
        if not reviews:
            return 0.0
        return sum(r.rating for r in reviews) / reviews.count()


# -------------------------------------------------------------------
# Chapter with Enhanced Features
# -------------------------------------------------------------------
class Chapter(models.Model):
    CHAPTER_TYPE_CHOICES = (
        ('lesson', 'Lesson with Documents'),
        ('reading', 'Reading Material'),
        ('quiz', 'Quiz Only'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(help_text="Order in the course")
    chapter_type = models.CharField(max_length=20, choices=CHAPTER_TYPE_CHOICES, default='lesson')
    
    # Documents - Primary content
    document_file = models.FileField(
        upload_to='chapter_documents/%Y/%m/%d/', 
        blank=True, 
        null=True,
        help_text="Upload PDF, PowerPoint, or Excel documents"
    )
    
    # Content
    video_url = models.URLField(blank=True, help_text="YouTube/Vimeo or self-hosted video URL (optional)")
    content = models.TextField(help_text="HTML or markdown content for the lesson")
    content_html = models.TextField(blank=True, help_text="Rendered HTML content")
    
    # Duration
    estimated_minutes = models.PositiveIntegerField(default=30, help_text="Estimated time to complete")
    
    # Google Doc integration
    template_doc_id = models.CharField(max_length=100, blank=True, help_text="Google Doc ID of the template")
    
    # Access control
    is_free_preview = models.BooleanField(default=False)
    requires_previous_quiz_pass = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = [['course', 'order']]
        indexes = [
            models.Index(fields=['course', 'order']),
            models.Index(fields=['chapter_type']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - Ch{self.order}: {self.title}"
    
    @property
    def next_chapter(self):
        """Get the next chapter in the course"""
        return Chapter.objects.filter(
            course=self.course, order__gt=self.order
        ).order_by('order').first()
    
    @property
    def previous_chapter(self):
        """Get the previous chapter in the course"""
        return Chapter.objects.filter(
            course=self.course, order__lt=self.order
        ).order_by('-order').first()


# -------------------------------------------------------------------
# Quizzes (Non‑graded, performance appraisal only)
# -------------------------------------------------------------------
class Quiz(models.Model):
    chapter = models.OneToOneField(Chapter, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200, default="Chapter Quiz")
    description = models.TextField(blank=True, help_text="Instructions for the quiz")
    pass_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum % to unlock next chapter"
    )
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Optional time limit")
    attempts_allowed = models.PositiveIntegerField(default=1)
    shuffle_questions = models.BooleanField(default=False)
    show_answers_after_submit = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Quiz: {self.chapter.course.code} - {self.chapter.title}"
    
    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    QUESTION_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('tf', 'True/False'),
        ('short', 'Short Answer'),
        ('essay', 'Essay'),
        ('matching', 'Matching'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')
    options = models.JSONField(default=list, help_text="For MCQ: list of options; for TF: ['True','False']")
    correct_answer = models.CharField(max_length=500)
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"
    
    def clean(self):
        """Validate that options are provided for MCQ questions"""
        if self.question_type == 'mcq' and len(self.options) < 2:
            raise ValidationError("MCQ questions must have at least 2 options")
        if self.question_type == 'tf' and self.options not in [['True','False'], ['False','True']]:
            self.options = ['True', 'False']
    
    def check_answer(self, user_answer):
        """Check if user answer is correct (case-insensitive for short answers)"""
        if self.question_type == 'short':
            return user_answer.strip().lower() == self.correct_answer.strip().lower()
        return user_answer == self.correct_answer


class QuizAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(help_text="Percentage score (0-100)")
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    answers = models.JSONField(default=dict, help_text="Stores student's answers")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = [['student', 'quiz']]
        indexes = [
            models.Index(fields=['student', 'passed']),
            models.Index(fields=['attempted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.chapter.title} - {self.score}%"
    
    @property
    def can_retake(self):
        """Check if student can retake the quiz"""
        if self.passed:
            return False
        return QuizAttempt.objects.filter(student=self.student, quiz=self.quiz).count() < self.quiz.attempts_allowed


# -------------------------------------------------------------------
# Graded Assignments & Submissions with Enhanced Features
# -------------------------------------------------------------------
class Assignment(models.Model):
    ASSIGNMENT_TYPE_CHOICES = (
        ('individual', 'Individual'),
        ('group', 'Group'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    chapter = models.ForeignKey(Chapter, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='individual')
    due_date = models.DateTimeField()
    soft_deadline = models.DateTimeField(null=True, blank=True, help_text="Late submission allowed until this date")
    late_penalty_percent = models.PositiveIntegerField(default=10, help_text="Penalty per day after due date")
    
    # Grading
    total_points = models.PositiveIntegerField(default=100)
    rubric = models.JSONField(default=dict, help_text="""Example: {
        'criteria': [
            {'name':'Quality','max_score':50,'description':'...'},
            {'name':'Completeness','max_score':30,'description':'...'},
            {'name':'Citations','max_score':20,'description':'...'}
        ]
    }""")
    
    # Integrations
    google_classroom_id = models.CharField(max_length=100, blank=True)
    turnitin_lti_id = models.CharField(max_length=100, blank=True)
    enable_plagiarism_check = models.BooleanField(default=False)
    turnitin_settings = models.JSONField(default=dict, blank=True, help_text="e.g., exclude quotes, bibliography")
    
    # Submission settings
    allow_late_submissions = models.BooleanField(default=True)
    max_file_size_mb = models.PositiveIntegerField(default=50)
    allowed_file_types = models.CharField(max_length=200, default='.pdf,.doc,.docx,.txt', help_text="Comma-separated file extensions")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['course', 'due_date']),
            models.Index(fields=['assignment_type']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"
    
    @property
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    @property
    def is_soft_deadline_passed(self):
        if self.soft_deadline:
            return timezone.now() > self.soft_deadline
        return self.is_overdue
    
    def calculate_late_penalty(self, submission_date):
        """Calculate late penalty based on submission date"""
        if submission_date <= self.due_date:
            return 0
        days_late = (submission_date - self.due_date).days
        return min(days_late * self.late_penalty_percent, 50)  # Max 50% penalty
    
    def get_submission_count(self):
        return self.submissions.count()
    
    def get_average_grade(self):
        submissions = self.submissions.filter(status='graded', grade__isnull=False)
        if not submissions:
            return None
        return sum(s.grade for s in submissions) / submissions.count()


class Submission(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
    )
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    
    # Google Docs integration
    google_doc_id = models.CharField(max_length=100, blank=True, help_text="Student's personal copy of template")
    
    # Turnitin results
    similarity_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    turnitin_report_url = models.URLField(blank=True, help_text="Iframe URL for report")
    turnitin_submission_id = models.CharField(max_length=100, blank=True)
    
    # File submission (alternative to Google Doc)
    submitted_file = models.FileField(
        upload_to='submissions/%Y/%m/',
        null=True, blank=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt'])]
    )
    
    # Submission metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Grading
    grade = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    rubric_scores = models.JSONField(default=dict, help_text="Scores per rubric criteria")
    feedback = models.TextField(blank=True)
    inline_comments = models.JSONField(default=dict, blank=True, help_text="Inline comments on document")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    graded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    
    # Revision tracking
    revision_count = models.PositiveIntegerField(default=0)
    previous_submission = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = [['assignment', 'student']]
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_late(self):
        return self.submitted_at > self.assignment.due_date
    
    @property
    def effective_grade(self):
        """Calculate final grade after late penalty"""
        if self.grade is None:
            return None
        if not self.is_late:
            return self.grade
        penalty = self.assignment.calculate_late_penalty(self.submitted_at)
        return max(self.grade - (self.grade * penalty / 100), 0)
    
    def calculate_grade_from_rubric(self):
        """Calculate grade based on rubric scores"""
        if not self.rubric_scores:
            return None
        total_scored = sum(self.rubric_scores.values())
        total_possible = sum(c['max_score'] for c in self.assignment.rubric.get('criteria', []))
        if total_possible == 0:
            return None
        return (total_scored / total_possible) * 100
    
    def submit_to_turnitin(self):
        """Trigger Turnitin submission (placeholder for actual API call)"""
        if self.assignment.enable_plagiarism_check and not self.turnitin_submission_id:
            # This would call Turnitin LTI API
            # For now, just mark as submitted
            pass


# -------------------------------------------------------------------
# Enrollment & Approval Workflow with Enhanced Features
# -------------------------------------------------------------------
class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('expelled', 'Expelled'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress = models.JSONField(default=dict, help_text="Stores completed chapters and quiz passes")
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Payment tracking (if applicable)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, default='unpaid', choices=[
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ])
    
    # Enrollment metadata
    enrolled_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='enrolled_students')
    enrollment_method = models.CharField(max_length=20, choices=[
        ('self', 'Self Registration'),
        ('admin', 'Admin Direct'),
        ('bulk', 'Bulk Import'),
    ], default='self')
    
    class Meta:
        unique_together = [['student', 'course']]
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} ({self.status})"
    
    def get_progress_percent(self):
        """Calculate overall progress percentage for this course"""
        total_chapters = self.course.chapters.count()
        if total_chapters == 0:
            return 0.0
        completed = len(self.progress.get('completed_chapters', []))
        return (completed / total_chapters) * 100
    
    def complete_course(self):
        """Mark course as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        # Generate certificate
        from .utils.certificate_gen import generate_certificate
        generate_certificate(self)
    
    def can_access_chapter(self, chapter):
        """Check if student can access a specific chapter"""
        if chapter.is_free_preview:
            return True
        if self.status != 'active':
            return False
        # Check if previous chapters are completed
        previous_chapters = Chapter.objects.filter(
            course=self.course, order__lt=chapter.order
        )
        completed_chapters = self.progress.get('completed_chapters', [])
        for prev in previous_chapters:
            if str(prev.id) not in completed_chapters:
                return False
        return True


class EnrollmentRequest(models.Model):
    REQUEST_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollment_requests')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollment_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Reason for request (if required)
    reason = models.TextField(blank=True, help_text="Why the student wants to enroll")
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status', 'requested_at']),
            models.Index(fields=['student', 'course']),
        ]
    
    def __str__(self):
        return f"{self.student.username} requesting {self.course.title} ({self.status})"
    
    def approve(self, approver):
        """Approve the enrollment request"""
        self.status = 'approved'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save()
        
        # Create the actual enrollment
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status='active',
            enrollment_method='self',
            enrolled_by=approver
        )
    
    def reject(self, approver, notes=""):
        """Reject the enrollment request"""
        self.status = 'rejected'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()


# -------------------------------------------------------------------
# Certificates with Enhanced Features
# -------------------------------------------------------------------
class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=100, unique=True, default=generate_certificate_id)
    pdf_file = models.FileField(upload_to='certificates/%Y/%m/')
    qr_code = models.ImageField(upload_to='qr_codes/%Y/%m/', blank=True)
    verification_url = models.URLField(blank=True, help_text="Public URL to verify certificate")
    
    # Additional metadata
    final_grade = models.FloatField(null=True, blank=True, help_text="Final course grade")
    completion_date = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='issued_certificates')
    
    # Blockchain / verification hash
    verification_hash = models.CharField(max_length=128, blank=True, help_text="SHA256 hash for verification")
    
    class Meta:
        ordering = ['-issued_at']
        unique_together = [['student', 'course']]
        indexes = [
            models.Index(fields=['certificate_id']),
            models.Index(fields=['student', 'course']),
        ]
    
    def __str__(self):
        return f"Certificate for {self.student.username} - {self.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.verification_hash:
            # Generate verification hash
            data = f"{self.certificate_id}{self.student.email}{self.course.id}{self.issued_at.isoformat()}"
            self.verification_hash = hashlib.sha256(data.encode()).hexdigest()
        if not self.verification_url:
            self.verification_url = reverse('lms:verify_certificate', args=[self.certificate_id])
        super().save(*args, **kwargs)
    
    def verify(self):
        """Verify certificate authenticity"""
        expected_hash = hashlib.sha256(
            f"{self.certificate_id}{self.student.email}{self.course.id}{self.issued_at.isoformat()}".encode()
        ).hexdigest()
        return self.verification_hash == expected_hash


# -------------------------------------------------------------------
# Course Reviews and Ratings
# -------------------------------------------------------------------
class CourseReview(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['course', 'student']]
        indexes = [
            models.Index(fields=['course', 'is_approved', 'rating']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}: {self.rating}/5"


# -------------------------------------------------------------------
# Notifications System
# -------------------------------------------------------------------
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('reminder', 'Reminder'),
        ('grade', 'Grade Posted'),
        ('certificate', 'Certificate Issued'),
        ('enrollment', 'Enrollment Update'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Link to related object (optional)
    related_url = models.URLField(blank=True)
    related_object_type = models.CharField(max_length=100, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username}: {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


# -------------------------------------------------------------------
# System Logs (Audit Trail)
# -------------------------------------------------------------------
class SystemLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('grade', 'Grade'),
        ('submit', 'Submit'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, help_text="What changed")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} - {self.object_type} at {self.created_at}"


class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_progress')
    completed_chapters = models.JSONField(default=list)
    quiz_passes = models.JSONField(default=list)
    overall_percent = models.FloatField(default=0.0)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['student', 'course']]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}: {self.overall_percent}%"


# -------------------------------------------------------------------
# Signals for Automatic Actions
# -------------------------------------------------------------------
@receiver(post_save, sender=User)
def create_user_notification_settings(sender, instance, created, **kwargs):
    """Create default notification preferences for new users"""
    if created:
        # You could create a UserPreferences model here
        pass


@receiver(post_save, sender=Submission)
def submission_created_notification(sender, instance, created, **kwargs):
    """Send notification when a submission is made"""
    if created and instance.status == 'submitted':
        # Notify instructors
        instructors = User.objects.filter(
            role='instructor',
            department=instance.assignment.course.department
        )
        for instructor in instructors:
            Notification.objects.create(
                recipient=instructor,
                title=f"New Submission: {instance.assignment.title}",
                message=f"{instance.student.get_full_name()} submitted {instance.assignment.title}",
                notification_type='info',
                related_url=reverse('lms:grade_submission', args=[instance.id])
            )


@receiver(post_save, sender=Enrollment)
def enrollment_created_notification(sender, instance, created, **kwargs):
    """Send notification when a student is enrolled"""
    if created:
        Notification.objects.create(
            recipient=instance.student,
            title=f"Enrolled in {instance.course.title}",
            message=f"You have been successfully enrolled in {instance.course.title}",
            notification_type='success',
            related_url=reverse('lms:course_detail', args=[instance.course.slug])
        )