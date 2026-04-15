# lms/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from .models import (
    User, Department, Course, Chapter, ChapterMaterial, Quiz, Question, QuizAttempt,
    Assignment, Submission, Enrollment, EnrollmentRequest, Certificate,
    CourseReview, Notification, SystemLog, StudentProgress
)

# -------------------------------------------------------------------
# Custom User Admin
# -------------------------------------------------------------------
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'department', 'is_approved', 'is_active', 'last_login')
    list_filter = ('role', 'is_approved', 'is_active', 'department', 'gender')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('last_login', 'date_joined', 'approval_token', 'approval_token_created_at', 
                       'login_count', 'failed_login_attempts', 'account_locked_until')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address', 
                                             'gender', 'date_of_birth', 'profile_picture')}),
        ('Role & Department', {'fields': ('role', 'department')}),
        ('Approval Status', {'fields': ('is_approved', 'approval_token', 'approval_token_created_at')}),
        ('Google Integration', {'fields': ('google_access_token', 'google_refresh_token', 'google_token_expiry')}),
        ('Security', {'fields': ('login_count', 'failed_login_attempts', 'account_locked_until')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'department'),
        }),
    )
    
    actions = ['approve_users', 'lock_users', 'unlock_users', 'send_welcome_email']
    
    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} users approved.")
    approve_users.short_description = "Approve selected users"
    
    def lock_users(self, request, queryset):
        for user in queryset:
            user.lock_account(30)
        self.message_user(request, f"{queryset.count()} users locked.")
    lock_users.short_description = "Lock selected users (30 min)"
    
    def unlock_users(self, request, queryset):
        for user in queryset:
            user.unlock_account()
        self.message_user(request, f"{queryset.count()} users unlocked.")
    unlock_users.short_description = "Unlock selected users"
    
    def send_welcome_email(self, request, queryset):
        # This would integrate with your email system
        self.message_user(request, f"Welcome emails sent to {queryset.count()} users.")
    send_welcome_email.short_description = "Send welcome email"

# -------------------------------------------------------------------
# Department Admin
# -------------------------------------------------------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'head', 'total_instructors', 'total_students', 'total_courses', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'code', 'description', 'mission', 'vision')}),
        ('Infrastructure & Resources', {'fields': ('infrastructure', 'resources', 'min_instructors', 'max_capacity')}),
        ('Staff & Contact', {'fields': ('head', 'contact_email', 'contact_phone', 'office_location')}),
        ('Status', {'fields': ('status', 'created_at', 'updated_at')}),
    )
    
    def total_instructors(self, obj):
        return obj.total_instructors
    total_instructors.short_description = "Instructors"
    
    def total_students(self, obj):
        return obj.total_students
    total_students.short_description = "Students"
    
    def total_courses(self, obj):
        return obj.total_courses
    total_courses.short_description = "Courses"

# -------------------------------------------------------------------
# Course Admin with Inline Chapters
# -------------------------------------------------------------------
class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1
    fields = ('title', 'order', 'chapter_type', 'estimated_minutes', 'is_free_preview')
    show_change_link = True

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'department', 'difficulty', 'status', 'total_chapters', 'total_students_enrolled', 'is_active')
    list_filter = ('department', 'difficulty', 'status', 'is_active', 'created_at')
    search_fields = ('title', 'code', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    inlines = [ChapterInline]
    
    fieldsets = (
        ('Basic Information', {'fields': ('department', 'title', 'slug', 'code', 'description', 'learning_objectives', 'prerequisites')}),
        ('Duration & Difficulty', {'fields': ('duration', 'estimated_hours', 'difficulty')}),
        ('Pricing', {'fields': ('price', 'currency')}),
        ('Grading & Quizzes', {'fields': ('assignment_weight', 'project_weight', 'require_quiz_pass', 'quiz_pass_score')}),
        ('Media', {'fields': ('thumbnail', 'promo_video_url')}),
        ('Integrations', {'fields': ('google_classroom_id', 'certificate_template')}),
        ('Status', {'fields': ('status', 'is_active', 'created_at', 'updated_at', 'published_at')}),
    )
    
    actions = ['publish_courses', 'archive_courses']
    
    def publish_courses(self, request, queryset):
        queryset.update(status='published', is_active=True, published_at=timezone.now())
        self.message_user(request, f"{queryset.count()} courses published.")
    publish_courses.short_description = "Publish selected courses"
    
    def archive_courses(self, request, queryset):
        queryset.update(status='archived', is_active=False)
        self.message_user(request, f"{queryset.count()} courses archived.")
    archive_courses.short_description = "Archive selected courses"
    
    def total_chapters(self, obj):
        return obj.total_chapters
    total_chapters.short_description = "Chapters"
    
    def total_students_enrolled(self, obj):
        return obj.total_students_enrolled
    total_students_enrolled.short_description = "Students"

# -------------------------------------------------------------------
# Chapter Admin
# -------------------------------------------------------------------
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'chapter_type', 'estimated_minutes', 'is_free_preview')
    list_filter = ('course__department', 'chapter_type', 'is_free_preview', 'course')
    search_fields = ('title', 'content')
    list_editable = ('order', 'estimated_minutes', 'is_free_preview')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {'fields': ('course', 'title', 'order', 'chapter_type')}),
        ('Content', {'fields': ('video_url', 'content', 'content_html')}),
        ('Duration & Access', {'fields': ('estimated_minutes', 'is_free_preview', 'requires_previous_quiz_pass')}),
        ('Google Integration', {'fields': ('template_doc_id',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

# -------------------------------------------------------------------
# Quiz & Question Admin
# -------------------------------------------------------------------
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('text', 'question_type', 'points', 'order')
    show_change_link = True

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'pass_score', 'time_limit_minutes', 'attempts_allowed')
    list_filter = ('chapter__course__department', 'chapter__course')
    search_fields = ('title', 'chapter__title')
    inlines = [QuestionInline]
    
    fieldsets = (
        ('Basic Information', {'fields': ('chapter', 'title', 'description')}),
        ('Quiz Settings', {'fields': ('pass_score', 'time_limit_minutes', 'attempts_allowed', 'shuffle_questions', 'show_answers_after_submit')}),
    )

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'quiz', 'question_type', 'points', 'order')
    list_filter = ('question_type', 'quiz__chapter__course')
    search_fields = ('text', 'correct_answer')
    list_editable = ('points', 'order')
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = "Question"

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'passed', 'attempted_at', 'time_taken_seconds')
    list_filter = ('passed', 'attempted_at', 'quiz__chapter__course')
    search_fields = ('student__username', 'quiz__chapter__title')
    readonly_fields = ('attempted_at', 'completed_at', 'answers')
    
    def has_add_permission(self, request):
        return False

# -------------------------------------------------------------------
# Assignment Admin
# -------------------------------------------------------------------
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'assignment_type', 'due_date', 'is_overdue', 'enable_plagiarism_check')
    list_filter = ('course__department', 'assignment_type', 'enable_plagiarism_check', 'due_date')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {'fields': ('course', 'chapter', 'title', 'description', 'assignment_type')}),
        ('Dates & Penalties', {'fields': ('due_date', 'soft_deadline', 'late_penalty_percent', 'allow_late_submissions')}),
        ('Grading', {'fields': ('total_points', 'rubric')}),
        ('Integrations', {'fields': ('google_classroom_id', 'turnitin_lti_id', 'enable_plagiarism_check', 'turnitin_settings')}),
        ('Submission Settings', {'fields': ('max_file_size_mb', 'allowed_file_types')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = "Overdue"

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'grade', 'similarity_score', 'submitted_at', 'is_late')
    list_filter = ('status', 'assignment__course', 'submitted_at')
    search_fields = ('student__username', 'assignment__title')
    readonly_fields = ('submitted_at', 'updated_at', 'submitted_file')
    
    fieldsets = (
        ('Submission Info', {'fields': ('assignment', 'student', 'status')}),
        ('Google & Turnitin', {'fields': ('google_doc_id', 'similarity_score', 'turnitin_report_url', 'turnitin_submission_id')}),
        ('File Submission', {'fields': ('submitted_file',)}),
        ('Grading', {'fields': ('grade', 'effective_grade', 'rubric_scores', 'feedback', 'inline_comments')}),
        ('Metadata', {'fields': ('submitted_at', 'updated_at', 'ip_address', 'user_agent', 'revision_count')}),
    )
    
    def is_late(self, obj):
        return obj.is_late
    is_late.boolean = True
    is_late.short_description = "Late"

# -------------------------------------------------------------------
# Enrollment Admin
# -------------------------------------------------------------------
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrolled_at', 'progress_percent', 'payment_status')
    list_filter = ('status', 'payment_status', 'enrollment_method', 'course__department')
    search_fields = ('student__username', 'course__title')
    readonly_fields = ('enrolled_at', 'completed_at')
    
    fieldsets = (
        ('Enrollment Info', {'fields': ('student', 'course', 'status', 'enrollment_method', 'enrolled_by')}),
        ('Progress', {'fields': ('progress', 'completed_at')}),
        ('Payment', {'fields': ('amount_paid', 'payment_status')}),
    )
    
    actions = ['mark_completed', 'mark_active', 'mark_dropped']
    
    def progress_percent(self, obj):
        return f"{obj.get_progress_percent():.1f}%"
    progress_percent.short_description = "Progress"
    
    def mark_completed(self, request, queryset):
        for enrollment in queryset:
            enrollment.complete_course()
        self.message_user(request, f"{queryset.count()} enrollments marked completed.")
    mark_completed.short_description = "Mark as completed"
    
    def mark_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} enrollments marked active.")
    mark_active.short_description = "Mark as active"
    
    def mark_dropped(self, request, queryset):
        queryset.update(status='dropped')
        self.message_user(request, f"{queryset.count()} enrollments marked dropped.")
    mark_dropped.short_description = "Mark as dropped"

@admin.register(EnrollmentRequest)
class EnrollmentRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'requested_at', 'approved_by')
    list_filter = ('status', 'requested_at')
    search_fields = ('student__username', 'course__title')
    readonly_fields = ('requested_at', 'approved_at')
    
    fieldsets = (
        ('Request Info', {'fields': ('student', 'course', 'reason')}),
        ('Approval', {'fields': ('status', 'approved_by', 'approved_at', 'approval_notes')}),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        for req in queryset:
            req.approve(request.user)
        self.message_user(request, f"{queryset.count()} requests approved.")
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        for req in queryset:
            req.reject(request.user)
        self.message_user(request, f"{queryset.count()} requests rejected.")
    reject_requests.short_description = "Reject selected requests"

# -------------------------------------------------------------------
# Certificate Admin
# -------------------------------------------------------------------
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'student', 'course', 'issued_at', 'verification_link')
    list_filter = ('course__department', 'issued_at')
    search_fields = ('certificate_id', 'student__username', 'course__title')
    readonly_fields = ('certificate_id', 'verification_hash', 'verification_url')
    
    fieldsets = (
        ('Certificate Info', {'fields': ('student', 'course', 'certificate_id')}),
        ('Files', {'fields': ('pdf_file', 'qr_code')}),
        ('Verification', {'fields': ('verification_url', 'verification_hash')}),
        ('Metadata', {'fields': ('final_grade', 'completion_date', 'issued_by', 'issued_at')}),
    )
    
    def verification_link(self, obj):
        if obj.verification_url:
            return format_html('<a href="{}" target="_blank">Verify</a>', obj.verification_url)
        return "-"
    verification_link.short_description = "Verification"

# -------------------------------------------------------------------
# Course Review Admin
# -------------------------------------------------------------------
@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'rating', 'title_preview', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'course__department')
    search_fields = ('course__title', 'student__username', 'comment')
    list_editable = ('is_approved',)
    
    def title_preview(self, obj):
        return obj.title[:50] if obj.title else "-"
    title_preview.short_description = "Title"
    
    actions = ['approve_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} reviews approved.")
    approve_reviews.short_description = "Approve selected reviews"

# -------------------------------------------------------------------
# Notification Admin
# -------------------------------------------------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Notification', {'fields': ('recipient', 'title', 'message', 'notification_type')}),
        ('Status', {'fields': ('is_read', 'read_at', 'created_at')}),
        ('Related Object', {'fields': ('related_url', 'related_object_type', 'related_object_id')}),
    )

# -------------------------------------------------------------------
# System Log Admin
# -------------------------------------------------------------------
@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'object_type', 'object_repr', 'created_at', 'ip_address')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('user__username', 'object_repr', 'object_id')
    readonly_fields = ('user', 'action', 'object_type', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# -------------------------------------------------------------------
# Student Progress Admin
# -------------------------------------------------------------------
@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'overall_percent', 'last_activity')
    list_filter = ('course__department', 'course')
    search_fields = ('student__username', 'course__title')
    readonly_fields = ('last_activity',)
    
    fieldsets = (
        ('Progress', {'fields': ('student', 'course', 'completed_chapters', 'quiz_passes', 'overall_percent', 'last_activity')}),
    )

# -------------------------------------------------------------------
# Chapter Material (Documents) Admin
# -------------------------------------------------------------------
@admin.register(ChapterMaterial)
class ChapterMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'material_type', 'get_icon', 'order', 'created_at')
    list_filter = ('material_type', 'chapter__course__department', 'created_at')
    search_fields = ('title', 'description', 'chapter__title')
    readonly_fields = ('created_at', 'updated_at', 'get_file_icon')
    ordering = ('chapter', 'order')
    
    fieldsets = (
        ('Basic Information', {'fields': ('chapter', 'material_type', 'title', 'description', 'order')}),
        ('Document', {'fields': ('file', 'get_file_icon'), 'description': 'Upload PDF, PowerPoint, or Excel files'}),
        ('Video (Optional)', {'fields': ('video_url',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_icon(self, obj):
        """Display icon for file type"""
        return format_html('<i class="{}"></i>', obj.icon_class)
    get_icon.short_description = 'Type'
    
    def get_file_icon(self, obj):
        """Display file type information"""
        if obj.file:
            return format_html(
                '<i class="{}"></i> {} ({} bytes)',
                obj.icon_class,
                obj.file.name.split('/')[-1],
                obj.file.size
            )
        return '-'
    get_file_icon.short_description = 'File'

# -------------------------------------------------------------------
# Dashboard Statistics (Custom Admin View)
# -------------------------------------------------------------------
class DashboardStats(admin.AdminSite):
    site_header = "Synego Training Institute Administration"
    site_title = "Synego LMS Admin"
    index_title = "Dashboard"
    
    def index(self, request, extra_context=None):
        # Add custom statistics to admin dashboard
        extra_context = extra_context or {}
        
        # Statistics
        extra_context['total_users'] = User.objects.count()
        extra_context['total_students'] = User.objects.filter(role='learner').count()
        extra_context['total_instructors'] = User.objects.filter(role='instructor').count()
        extra_context['total_courses'] = Course.objects.filter(is_active=True).count()
        extra_context['total_departments'] = Department.objects.filter(status='active').count()
        extra_context['pending_approvals'] = EnrollmentRequest.objects.filter(status='pending').count()
        extra_context['pending_submissions'] = Submission.objects.filter(status='submitted').count()
        extra_context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        extra_context['recent_submissions'] = Submission.objects.select_related('student', 'assignment').order_by('-submitted_at')[:5]
        
        # Course completion stats
        courses = Course.objects.filter(is_active=True).annotate(
            student_count=Count('enrollments', filter=models.Q(enrollments__status='active')),
            avg_rating=Avg('reviews__rating', filter=models.Q(reviews__is_approved=True))
        )[:10]
        extra_context['course_stats'] = courses
        
        return super().index(request, extra_context)

# Uncomment to use custom admin site
# admin_site = DashboardStats(name='synego_admin')