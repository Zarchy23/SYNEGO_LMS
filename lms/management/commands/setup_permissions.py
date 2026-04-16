"""
Management command to setup enterprise permissions
Run: python manage.py setup_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from lms.models import User
from lms.permissions_enterprise import (
    CoursePermissions,
    AIPermissions,
    BlockchainPermissions,
    VRARPermissions,
    AssessmentPermissions,
    AnalyticsPermissions,
    IntegrationPermissions,
    SecurityPermissions,
    ContentPermissions,
    DiscussionPermissions,
    CollaborationPermissions,
    GradingPermissions,
    DepartmentManagementPermissions,
    ApprovalWorkflowPermissions,
    SystemAdminPermissions,
    MobileOfflinePermissions,
    StudentAssessmentPermissions,
    SuperuserOnlyPermissions,
)
from lms.role_permissions import RolePermissionAssignment


class Command(BaseCommand):
    help = 'Setup enterprise permissions and role groups for Synego LMS'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all permissions and groups before setting up',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setting up enterprise permissions system...'))
        
        content_type = ContentType.objects.get_for_model(User)
        
        # Reset if requested
        if options['reset']:
            self.stdout.write(self.style.WARNING('🔄 Resetting existing permissions and groups...'))
            Permission.objects.filter(content_type=content_type).delete()
            Group.objects.all().delete()
        
        # Create permission groups
        self.stdout.write('📝 Creating permission groups...')
        groups = {
            'learner': Group.objects.get_or_create(name='Learner')[0],
            'instructor': Group.objects.get_or_create(name='Instructor')[0],
            'dept_head': Group.objects.get_or_create(name='Department Head')[0],
            'approver': Group.objects.get_or_create(name='Approver')[0],
            'admin': Group.objects.get_or_create(name='Admin')[0],
            'superuser': Group.objects.get_or_create(name='Superuser')[0],
        }
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(groups)} groups'))
        
        # Collect all permissions
        all_permissions = {
            'Course Management': CoursePermissions.ALL_COURSE_PERMISSIONS,
            'Content': ContentPermissions.ALL_CONTENT_PERMISSIONS,
            'AI & ML': AIPermissions.ALL_AI_PERMISSIONS,
            'Blockchain': BlockchainPermissions.ALL_BLOCKCHAIN_PERMISSIONS,
            'VR/AR': VRARPermissions.ALL_VRAR_PERMISSIONS,
            'Assessment': AssessmentPermissions.ALL_ASSESSMENT_PERMISSIONS,
            'Student Assessment': StudentAssessmentPermissions.ALL_STUDENT_ASSESSMENT_PERMISSIONS,
            'Grading': GradingPermissions.ALL_GRADING_PERMISSIONS,
            'Discussion': DiscussionPermissions.ALL_DISCUSSION_PERMISSIONS,
            'Collaboration': CollaborationPermissions.ALL_COLLABORATION_PERMISSIONS,
            'Analytics': AnalyticsPermissions.ALL_ANALYTICS_PERMISSIONS,
            'Integration': IntegrationPermissions.ALL_INTEGRATION_PERMISSIONS,
            'Department Management': DepartmentManagementPermissions.ALL_DEPT_PERMISSIONS,
            'Approval Workflow': ApprovalWorkflowPermissions.ALL_APPROVAL_PERMISSIONS,
            'System Admin': SystemAdminPermissions.ALL_SYSTEM_ADMIN_PERMISSIONS,
            'Security': SecurityPermissions.ALL_SECURITY_PERMISSIONS,
            'Mobile & Offline': MobileOfflinePermissions.ALL_MOBILE_OFFLINE_PERMISSIONS,
            'Superuser Only': SuperuserOnlyPermissions.ALL_SUPERUSER_ONLY_PERMISSIONS,
        }
        
        created_permissions = {}
        total_perms = 0
        
        # Create all permissions
        for category, perms in all_permissions.items():
            self.stdout.write(f'\n📌 {category}:')
            cat_count = 0
            for perm_codename in perms:
                perm, created = Permission.objects.get_or_create(
                    codename=perm_codename,
                    content_type=content_type,
                    defaults={
                        'name': perm_codename.replace('_', ' ').replace('can ', 'Can ').title()
                    }
                )
                if created:
                    cat_count += 1
                    total_perms += 1
            
            if cat_count > 0:
                self.stdout.write(f'   ✅ Created {cat_count} permissions')
            else:
                self.stdout.write(f'   ℹ️  Already exists')
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Total permissions created: {total_perms}'))
        
        # Assign permissions to groups
        self.stdout.write('\n🔐 Assigning permissions to groups...\n')
        
        for role, group in groups.items():
            role_perms = RolePermissionAssignment.ROLE_PERMISSIONS.get(role, [])
            assigned = 0
            
            for perm_codename in role_perms:
                try:
                    perm = Permission.objects.get(codename=perm_codename)
                    group.permissions.add(perm)
                    assigned += 1
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Permission not found: {perm_codename} (for {role})')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ {role.upper():<15} → {assigned} permissions assigned')
            )
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Enterprise permissions system setup complete!'))
        self.stdout.write(self.style.SUCCESS(f'📈 Total permissions: {Permission.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'👥 Total groups: {Group.objects.count()}'))
