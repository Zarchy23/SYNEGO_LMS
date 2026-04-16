"""
Permission checking utilities for Synego LMS
Helper functions for permission verification in views and templates
"""

from django.contrib.auth.models import Permission
from django.core.cache import cache


class PermissionCache:
    """Cache for permission lookups"""
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_user_permissions(user):
        """Get all user permissions (cached)"""
        if not user.is_authenticated:
            return set()
        
        cache_key = f'user_permissions_{user.id}'
        perms = cache.get(cache_key)
        
        if perms is None:
            perms = set(user.get_all_permissions())
            cache.set(cache_key, perms, PermissionCache.CACHE_TIMEOUT)
        
        return perms
    
    @staticmethod
    def clear_user_permissions(user):
        """Clear cached permissions for user"""
        cache_key = f'user_permissions_{user.id}'
        cache.delete(cache_key)
    
    @staticmethod
    def get_role_permissions(role):
        """Get permissions for a role (cached)"""
        cache_key = f'role_permissions_{role}'
        perms = cache.get(cache_key)
        
        if perms is None:
            from lms.role_permissions import RolePermissionAssignment
            perms = set(RolePermissionAssignment.get_role_permissions(role))
            cache.set(cache_key, perms, PermissionCache.CACHE_TIMEOUT)
        
        return perms


class PermissionChecker:
    """Utility class for permission checks"""
    
    @staticmethod
    def has_permission(user, perm_codename):
        """Check if user has a specific permission"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        return user.has_perm(f'lms.{perm_codename}')
    
    @staticmethod
    def has_any_permission(user, *perm_codenames):
        """Check if user has ANY of the permissions"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        return any(user.has_perm(f'lms.{perm}') for perm in perm_codenames)
    
    @staticmethod
    def has_all_permissions(user, *perm_codenames):
        """Check if user has ALL permissions"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        return all(user.has_perm(f'lms.{perm}') for perm in perm_codenames)
    
    @staticmethod
    def can_create_course(user):
        """Check if user can create courses"""
        return PermissionChecker.has_permission(user, 'can_create_course')
    
    @staticmethod
    def can_manage_users(user):
        """Check if user can manage users"""
        return PermissionChecker.has_permission(user, 'can_manage_users')
    
    @staticmethod
    def can_grade(user):
        """Check if user can grade submissions"""
        return PermissionChecker.has_any_permission(
            user,
            'can_grade_submission',
            'can_grade_code',
            'can_grade_group'
        )
    
    @staticmethod
    def can_view_analytics(user):
        """Check if user can view analytics"""
        return PermissionChecker.has_any_permission(
            user,
            'can_view_realtime_dashboard',
            'can_view_learning_analytics',
            'can_view_engagement_metrics'
        )
    
    @staticmethod
    def can_use_ai_features(user):
        """Check if user can use AI features"""
        return PermissionChecker.has_any_permission(
            user,
            'can_use_ai_assistant',
            'can_view_knowledge_state',
            'can_generate_personalized_content'
        )
    
    @staticmethod
    def can_use_vr_ar(user):
        """Check if user can use VR/AR features"""
        return PermissionChecker.has_any_permission(
            user,
            'can_join_vr_session',
            'can_create_vr_session',
            'can_use_ar_simulation'
        )
    
    @staticmethod
    def can_access_blockchain(user):
        """Check if user can access blockchain features"""
        return PermissionChecker.has_any_permission(
            user,
            'can_view_certificate',
            'can_issue_blockchain_certificate',
            'can_mint_badge_nft'
        )
    
    @staticmethod
    def get_missing_permissions(user, *perm_codenames):
        """Return list of permissions user is missing"""
        if user.is_superuser:
            return []
        
        missing = []
        for perm in perm_codenames:
            if not user.has_perm(f'lms.{perm}'):
                missing.append(perm)
        
        return missing


class PermissionRequirement:
    """Context manager for permission requirements"""
    
    def __init__(self, user, *perm_codenames, require_all=False):
        self.user = user
        self.perm_codenames = perm_codenames
        self.require_all = require_all
    
    def check(self):
        """Check if requirement is met"""
        if self.require_all:
            return PermissionChecker.has_all_permissions(self.user, *self.perm_codenames)
        else:
            return PermissionChecker.has_any_permission(self.user, *self.perm_codenames)


def get_role_description(role):
    """Get human-readable description of a role"""
    descriptions = {
        'learner': 'Student - Can access courses, take quizzes, submit assignments',
        'instructor': 'Instructor - Can create courses, grade submissions, create assessments',
        'dept_head': 'Department Head - Can manage department, approve course quality, view reports',
        'approver': 'Approver - Can approve student enrollment requests',
        'admin': 'Administrator - Can manage system, users, integrations, and analytics',
        'superuser': 'Superuser - Full system access including Django admin',
    }
    return descriptions.get(role, 'Unknown Role')


def get_permission_description(perm_codename):
    """Get human-readable description of a permission"""
    descriptions = {
        'can_create_course': 'Create new courses',
        'can_edit_course': 'Edit course details',
        'can_delete_course': 'Delete courses',
        'can_publish_course': 'Publish/unpublish courses',
        'can_create_quiz': 'Create quizzes',
        'can_create_code_exercise': 'Create coding exercises',
        'can_grade_submission': 'Grade student submissions',
        'can_view_analytics': 'View analytics dashboards',
        'can_use_ai_assistant': 'Use AI teaching assistant',
        'can_access_blockchain': 'Access blockchain certificates',
        'can_manage_users': 'Manage user accounts',
        'can_configure_security': 'Configure security policies',
    }
    return descriptions.get(perm_codename, perm_codename.replace('_', ' ').title())


# Module-level convenience functions
def has_permission(user, perm_codename):
    """Module-level wrapper for checking user permission"""
    return PermissionChecker.has_permission(user, perm_codename)
