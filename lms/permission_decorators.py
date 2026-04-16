"""
Permission check decorators for Synego LMS
Provides granular access control for views
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect


def permission_required(perm_codename):
    """Decorator to check if user has a specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('lms:login')
            
            if not request.user.has_perm(f'lms.{perm_codename}'):
                raise PermissionDenied(f"Permission '{perm_codename}' required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def any_permission_required(*perm_codenames):
    """Decorator to check if user has ANY of the specified permissions"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('lms:login')
            
            for perm in perm_codenames:
                if request.user.has_perm(f'lms.{perm}'):
                    return view_func(request, *args, **kwargs)
            
            raise PermissionDenied(f"Need one of permissions: {perm_codenames}")
        return wrapper
    return decorator


def all_permissions_required(*perm_codenames):
    """Decorator to check if user has ALL specified permissions"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('lms:login')
            
            missing = []
            for perm in perm_codenames:
                if not request.user.has_perm(f'lms.{perm}'):
                    missing.append(perm)
            
            if missing:
                raise PermissionDenied(f"Missing permissions: {missing}")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def ai_feature_required(view_func):
    """Decorator for AI/ML feature access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        ai_perms = [
            'can_use_ai_assistant',
            'can_view_knowledge_state',
            'can_generate_personalized_content',
            'can_view_predictions',
        ]
        
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        has_ai_access = any(request.user.has_perm(f'lms.{perm}') for perm in ai_perms)
        if not has_ai_access:
            raise PermissionDenied("AI features are not available for your role")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def vr_ar_feature_required(view_func):
    """Decorator for VR/AR feature access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        vr_ar_perms = [
            'can_join_vr_session',
            'can_create_vr_session',
            'can_use_ar_simulation',
            'can_view_360_video',
        ]
        
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        has_vr_ar_access = any(request.user.has_perm(f'lms.{perm}') for perm in vr_ar_perms)
        if not has_vr_ar_access:
            raise PermissionDenied("VR/AR features are not available for your role")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def blockchain_feature_required(view_func):
    """Decorator for blockchain/NFT feature access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        blockchain_perms = [
            'can_view_certificate',
            'can_download_certificate',
            'can_issue_blockchain_certificate',
            'can_mint_badge_nft',
        ]
        
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        has_blockchain_access = any(request.user.has_perm(f'lms.{perm}') for perm in blockchain_perms)
        if not has_blockchain_access:
            raise PermissionDenied("Blockchain features are not available for your role")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def proctoring_required(view_func):
    """Decorator for proctoring features"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        if not request.user.has_perm('lms.can_enable_proctoring'):
            raise PermissionDenied("Proctoring features require instructor or admin access")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def analytics_required(view_func):
    """Decorator for analytics/reporting access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        analytics_perms = [
            'can_view_realtime_dashboard',
            'can_view_learning_analytics',
            'can_view_engagement_metrics',
        ]
        
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        has_analytics_access = any(request.user.has_perm(f'lms.{perm}') for perm in analytics_perms)
        if not has_analytics_access:
            raise PermissionDenied("Analytics access required")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def api_key_required(view_func):
    """Decorator for API endpoint access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        if not request.user.has_perm('lms.can_create_api_key'):
            raise PermissionDenied("API access requires appropriate permissions")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def audit_access_required(view_func):
    """Decorator for audit trail access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        if not request.user.has_perm('lms.can_view_audit_trail'):
            raise PermissionDenied("Audit access required")
        
        return view_func(request, *args, **kwargs)
    return wrapper


# Convenience decorators for common roles

def admin_required(view_func):
    """Decorator for admin access - checks for admin permissions"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        # Check if user is superuser or has admin permissions
        admin_perms = [
            'can_manage_users',
            'can_create_course',
            'can_manage_courses',
            'can_manage_permissions',
            'can_manage_system_settings',
        ]
        
        is_admin = request.user.is_superuser or any(
            request.user.has_perm(f'lms.{perm}') for perm in admin_perms
        )
        
        if not is_admin:
            raise PermissionDenied("Admin access required")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def instructor_required(view_func):
    """Decorator for instructor access - checks for instructor permissions"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        # Check if user is superuser or has instructor permissions
        instructor_perms = [
            'can_create_course',
            'can_edit_course',
            'can_create_assignment',
            'can_grade_submission',
            'can_enable_proctoring',
            'can_view_realtime_dashboard',
        ]
        
        is_instructor = request.user.is_superuser or any(
            request.user.has_perm(f'lms.{perm}') for perm in instructor_perms
        )
        
        if not is_instructor:
            raise PermissionDenied("Instructor access required")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def learner_required(view_func):
    """Decorator for learner access - checks for learner permissions"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        
        # All authenticated users are learners, check basic learner permissions
        learner_perms = [
            'can_submit_assignment',
            'can_view_course_materials',
            'can_join_discussion',
        ]
        
        # If user has any learner permission or is authenticated, allow access
        is_learner = request.user.is_superuser or request.user.has_perm('lms.can_view_course_materials')
        
        # If no specific permission, still allow authenticated users as learners
        if not is_learner and request.user.is_authenticated:
            is_learner = True
        
        if not is_learner:
            raise PermissionDenied("Learner access required")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def course_creator_required(view_func):
    """Decorator for course creation access"""
    return permission_required('can_create_course')(view_func)


def course_editor_required(view_func):
    """Decorator for course editing access"""
    return any_permission_required('can_edit_course', 'can_edit_module')(view_func)


def assessment_creator_required(view_func):
    """Decorator for assessment creation"""
    return any_permission_required(
        'can_create_quiz',
        'can_create_code_exercise',
        'can_create_group_assignment'
    )(view_func)


def grading_required(view_func):
    """Decorator for grading/evaluation access"""
    return any_permission_required(
        'can_grade_submission',
        'can_grade_code',
        'can_grade_group',
        'can_override_ai_scores'
    )(view_func)


def reporting_required(view_func):
    """Decorator for reporting/exporting access"""
    return any_permission_required(
        'can_create_custom_report',
        'can_export_reports',
        'can_export_predictions'
    )(view_func)


def integration_admin_required(view_func):
    """Decorator for integration configuration"""
    return any_permission_required(
        'can_configure_google_integration',
        'can_configure_turnitin',
        'can_configure_zoom',
        'can_configure_payment_gateway'
    )(view_func)
