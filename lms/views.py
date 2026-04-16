# lms/views.py
import json
import uuid
import csv
import io
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from django.utils.text import slugify
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Count, Avg, Q, Sum, F
from django.db import transaction, IntegrityError
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile

from .models import (
    User, Module, Course, Chapter, Quiz, Question, QuizAttempt,
    Assignment, Submission, Enrollment, EnrollmentRequest, Certificate,
    CourseReview, Notification, SystemLog, StudentProgress
)

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

def get_item(dictionary, key):
    """Template filter to get item from dictionary"""
    return dictionary.get(key, '') if dictionary else ''

def log_action(user, action, obj, request, changes=None):
    """Log user action for audit trail"""
    SystemLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=str(obj.id),
        object_repr=str(obj)[:200],
        changes=changes or {},
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_notification(user, title, message, notif_type='info', related_url=''):
    """Send notification to a user"""
    Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        notification_type=notif_type,
        related_url=related_url
    )

def send_email_notification(subject, message, recipient_list, html_message=None):
    """Send email notification (with fallback for development)"""
    if settings.DEBUG:
        print(f"[EMAIL PREVIEW] {subject} to {recipient_list}")
        print(f"[CONTENT PREVIEW] {message[:200]}...")
        return True
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def build_embed_video_url(video_url):
    """Convert common YouTube URL formats into an embeddable URL."""
    if not video_url:
        return ""

    url = video_url.strip()
    if not url:
        return ""

    # Keep already embeddable links; ensure lightweight params.
    if "youtube.com/embed/" in url:
        return f"{url.split('?')[0]}?rel=0&modestbranding=1"

    try:
        parsed = urlparse(url)
    except Exception:
        return ""

    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").strip("/")

    if "youtu.be" in host and path:
        return f"https://www.youtube.com/embed/{path}?rel=0&modestbranding=1"

    if "youtube.com" in host:
        if path == "watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1"
        if path.startswith("shorts/"):
            video_id = path.split("/", 1)[1]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1"

    # Allow direct non-YouTube embeds only when they are explicit iframe-friendly URLs.
    if url.startswith("https://") and ("vimeo.com/video/" in url or "player.vimeo.com/video/" in url):
        return url

    return ""


def strip_iframe_tags(html):
    """Remove iframe blocks from rich text content to avoid duplicate/broken embeds."""
    if not html:
        return ""
    return re.sub(r"<iframe\b[^>]*>.*?</iframe>", "", html, flags=re.IGNORECASE | re.DOTALL)

def check_role_required(roles):
    """Decorator factory for role-based access control"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('lms:login')
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('lms:student_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Role-based decorators
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and (u.role == 'admin' or u.is_superuser))(view_func)

def instructor_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role in ['admin', 'instructor', 'module_head'])(view_func)

def learner_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == 'learner')(view_func)

# -------------------------------------------------------------------
# Public Views
# -------------------------------------------------------------------

def index(request):
    """Landing page"""
    featured_courses = Course.objects.filter(status='published', is_active=True)[:6]
    modules = Module.objects.filter(status='active')[:7]
    stats = {
        'total_students': User.objects.filter(role='learner', is_approved=True).count(),
        'total_courses': Course.objects.filter(status='published').count(),
        'total_instructors': User.objects.filter(role='instructor').count(),
        'total_modules': Module.objects.filter(status='active').count(),
    }
    context = {
        'featured_courses': featured_courses,
        'modules': modules,
        'stats': stats,
    }
    return render(request, 'lms/index.html', context)

def about(request):
    """About page"""
    return render(request, 'lms/about.html')

def contact(request):
    """Contact page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Send email to admin
        send_email_notification(
            f"Contact Form: {name}",
            f"From: {name} ({email})\n\n{message}",
            [settings.DEFAULT_FROM_EMAIL]
        )
        messages.success(request, "Thank you for contacting us. We'll get back to you soon.")
        return redirect('lms:contact')
    return render(request, 'lms/contact.html')


def featured_courses(request):
    """Featured courses landing page with brutalism design"""
    from django.db.models import Count
    
    # Get featured/published courses with enrollment count
    courses = Course.objects.filter(
        is_published=True
    ).annotate(
        enrollment_count=Count('enrollment')
    ).order_by('-created_at')[:12]
    
    # Get statistics
    total_courses = Course.objects.filter(is_published=True).count()
    total_students = User.objects.filter(role='student').count()
    total_modules = Module.objects.count()
    
    context = {
        'featured_courses': courses,
        'total_courses': total_courses,
        'featured_users': total_students,
        'total_modules': total_modules,
    }
    
    return render(request, 'lms/landing.html', context)

# -------------------------------------------------------------------
# Authentication Views
# -------------------------------------------------------------------

class CustomLoginView(LoginView):
    template_name = 'lms/registration/login.html'
    redirect_authenticated_user = False
    
    def form_valid(self, form):
        """Record successful login attempt"""
        user = form.get_user()
        if user.is_account_locked:
            remaining = user.account_locked_until - timezone.now()
            minutes = max(1, int(remaining.total_seconds() // 60))
            messages.error(self.request, f"Account is temporarily locked. Try again in {minutes} minute(s).")
            return self.render_to_response(self.get_context_data(form=form))

        response = super().form_valid(form)
        self.request.user.record_login_attempt(success=True)
        log_action(self.request.user, 'login', self.request.user, self.request)
        
        # Redirect based on role
        if self.request.user.role == 'admin':
            return redirect('lms:admin_dashboard')
        elif self.request.user.role == 'instructor':
            return redirect('lms:instructor_dashboard')
        elif self.request.user.role == 'module_head':
            return redirect('lms:module_head_dashboard')
        else:
            return redirect('lms:student_dashboard')
    
    def form_invalid(self, form):
        """Record failed login attempt"""
        username = form.cleaned_data.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                user.record_login_attempt(success=False)
            except User.DoesNotExist:
                pass
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    http_method_names = ['get', 'post', 'options']
    next_page = 'lms:index'

    def get(self, request, *args, **kwargs):
        """Support logout via GET for nav links."""
        return self.post(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        log_action(request.user, 'logout', request.user, request)
        return super().dispatch(request, *args, **kwargs)

def self_register(request):
    """Self-registration with approval workflow"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        course_id = request.POST.get('course_id')
        
        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('lms:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('lms:register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('lms:register')
        
        # Create user (pending approval)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role='learner',
            is_active=True,
            is_approved=False
        )
        
        # Generate approval token
        token = user.generate_approval_token()
        
        # Create enrollment request
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            EnrollmentRequest.objects.create(
                student=user,
                course=course,
                reason=request.POST.get('reason', '')
            )
        
        # Notify admins and instructors
        approvers = User.objects.filter(
            Q(role='admin') | Q(role='approver') | Q(role='module_head')
        )
        approval_url = request.build_absolute_uri(reverse('lms:approve_registration', args=[token]))
        
        for approver in approvers:
            send_notification(
                approver,
                f"New Registration Approval Required",
                f"User {user.get_full_name()} ({user.email}) has registered and needs approval.",
                'warning',
                approval_url
            )
            
            send_email_notification(
                f"New User Registration: {user.username}",
                f"""
                A new user has registered and needs approval.
                
                Name: {user.get_full_name()}
                Email: {user.email}
                Phone: {phone_number}
                
                Approve: {approval_url}
                """,
                [approver.email]
            )
        
        messages.success(request, "Registration submitted! You will receive an email once your account is approved.")
        return redirect('lms:registration_success')
    
    courses = Course.objects.filter(status='published', is_active=True)
    return render(request, 'lms/registration/register.html', {'courses': courses})

def registration_success(request):
    """Success page after registration"""
    return render(request, 'lms/registration/registration_success.html')

def approve_registration(request, token):
    """Approve a user registration"""
    user = get_object_or_404(User, approval_token=token)
    
    if not user.is_approval_token_valid():
        messages.error(request, "Approval link has expired. Please contact support.")
        return redirect('lms:index')
    
    user.is_approved = True
    user.approval_token = None
    user.approval_token_created_at = None
    user.save()
    
    # Process pending enrollment requests
    pending_requests = EnrollmentRequest.objects.filter(student=user, status='pending')
    for req in pending_requests:
        req.approve(request.user)
    
    log_action(request.user, 'approve', user, request)
    
    # Send welcome email
    welcome_html = render_to_string('lms/registration/welcome_email.html', {'user': user})
    send_email_notification(
        f"Welcome to Synego Institute, {user.first_name}!",
        f"Your account has been approved. You can now log in at {request.build_absolute_uri(reverse('lms:login'))}",
        [user.email],
        welcome_html
    )
    
    send_notification(user, "Account Approved!", "Your account has been approved. You can now log in and start learning.", 'success')
    
    messages.success(request, f"User {user.username} has been approved.")
    return redirect('lms:admin_dashboard' if request.user.is_authenticated else 'lms:login')

def reject_registration(request, token):
    """Reject a user registration"""
    user = get_object_or_404(User, approval_token=token)
    
    user.delete()  # Remove the pending user
    
    messages.success(request, f"Registration for {user.username} has been rejected.")
    return redirect('lms:admin_dashboard' if request.user.is_authenticated else 'lms:index')

def set_password(request, token):
    """Set password for admin-created accounts"""
    try:
        user = User.objects.get(approval_token=token)
    except User.DoesNotExist:
        messages.error(request, "Invalid or expired link.")
        return redirect('lms:login')
    
    if not user.is_approval_token_valid():
        messages.error(request, "Link has expired. Please request a new one.")
        return redirect('lms:login')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('lms:set_password', token=token)
        
        user.set_password(password)
        user.approval_token = None
        user.approval_token_created_at = None
        user.is_approved = True
        user.save()
        
        login(request, user)
        messages.success(request, "Password set successfully! Welcome to Synego Institute.")
        return redirect('lms:student_dashboard')
    
    return render(request, 'lms/registration/set_password.html', {'token': token})

# -------------------------------------------------------------------
# Profile Views
# -------------------------------------------------------------------

@login_required
def profile_view(request):
    """View user profile"""
    enrollments = request.user.enrollments.select_related('course').all()
    certificates = request.user.certificates.select_related('course').all()
    
    context = {
        'user': request.user,
        'enrollments': enrollments,
        'certificates': certificates,
        'completion_rate': request.user.get_completion_rate(),
    }
    return render(request, 'lms/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.phone_number = request.POST.get('phone_number')
        request.user.address = request.POST.get('address')
        request.user.gender = request.POST.get('gender')
        request.user.date_of_birth = request.POST.get('date_of_birth') or None
        request.user.receive_notifications = request.POST.get('receive_notifications') == 'on'
        
        if request.FILES.get('profile_picture'):
            request.user.profile_picture = request.FILES.get('profile_picture')
        
        request.user.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('lms:profile')
    
    return render(request, 'lms/edit_profile.html', {'user': request.user})

# -------------------------------------------------------------------
# Dashboard Views (Role-based)
# -------------------------------------------------------------------

@learner_required
def student_dashboard(request):
    """Student dashboard"""
    active_enrollments = request.user.enrollments.filter(status='active').select_related('course')
    completed_courses = request.user.enrollments.filter(status='completed').select_related('course')
    
    # Calculate progress for each enrollment
    for enrollment in active_enrollments:
        enrollment.progress_percent = enrollment.get_progress_percent()
    
    # Upcoming deadlines
    upcoming_assignments = Assignment.objects.filter(
        course__in=[e.course for e in active_enrollments],
        due_date__gte=timezone.now(),
        submissions__student=request.user,
        submissions__status__in=['draft', 'returned']
    ).distinct()[:5]
    
    # Recent certificates
    recent_certificates = request.user.certificates.select_related('course').order_by('-issued_at')[:3]
    
    # Notifications
    unread_notifications = request.user.notifications.filter(is_read=False).count()
    
    context = {
        'active_enrollments': active_enrollments,
        'completed_courses': completed_courses,
        'upcoming_assignments': upcoming_assignments,
        'recent_certificates': recent_certificates,
        'unread_notifications': unread_notifications,
        'total_quiz_attempts': request.user.quiz_attempts.count(),
        'avg_quiz_score': request.user.quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0,
    }
    return render(request, 'lms/student/student_dashboard.html', context)

@login_required
def instructor_dashboard(request):
    """Instructor dashboard"""
    if request.user.role not in ['instructor', 'admin', 'module_head']:
        return redirect('lms:student_dashboard')
    
    # Courses taught by this instructor
    courses = Course.objects.filter(department=request.user.module, is_active=True)
    
    # Statistics
    total_students = Enrollment.objects.filter(course__in=courses, status='active').count()
    pending_submissions = Submission.objects.filter(
        assignment__course__in=courses,
        status='submitted'
    ).count()
    
    # Recent submissions needing grading
    recent_submissions = Submission.objects.filter(
        assignment__course__in=courses,
        status='submitted'
    ).select_related('student', 'assignment')[:10]
    
    # Course performance
    course_stats = []
    for course in courses:
        enrolled = Enrollment.objects.filter(course=course, status='active').count()
        completed = Enrollment.objects.filter(course=course, status='completed').count()
        avg_grade = Submission.objects.filter(
            assignment__course=course,
            status='graded',
            grade__isnull=False
        ).aggregate(Avg('grade'))['grade__avg'] or 0
        
        course_stats.append({
            'course': course,
            'enrolled': enrolled,
            'completed': completed,
            'completion_rate': (completed / enrolled * 100) if enrolled > 0 else 0,
            'avg_grade': avg_grade
        })
    
    context = {
        'courses': courses,
        'total_students': total_students,
        'pending_submissions': pending_submissions,
        'recent_submissions': recent_submissions,
        'course_stats': course_stats,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/instructor/instructor_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('lms:student_dashboard')
    
    # Statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(role='learner').count()
    total_instructors = User.objects.filter(role='instructor').count()
    total_courses = Course.objects.count()
    total_departments = Module.objects.count()
    pending_approvals = EnrollmentRequest.objects.filter(status='pending').count()
    pending_submissions = Submission.objects.filter(status='submitted').count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:5]
    recent_logs = SystemLog.objects.select_related('user').order_by('-created_at')[:10]
    manageable_courses = Course.objects.filter(is_active=True).select_related('department').order_by('-updated_at')[:6]
    
    # Monthly enrollment trends (last 6 months)
    monthly_data = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=32)
        count = Enrollment.objects.filter(enrolled_at__gte=month_start, enrolled_at__lt=month_end).count()
        monthly_data.append({
            'month': month_start.strftime('%B %Y'),
            'count': count
        })
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'total_departments': total_departments,
        'pending_approvals': pending_approvals,
        'pending_submissions': pending_submissions,
        'recent_users': recent_users,
        'recent_enrollments': recent_enrollments,
        'recent_logs': recent_logs,
        'manageable_courses': manageable_courses,
        'monthly_data': monthly_data[::-1],
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/admin/admin_dashboard.html', context)

@login_required
def module_head_dashboard(request):
    """Module head dashboard"""
    if request.user.role != 'module_head' or not request.user.module:
        return redirect('lms:student_dashboard')
    
    module = request.user.module
    courses = module.courses.filter(is_active=True)
    instructors = module.members.filter(role='instructor')
    students = module.members.filter(role='learner', is_approved=True)
    
    context = {
        'module': module,
        'courses': courses,
        'instructors': instructors,
        'students': students,
        'total_courses': courses.count(),
        'total_instructors': instructors.count(),
        'total_students': students.count(),
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/module_head_dashboard.html', context)

# -------------------------------------------------------------------
# Module Views
# -------------------------------------------------------------------

def module_list(request):
    """List all modules"""
    modules = Module.objects.filter(status='active')
    return render(request, 'lms/modules/module_list.html', {'modules': modules})


def module_detail(request, slug):
    """Module detail page"""
    module = get_object_or_404(Module, slug=slug, status='active')
    courses = list(module.courses.filter(status='published', is_active=True).order_by('title'))

    level_map = {
        'beginner': 'Certificate / Short Course',
        'intermediate': 'Certificate / Diploma',
        'advanced': 'Diploma / Advanced Certificate',
    }
    for course in courses:
        course.programme_level = level_map.get(course.difficulty, course.get_difficulty_display())

    sample_curriculum = []
    if not courses and 'civil' in module.name.lower():
        sample_curriculum = [
            {
                'programme': 'Engineering Surveying',
                'level': 'Certificate / Diploma',
                'duration': '6 - 12 months',
            },
            {
                'programme': 'Road Construction and Maintenance',
                'level': 'Certificate / Diploma',
                'duration': '6 - 12 months',
            },
            {
                'programme': 'Concrete Technology and Testing',
                'level': 'Certificate / Short Course',
                'duration': '3 months',
            },
            {
                'programme': 'Structural Design Fundamentals',
                'level': 'Certificate',
                'duration': '6 months',
            },
            {
                'programme': 'Materials Testing Laboratory Practice',
                'level': 'Short Course',
                'duration': '4 - 8 weeks',
            },
            {
                'programme': 'Environmental Compliance in Construction',
                'level': 'Short Course',
                'duration': '2 weeks',
            },
        ]

    return render(request, 'lms/modules/module_detail.html', {
        'module': module,
        'courses': courses,
        'sample_curriculum': sample_curriculum,
        'total_programmes': len(courses) + len(sample_curriculum),
    })

# -------------------------------------------------------------------
# Course Views
# -------------------------------------------------------------------

def course_list(request):
    """List all courses with filtering and pagination"""
    courses = Course.objects.filter(status='published', is_active=True).select_related('department')
    
    # Filtering
    module_param = request.GET.get('module')
    if module_param:
        # Handle both module ID and slug
        if module_param.isdigit():
            courses = courses.filter(department_id=module_param)
        else:
            courses = courses.filter(department__slug=module_param)
    
    difficulty = request.GET.get('difficulty')
    if difficulty:
        courses = courses.filter(difficulty=difficulty)
    
    search = request.GET.get('q')
    if search:
        courses = courses.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    departments = Module.objects.filter(status='active')
    
    context = {
        'page_obj': page_obj,
        'modules': departments,
        'selected_module': module_param,
        'selected_difficulty': difficulty,
        'search_query': search,
    }
    return render(request, 'lms/courses/course_list.html', context)

@learner_required
def my_enrolled_courses(request):
    """List courses the learner is enrolled in"""
    enrollments = request.user.enrollments.filter(status__in=['active', 'completed']).select_related('course')
    courses = [e.course for e in enrollments]
    
    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'My Enrolled Courses',
        'is_my_courses': True,
    }
    return render(request, 'lms/courses/course_list.html', context)

def course_detail(request, slug):
    """Course detail page"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    # Check if user is enrolled
    is_enrolled = False
    enrollment = None
    progress = {}
    
    if request.user.is_authenticated and request.user.role == 'learner':
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        is_enrolled = enrollment is not None and enrollment.status == 'active'
        
        if is_enrolled:
            progress = enrollment.progress
            # Calculate overall progress
            total_chapters = course.chapters.count()
            completed_chapters = len(progress.get('completed_chapters', []))
            enrollment.progress_percent = (completed_chapters / total_chapters * 100) if total_chapters > 0 else 0
    
    # Get chapters
    chapters = course.chapters.all().order_by('order')
    
    # Check if there's a pending enrollment request
    has_pending_request = False
    if request.user.is_authenticated:
        has_pending_request = EnrollmentRequest.objects.filter(
            student=request.user, course=course, status='pending'
        ).exists()
    
    context = {
        'course': course,
        'chapters': chapters,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'has_pending_request': has_pending_request,
        'total_chapters': chapters.count(),
    }
    return render(request, 'lms/courses/course_detail.html', context)

@login_required
def enroll_course(request, slug):
    """Enroll in a course (direct enrollment or request)"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.warning(request, "You are already enrolled in this course.")
        return redirect('lms:course_detail', slug=course.slug)
    
    # Check if there's a pending request
    if EnrollmentRequest.objects.filter(student=request.user, course=course, status='pending').exists():
        messages.warning(request, "You already have a pending enrollment request.")
        return redirect('lms:course_detail', slug=course.slug)
    
    # If course requires approval or user is self-registered, create request
    enrollment_request = EnrollmentRequest.objects.create(
        student=request.user,
        course=course,
        reason=request.POST.get('reason', 'Direct enrollment request')
    )
    
    # Notify instructors
    instructors = User.objects.filter(
        Q(role='instructor', department=course.department) |
        Q(role='admin') |
        Q(role='approver')
    )
    
    approval_url = request.build_absolute_uri(reverse('lms:admin_enrollment_requests'))
    for instructor in instructors:
        send_notification(
            instructor,
            f"New Enrollment Request: {course.title}",
            f"{request.user.get_full_name()} has requested to enroll in {course.title}.",
            'info',
            approval_url
        )
    
    messages.success(request, "Your enrollment request has been submitted. You will be notified when approved.")
    return redirect('lms:course_detail', slug=course.slug)

@login_required
def unenroll_course(request, slug):
    """Unenroll from a course"""
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    enrollment.status = 'dropped'
    enrollment.save()
    
    log_action(request.user, 'update', enrollment, request, {'status': 'dropped'})
    messages.success(request, f"You have been unenrolled from {course.title}.")
    return redirect('lms:course_list')

# -------------------------------------------------------------------
# Chapter Views
# -------------------------------------------------------------------

@login_required
def chapter_detail(request, course_slug, chapter_id):
    """View a chapter's content"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    chapter = get_object_or_404(Chapter, id=chapter_id, course=course)
    
    # Check access
    is_admin_access = request.user.is_superuser or request.user.role == 'admin'
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    
    if not is_admin_access and not chapter.is_free_preview and (not enrollment or enrollment.status != 'active'):
        messages.error(request, "Please enroll in this course to access this chapter.")
        return redirect('lms:course_detail', slug=course.slug)
    
    # Check if previous chapters are completed (if required)
    if not is_admin_access and chapter.requires_previous_quiz_pass and not chapter.is_free_preview:
        previous_chapters = Chapter.objects.filter(course=course, order__lt=chapter.order)
        progress = enrollment.progress if enrollment else {}
        completed_chapters = progress.get('completed_chapters', [])
        
        for prev in previous_chapters:
            if str(prev.id) not in completed_chapters:
                messages.warning(request, f"Please complete Chapter {prev.order} first.")
                return redirect('lms:course_detail', slug=course.slug)
    
    # Get quiz for this chapter (if exists)
    quiz = None
    if hasattr(chapter, 'quiz'):
        quiz = chapter.quiz
    
    # Get previous and next chapters
    prev_chapter = Chapter.objects.filter(course=course, order=chapter.order - 1).first()
    next_chapter = Chapter.objects.filter(course=course, order=chapter.order + 1).first()

    chapter_video_embed_url = build_embed_video_url(chapter.video_url)
    chapter_content_html = strip_iframe_tags(chapter.content)
    
    context = {
        'course': course,
        'chapter': chapter,
        'quiz': quiz,
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter,
        'enrollment': enrollment,
        'is_admin_access': is_admin_access,
        'chapter_video_embed_url': chapter_video_embed_url,
        'chapter_content_html': chapter_content_html,
    }
    return render(request, 'lms/courses/chapter_detail.html', context)

@login_required
def mark_chapter_complete(request, course_slug, chapter_id):
    """Mark a chapter as completed"""
    course = get_object_or_404(Course, slug=course_slug)
    chapter = get_object_or_404(Chapter, id=chapter_id, course=course)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Update progress
    progress = enrollment.progress or {}
    completed_chapters = progress.get('completed_chapters', [])
    
    if str(chapter.id) not in completed_chapters:
        completed_chapters.append(str(chapter.id))
        progress['completed_chapters'] = completed_chapters
        enrollment.progress = progress
        enrollment.save()
        
        # Update StudentProgress cache
        StudentProgress.objects.update_or_create(
            student=request.user,
            course=course,
            defaults={'overall_percent': enrollment.get_progress_percent()}
        )
        
        messages.success(request, f"Chapter '{chapter.title}' completed!")
    
    return redirect('lms:chapter_detail', course_slug=course_slug, chapter_id=chapter_id)

# -------------------------------------------------------------------
# Quiz Views (Non-graded)
# -------------------------------------------------------------------

@login_required
def take_quiz(request, quiz_id):
    """Take a quiz (non-graded, performance appraisal only)"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    chapter = quiz.chapter
    course = chapter.course
    
    # Check enrollment
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Check if already attempted and no retakes allowed
    existing_attempt = QuizAttempt.objects.filter(student=request.user, quiz=quiz).first()
    if existing_attempt and existing_attempt.passed and quiz.attempts_allowed == 1:
        messages.warning(request, "You have already passed this quiz and cannot retake it.")
        return redirect('lms:chapter_detail', course_slug=course.slug, chapter_id=chapter.id)
    
    if existing_attempt and QuizAttempt.objects.filter(student=request.user, quiz=quiz).count() >= quiz.attempts_allowed:
        messages.warning(request, "You have used all allowed attempts for this quiz.")
        return redirect('lms:chapter_detail', course_slug=course.slug, chapter_id=chapter.id)
    
    questions = quiz.questions.all()
    
    if request.method == 'POST':
        # Process answers
        score = 0
        total_points = 0
        answers = {}
        
        for question in questions:
            total_points += question.points
            user_answer = request.POST.get(f'question_{question.id}', '')
            answers[str(question.id)] = user_answer
            
            if question.check_answer(user_answer):
                score += question.points
        
        score_percent = (score / total_points * 100) if total_points > 0 else 0
        passed = score_percent >= quiz.pass_score
        
        # Record attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=score_percent,
            passed=passed,
            answers=answers,
            completed_at=timezone.now()
        )
        
        log_action(request.user, 'create', attempt, request)
        
        # Update chapter progress if passed
        if passed:
            progress = enrollment.progress or {}
            quiz_passes = progress.get('quiz_passes', [])
            if str(quiz.id) not in quiz_passes:
                quiz_passes.append(str(quiz.id))
                progress['quiz_passes'] = quiz_passes
                enrollment.progress = progress
                enrollment.save()
        
        return redirect('lms:quiz_result', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'chapter': chapter,
        'course': course,
        'questions': questions,
        'time_limit': quiz.time_limit_minutes,
    }
    return render(request, 'lms/courses/quiz_take.html', context)

@login_required
def quiz_result(request, quiz_id):
    """Show quiz results"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = get_object_or_404(QuizAttempt, student=request.user, quiz=quiz)
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'chapter': quiz.chapter,
    }
    return render(request, 'lms/courses/quiz_result.html', context)

@login_required
def retake_quiz(request, quiz_id):
    """Allow retaking a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if retake is allowed
    attempt_count = QuizAttempt.objects.filter(student=request.user, quiz=quiz).count()
    if attempt_count >= quiz.attempts_allowed:
        messages.error(request, "You have reached the maximum number of attempts.")
        return redirect('lms:chapter_detail', course_slug=quiz.chapter.course.slug, chapter_id=quiz.chapter.id)
    
    return redirect('lms:take_quiz', quiz_id=quiz_id)

# -------------------------------------------------------------------
# Assignment Views (Student)
# -------------------------------------------------------------------

@login_required
def assignment_detail(request, assignment_id):
    """View assignment details"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    
    # Check enrollment
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Get or create submission
    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student=request.user,
        defaults={'status': 'draft'}
    )
    
    # Check if assignment is overdue
    is_overdue = assignment.is_overdue
    
    context = {
        'assignment': assignment,
        'course': course,
        'submission': submission,
        'is_overdue': is_overdue,
    }
    return render(request, 'lms/assignments/assignment_detail.html', context)

@login_required
def submit_assignment(request, assignment_id):
    """Submit an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student=request.user,
        defaults={'status': 'draft'}
    )
    
    if request.method == 'POST':
        # Handle file upload
        if request.FILES.get('submitted_file'):
            submission.submitted_file = request.FILES['submitted_file']
        
        # Handle Google Doc ID
        google_doc_id = request.POST.get('google_doc_id')
        if google_doc_id:
            submission.google_doc_id = google_doc_id
        
        submission.status = 'submitted'
        submission.submitted_at = timezone.now()
        submission.ip_address = get_client_ip(request)
        submission.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        submission.save()
        
        # Submit to Turnitin if enabled
        if assignment.enable_plagiarism_check:
            submission.submit_to_turnitin()
        
        log_action(request.user, 'submit', submission, request)
        
        # Notify instructors
        instructors = User.objects.filter(
            Q(role='instructor', department=course.module) |
            Q(role='admin')
        )
        grade_url = request.build_absolute_uri(reverse('lms:grade_submission', args=[submission.id]))
        
        for instructor in instructors:
            send_notification(
                instructor,
                f"New Submission: {assignment.title}",
                f"{request.user.get_full_name()} has submitted {assignment.title}",
                'info',
                grade_url
            )
        
        messages.success(request, "Assignment submitted successfully!")
        return redirect('lms:course_detail', slug=course.slug)
    
    return redirect('lms:assignment_detail', assignment_id=assignment_id)

@login_required
def view_submission(request, submission_id):
    """View a submission"""
    submission = get_object_or_404(Submission, id=submission_id, student=request.user)
    
    context = {
        'submission': submission,
        'assignment': submission.assignment,
        'course': submission.assignment.course,
    }
    return render(request, 'lms/assignments/submission_view.html', context)

@login_required
def edit_submission(request, submission_id):
    """Edit a draft submission"""
    submission = get_object_or_404(Submission, id=submission_id, student=request.user, status='draft')
    
    if request.method == 'POST':
        if request.FILES.get('submitted_file'):
            submission.submitted_file = request.FILES['submitted_file']
        if request.POST.get('google_doc_id'):
            submission.google_doc_id = request.POST.get('google_doc_id')
        submission.save()
        messages.success(request, "Submission updated.")
        return redirect('lms:assignment_detail', assignment_id=submission.assignment.id)
    
    return redirect('lms:assignment_detail', assignment_id=submission.assignment.id)

# -------------------------------------------------------------------
# Grading Views (Instructor)
# -------------------------------------------------------------------

@instructor_required
def instructor_assignments(request):
    """List all assignments for instructor"""
    courses = Course.objects.filter(department=request.user.module, is_active=True)
    assignments = Assignment.objects.filter(course__in=courses).select_related('course')
    
    context = {
        'assignments': assignments,
        'courses': courses,
    }
    return render(request, 'lms/instructor/assignments_list.html', context)

@instructor_required
def submission_list(request, assignment_id):
    """List all submissions for an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = assignment.submissions.select_related('student').all()
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
    }
    return render(request, 'lms/instructor/submission_list.html', context)

@instructor_required
def grade_submission(request, submission_id):
    """Grade a submission"""
    submission = get_object_or_404(Submission, id=submission_id)
    
    if request.method == 'POST':
        grade = float(request.POST.get('grade', 0))
        feedback = request.POST.get('feedback', '')
        
        # Calculate rubric scores if provided
        rubric_scores = {}
        if request.POST.get('rubric_scores'):
            rubric_scores = json.loads(request.POST.get('rubric_scores'))
        
        submission.grade = grade
        submission.feedback = feedback
        submission.rubric_scores = rubric_scores
        submission.status = 'graded'
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        
        # Update grade in Google Classroom if integrated
        if submission.assignment.google_classroom_id:
            # This would call Google Classroom API
            pass
        
        log_action(request.user, 'grade', submission, request, {'grade': grade})
        
        # Notify student
        send_notification(
            submission.student,
            f"Grade Posted: {submission.assignment.title}",
            f"You received {grade}% on {submission.assignment.title}. Feedback: {feedback[:100]}",
            'grade',
            reverse('lms:view_submission', args=[submission.id])
        )
        
        messages.success(request, f"Submission graded: {grade}%")
        return redirect('lms:submission_list', assignment_id=submission.assignment.id)
    
    context = {
        'submission': submission,
        'assignment': submission.assignment,
        'student': submission.student,
    }
    return render(request, 'lms/instructor/grade_submission.html', context)

@instructor_required
def return_submission(request, submission_id):
    """Return a submission for revision"""
    submission = get_object_or_404(Submission, id=submission_id)
    
    submission.status = 'returned'
    submission.revision_count += 1
    submission.save()
    
    send_notification(
        submission.student,
        f"Assignment Returned: {submission.assignment.title}",
        f"Your submission has been returned for revision. Please review the feedback and resubmit.",
        'warning',
        reverse('lms:assignment_detail', args=[submission.assignment.id])
    )
    
    messages.success(request, "Submission returned to student for revision.")
    return redirect('lms:submission_list', assignment_id=submission.assignment.id)

@instructor_required
def assignment_analytics(request, assignment_id):
    """View analytics for an assignment"""
    if request.user.role not in ['instructor', 'admin', 'module_head']:
        return redirect('lms:student_dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = assignment.submissions.filter(status='graded', grade__isnull=False)
    
    grades = [s.grade for s in submissions]
    avg_grade = sum(grades) / len(grades) if grades else 0
    min_grade = min(grades) if grades else 0
    max_grade = max(grades) if grades else 0
    
    grade_distribution = {
        '90-100': len([g for g in grades if g >= 90]),
        '80-89': len([g for g in grades if 80 <= g < 90]),
        '70-79': len([g for g in grades if 70 <= g < 80]),
        '60-69': len([g for g in grades if 60 <= g < 70]),
        'Below 60': len([g for g in grades if g < 60]),
    }
    
    context = {
        'assignment': assignment,
        'submissions_count': submissions.count(),
        'avg_grade': avg_grade,
        'min_grade': min_grade,
        'max_grade': max_grade,
        'grade_distribution': grade_distribution,
    }
    return render(request, 'lms/instructor/assignment_analytics.html', context)

# -------------------------------------------------------------------
# Assignment Creation Views (Instructor)
# -------------------------------------------------------------------

@login_required
def api_course_chapters(request, course_slug):
    """API endpoint to fetch chapters for a course"""
    try:
        course = get_object_or_404(Course, slug=course_slug)
        
        # Check if user is an instructor in this course's department
        if request.user.role not in ['instructor', 'admin', 'module_head']:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        if request.user.role in ['instructor', 'module_head'] and course.department != request.user.module:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        chapters = course.chapters.all().values('id', 'title', 'order')
        return JsonResponse({
            'success': True,
            'chapters': list(chapters)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@instructor_required
def create_assignment(request, course_slug=None):
    """Create a new assignment"""
    # Get all courses in the instructor's module
    instructor_courses = Course.objects.filter(department=request.user.module, is_active=True)
    
    # Get selected course (from POST or URL parameter)
    selected_course_slug = request.POST.get('course_slug') or course_slug
    
    if not selected_course_slug and instructor_courses.exists():
        selected_course_slug = instructor_courses.first().slug
    
    # Get the course object
    if selected_course_slug:
        course = get_object_or_404(Course, slug=selected_course_slug, department=request.user.module)
    else:
        course = None
    
    if request.method == 'POST' and course:
        assignment = Assignment.objects.create(
            course=course,
            chapter_id=request.POST.get('chapter_id') or None,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            assignment_type=request.POST.get('assignment_type', 'individual'),
            due_date=request.POST.get('due_date'),
            soft_deadline=request.POST.get('soft_deadline') or None,
            late_penalty_percent=int(request.POST.get('late_penalty_percent', 10)),
            total_points=int(request.POST.get('total_points', 100)),
            rubric=json.loads(request.POST.get('rubric', '{}')),
            enable_plagiarism_check=request.POST.get('enable_plagiarism_check') == 'on',
            max_file_size_mb=int(request.POST.get('max_file_size_mb', 50)),
            allowed_file_types=request.POST.get('allowed_file_types', '.pdf,.doc,.docx,.txt'),
        )
        
        log_action(request.user, 'create', assignment, request)
        messages.success(request, f"Assignment '{assignment.title}' created successfully!")
        return redirect('lms:instructor_assignments')
    
    chapters = course.chapters.all() if course else []
    
    # Define assignment type choices
    assignment_types = [
        ('individual', 'Individual Assignment'),
        ('group', 'Group Assignment'),
    ]
    
    # Define file type presets
    file_type_presets = {
        'documents': '.pdf,.doc,.docx,.txt,.rtf',
        'images': '.jpg,.jpeg,.png,.gif,.webp',
        'media': '.mp4,.mkv,.avi,.mov,.webm,.mp3,.wav',
        'code': '.py,.java,.js,.cpp,.c,.html,.css,.txt',
        'spreadsheet': '.xlsx,.xls,.csv,.ods',
        'all': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.mp4,.mkv,.avi,.mov,.zip,.rar',
    }
    
    context = {
        'course': course,
        'instructor_courses': instructor_courses,
        'chapters': chapters,
        'assignment_types': assignment_types,
        'file_type_presets': file_type_presets,
    }
    return render(request, 'lms/instructor/assignment_form.html', context)

@instructor_required
def edit_assignment(request, assignment_id):
    """Edit an existing assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.method == 'POST':
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.assignment_type = request.POST.get('assignment_type')
        assignment.due_date = request.POST.get('due_date')
        assignment.soft_deadline = request.POST.get('soft_deadline') or None
        assignment.late_penalty_percent = int(request.POST.get('late_penalty_percent', 10))
        assignment.total_points = int(request.POST.get('total_points', 100))
        assignment.rubric = json.loads(request.POST.get('rubric', '{}'))
        assignment.enable_plagiarism_check = request.POST.get('enable_plagiarism_check') == 'on'
        assignment.save()
        
        log_action(request.user, 'update', assignment, request)
        messages.success(request, "Assignment updated successfully!")
        return redirect('lms:instructor_assignments')
    
    context = {'assignment': assignment}
    return render(request, 'lms/instructor/assignment_form.html', context)

@instructor_required
def delete_assignment(request, assignment_id):
    """Delete an assignment"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    assignment.delete()
    
    log_action(request.user, 'delete', assignment, request)
    messages.success(request, "Assignment deleted.")
    return redirect('lms:instructor_assignments')


# -------------------------------------------------------------------
# Course Material Management Views (Admin & Instructor)
# -------------------------------------------------------------------

def _redirect_course_management(course_slug):
    """Redirect helper that falls back to course detail if manage route is unavailable."""
    try:
        return redirect('lms:manage_course', course_slug=course_slug)
    except Exception:
        return redirect('lms:course_detail', slug=course_slug)


@instructor_required
def manage_course(request, course_slug):
    """Course management hub for admin/instructor/department head."""
    course = get_object_or_404(Course, slug=course_slug)

    if request.user.role in ['instructor', 'module_head'] and course.department != request.user.module:
        messages.error(request, "You can only manage courses in your department.")
        return redirect('lms:course_detail', slug=course.slug)

    chapters = course.chapters.all().order_by('order')
    assignments = course.assignments.all().order_by('due_date')
    quizzes = Quiz.objects.filter(chapter__course=course).select_related('chapter').order_by('chapter__order')

    context = {
        'course': course,
        'chapters': chapters,
        'assignments': assignments,
        'quizzes': quizzes,
    }
    return render(request, 'lms/admin/manage_course.html', context)


@instructor_required
def add_course_material(request, course_slug):
    """Add material (chapter, assignment, quiz) to a course."""
    course = get_object_or_404(Course, slug=course_slug)

    if request.user.role in ['instructor', 'module_head'] and course.department != request.user.module:
        messages.error(request, "You can only add materials to courses in your module.")
        return redirect('lms:course_detail', slug=course.slug)

    chapters = course.chapters.all().order_by('order')
    context = {
        'course': course,
        'chapters': chapters,
    }
    return render(request, 'lms/admin/add_course_material.html', context)


@admin_required
def admin_add_chapter(request, course_slug):
    """Admin view to add a chapter to a course."""
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        # Handle file upload - documents are primary
        document_file = None
        if 'document_file' in request.FILES:
            uploaded_file = request.FILES['document_file']
            # Validate file extension
            allowed_extensions = ('.pdf', '.pptx', '.ppt', '.xlsx', '.xls')
            if not any(uploaded_file.name.lower().endswith(ext) for ext in allowed_extensions):
                messages.error(request, "Only PDF, PowerPoint (.pptx, .ppt), and Excel (.xlsx, .xls) files are allowed.")
                return redirect('lms:admin_add_chapter', course_slug=course.slug)
            document_file = uploaded_file
        
        chapter = Chapter.objects.create(
            course=course,
            title=request.POST.get('title', '').strip(),
            order=int(request.POST.get('order', 1)),
            chapter_type=request.POST.get('chapter_type', 'lesson'),
            document_file=document_file,
            video_url=request.POST.get('video_url', '').strip(),  # Optional
            content=request.POST.get('content', ''),
            estimated_minutes=int(request.POST.get('estimated_minutes', 30)),
            template_doc_id=request.POST.get('template_doc_id', '').strip(),
            is_free_preview=request.POST.get('is_free_preview') == 'on',
            requires_previous_quiz_pass=request.POST.get('requires_previous_quiz_pass') == 'on',
        )
        log_action(request.user, 'create', chapter, request)
        messages.success(request, f"Chapter '{chapter.title}' added to {course.title}.")

        if chapter.chapter_type == 'quiz':
            return redirect('lms:admin_add_quiz_with_chapter', course_slug=course.slug, chapter_id=chapter.id)

        return _redirect_course_management(course.slug)

    context = {
        'course': course,
        'chapter_types': Chapter.CHAPTER_TYPE_CHOICES,
    }
    return render(request, 'lms/admin/add_chapter.html', context)


@admin_required
def admin_add_assignment(request, course_slug):
    """Admin view to add an assignment to a course."""
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        rubric_raw = request.POST.get('rubric', '{}')
        try:
            rubric_value = json.loads(rubric_raw)
        except json.JSONDecodeError:
            messages.error(request, "Rubric JSON is invalid.")
            return redirect('lms:admin_add_assignment', course_slug=course.slug)

        assignment = Assignment.objects.create(
            course=course,
            chapter_id=request.POST.get('chapter_id') or None,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', ''),
            assignment_type=request.POST.get('assignment_type', 'individual'),
            due_date=request.POST.get('due_date'),
            soft_deadline=request.POST.get('soft_deadline') or None,
            late_penalty_percent=int(request.POST.get('late_penalty_percent', 10)),
            total_points=int(request.POST.get('total_points', 100)),
            rubric=rubric_value,
            enable_plagiarism_check=request.POST.get('enable_plagiarism_check') == 'on',
            max_file_size_mb=int(request.POST.get('max_file_size_mb', 50)),
            allowed_file_types=request.POST.get('allowed_file_types', '.pdf,.doc,.docx,.txt'),
        )
        log_action(request.user, 'create', assignment, request)
        messages.success(request, f"Assignment '{assignment.title}' added to {course.title}.")
        return _redirect_course_management(course.slug)

    chapters = course.chapters.all().order_by('order')
    context = {
        'course': course,
        'chapters': chapters,
        'assignment_types': Assignment.ASSIGNMENT_TYPE_CHOICES,
    }
    return render(request, 'lms/admin/add_assignment.html', context)


@admin_required
def admin_add_quiz(request, course_slug, chapter_id=None):
    """Admin view to add a quiz to a chapter."""
    course = get_object_or_404(Course, slug=course_slug)
    selected_chapter = None
    if chapter_id is not None:
        selected_chapter = get_object_or_404(Chapter, id=chapter_id, course=course)

    if request.method == 'POST':
        chapter = get_object_or_404(Chapter, id=request.POST.get('chapter_id'), course=course)

        if hasattr(chapter, 'quiz'):
            messages.warning(request, f"Chapter '{chapter.title}' already has a quiz. You can edit it instead.")
            return redirect('lms:admin_edit_quiz', quiz_id=chapter.quiz.id)

        quiz = Quiz.objects.create(
            chapter=chapter,
            title=request.POST.get('title', '').strip() or f"Quiz for {chapter.title}",
            description=request.POST.get('description', ''),
            pass_score=int(request.POST.get('pass_score', 70)),
            time_limit_minutes=int(request.POST.get('time_limit_minutes')) if request.POST.get('time_limit_minutes') else None,
            attempts_allowed=int(request.POST.get('attempts_allowed', 1)),
            shuffle_questions=request.POST.get('shuffle_questions') == 'on',
            show_answers_after_submit=request.POST.get('show_answers_after_submit') == 'on',
        )
        log_action(request.user, 'create', quiz, request)
        messages.success(request, f"Quiz added to chapter '{chapter.title}'.")
        return redirect('lms:admin_add_quiz_questions', quiz_id=quiz.id)

    chapters = course.chapters.all().order_by('order')
    context = {
        'course': course,
        'chapters': chapters,
        'selected_chapter': selected_chapter,
    }
    return render(request, 'lms/admin/add_quiz.html', context)


@admin_required
def admin_add_quiz_questions(request, quiz_id):
    """Add questions to a quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    chapter = quiz.chapter
    course = chapter.course

    if request.method == 'POST':
        question_text = request.POST.get('question_text', '').strip()
        question_type = request.POST.get('question_type', 'mcq')
        points = int(request.POST.get('points', 1))
        next_order = quiz.questions.count() + 1

        if not question_text:
            messages.error(request, "Question text is required.")
            return redirect('lms:admin_add_quiz_questions', quiz_id=quiz.id)

        if question_type == 'mcq':
            options = [o.strip() for o in request.POST.getlist('options[]') if o.strip()]
            correct_answer = request.POST.get('correct_answer', '').strip()
            Question.objects.create(
                quiz=quiz,
                text=question_text,
                question_type='mcq',
                options=options,
                correct_answer=correct_answer,
                points=points,
                order=next_order,
            )
        elif question_type == 'tf':
            correct_answer = request.POST.get('correct_answer', 'True')
            Question.objects.create(
                quiz=quiz,
                text=question_text,
                question_type='tf',
                options=['True', 'False'],
                correct_answer=correct_answer,
                points=points,
                order=next_order,
            )
        elif question_type == 'short':
            correct_answer = request.POST.get('correct_answer', '').strip()
            Question.objects.create(
                quiz=quiz,
                text=question_text,
                question_type='short',
                options=[],
                correct_answer=correct_answer,
                points=points,
                order=next_order,
            )

        messages.success(request, "Question added successfully.")
        if request.POST.get('add_another') == 'on':
            return redirect('lms:admin_add_quiz_questions', quiz_id=quiz.id)
        return _redirect_course_management(course.slug)

    questions = quiz.questions.all().order_by('order', 'id')
    context = {
        'quiz': quiz,
        'chapter': chapter,
        'course': course,
        'questions': questions,
        'question_types': [
            ('mcq', 'Multiple Choice'),
            ('tf', 'True/False'),
            ('short', 'Short Answer'),
        ],
    }
    return render(request, 'lms/admin/add_quiz_questions.html', context)


@admin_required
def admin_edit_chapter(request, chapter_id):
    """Edit an existing chapter."""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    course = chapter.course

    if request.method == 'POST':
        chapter.title = request.POST.get('title', '').strip()
        chapter.order = int(request.POST.get('order', 1))
        chapter.chapter_type = request.POST.get('chapter_type', chapter.chapter_type)
        chapter.content = request.POST.get('content', '')
        chapter.estimated_minutes = int(request.POST.get('estimated_minutes', 30))
        chapter.template_doc_id = request.POST.get('template_doc_id', '').strip()
        chapter.is_free_preview = request.POST.get('is_free_preview') == 'on'
        chapter.requires_previous_quiz_pass = request.POST.get('requires_previous_quiz_pass') == 'on'
        
        # Handle document file upload
        if 'document_file' in request.FILES:
            uploaded_file = request.FILES['document_file']
            # Validate file extension
            allowed_extensions = ('.pdf', '.pptx', '.ppt', '.xlsx', '.xls')
            if not any(uploaded_file.name.lower().endswith(ext) for ext in allowed_extensions):
                messages.error(request, "Only PDF, PowerPoint (.pptx, .ppt), and Excel (.xlsx, .xls) files are allowed.")
                return redirect('lms:admin_edit_chapter', chapter_id=chapter.id)
            # Delete old file if exists
            if chapter.document_file:
                chapter.document_file.delete()
            chapter.document_file = uploaded_file
        
        # Video URL is optional
        chapter.video_url = request.POST.get('video_url', '').strip()
        
        chapter.save()

        log_action(request.user, 'update', chapter, request)
        messages.success(request, f"Chapter '{chapter.title}' updated successfully.")
        return _redirect_course_management(course.slug)

    context = {
        'chapter': chapter,
        'course': course,
        'chapter_types': Chapter.CHAPTER_TYPE_CHOICES,
    }
    return render(request, 'lms/admin/edit_chapter.html', context)


@admin_required
def admin_delete_chapter(request, chapter_id):
    """Delete a chapter."""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    course = chapter.course
    chapter_title = chapter.title

    if request.method == 'POST':
        log_action(request.user, 'delete', chapter, request)
        chapter.delete()
        messages.success(request, f"Chapter '{chapter_title}' deleted successfully.")
        return _redirect_course_management(course.slug)

    context = {
        'chapter': chapter,
        'course': course,
    }
    return render(request, 'lms/admin/confirm_delete_chapter.html', context)


@admin_required
def admin_edit_assignment(request, assignment_id):
    """Edit an existing assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course

    if request.method == 'POST':
        rubric_raw = request.POST.get('rubric', '{}')
        try:
            rubric_value = json.loads(rubric_raw)
        except json.JSONDecodeError:
            messages.error(request, "Rubric JSON is invalid.")
            return redirect('lms:admin_edit_assignment', assignment_id=assignment.id)

        assignment.title = request.POST.get('title', '').strip()
        assignment.description = request.POST.get('description', '')
        assignment.assignment_type = request.POST.get('assignment_type', assignment.assignment_type)
        assignment.due_date = request.POST.get('due_date')
        assignment.soft_deadline = request.POST.get('soft_deadline') or None
        assignment.late_penalty_percent = int(request.POST.get('late_penalty_percent', 10))
        assignment.total_points = int(request.POST.get('total_points', 100))
        assignment.rubric = rubric_value
        assignment.enable_plagiarism_check = request.POST.get('enable_plagiarism_check') == 'on'
        assignment.max_file_size_mb = int(request.POST.get('max_file_size_mb', 50))
        assignment.allowed_file_types = request.POST.get('allowed_file_types', '.pdf,.doc,.docx,.txt')
        assignment.save()

        log_action(request.user, 'update', assignment, request)
        messages.success(request, f"Assignment '{assignment.title}' updated successfully.")
        return _redirect_course_management(course.slug)

    context = {
        'assignment': assignment,
        'course': course,
        'assignment_types': Assignment.ASSIGNMENT_TYPE_CHOICES,
    }
    return render(request, 'lms/admin/edit_assignment.html', context)


@admin_required
def admin_delete_assignment(request, assignment_id):
    """Delete an assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course
    assignment_title = assignment.title

    if request.method == 'POST':
        log_action(request.user, 'delete', assignment, request)
        assignment.delete()
        messages.success(request, f"Assignment '{assignment_title}' deleted successfully.")
        return _redirect_course_management(course.slug)

    context = {
        'assignment': assignment,
        'course': course,
    }
    return render(request, 'lms/admin/confirm_delete_assignment.html', context)


@admin_required
def admin_edit_quiz(request, quiz_id):
    """Edit an existing quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    chapter = quiz.chapter
    course = chapter.course

    if request.method == 'POST':
        quiz.title = request.POST.get('title', '').strip() or quiz.title
        quiz.description = request.POST.get('description', '')
        quiz.pass_score = int(request.POST.get('pass_score', 70))
        quiz.time_limit_minutes = int(request.POST.get('time_limit_minutes')) if request.POST.get('time_limit_minutes') else None
        quiz.attempts_allowed = int(request.POST.get('attempts_allowed', 1))
        quiz.shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        quiz.show_answers_after_submit = request.POST.get('show_answers_after_submit') == 'on'
        quiz.save()

        log_action(request.user, 'update', quiz, request)
        messages.success(request, "Quiz updated successfully.")
        return _redirect_course_management(course.slug)

    context = {
        'quiz': quiz,
        'chapter': chapter,
        'course': course,
    }
    return render(request, 'lms/admin/edit_quiz.html', context)


@admin_required
def admin_delete_quiz(request, quiz_id):
    """Delete a quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    chapter = quiz.chapter
    course = chapter.course

    if request.method == 'POST':
        log_action(request.user, 'delete', quiz, request)
        quiz.delete()
        messages.success(request, "Quiz deleted successfully.")
        return _redirect_course_management(course.slug)

    context = {
        'quiz': quiz,
        'chapter': chapter,
        'course': course,
    }
    return render(request, 'lms/admin/confirm_delete_quiz.html', context)


@admin_required
def admin_edit_question(request, question_id):
    """Edit a quiz question."""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz

    if request.method == 'POST':
        question.text = request.POST.get('question_text', '').strip()
        question.question_type = request.POST.get('question_type', question.question_type)
        question.points = int(request.POST.get('points', 1))

        if question.question_type == 'mcq':
            question.options = [o.strip() for o in request.POST.getlist('options[]') if o.strip()]
            question.correct_answer = request.POST.get('correct_answer', '').strip()
        elif question.question_type == 'tf':
            question.options = ['True', 'False']
            question.correct_answer = request.POST.get('correct_answer', 'True')
        elif question.question_type == 'short':
            question.options = []
            question.correct_answer = request.POST.get('correct_answer', '').strip()

        question.save()
        log_action(request.user, 'update', question, request)
        messages.success(request, "Question updated successfully.")
        return redirect('lms:admin_add_quiz_questions', quiz_id=quiz.id)

    context = {
        'question': question,
        'quiz': quiz,
    }
    return render(request, 'lms/admin/edit_question.html', context)


@admin_required
def admin_delete_question(request, question_id):
    """Delete a quiz question."""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz

    if request.method == 'POST':
        log_action(request.user, 'delete', question, request)
        question.delete()
        messages.success(request, "Question deleted successfully.")
        return redirect('lms:admin_add_quiz_questions', quiz_id=quiz.id)

    context = {
        'question': question,
        'quiz': quiz,
    }
    return render(request, 'lms/admin/confirm_delete_question.html', context)

# -------------------------------------------------------------------
# Admin Views
# -------------------------------------------------------------------

@admin_required
def admin_users(request):
    """User management for admin"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filtering
    role = request.GET.get('role')
    if role:
        users = users.filter(role=role)
    
    status = request.GET.get('status')
    if status == 'approved':
        users = users.filter(is_approved=True)
    elif status == 'pending':
        users = users.filter(is_approved=False)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'role_filter': role,
        'status_filter': status,
        'role_choices': User.ROLE_CHOICES,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/admin/user_management.html', context)

@admin_required
def admin_add_student(request):
    """Add a student manually (direct addition)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        module_id = request.POST.get('module_id')
        course_ids = request.POST.getlist('course_ids')
        
        # Generate random password
        temp_password = User.objects.make_random_password()
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=temp_password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role='learner',
            is_approved=True,
            is_active=True,
            temp_password=temp_password,
            department_id=module_id or None
        )
        
        # Generate approval token for password setup
        token = user.generate_approval_token()
        
        # Enroll in selected courses
        for course_id in course_ids:
            Enrollment.objects.create(
                student=user,
                course_id=course_id,
                status='active',
                enrollment_method='admin',
                enrolled_by=request.user
            )
        
        # Send credentials email
        set_password_url = request.build_absolute_uri(reverse('lms:set_password', args=[token]))
        
        email_html = render_to_string('lms/registration/credentials_email.html', {
            'user': user,
            'temp_password': temp_password,
            'set_password_url': set_password_url
        })
        
        send_email_notification(
            f"Welcome to Synego Institute, {first_name}!",
            f"Your account has been created. Please set your password using: {set_password_url}",
            [email],
            email_html
        )
        
        log_action(request.user, 'create', user, request)
        messages.success(request, f"Student {username} added successfully. Credentials emailed.")
        return redirect('lms:admin_users')
    
    departments = Module.objects.filter(status='active')
    courses = Course.objects.filter(status='published', is_active=True)
    
    context = {
        'modules': departments,
        'courses': courses,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/admin/add_student.html', context)

@admin_required
def admin_enrollment_requests(request):
    """Manage enrollment requests"""
    requests = EnrollmentRequest.objects.select_related('student', 'course').filter(status='pending')
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        enrollment_request = get_object_or_404(EnrollmentRequest, id=request_id)
        
        if action == 'approve':
            enrollment_request.approve(request.user)
            messages.success(request, f"Enrollment request for {enrollment_request.student.username} approved.")
        elif action == 'reject':
            enrollment_request.reject(request.user, request.POST.get('notes', ''))
            messages.success(request, f"Enrollment request for {enrollment_request.student.username} rejected.")
        
        return redirect('lms:admin_enrollment_requests')
    
    context = {'requests': requests, 'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0}
    return render(request, 'lms/admin/enrollment_requests.html', context)

@admin_required
def admin_reports(request):
    """Generate admin reports"""
    from django.db.models.functions import TruncMonth
    
    report_type = request.GET.get('type', 'enrollment')
    
    if report_type == 'enrollment':
        # Enrollment report
        data = Enrollment.objects.select_related('student', 'course').values(
            'course__title', 'course__department__name'
        ).annotate(
            count=Count('id'),
            completed=Count('id', filter=Q(status='completed'))
        )
    elif report_type == 'completion':
        # Completion report - group by month of issued_at
        data = Certificate.objects.select_related('student', 'course').annotate(
            month=TruncMonth('issued_at')
        ).values('course__title', 'month').annotate(count=Count('id')).order_by('-month')
    else:
        data = []
    
    # Summary statistics
    total_active_students = User.objects.filter(role='learner', is_active=True).count()
    total_enrolled = Enrollment.objects.count()
    total_certificates = Certificate.objects.count()
    total_courses = Course.objects.filter(is_active=True).count()
    
    context = {
        'report_type': report_type,
        'data': data,
        'report_choices': [
            ('enrollment', 'Enrollment Report'),
            ('completion', 'Completion Report'),
            ('quiz', 'Quiz Performance Report'),
            ('assignment', 'Assignment Report'),
        ],
        'total_active_students': total_active_students,
        'total_enrolled': total_enrolled,
        'total_certificates': total_certificates,
        'total_courses': total_courses,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/admin/reports.html', context)

@admin_required
def download_report(request, report_type):
    """Download report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'enrollment':
        writer.writerow(['Course', 'Module', 'Total Enrollments', 'Completed'])
        data = Enrollment.objects.select_related('course').values(
            'course__title', 'course__department__name'
        ).annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed'))
        )
        for row in data:
            writer.writerow([row['course__title'], row['course__department__name'], row['total'], row['completed']])
    
    return response


@admin_required
def admin_system_logs(request):
    """View system logs for admin"""
    logs = SystemLog.objects.select_related('user').all().order_by('-created_at')
    
    # Filtering
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    object_type = request.GET.get('object_type')
    if object_type:
        logs = logs.filter(object_type=object_type)
    
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    actions = SystemLog.objects.values_list('action', flat=True).distinct()
    object_types = SystemLog.objects.values_list('object_type', flat=True).distinct()
    users = User.objects.filter(id__in=SystemLog.objects.values_list('user_id', flat=True).distinct())
    
    context = {
        'page_obj': page_obj,
        'actions': actions,
        'object_types': object_types,
        'users': users,
        'selected_action': action,
        'selected_object_type': object_type,
        'selected_user': user_id,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/admin/system_logs.html', context)


@admin_required
def admin_edit_user(request, user_id):
    """Edit user from admin panel"""
    edit_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        edit_user.username = request.POST.get('username')
        edit_user.email = request.POST.get('email')
        edit_user.first_name = request.POST.get('first_name')
        edit_user.last_name = request.POST.get('last_name')
        edit_user.phone_number = request.POST.get('phone_number')
        edit_user.role = request.POST.get('role')
        edit_user.module_id = request.POST.get('module_id') or None
        edit_user.is_approved = request.POST.get('is_approved') == 'on'
        edit_user.is_active = request.POST.get('is_active') == 'on'
        
        edit_user.save()
        
        log_action(request.user, 'update', edit_user, request)
        messages.success(request, f"User {edit_user.username} updated successfully.")
        return redirect('lms:admin_users')
    
    departments = Module.objects.filter(status='active')
    context = {
        'edit_user': edit_user,
        'modules': departments,
        'role_choices': User.ROLE_CHOICES,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/admin/edit_user.html', context)


@admin_required
def admin_delete_user(request, user_id):
    """Delete user from admin panel"""
    delete_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = delete_user.username
        delete_user.delete()
        log_action(request.user, 'delete', delete_user, request)
        messages.success(request, f"User {username} deleted successfully.")
        return redirect('lms:admin_users')
    
    return render(request, 'lms/admin/confirm_delete_user.html', {'user': delete_user, 'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0})


@admin_required
def admin_modules(request):
    """Manage modules"""
    modules = Module.objects.all().order_by('name')
    
    context = {
        'modules': modules,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'lms/admin/modules.html', context)


@admin_required
def admin_add_module(request):
    """Add a new module"""
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')
        mission = request.POST.get('mission')
        vision = request.POST.get('vision')
        infrastructure = request.POST.get('infrastructure')
        resources = request.POST.get('resources')
        contact_email = request.POST.get('contact_email')
        contact_phone = request.POST.get('contact_phone')
        office_location = request.POST.get('office_location')
        min_instructors = request.POST.get('min_instructors', 1)
        max_capacity = request.POST.get('max_capacity', 100)
        
        module = Module.objects.create(
            name=name,
            code=code,
            description=description,
            mission=mission,
            vision=vision,
            infrastructure=infrastructure,
            resources=resources,
            contact_email=contact_email,
            contact_phone=contact_phone,
            office_location=office_location,
            min_instructors=min_instructors,
            max_capacity=max_capacity
        )
        
        log_action(request.user, 'create', module, request)
        messages.success(request, f"Module {name} created successfully.")
        return redirect('lms:admin_modules')
    
    return render(request, 'lms/admin/add_module.html', {'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0})


@admin_required
def admin_edit_module(request, module_id):
    """Edit a module"""
    module = get_object_or_404(Module, id=module_id)
    
    if request.method == 'POST':
        module.name = request.POST.get('name')
        module.code = request.POST.get('code')
        module.description = request.POST.get('description')
        module.mission = request.POST.get('mission')
        module.vision = request.POST.get('vision')
        module.infrastructure = request.POST.get('infrastructure')
        module.resources = request.POST.get('resources')
        module.contact_email = request.POST.get('contact_email')
        module.contact_phone = request.POST.get('contact_phone')
        module.office_location = request.POST.get('office_location')
        module.min_instructors = request.POST.get('min_instructors', 1)
        module.max_capacity = request.POST.get('max_capacity', 100)
        module.status = request.POST.get('status')
        
        module.save()
        
        log_action(request.user, 'update', module, request)
        messages.success(request, f"Module {module.name} updated successfully.")
        return redirect('lms:admin_modules')
    
    context = {'module': module, 'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0}
    return render(request, 'lms/admin/edit_module.html', context)


@admin_required
def admin_process_request(request, request_id):
    """Process an enrollment request via AJAX or direct POST"""
    enrollment_request = get_object_or_404(EnrollmentRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            enrollment_request.approve(request.user)
            messages.success(request, f"Enrollment request for {enrollment_request.student.username} approved.")
        elif action == 'reject':
            enrollment_request.reject(request.user, notes)
            messages.success(request, f"Enrollment request for {enrollment_request.student.username} rejected.")
        
        return redirect('lms:admin_enrollment_requests')
    
    context = {'request_obj': enrollment_request, 'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0}
    return render(request, 'lms/admin/process_request.html', context)


@admin_required
def download_bulk_enroll_template(request):
    """Download CSV template for bulk enrollment"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bulk_enrollment_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['email', 'username', 'first_name', 'last_name'])
    writer.writerow(['student1@example.com', 'student1', 'John', 'Doe'])
    writer.writerow(['student2@example.com', 'student2', 'Jane', 'Smith'])
    writer.writerow(['student3@example.com', 'student3', 'Bob', 'Johnson'])
    
    return response


@admin_required
def bulk_enroll_students(request):
    """Bulk enroll students via CSV upload"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        course_id = request.POST.get('course_id')
        
        if not csv_file or not course_id:
            messages.error(request, "Please provide both CSV file and course.")
            return redirect('lms:bulk_enroll_students')
        
        course = get_object_or_404(Course, id=course_id)
        
        # Read CSV
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        created_count = 0
        enrolled_count = 0
        errors = []
        
        for row in reader:
            email = row.get('email')
            username = row.get('username', email.split('@')[0])
            first_name = row.get('first_name', '')
            last_name = row.get('last_name', '')
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'learner',
                    'is_approved': True,
                    'is_active': True
                }
            )
            
            if created:
                # Generate temp password
                temp_password = User.objects.make_random_password()
                user.set_password(temp_password)
                user.temp_password = temp_password
                user.save()
                created_count += 1
            
            # Enroll in course
            enrollment, enrolled = Enrollment.objects.get_or_create(
                student=user,
                course=course,
                defaults={'status': 'active', 'enrollment_method': 'bulk'}
            )
            if enrolled:
                enrolled_count += 1
        
        messages.success(request, f"Bulk enrollment complete! {created_count} users created, {enrolled_count} enrollments added.")
        if errors:
            messages.warning(request, f"Errors: {', '.join(errors[:5])}")
        
        return redirect('lms:admin_users')
    
    courses = Course.objects.filter(status='published', is_active=True)
    context = {'courses': courses, 'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0}
    return render(request, 'lms/admin/bulk_enroll.html', context)


@admin_required
def bulk_upload_courses(request):
    """Bulk upload courses via CSV"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, "Please provide a CSV file.")
            return redirect('lms:bulk_upload_courses')
        
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        created_count = 0
        errors = []
        
        for row in reader:
            try:
                department = Module.objects.get(code=row.get('department_code'))
                
                course = Course.objects.create(
                    department=department,
                    title=row.get('title'),
                    code=row.get('code'),
                    description=row.get('description', ''),
                    duration=row.get('duration'),
                    difficulty=row.get('difficulty', 'beginner'),
                    price=float(row.get('price', 0)),
                    status='draft'
                )
                created_count += 1
            except Exception as e:
                errors.append(f"{row.get('code', 'Unknown')}: {str(e)}")
        
        messages.success(request, f"Bulk upload complete! {created_count} courses created.")
        if errors:
            messages.warning(request, f"Errors: {', '.join(errors[:5])}")
        
        return redirect('lms:course_list')
    
    return render(request, 'lms/admin/bulk_upload_courses.html', {'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0})

# -------------------------------------------------------------------
# Certificate Views
# -------------------------------------------------------------------

def view_certificate(request, certificate_id):
    """View a certificate"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    return render(request, 'lms/certificates/certificate_view.html', {'certificate': certificate})

def download_certificate(request, certificate_id):
    """Download certificate PDF"""
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    response = HttpResponse(certificate.pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{certificate_id}.pdf"'
    return response

def verify_certificate(request, certificate_id):
    """Verify certificate authenticity"""
    try:
        certificate = Certificate.objects.get(certificate_id=certificate_id)
        is_valid = certificate.verify()
    except Certificate.DoesNotExist:
        certificate = None
        is_valid = False
    
    context = {
        'certificate': certificate,
        'is_valid': is_valid,
    }
    return render(request, 'lms/certificates/verify_certificate.html', context)

# -------------------------------------------------------------------
# Google Integration Views (Placeholders)
# -------------------------------------------------------------------

@login_required
def google_login(request):
    """Initiate Google OAuth login"""
    # This would integrate with django-allauth
    return redirect('/accounts/google/login/')

@login_required
def google_callback(request):
    """Handle Google OAuth callback"""
    # Handled by allauth
    return redirect('lms:student_dashboard')

@login_required
def sync_google_classroom(request):
    """Sync courses from Google Classroom"""
    messages.success(request, "Google Classroom sync initiated.")
    return redirect('lms:instructor_dashboard')

@login_required
def create_google_doc(request, assignment_id):
    """Create a Google Doc from template"""
    messages.success(request, "Google Doc created.")
    return redirect('lms:assignment_detail', assignment_id=assignment_id)

# -------------------------------------------------------------------
# Turnitin Integration Views (Placeholders)
# -------------------------------------------------------------------

@login_required
def turnitin_launch(request, submission_id):
    """Launch Turnitin LTI"""
    submission = get_object_or_404(Submission, id=submission_id)
    # This would implement LTI 1.3 launch
    return render(request, 'lms/turnitin/turnitin_launch.html', {'submission': submission})

@csrf_exempt
def turnitin_callback(request):
    """Handle Turnitin callback"""
    return JsonResponse({'status': 'ok'})

@login_required
def turnitin_report(request, submission_id):
    """View Turnitin similarity report"""
    submission = get_object_or_404(Submission, id=submission_id)
    return render(request, 'lms/turnitin/turnitin_report.html', {'submission': submission})

# -------------------------------------------------------------------
# Progress & Grades Views
# -------------------------------------------------------------------

@learner_required
def my_progress(request):
    """View overall progress"""
    enrollments = request.user.enrollments.filter(status='active').select_related('course')
    
    for enrollment in enrollments:
        enrollment.progress_percent = enrollment.get_progress_percent()
    
    context = {'enrollments': enrollments}
    return render(request, 'lms/student/my_progress.html', context)

@learner_required
def course_progress(request, course_slug):
    """View progress for a specific course"""
    course = get_object_or_404(Course, slug=course_slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    chapters = course.chapters.all().order_by('order')
    completed_chapters = enrollment.progress.get('completed_chapters', [])
    
    for chapter in chapters:
        chapter.is_completed = str(chapter.id) in completed_chapters
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'chapters': chapters,
    }
    return render(request, 'lms/student/course_progress.html', context)

@learner_required
def my_grades(request):
    """View all grades"""
    submissions = Submission.objects.filter(
        student=request.user,
        status='graded',
        grade__isnull=False
    ).select_related('assignment', 'assignment__course')
    
    context = {'submissions': submissions}
    return render(request, 'lms/student/my_grades.html', context)

@learner_required
def course_grades(request, course_slug):
    """View grades for a specific course"""
    course = get_object_or_404(Course, slug=course_slug)
    submissions = Submission.objects.filter(
        student=request.user,
        assignment__course=course,
        status='graded',
        grade__isnull=False
    ).select_related('assignment')
    
    context = {
        'course': course,
        'submissions': submissions,
    }
    return render(request, 'lms/student/course_grades.html', context)

# -------------------------------------------------------------------
# Notification Views
# -------------------------------------------------------------------

@login_required
def notification_list(request):
    """List all notifications"""
    notifications = request.user.notifications.all()
    
    # Mark as read if requested
    if request.GET.get('mark_read'):
        notification_id = request.GET.get('notification_id')
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
            notification.mark_as_read()
        else:
            request.user.notifications.filter(is_read=False).update(is_read=True)
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'lms/notifications/notification_list.html', context)

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    request.user.notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
    messages.success(request, "All notifications marked as read.")
    return redirect('lms:notification_list')

# -------------------------------------------------------------------
# Search View
# -------------------------------------------------------------------

def search(request):
    """Global search"""
    query = request.GET.get('q', '')
    
    if not query:
        return render(request, 'lms/search.html', {'query': query, 'results': []})
    
    courses = Course.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        status='published', is_active=True
    )
    
    departments = Module.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        status='active'
    )
    
    users = User.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query),
        is_approved=True
    )[:10] if request.user.is_authenticated and request.user.role in ['admin', 'instructor'] else []
    
    context = {
        'query': query,
        'courses': courses,
        'modules': departments,
        'users': users,
    }
    return render(request, 'lms/search.html', context)

# -------------------------------------------------------------------
# API Endpoints (AJAX)
# -------------------------------------------------------------------

@login_required
def api_chapter_progress(request):
    """Get chapter progress for a course"""
    course_slug = request.GET.get('course_slug')
    course = get_object_or_404(Course, slug=course_slug)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    
    if not enrollment:
        return JsonResponse({'error': 'Not enrolled'}, status=403)
    
    return JsonResponse({'progress': enrollment.progress})

@login_required
def api_update_progress(request):
    """Update chapter progress via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    data = json.loads(request.body)
    chapter_id = data.get('chapter_id')
    completed = data.get('completed', False)
    
    chapter = get_object_or_404(Chapter, id=chapter_id)
    enrollment = Enrollment.objects.filter(student=request.user, course=chapter.course).first()
    
    if not enrollment:
        return JsonResponse({'error': 'Not enrolled'}, status=403)
    
    progress = enrollment.progress or {}
    completed_chapters = progress.get('completed_chapters', [])
    
    if completed and str(chapter_id) not in completed_chapters:
        completed_chapters.append(str(chapter_id))
    elif not completed and str(chapter_id) in completed_chapters:
        completed_chapters.remove(str(chapter_id))
    
    progress['completed_chapters'] = completed_chapters
    enrollment.progress = progress
    enrollment.save()
    
    return JsonResponse({'status': 'ok', 'progress_percent': enrollment.get_progress_percent()})

@login_required
def api_mark_notification_read(request):
    """Mark a notification as read via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    data = json.loads(request.body)
    notification_id = data.get('notification_id')
    
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    return JsonResponse({'status': 'ok'})

@login_required
def api_get_notifications(request):
    """Get unread notifications via AJAX"""
    notifications = request.user.notifications.filter(is_read=False).values('id', 'title', 'message', 'created_at')
    return JsonResponse({'notifications': list(notifications)})

# -------------------------------------------------------------------
# Help & Support Views
# -------------------------------------------------------------------

def help_center(request):
    """Help center landing page"""
    topics = [
        {'slug': 'getting-started', 'title': 'Getting Started', 'icon': '🚀'},
        {'slug': 'courses', 'title': 'Courses & Enrollment', 'icon': '📚'},
        {'slug': 'assignments', 'title': 'Assignments', 'icon': '📝'},
        {'slug': 'certificates', 'title': 'Certificates', 'icon': '🎓'},
        {'slug': 'technical', 'title': 'Technical Support', 'icon': '💻'},
    ]
    return render(request, 'lms/help/help_center.html', {'topics': topics})

def help_topic(request, topic):
    """Help topic detail"""
    return render(request, f'lms/help/{topic}.html', {'topic': topic})

@login_required
def create_support_ticket(request):
    """Create a support ticket"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # This would integrate with a ticketing system
        send_email_notification(
            f"Support Ticket: {subject}",
            f"From: {request.user.email}\n\n{message}",
            [settings.DEFAULT_FROM_EMAIL]
        )
        
        messages.success(request, "Support ticket created. We'll respond within 24 hours.")
        return redirect('lms:help_center')
    
    return render(request, 'lms/help/create_ticket.html')

# -------------------------------------------------------------------
# System Settings & Enterprise Features Dashboard
# -------------------------------------------------------------------

@login_required
@admin_required
def admin_system_settings(request):
    """System settings and enterprise features dashboard"""
    from django.urls import reverse
    
    # Organize all enterprise features by category
    features = {
        'ai_administration': {
            'title': 'AI Administration',
            'icon': '🤖',
            'description': 'Manage AI models, configuration, and performance',
            'items': [
                {
                    'name': 'AI Models',
                    'url': reverse('lms:ai_models'),
                    'description': 'Manage AI models and deployment',
                    'icon': '🧠'
                },
                {
                    'name': 'AI Configuration',
                    'url': reverse('lms:ai_config'),
                    'description': 'Configure prediction models and adaptation',
                    'icon': '⚙️'
                },
                {
                    'name': 'AI Performance',
                    'url': reverse('lms:ai_performance'),
                    'description': 'Monitor AI model performance metrics',
                    'icon': '📊'
                },
            ]
        },
        'blockchain': {
            'title': 'Blockchain & Credentials',
            'icon': '⛓️',
            'description': 'Manage smart contracts and credential registry',
            'items': [
                {
                    'name': 'Smart Contracts',
                    'url': reverse('lms:smart_contracts'),
                    'description': 'Deploy and manage blockchain contracts',
                    'icon': '📜'
                },
                {
                    'name': 'Contract Registry',
                    'url': reverse('lms:contract_registry'),
                    'description': 'View certificate and badge contracts',
                    'icon': '📋'
                },
            ]
        },
        'integrations': {
            'title': 'Integrations & API',
            'icon': '🔌',
            'description': 'Manage third-party integrations and webhooks',
            'items': [
                {
                    'name': 'API Management',
                    'url': reverse('lms:api_management'),
                    'description': 'Configure and manage APIs',
                    'icon': '🔑'
                },
                {
                    'name': 'Third-Party Services',
                    'url': reverse('lms:third_party_services'),
                    'description': 'Configure external integrations',
                    'icon': '🔗'
                },
                {
                    'name': 'Webhooks',
                    'url': reverse('lms:webhooks'),
                    'description': 'Manage webhook endpoints',
                    'icon': '🪝'
                },
            ]
        },
        'security': {
            'title': 'Security & Compliance',
            'icon': '🔒',
            'description': 'Manage authentication, encryption, and audit logs',
            'items': [
                {
                    'name': 'Authentication',
                    'url': reverse('lms:authentication'),
                    'description': 'Configure authentication methods',
                    'icon': '🔐'
                },
                {
                    'name': 'Encryption Keys',
                    'url': reverse('lms:encryption'),
                    'description': 'Manage encryption keys and certificates',
                    'icon': '🔑'
                },
                {
                    'name': 'Audit Trail',
                    'url': reverse('lms:audit_trail'),
                    'description': 'View system audit logs',
                    'icon': '📝'
                },
                {
                    'name': 'Compliance',
                    'url': reverse('lms:compliance'),
                    'description': 'Manage compliance policies',
                    'icon': '✅'
                },
            ]
        },
        'system_config': {
            'title': 'System Configuration',
            'icon': '⚙️',
            'description': 'Configure email, storage, themes, and plugins',
            'items': [
                {
                    'name': 'Email Configuration',
                    'url': reverse('lms:email_config'),
                    'description': 'Configure email settings',
                    'icon': '📧'
                },
                {
                    'name': 'Storage & Backup',
                    'url': reverse('lms:storage_backup'),
                    'description': 'Configure storage and backup',
                    'icon': '💾'
                },
                {
                    'name': 'Theme Customization',
                    'url': reverse('lms:theme'),
                    'description': 'Customize system theme',
                    'icon': '🎨'
                },
                {
                    'name': 'Plugins',
                    'url': reverse('lms:plugins'),
                    'description': 'Manage installed plugins',
                    'icon': '🧩'
                },
                {
                    'name': 'Licenses',
                    'url': reverse('lms:licenses'),
                    'description': 'Manage software licenses',
                    'icon': '📜'
                },
            ]
        },
        'analytics': {
            'title': 'Analytics & Reporting',
            'icon': '📊',
            'description': 'Configure business intelligence and reports',
            'items': [
                {
                    'name': 'BI Integration',
                    'url': reverse('lms:bi_integration'),
                    'description': 'Configure BI tools integration',
                    'icon': '💡'
                },
                {
                    'name': 'Report Scheduling',
                    'url': reverse('lms:report_scheduling'),
                    'description': 'Schedule automated reports',
                    'icon': '📅'
                },
                {
                    'name': 'System Health',
                    'url': reverse('lms:system_health'),
                    'description': 'Monitor system health metrics',
                    'icon': '❤️'
                },
            ]
        },
    }
    
    context = {
        'features': features,
        'unread_notifications': request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0
    }
    
    return render(request, 'lms/admin/system_settings.html', context)

# -------------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------------

def bad_request(request, exception=None):
    return render(request, 'lms/400.html', status=400)

def permission_denied(request, exception=None):
    return render(request, 'lms/403.html', status=403)

def page_not_found(request, exception=None):
    return render(request, 'lms/404.html', status=404)

def server_error(request):
    return render(request, 'lms/500.html', status=500)