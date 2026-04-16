# Synego LMS Enterprise Permissions System

## Overview

The Synego LMS implements a comprehensive, enterprise-grade permissions system with **275+ granular permissions** across **18 categories**, supporting complex organizational structures and compliance requirements.

## Permission Categories

| Category | # Permissions | Examples |
|----------|---------------|----------|
| **Course Management** | 20 | Create, edit, publish courses; manage modules; versioning |
| **AI & Machine Learning** | 24 | Knowledge tracing, adaptive content, predictions, essay scoring |
| **Blockchain & Certification** | 17 | Issue certificates, NFT badges, verifiable credentials |
| **VR/AR & Immersive** | 18 | VR sessions, AR simulations, 360° videos, device management |
| **Assessment & Proctoring** | 24 | Quizzes, code exercises, proctoring, group assignments |
| **Analytics & Reporting** | 17 | Dashboards, predictive insights, custom reports, BI integration |
| **Integration & APIs** | 19 | API keys, webhooks, Google, Turnitin, Zoom, LTI |
| **Security & Compliance** | 22 | User management, MFA, audit trail, GDPR, encryption |

---

## Role Hierarchy

```
Superuser (All Permissions)
  ├── Admin (275+ permissions)
  │   ├── Dept Head (200+ permissions)
  │   │   ├── Instructor (150+ permissions)
  │   │   │   └── Learner (40+ permissions)
  │   └── Approver (Limited permissions)
```

### Role Permissions Summary

#### 👤 Learner (40+ permissions)
- View and complete courses
- Take quizzes and submit assignments
- Use AI assistant
- Join VR sessions
- Download certificates and NFTs
- Request data export/deletion (GDPR)

#### 👨‍🏫 Instructor (150+ permissions)
- All learner permissions
- Create and manage courses
- Create quizzes and code exercises
- Grade submissions
- Generate AI questions
- Create VR sessions
- View analytics and create reports
- Issue certificates and NFTs

#### 🏢 Department Head (200+ permissions)
- All instructor permissions
- Manage department users
- Approve course quality
- Evaluate instructors
- View department reports
- Manage budgets and resources

#### ✅ Approver (Limited permissions)
- View enrollment requests
- Approve/reject enrollments
- View approval history
- Limited analytics

#### 🔐 Admin (275+ permissions)
- All dept head permissions
- System-wide user management
- Configure integrations (Google, Turnitin, Zoom)
- Deploy AI models
- Deploy smart contracts
- Manage API keys and webhooks
- Configure security policies
- Audit and compliance reporting

#### 👑 Superuser (All permissions)
- All admin permissions
- Django admin access
- Database schema management
- Deployment configuration
- SSL certificates

---

## Using Permissions in Code

### Method 1: View Decorators

```python
from lms.permission_decorators import (
    permission_required,
    any_permission_required,
    all_permissions_required,
    ai_feature_required,
    vr_ar_feature_required,
    analytics_required,
    proctoring_required,
)

# Single permission required
@permission_required('can_create_course')
def create_course_view(request):
    pass

# Any permission required
@any_permission_required('can_grade_submission', 'can_grade_code')
def grade_view(request):
    pass

# All permissions required
@all_permissions_required('can_create_course', 'can_publish_course')
def publish_course_view(request):
    pass

# Feature-specific decorators
@ai_feature_required
def ai_dashboard_view(request):
    pass

@vr_ar_feature_required
def vr_session_view(request):
    pass
```

### Method 2: Permission Checking in Views

```python
from lms.permission_utils import PermissionChecker

def some_view(request):
    # Check single permission
    if PermissionChecker.has_permission(request.user, 'can_create_course'):
        # Show course creation UI
        pass
    
    # Check any permission
    if PermissionChecker.has_any_permission(
        request.user,
        'can_grade_submission',
        'can_grade_code'
    ):
        # Show grading interface
        pass
    
    # Check all permissions
    if PermissionChecker.has_all_permissions(
        request.user,
        'can_create_course',
        'can_publish_course'
    ):
        # Show publish button
        pass
    
    # Convenience methods
    if PermissionChecker.can_grade(request.user):
        pass
    
    if PermissionChecker.can_view_analytics(request.user):
        pass
    
    if PermissionChecker.can_use_ai_features(request.user):
        pass
```

### Method 3: Template Checks

```html
{% load static %}

{% if perms.lms.can_create_course %}
  <a href="{% url 'lms:create_course' %}" class="btn btn-primary">
    Create Course
  </a>
{% endif %}

{% if perms.lms.can_grade_submission or perms.lms.can_grade_code %}
  <a href="{% url 'lms:grading_queue' %}" class="btn btn-secondary">
    View Grading Queue
  </a>
{% endif %}

{% if perms.lms.can_view_realtime_dashboard %}
  <a href="{% url 'lms:analytics' %}" class="btn btn-info">
    Analytics
  </a>
{% endif %}
```

### Method 4: Programmatic Permission Assignment

```python
from django.contrib.auth.models import Group, Permission
from lms.role_permissions import RolePermissionAssignment

# Get a group
instructor_group = Group.objects.get(name='Instructor')

# Get all permissions for a role
role_perms = RolePermissionAssignment.get_role_permissions('instructor')

# Add permissions to user
user.groups.add(instructor_group)
user.save()  # User now has all instructor permissions

# Check permissions
user.has_perm('lms.can_create_course')  # True
```

---

## Setting Up Permissions

### Initial Setup

```bash
# Setup permissions and role groups
python manage.py setup_permissions

# Reset and setup (deletes existing)
python manage.py setup_permissions --reset
```

This command will:
- Create 275+ permission objects
- Create 6 role groups (learner, instructor, dept_head, approver, admin, superuser)
- Assign permissions to each group

### Manual Permission Assignment

```python
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from lms.models import User

# Create a custom role
custom_group, created = Group.objects.get_or_create(name='Custom Role')

# Add specific permissions
content_type = ContentType.objects.get_for_model(User)
perm = Permission.objects.get(
    codename='can_create_course',
    content_type=content_type
)
custom_group.permissions.add(perm)

# Assign user to group
user.groups.add(custom_group)
user.save()
```

---

## Advanced Features

### Permission Caching

Permissions are cached for performance:

```python
from lms.permission_utils import PermissionCache

# Get cached permissions for user
perms = PermissionCache.get_user_permissions(request.user)

# Clear cache when permissions change
PermissionCache.clear_user_permissions(user)
```

### Permission Requirements Context

```python
from lms.permission_utils import PermissionRequirement

# Check multiple permissions with context
req = PermissionRequirement(
    user,
    'can_create_course',
    'can_publish_course',
    require_all=True
)

if req.check():
    # User has all required permissions
    pass
```

### Getting Missing Permissions

```python
from lms.permission_utils import PermissionChecker

missing = PermissionChecker.get_missing_permissions(
    user,
    'can_create_course',
    'can_publish_course',
    'can_delete_course'
)

print(f"User missing: {missing}")
```

---

## Compliance & Security

### GDPR Support
- `can_request_data_export` - Students can request their data
- `can_request_account_deletion` - Students can request account deletion
- `can_anonymize_data` - Admins can anonymize user data

### Audit & Compliance
- `can_view_audit_trail` - Track all user actions
- `can_export_audit_logs` - Export audit records
- `can_view_compliance_reports` - GDPR/HIPAA compliance reports
- `can_configure_retention` - Data retention policies

### Security Management
- `can_enforce_mfa` - Require multi-factor authentication
- `can_configure_security_policies` - Set security rules
- `can_manage_encryption_keys` - Manage data encryption
- `can_configure_ip_whitelist` - Whitelist IP addresses

---

## Best Practices

### 1. Use Specific Permissions
```python
# ✅ Good - Precise permission check
@permission_required('can_grade_submission')
def grade_view(request):
    pass

# ❌ Avoid - Too general
@admin_required
def grade_view(request):
    pass
```

### 2. Leverage Role Inheritance
```python
# ✅ Instructor inherits learner permissions
# User can both create courses AND take quizzes
```

### 3. Cache Permission Results
```python
# ✅ Use cached permissions in loops
for user in users:
    if PermissionChecker.can_grade(user):  # Cached lookup
        # Grade user submissions
        pass
```

### 4. Document Custom Permissions
```python
# When adding custom permissions, document their purpose
CAN_CUSTOM_FEATURE = 'can_custom_feature'  # Used for X, Y, Z
```

### 5. Test Permission Logic
```python
def test_permission_required():
    user = User.objects.create_user(username='test')
    assert not PermissionChecker.can_grade(user)
    
    # Add permission
    group = Group.objects.get(name='Instructor')
    user.groups.add(group)
    
    assert PermissionChecker.can_grade(user)
```

---

## Troubleshooting

### Permissions Not Showing

```bash
# Clear permission cache
python manage.py clear_cache

# Check if groups exist
python manage.py shell
>>> from django.contrib.auth.models import Group
>>> Group.objects.all()

# Recreate permissions if needed
python manage.py setup_permissions --reset
```

### User Can't Perform Action

```python
# Debug permission check
from lms.permission_utils import PermissionChecker

user = User.objects.get(username='john')
missing = PermissionChecker.get_missing_permissions(
    user,
    'can_create_course'
)

print(f"Missing permissions: {missing}")
print(f"User groups: {user.groups.all()}")
print(f"User permissions: {user.get_all_permissions()}")
```

---

## Summary

The Synego Enterprise Permissions System provides:

✅ **275+ granular permissions** across enterprise features  
✅ **6 role levels** with inheritance support  
✅ **Multiple checking methods** (decorators, utils, templates)  
✅ **Caching** for performance optimization  
✅ **GDPR & compliance** support  
✅ **Audit trails** for security  
✅ **Easy setup** with management command  
✅ **Flexible** for custom needs  

For questions or custom implementations, refer to the permission constants in `lms/permissions_enterprise.py`.
