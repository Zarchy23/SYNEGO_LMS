"""
Role-based permission assignments for Synego LMS
Maps permissions to roles with inheritance
"""

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


class RolePermissionAssignment:
    """Map permissions to roles with inheritance"""
    
    # Learner-only permissions
    LEARNER_PERMISSIONS = [
        # Course access
        ContentPermissions.CAN_VIEW_COURSE,
        ContentPermissions.CAN_VIEW_MODULE,
        ContentPermissions.CAN_VIEW_LESSON,
        ContentPermissions.CAN_COMPLETE_LESSON,
        ContentPermissions.CAN_VIEW_LEARNING_PATH,
        
        # Assessment (student-facing)
        StudentAssessmentPermissions.CAN_TAKE_QUIZ,
        StudentAssessmentPermissions.CAN_SUBMIT_ASSIGNMENT,
        StudentAssessmentPermissions.CAN_VIEW_QUIZ_RESULTS,
        StudentAssessmentPermissions.CAN_VIEW_OWN_GRADES,
        StudentAssessmentPermissions.CAN_RETAKE_QUIZ,
        
        # AI Features (read-only)
        AIPermissions.CAN_USE_AI_ASSISTANT,
        AIPermissions.CAN_VIEW_KNOWLEDGE_STATE,
        AIPermissions.CAN_VIEW_PREDICTIONS,
        
        # VR/AR
        VRARPermissions.CAN_JOIN_VR_SESSION,
        VRARPermissions.CAN_USE_AR_SIMULATION,
        VRARPermissions.CAN_VIEW_360_VIDEO,
        
        # Collaboration
        DiscussionPermissions.CAN_PARTICIPATE_DISCUSSION,
        CollaborationPermissions.CAN_JOIN_STUDY_GROUP,
        CollaborationPermissions.CAN_REQUEST_PEER_REVIEW,
        
        # Blockchain (viewer)
        BlockchainPermissions.CAN_VERIFY_CERTIFICATE,
        BlockchainPermissions.CAN_DOWNLOAD_CERTIFICATE,
        BlockchainPermissions.CAN_SHARE_CERTIFICATE,
        BlockchainPermissions.CAN_VIEW_NFT_GALLERY,
        BlockchainPermissions.CAN_CONNECT_WALLET,
        
        # Security
        SecurityPermissions.CAN_REQUEST_DATA_EXPORT,
        SecurityPermissions.CAN_REQUEST_ACCOUNT_DELETION,
        
        # Mobile & Offline
        MobileOfflinePermissions.CAN_USE_MOBILE_APP,
        MobileOfflinePermissions.CAN_DOWNLOAD_OFFLINE_CONTENT,
    ]
    
    # Instructor-only permissions (+ all learner permissions)
    INSTRUCTOR_PERMISSIONS = LEARNER_PERMISSIONS + [
        # Course Management
        CoursePermissions.CAN_CREATE_COURSE,
        CoursePermissions.CAN_EDIT_COURSE,
        CoursePermissions.CAN_CREATE_MODULE,
        CoursePermissions.CAN_EDIT_MODULE,
        CoursePermissions.CAN_REORDER_CONTENT,
        CoursePermissions.CAN_CREATE_LEARNING_PATH,
        CoursePermissions.CAN_PUBLISH_COURSE,
        
        # Content Creation
        ContentPermissions.CAN_CREATE_LESSON,
        ContentPermissions.CAN_EDIT_LESSON,
        ContentPermissions.CAN_UPLOAD_VIDEO,
        ContentPermissions.CAN_UPLOAD_DOCUMENT,
        
        # Assessment
        AssessmentPermissions.CAN_CREATE_QUIZ,
        AssessmentPermissions.CAN_EDIT_QUIZ,
        AssessmentPermissions.CAN_CREATE_CODE_EXERCISE,
        AssessmentPermissions.CAN_VIEW_QUIZ_ANALYTICS,
        AssessmentPermissions.CAN_GRADE_CODE,
        
        # AI Features
        AIPermissions.CAN_GENERATE_QUESTIONS,
        AIPermissions.CAN_APPROVE_GENERATED_QUESTIONS,
        AIPermissions.CAN_VIEW_PREDICTIONS,
        AIPermissions.CAN_CONFIGURE_ADAPTATION,
        AIPermissions.CAN_OVERRIDE_AI_SCORES,
        
        # VR/AR
        VRARPermissions.CAN_CREATE_VR_SESSION,
        VRARPermissions.CAN_MODERATE_VR_SESSION,
        VRARPermissions.CAN_UPLOAD_VR_CONTENT,
        VRARPermissions.CAN_ADD_VIDEO_HOTSPOTS,
        VRARPermissions.CAN_CREATE_AR_SIMULATION,
        
        # Analytics
        AnalyticsPermissions.CAN_VIEW_REALTIME_DASHBOARD,
        AnalyticsPermissions.CAN_VIEW_ENGAGEMENT_METRICS,
        AnalyticsPermissions.CAN_VIEW_COMPLETION_ANALYTICS,
        AnalyticsPermissions.CAN_CREATE_CUSTOM_REPORT,
        
        # Collaboration
        ContentPermissions.CAN_CREATE_ANNOUNCEMENT,
        DiscussionPermissions.CAN_MODERATE_DISCUSSIONS,
        CollaborationPermissions.CAN_CREATE_STUDY_GROUP,
        
        # Proctoring
        AssessmentPermissions.CAN_ENABLE_PROCTORING,
        AssessmentPermissions.CAN_VIEW_PROCTORING_REPORTS,
        
        # Blockchain
        BlockchainPermissions.CAN_ISSUE_BLOCKCHAIN_CERTIFICATE,
        BlockchainPermissions.CAN_MINT_BADGE_NFT,
        
        # Integrations
        IntegrationPermissions.CAN_UPLOAD_SCORM,
        IntegrationPermissions.CAN_LAUNCH_LTI,
        
        # Grading & Submission
        GradingPermissions.CAN_VIEW_SUBMISSIONS,
        GradingPermissions.CAN_GRADE_SUBMISSION,
        GradingPermissions.CAN_RETURN_FOR_REVISION,
    ]
    
    # Module Head permissions (+ all instructor permissions)
    MODULE_HEAD_PERMISSIONS = INSTRUCTOR_PERMISSIONS + [
        # Module Management
        DepartmentManagementPermissions.CAN_MANAGE_DEPARTMENT_USERS,
        DepartmentManagementPermissions.CAN_ASSIGN_INSTRUCTORS,
        DepartmentManagementPermissions.CAN_VIEW_DEPARTMENT_ANALYTICS,
        CoursePermissions.CAN_APPROVE_COURSE_QUALITY,
        DepartmentManagementPermissions.CAN_VIEW_DEPARTMENT_REPORTS,
        AnalyticsPermissions.CAN_COMPARE_COHORTS,
        
        # Budget/Resource Management
        DepartmentManagementPermissions.CAN_VIEW_DEPARTMENT_BUDGET,
        DepartmentManagementPermissions.CAN_REQUEST_RESOURCES,
        DepartmentManagementPermissions.CAN_APPROVE_RESOURCE_REQUESTS,
        
        # Staff Management
        DepartmentManagementPermissions.CAN_EVALUATE_INSTRUCTORS,
        DepartmentManagementPermissions.CAN_VIEW_INSTRUCTOR_PERFORMANCE,
        DepartmentManagementPermissions.CAN_SCHEDULE_MEETINGS,
    ]
    
    # Approver permissions (limited to enrollment)
    APPROVER_PERMISSIONS = [
        # Enrollment Management
        ApprovalWorkflowPermissions.CAN_VIEW_ENROLLMENT_REQUESTS,
        ApprovalWorkflowPermissions.CAN_APPROVE_ENROLLMENT,
        ApprovalWorkflowPermissions.CAN_REJECT_ENROLLMENT,
        ApprovalWorkflowPermissions.CAN_VIEW_PENDING_REQUESTS,
        ApprovalWorkflowPermissions.CAN_ADD_APPROVAL_NOTES,
        ApprovalWorkflowPermissions.CAN_VIEW_STUDENT_BASIC_INFO,
        
        # Limited Analytics
        ApprovalWorkflowPermissions.CAN_VIEW_ENROLLMENT_ANALYTICS,
        ApprovalWorkflowPermissions.CAN_VIEW_APPROVAL_HISTORY,
    ]
    
    # Admin permissions (+ all module_head permissions)
    ADMIN_PERMISSIONS = MODULE_HEAD_PERMISSIONS + [
        # System Management
        SystemAdminPermissions.CAN_MANAGE_SYSTEM_SETTINGS,
        SystemAdminPermissions.CAN_CONFIGURE_EMAIL,
        SystemAdminPermissions.CAN_CONFIGURE_STORAGE,
        SystemAdminPermissions.CAN_VIEW_SYSTEM_HEALTH,
        SystemAdminPermissions.CAN_MANAGE_BACKUP,
        SystemAdminPermissions.CAN_RESTORE_BACKUP,
        
        # User Management (full)
        SecurityPermissions.CAN_MANAGE_USERS,
        SecurityPermissions.CAN_ASSIGN_ROLES,
        SecurityPermissions.CAN_RESET_PASSWORDS,
        SecurityPermissions.CAN_IMPERSONATE_USER,
        SecurityPermissions.CAN_LOCK_ACCOUNTS,
        SecurityPermissions.CAN_ENFORCE_MFA,
        
        # Security
        SecurityPermissions.CAN_CONFIGURE_SECURITY_POLICIES,
        SecurityPermissions.CAN_CONFIGURE_IP_WHITELIST,
        SecurityPermissions.CAN_VIEW_SECURITY_ALERTS,
        SecurityPermissions.CAN_MANAGE_ENCRYPTION_KEYS,
        SecurityPermissions.CAN_CONFIGURE_RETENTION,
        
        # AI Model Management
        AIPermissions.CAN_MANAGE_AI_MODELS,
        AIPermissions.CAN_DEPLOY_MODELS,
        AIPermissions.CAN_MONITOR_MODEL_PERFORMANCE,
        AIPermissions.CAN_TRAIN_MODELS,
        
        # Blockchain
        BlockchainPermissions.CAN_DEPLOY_CONTRACT,
        BlockchainPermissions.CAN_UPGRADE_CONTRACT,
        BlockchainPermissions.CAN_VIEW_CONTRACT_STATE,
        
        # Integration Management
        IntegrationPermissions.CAN_CREATE_API_KEY,
        IntegrationPermissions.CAN_CONFIGURE_RATE_LIMITS,
        IntegrationPermissions.CAN_CONFIGURE_GOOGLE_INTEGRATION,
        IntegrationPermissions.CAN_CONFIGURE_TURNITIN,
        IntegrationPermissions.CAN_CONFIGURE_ZOOM,
        IntegrationPermissions.CAN_CONFIGURE_PAYMENT_GATEWAY,
        IntegrationPermissions.CAN_CREATE_WEBHOOK,
        
        # Reporting
        SecurityPermissions.CAN_VIEW_AUDIT_TRAIL,
        SecurityPermissions.CAN_EXPORT_AUDIT_LOGS,
        SecurityPermissions.CAN_VIEW_COMPLIANCE_REPORTS,
        AnalyticsPermissions.CAN_SCHEDULE_REPORTS,
        AnalyticsPermissions.CAN_EXPORT_REPORTS,
        
        # System Configuration
        SystemAdminPermissions.CAN_CONFIGURE_AUTHENTICATION,
        SystemAdminPermissions.CAN_CONFIGURE_NOTIFICATIONS,
        SystemAdminPermissions.CAN_CONFIGURE_THEME,
        SystemAdminPermissions.CAN_MANAGE_PLUGINS,
        SystemAdminPermissions.CAN_MANAGE_LICENSES,
        
        # Analytics (full)
        AnalyticsPermissions.CAN_CONNECT_BI_TOOL,
        AnalyticsPermissions.CAN_CREATE_BI_DATASET,
        AIPermissions.CAN_CONFIGURE_PREDICTION_MODELS,
    ]
    
    # Superuser permissions (all admin + django admin)
    SUPERUSER_PERMISSIONS = ADMIN_PERMISSIONS + [
        SuperuserOnlyPermissions.CAN_ACCESS_DJANGO_ADMIN,
        SuperuserOnlyPermissions.CAN_MANAGE_SUPERUSERS,
        SuperuserOnlyPermissions.CAN_MODIFY_SYSTEM_CODE,
        SuperuserOnlyPermissions.CAN_ACCESS_SERVER_SHELL,
        SuperuserOnlyPermissions.CAN_MANAGE_DATABASE_SCHEMA,
        SuperuserOnlyPermissions.CAN_CONFIGURE_DEPLOYMENT,
        SuperuserOnlyPermissions.CAN_MANAGE_SSL_CERTIFICATES,
        SuperuserOnlyPermissions.CAN_CONFIGURE_LOAD_BALANCING,
    ]
    
    # Role-to-permissions mapping
    ROLE_PERMISSIONS = {
        'learner': LEARNER_PERMISSIONS,
        'instructor': INSTRUCTOR_PERMISSIONS,
        'module_head': MODULE_HEAD_PERMISSIONS,
        'approver': APPROVER_PERMISSIONS,
        'admin': ADMIN_PERMISSIONS,
        'superuser': SUPERUSER_PERMISSIONS,
    }
    
    @staticmethod
    def get_role_permissions(role):
        """Get all permissions for a role"""
        return RolePermissionAssignment.ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def get_all_permissions():
        """Get all unique permissions across all roles"""
        all_perms = set()
        for role_perms in RolePermissionAssignment.ROLE_PERMISSIONS.values():
            all_perms.update(role_perms)
        return list(all_perms)
