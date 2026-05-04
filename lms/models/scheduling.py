# lms/models/scheduling.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta

User = get_user_model()

# ============================================================
# COURSE INTAKE / SCHEDULE MODEL
# ============================================================

class CourseIntake(models.Model):
    """Course intake schedule - when a course is offered"""
    
    STATUS_CHOICES = (
        ('upcoming', '📅 Upcoming'),
        ('open', '✅ Open for Registration'),
        ('in_progress', '🔄 In Progress'),
        ('completed', '✓ Completed'),
        ('cancelled', '❌ Cancelled'),
        ('full', '🔴 Fully Booked'),
    )
    
    DELIVERY_CHOICES = (
        ('online', '💻 Online Live'),
        ('in_person', '🏛️ In Person'),
        ('hybrid', '🎯 Hybrid'),
        ('self_paced', '⚡ Self-Paced'),
    )
    
    WEEKDAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    # Basic Information
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='intakes')
    title = models.CharField(max_length=200, help_text="e.g., 'March 2025 Intake'")
    description = models.TextField(blank=True, help_text="Additional details about this intake")
    
    # Registration Dates
    registration_start_date = models.DateTimeField(help_text="When registration opens")
    registration_end_date = models.DateTimeField(help_text="When registration closes")
    
    # Course Dates
    course_start_date = models.DateTimeField(help_text="First day of course")
    course_end_date = models.DateTimeField(help_text="Last day of course")
    
    # Schedule Details
    weekday = models.CharField(max_length=20, choices=WEEKDAY_CHOICES, default='monday')
    start_time = models.TimeField(help_text="Class start time")
    end_time = models.TimeField(help_text="Class end time")
    duration_weeks = models.PositiveIntegerField(default=0, help_text="Total duration in weeks")
    total_hours = models.PositiveIntegerField(default=0, help_text="Total course hours")
    
    # Capacity
    max_students = models.PositiveIntegerField(default=30, help_text="Maximum students allowed")
    current_enrolled = models.PositiveIntegerField(default=0)
    
    # Delivery
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='in_person')
    venue = models.CharField(max_length=500, blank=True, help_text="Physical location for in-person")
    meeting_link = models.URLField(blank=True, help_text="Zoom/Teams link for online")
    
    # Pricing
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    early_bird_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    early_bird_deadline = models.DateTimeField(null=True, blank=True, help_text="Last day for early bird discount")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    is_featured = models.BooleanField(default=False, help_text="Show on homepage featured section")
    is_visible = models.BooleanField(default=True)
    
    # Instructor
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='course_intakes', 
                                   limit_choices_to={'groups__name__in': ['instructor', 'admin']})
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_intakes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course_start_date']
        indexes = [
            models.Index(fields=['course_start_date', 'status']),
            models.Index(fields=['course', 'is_visible', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def available_spots(self):
        return self.max_students - self.current_enrolled
    
    @property
    def is_full(self):
        return self.current_enrolled >= self.max_students
    
    @property
    def is_early_bird_available(self):
        if self.early_bird_deadline and self.early_bird_price:
            return datetime.now() < self.early_bird_deadline
        return False
    
    @property
    def current_price(self):
        if self.is_early_bird_available:
            return self.early_bird_price
        return self.regular_price
    
    @property
    def registration_status(self):
        now = datetime.now()
        if now < self.registration_start_date:
            return 'not_open'
        elif now > self.registration_end_date:
            return 'closed'
        else:
            return 'open'
    
    @property
    def formatted_schedule(self):
        """Returns formatted schedule string like 'Mondays, 6:00 PM - 8:00 PM'"""
        return f"{self.get_weekday_display()}s, {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
    
    @property
    def formatted_date_range(self):
        """Returns formatted date range like 'Mar 15 - Apr 30, 2025'"""
        return f"{self.course_start_date.strftime('%b %d')} - {self.course_end_date.strftime('%b %d, %Y')}"
    
    def update_status_automatically(self):
        """Auto-update status based on dates"""
        now = datetime.now()
        if now > self.course_end_date:
            self.status = 'completed'
        elif now > self.course_start_date:
            self.status = 'in_progress'
        elif self.is_full:
            self.status = 'full'
        elif self.registration_start_date <= now <= self.registration_end_date:
            self.status = 'open'
        else:
            self.status = 'upcoming'
        self.save(update_fields=['status'])


# ============================================================
# ENROLLMENT MODEL
# ============================================================

class IntakeEnrollment(models.Model):
    """Student enrollment in a specific course intake"""
    
    STATUS_CHOICES = (
        ('pending', '⏳ Pending Payment'),
        ('enrolled', '✅ Enrolled'),
        ('waitlisted', '📋 Waitlisted'),
        ('dropped', '❌ Dropped'),
        ('completed', '🎓 Completed'),
        ('certified', '🏆 Certified'),
    )
    
    intake = models.ForeignKey(CourseIntake, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='intake_enrollments')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    price_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, default='unpaid')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    enrolled_at = models.DateTimeField(auto_now_add=True, help_text="Time of enrollment")
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['intake', 'student']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.intake.title}"


# ============================================================
# CLASS SESSIONS (Individual Sessions within an Intake)
# ============================================================

class ClassSession(models.Model):
    """Individual class sessions within a course intake"""
    
    SESSION_TYPE = (
        ('lecture', 'Lecture'),
        ('practical', 'Practical/Lab'),
        ('workshop', 'Workshop'),
        ('assessment', 'Assessment/Exam'),
        ('guest_lecture', 'Guest Lecture'),
        ('field_trip', 'Field Trip'),
    )
    
    intake = models.ForeignKey(CourseIntake, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    title = models.CharField(max_length=200)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE, default='lecture')
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Content
    description = models.TextField(blank=True)
    learning_objectives = models.TextField(blank=True)
    materials_needed = models.TextField(blank=True)
    
    # Resources
    recording_url = models.URLField(blank=True)
    slides_url = models.URLField(blank=True)
    additional_resources = models.JSONField(default=list)
    
    # Attendance
    attendance_code = models.CharField(max_length=10, blank=True, unique=True)
    attendance_taken = models.BooleanField(default=False)
    
    # Live Session
    meeting_link = models.URLField(blank=True)
    meeting_id = models.CharField(max_length=100, blank=True)
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # Status
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.intake.course.title} - {self.title} ({self.start_time.strftime('%b %d, %H:%M')})"
    
    @property
    def is_upcoming(self):
        return datetime.now() < self.start_time
    
    @property
    def is_ongoing(self):
        return self.start_time <= datetime.now() <= self.end_time
    
    @property
    def is_past(self):
        return datetime.now() > self.end_time


# ============================================================
# SESSION ATTENDANCE
# ============================================================

class SessionAttendance(models.Model):
    """Track attendance for individual sessions"""
    
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='attendance')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(IntakeEnrollment, on_delete=models.CASCADE, null=True, blank=True)
    
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('online', 'Online Attendance'),
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_attendance')
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.session.title}: {self.status}"


# ============================================================
# CALENDAR & EVENTS
# ============================================================

class CalendarEvent(models.Model):
    """Institutional calendar events (holidays, exams, registration deadlines)"""
    
    EVENT_TYPES = (
        ('holiday', 'Holiday'),
        ('exam', 'Examination Period'),
        ('registration', 'Registration Period'),
        ('workshop', 'Workshop/Training'),
        ('seminar', 'Seminar'),
        ('career_fair', 'Career Fair'),
        ('open_day', 'Open Day'),
        ('graduation', 'Graduation Ceremony'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    
    location = models.CharField(max_length=500, blank=True)
    meeting_link = models.URLField(blank=True)
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True, help_text="RRULE format")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_date']
    
    def __str__(self):
        return self.title


# ============================================================
# COURSE ADVERTISEMENT / PROMOTION
# ============================================================

class CourseAdvertisement(models.Model):
    """Promote upcoming course intakes and special offers"""
    
    AD_TYPES = (
        ('banner', 'Banner Advertisement'),
        ('featured', 'Featured Course'),
        ('flash_sale', 'Flash Sale'),
        ('scholarship', 'Scholarship Announcement'),
        ('early_bird', 'Early Bird Special'),
    )
    
    intake = models.ForeignKey(CourseIntake, on_delete=models.CASCADE, related_name='advertisements', null=True, blank=True)
    ad_type = models.CharField(max_length=20, choices=AD_TYPES)
    
    title = models.CharField(max_length=200)
    headline = models.CharField(max_length=100, help_text="Short catchy headline")
    description = models.TextField()
    
    # Media
    banner_image = models.ImageField(upload_to='ad_banners/', null=True, blank=True)
    video_promo_url = models.URLField(blank=True)
    
    # Offer Details
    discount_percentage = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)])
    promo_code = models.CharField(max_length=20, blank=True)
    offer_valid_until = models.DateTimeField(null=True, blank=True)
    
    # Targeting
    target_audience = models.CharField(max_length=200, blank=True)
    
    # Display Settings
    priority = models.IntegerField(default=0, help_text="Higher number = more prominent")
    clicks = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.ad_type}: {self.title}"
    
    def record_click(self):
        self.clicks += 1
        self.save()
    
    def record_impression(self):
        self.impressions += 1
        self.save()
    
    @property
    def click_through_rate(self):
        if self.impressions > 0:
            return (self.clicks / self.impressions) * 100
        return 0


# ============================================================
# REMINDERS & NOTIFICATIONS
# ============================================================

class CourseReminder(models.Model):
    """Automated reminders for course events"""
    
    REMINDER_TYPES = (
        ('course_start', 'Course Start Reminder'),
        ('session_start', 'Session Start Reminder'),
        ('assignment_due', 'Assignment Due'),
        ('payment_due', 'Payment Due'),
        ('early_bird_end', 'Early Bird Deadline'),
    )
    
    intake = models.ForeignKey(CourseIntake, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    
    send_at = models.DateTimeField(help_text="When to send the reminder")
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Optional: specific session
    session = models.ForeignKey(ClassSession, null=True, blank=True, on_delete=models.CASCADE)
    
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} for {self.intake.title}"


# ============================================================
# BACKWARD COMPATIBILITY ALIASES
# ============================================================
# Keep CourseSchedule as an alias for CourseIntake to avoid breaking existing code
CourseSchedule = CourseIntake
ScheduleEnrollment = IntakeEnrollment
