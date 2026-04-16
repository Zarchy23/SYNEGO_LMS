
from django.utils import timezone
from datetime import timedelta


def app_info(request):
    """Global app information."""
    return {
        "APP_NAME": "Synego Training Institute",
    }


def sidebar_context(request):
    """
    Add role-specific sidebar data and navigation context to all templates.
    This is called by the context processor and provides:
    - role-specific navigation links
    - badge counts (notifications, pending submissions, etc.)
    - user role display information
    """
    context = {
        'sidebar_active_page': None,
        'user_role': None,
    }

    if not request.user.is_authenticated:
        return context

    # Set user role info
    role_display = {
        'learner': 'Learner',
        'instructor': 'Instructor',
        'module_head': 'Module Head',
        'approver': 'Approver',
        'admin': 'Administrator',
    }
    context['user_role'] = role_display.get(request.user.role, 'User')
    context['user_role_abbr'] = request.user.role.upper()[:3]

    # Unread notifications count (for all roles)
    try:
        from lms.models import Notification
        context['unread_notifications'] = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
    except Exception:
        context['unread_notifications'] = 0

    # Learner-specific counts
    if request.user.role == 'learner':
        try:
            from lms.models import Submission, Enrollment, EnrollmentRequest
            
            # Enrolled courses count
            context['active_courses'] = Enrollment.objects.filter(
                student=request.user, status='active'
            ).count()
            
            # Pending submissions (assignments due soon)
            context['pending_submissions'] = Submission.objects.filter(
                student=request.user, status='draft'
            ).count()
            
            # Pending enrollment requests
            context['pending_enrollments'] = EnrollmentRequest.objects.filter(
                student=request.user, status='pending'
            ).count()
        except Exception:
            pass

    # Instructor-specific counts
    elif request.user.role == 'instructor':
        try:
            from lms.models import Submission, Course
            
            # Get instructor's courses (from their department)
            instructor_courses = Course.objects.filter(
                department=request.user.module, is_active=True
            )
            
            # Pending submissions requiring grading
            context['pending_submissions'] = Submission.objects.filter(
                assignment__course__in=instructor_courses,
                status='submitted'
            ).count()
            
            # My courses count
            context['my_courses'] = instructor_courses.count()
        except Exception:
            pass

    # Module Head-specific counts
    elif request.user.role == 'module_head':
        try:
            from lms.models import EnrollmentRequest, Course, Enrollment, Submission
            
            # Pending enrollment requests for their department
            context['pending_requests'] = EnrollmentRequest.objects.filter(
                course__department=request.user.module,
                status='pending'
            ).count()
            
            # Module courses count
            context['dept_courses'] = Course.objects.filter(
                department=request.user.module, is_active=True
            ).count()
            
            # Module students count
            dept_students = Enrollment.objects.filter(
                course__department=request.user.module,
                status__in=['active', 'completed']
            ).values('student').distinct().count()
            context['dept_students'] = dept_students
            
            # Pending submissions in department
            context['pending_submissions'] = Submission.objects.filter(
                assignment__course__department=request.user.module,
                status='submitted'
            ).count()
        except Exception:
            pass

    # Approver-specific counts
    elif request.user.role == 'approver':
        try:
            from lms.models import EnrollmentRequest
            
            # All pending enrollment requests
            context['pending_requests'] = EnrollmentRequest.objects.filter(
                status='pending'
            ).count()
            
            # Viewed requests count
            context['approved_count'] = EnrollmentRequest.objects.filter(
                status='approved'
            ).count()
            
            context['rejected_count'] = EnrollmentRequest.objects.filter(
                status='rejected'
            ).count()
        except Exception:
            pass

    # Admin-specific counts
    elif request.user.role == 'admin' or request.user.is_superuser:
        try:
            from lms.models import User, Course, Module, EnrollmentRequest, Submission
            
            # System-wide counts
            context['total_users'] = User.objects.count()
            context['total_students'] = User.objects.filter(role='learner').count()
            context['total_instructors'] = User.objects.filter(role='instructor').count()
            context['total_courses'] = Course.objects.count()
            context['total_modules'] = Module.objects.count()
            
            # Pending approvals
            context['pending_requests'] = EnrollmentRequest.objects.filter(
                status='pending'
            ).count()
            
            # Pending submissions
            context['pending_submissions'] = Submission.objects.filter(
                status='submitted'
            ).count()
        except Exception:
            pass

    return context

