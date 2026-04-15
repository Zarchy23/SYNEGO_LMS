"""Role-based permission utilities and decorators for Synego LMS."""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

try:
    from rest_framework import permissions
except Exception:  # pragma: no cover - fallback when DRF isn't installed
    class _BasePermission:
        def has_permission(self, request, view):
            return False

        def has_object_permission(self, request, view, obj):
            return False

    class _PermissionsModule:
        BasePermission = _BasePermission

    permissions = _PermissionsModule()


def require_roles(user, allowed_roles):
    """Raise PermissionDenied if user is not authenticated or not in allowed roles."""
    if not user.is_authenticated or user.role not in allowed_roles:
        raise PermissionDenied("You do not have permission to perform this action.")


# ============================================================================
# FUNCTION-BASED VIEW DECORATORS (for traditional Django views)
# ============================================================================

def learner_required(view_func):
    """Restrict access to learners only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        if request.user.role != 'learner':
            raise PermissionDenied("Learner access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def instructor_required(view_func):
    """Restrict access to instructors, department heads, and admins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        if request.user.role not in ['instructor', 'dept_head', 'admin'] and not request.user.is_superuser:
            raise PermissionDenied("Instructor access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def dept_head_required(view_func):
    """Restrict access to department heads and admins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        if request.user.role not in ['dept_head', 'admin'] and not request.user.is_superuser:
            raise PermissionDenied("Department head access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def approver_required(view_func):
    """Restrict access to approvers, department heads, and admins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        if request.user.role not in ['approver', 'dept_head', 'admin'] and not request.user.is_superuser:
            raise PermissionDenied("Approval access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Restrict access to admins only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('lms:login')
        if request.user.role != 'admin' and not request.user.is_superuser:
            raise PermissionDenied("Admin access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================================================
# DRF PERMISSION CLASSES (for REST API views)
# ============================================================================

class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == "admin"


class IsInstructor(permissions.BasePermission):
    """Allow access only to instructors, department heads, and admins."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["instructor", "dept_head", "admin"]

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "admin":
            return True

        if request.user.role == "dept_head":
            if hasattr(obj, "course") and hasattr(obj.course, "department"):
                return obj.course.department == request.user.department
            if hasattr(obj, "department"):
                return obj.department == request.user.department

        if request.user.role == "instructor":
            if hasattr(obj, "course"):
                return obj.course.department == request.user.department
            if hasattr(obj, "assignment") and hasattr(obj.assignment, "course"):
                return obj.assignment.course.department == request.user.department

        return False


class IsLearner(permissions.BasePermission):
    """Allow access only to approved learners."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "learner"
            and request.user.is_approved
        )

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if hasattr(obj, "student") and obj.student == request.user:
            return True
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        return request.user.role == "learner" and request.user.is_approved


class IsApprover(permissions.BasePermission):
    """Allow access to users who can approve enrollments."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["admin", "approver", "dept_head"]

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "admin":
            return True

        if request.user.role == "dept_head":
            if hasattr(obj, "course") and hasattr(obj.course, "department"):
                return obj.course.department == request.user.department

        return request.user.role == "approver"


class CanAccessCourse(permissions.BasePermission):
    """Check if user can access course content."""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "admin":
            return True

        if hasattr(obj, "is_free_preview") and obj.is_free_preview:
            return True

        if request.user.role in ["instructor", "dept_head"]:
            if hasattr(obj, "course"):
                return obj.course.department == request.user.department

        if request.user.role == "learner" and request.user.is_approved:
            from lms.models import Enrollment

            if hasattr(obj, "course"):
                return Enrollment.objects.filter(
                    student=request.user, course=obj.course, status="active"
                ).exists()

        return False


class CanGradeSubmission(permissions.BasePermission):
    """Check if user can grade a submission."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "instructor",
            "dept_head",
            "admin",
        ]

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "admin":
            return True

        if request.user.role == "dept_head":
            if hasattr(obj, "assignment") and hasattr(obj.assignment, "course"):
                return obj.assignment.course.department == request.user.department

        if request.user.role == "instructor":
            if hasattr(obj, "assignment") and hasattr(obj.assignment, "course"):
                return obj.assignment.course.department == request.user.department

        return False


class CanEditCourse(permissions.BasePermission):
    """Check if user can edit course content."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "instructor",
            "dept_head",
            "admin",
        ]

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "admin":
            return True

        if request.user.role == "dept_head":
            if hasattr(obj, "department"):
                return obj.department == request.user.department
            if hasattr(obj, "course") and hasattr(obj.course, "department"):
                return obj.course.department == request.user.department

        if request.user.role == "instructor":
            if hasattr(obj, "course"):
                return obj.course.department == request.user.department
            if hasattr(obj, "department"):
                return obj.department == request.user.department

        return False


class IsOwner(permissions.BasePermission):
    """Check if user is the owner of the object."""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if hasattr(obj, "student"):
            return obj.student == request.user

        if hasattr(obj, "user"):
            return obj.user == request.user

        return False


class CanViewReport(permissions.BasePermission):
    """Check if user can view reports."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "admin",
            "dept_head",
            "instructor",
        ]

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "admin":
            return True

        if request.user.role == "dept_head":
            if hasattr(obj, "department"):
                return obj.department == request.user.department
            if hasattr(obj, "course") and hasattr(obj.course, "department"):
                return obj.course.department == request.user.department

        if request.user.role == "instructor":
            if hasattr(obj, "course"):
                return obj.course.department == request.user.department

        return False
