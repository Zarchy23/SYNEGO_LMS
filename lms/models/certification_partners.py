
# lms/models/certification_partners.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.utils import timezone
import uuid

User = get_user_model()

# ============================================================
# CERTIFICATION PROVIDER (Third Party)
# ============================================================

class CertificationProvider(models.Model):
    """Third-party certification bodies like CompTIA, ISACA, EC-Council, etc."""
    
    PROVIDER_TYPES = (
        ('global', 'Global Certification Body'),
        ('regional', 'Regional/African Body'),
        ('local', 'Zimbabwean Body'),
        ('vendor', 'Vendor-Specific'),
    )
    
    # Basic Information
    name = models.CharField(max_length=200, help_text="e.g., 'CompTIA', 'ISACA', 'EC-Council'")
    short_name = models.CharField(max_length=50, help_text="e.g., 'CompTIA', 'CISA'")
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES, default='global')
    logo = models.ImageField(upload_to='certification_partners/logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    
    # Partnership Details
    partnership_status = models.CharField(max_length=20, choices=[
        ('active', 'Active Partner'),
        ('pending', 'Pending Approval'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], default='pending')
    partnership_start_date = models.DateField(null=True, blank=True)
    partnership_end_date = models.DateField(null=True, blank=True)
    partnership_agreement = models.FileField(upload_to='certification_partners/agreements/', null=True, blank=True)
    
    # Contact Information
    contact_person = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    
    # API Integration (for exam registration)
    api_endpoint = models.URLField(blank=True, help_text="API endpoint for exam registration")
    api_key = models.CharField(max_length=500, blank=True)
    api_secret = models.CharField(max_length=500, blank=True)
    webhook_url = models.URLField(blank=True, help_text="Webhook for result notifications")
    
    # Settings
    is_active = models.BooleanField(default=True)
    requires_voucher = models.BooleanField(default=True, help_text="Whether exam requires purchase of voucher")
    voucher_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['provider_type', 'partnership_status']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_certification_count(self):
        return self.certifications.filter(is_active=True).count()


# ============================================================
# CERTIFICATION (Course from Third Party)
# ============================================================

class Certification(models.Model):
    """Specific certification offered by a provider (e.g., CompTIA A+, CISSP, CEH)"""
    
    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )
    
    provider = models.ForeignKey(CertificationProvider, on_delete=models.CASCADE, related_name='certifications')
    
    # Basic Information
    code = models.CharField(max_length=50, unique=True, help_text="e.g., 'CS0-003', 'CISSP-2024'")
    title = models.CharField(max_length=200, help_text="e.g., 'CompTIA Security+', 'Certified Ethical Hacker'")
    full_title = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    
    # Details
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    exam_code = models.CharField(max_length=50, blank=True, help_text="Official exam code")
    exam_duration_minutes = models.PositiveIntegerField(default=90)
    number_of_questions = models.PositiveIntegerField(default=90)
    passing_score = models.PositiveIntegerField(default=750, help_text="Passing score (if scaled)")
    passing_percentage = models.PositiveIntegerField(default=70, help_text="Passing percentage")
    
    # Validity
    validity_years = models.PositiveIntegerField(default=3, help_text="Certification validity in years")
    renewal_requirements = models.TextField(blank=True)
    continuing_education_units = models.PositiveIntegerField(default=0, help_text="CEU required for renewal")
    
    # Synego Course Mapping
    synego_course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='certifications', help_text="Corresponding Synego course")
    
    # Pricing
    exam_voucher_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Price for exam voucher")
    training_material_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    
    # Media
    syllabus_pdf = models.FileField(upload_to='certifications/syllabi/', null=True, blank=True)
    logo = models.ImageField(upload_to='certifications/logos/', null=True, blank=True)
    featured_image = models.ImageField(upload_to='certifications/images/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['provider', 'title']
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['code']),
            models.Index(fields=['difficulty']),
        ]
    
    def __str__(self):
        return f"{self.provider.short_name} - {self.title}"
    
    @property
    def display_title(self):
        return f"{self.provider.short_name} {self.title}"
    
    @property
    def passing_score_display(self):
        if self.passing_score:
            return f"{self.passing_score} points"
        return f"{self.passing_percentage}%"


# ============================================================
# CERTIFICATION EXAM REGISTRATION
# ============================================================

class ExamRegistration(models.Model):
    """Student registration for third-party certification exam"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_payment', 'Pending Payment'),
        ('payment_verified', 'Payment Verified'),
        ('registered', 'Registered with Provider'),
        ('voucher_issued', 'Voucher Issued'),
        ('exam_scheduled', 'Exam Scheduled'),
        ('exam_completed', 'Exam Completed'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('certificate_issued', 'Certificate Issued'),
        ('cancelled', 'Cancelled'),
    )
    
    # Basic Information
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_registrations')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='registrations')
    course_intake = models.ForeignKey('CourseIntake', on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='exam_registrations')
    
    # Registration Details
    registration_date = models.DateTimeField(auto_now_add=True)
    exam_date = models.DateTimeField(null=True, blank=True)
    exam_location = models.CharField(max_length=500, blank=True, help_text="Testing center location")
    exam_language = models.CharField(max_length=50, default='English')
    
    # Payment
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    voucher_code = models.CharField(max_length=100, blank=True, help_text="Exam voucher code")
    voucher_expiry = models.DateField(null=True, blank=True)
    
    # Provider Integration
    provider_reference = models.CharField(max_length=200, blank=True, help_text="Reference ID from provider")
    provider_candidate_id = models.CharField(max_length=200, blank=True)
    
    # Results
    exam_score = models.PositiveIntegerField(null=True, blank=True)
    exam_percentage = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    results_received_at = models.DateTimeField(null=True, blank=True)
    results_details = models.JSONField(default=dict, blank=True, help_text="Detailed score report")
    
    # Certificate
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_issue_date = models.DateField(null=True, blank=True)
    certificate_expiry_date = models.DateField(null=True, blank=True)
    certificate_file = models.FileField(upload_to='student_certificates/', null=True, blank=True)
    certificate_url = models.URLField(blank=True, help_text="Provider's verification URL")
    
    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    # Tracking
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='registered_exams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['certification', 'status']),
            models.Index(fields=['voucher_code']),
            models.Index(fields=['provider_reference']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.certification.title} ({self.status})"
    
    def update_status(self):
        """Auto-update status based on dates and results"""
        if self.passed and self.certificate_file:
            self.status = 'certificate_issued'
        elif self.passed and not self.certificate_file:
            self.status = 'passed'
        elif self.exam_score is not None:
            self.status = 'exam_completed'
        self.save(update_fields=['status'])
    
    def issue_certificate(self, certificate_number, expiry_date, certificate_file=None):
        """Issue certificate after passing exam"""
        self.certificate_number = certificate_number
        self.certificate_issue_date = timezone.now().date()
        self.certificate_expiry_date = expiry_date
        if certificate_file:
            self.certificate_file = certificate_file
        self.status = 'certificate_issued'
        self.save()


# ============================================================
# STUDENT CERTIFICATION TRACKING
# ============================================================

class StudentCertification(models.Model):
    """Track certifications earned by students"""
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_certifications')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='earned_by')
    exam_registration = models.OneToOneField(ExamRegistration, on_delete=models.CASCADE, related_name='earned_certificate')
    
    certificate_number = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    
    # Credential
    credential_id = models.CharField(max_length=100, blank=True, help_text="Digital credential ID")
    badge_url = models.URLField(blank=True, help_text="Digital badge URL")
    verification_url = models.URLField(blank=True, help_text="Verification URL")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['certificate_number']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.certification.title}"
    
    def share_on_linkedin(self):
        """Generate LinkedIn share URL"""
        return f"https://www.linkedin.com/sharing/share-offsite/?url={self.verification_url}"


# ============================================================
# PARTNER INTEGRATION LOGS
# ============================================================

class PartnerIntegrationLog(models.Model):
    """Log all API interactions with certification providers"""
    
    provider = models.ForeignKey(CertificationProvider, on_delete=models.CASCADE, related_name='api_logs')
    endpoint = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    status_code = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'success']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.provider.name} - {self.method} {self.endpoint} - {'Success' if self.success else 'Failed'}"
