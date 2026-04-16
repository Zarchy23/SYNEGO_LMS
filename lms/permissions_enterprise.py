"""
Enterprise-grade permissions system for Synego LMS
Covers 275+ permissions across 18 categories
"""

from enum import Enum


class PermissionCategory(Enum):
    """Enterprise permission categories"""
    COURSE = "course"
    CONTENT = "content"
    ASSESSMENT = "assessment"
    ANALYTICS = "analytics"
    AI = "ai"
    BLOCKCHAIN = "blockchain"
    VR_AR = "vr_ar"
    COLLABORATION = "collaboration"
    SECURITY = "security"
    INTEGRATION = "integration"
    REPORTING = "reporting"
    AUTOMATION = "automation"
    PROCTORING = "proctoring"
    CERTIFICATION = "certification"
    MOBILE = "mobile"
    OFFLINE = "offline"
    API = "api"
    SYSTEM = "system"


class CoursePermissions:
    """Enterprise course management permissions"""
    
    # Course Creation & Management
    CAN_CREATE_COURSE = 'can_create_course'
    CAN_EDIT_COURSE = 'can_edit_course'
    CAN_DELETE_COURSE = 'can_delete_course'
    CAN_PUBLISH_COURSE = 'can_publish_course'
    CAN_DUPLICATE_COURSE = 'can_duplicate_course'
    CAN_ARCHIVE_COURSE = 'can_archive_course'
    
    # Course Hierarchy
    CAN_CREATE_MODULE = 'can_create_module'
    CAN_EDIT_MODULE = 'can_edit_module'
    CAN_DELETE_MODULE = 'can_delete_module'
    CAN_REORDER_CONTENT = 'can_reorder_content'
    
    # Learning Paths
    CAN_CREATE_LEARNING_PATH = 'can_create_learning_path'
    CAN_ASSIGN_LEARNING_PATH = 'can_assign_learning_path'
    CAN_EDIT_LEARNING_PATH = 'can_edit_learning_path'
    
    # Course Quality
    CAN_REVIEW_COURSE_QUALITY = 'can_review_course_quality'
    CAN_APPROVE_COURSE_QUALITY = 'can_approve_course_quality'
    CAN_REQUEST_COURSE_REVIEW = 'can_request_course_review'
    
    # Course Versioning
    CAN_VIEW_COURSE_VERSIONS = 'can_view_course_versions'
    CAN_ROLLBACK_COURSE = 'can_rollback_course'
    CAN_CREATE_COURSE_DRAFT = 'can_create_course_draft'
    CAN_PUBLISH_DRAFT = 'can_publish_draft'
    
    ALL_COURSE_PERMISSIONS = [
        CAN_CREATE_COURSE, CAN_EDIT_COURSE, CAN_DELETE_COURSE,
        CAN_PUBLISH_COURSE, CAN_DUPLICATE_COURSE, CAN_ARCHIVE_COURSE,
        CAN_CREATE_MODULE, CAN_EDIT_MODULE, CAN_DELETE_MODULE,
        CAN_REORDER_CONTENT, CAN_CREATE_LEARNING_PATH,
        CAN_ASSIGN_LEARNING_PATH, CAN_EDIT_LEARNING_PATH,
        CAN_REVIEW_COURSE_QUALITY, CAN_APPROVE_COURSE_QUALITY,
        CAN_REQUEST_COURSE_REVIEW, CAN_VIEW_COURSE_VERSIONS,
        CAN_ROLLBACK_COURSE, CAN_CREATE_COURSE_DRAFT, CAN_PUBLISH_DRAFT,
    ]


class AIPermissions:
    """AI-powered learning permissions"""
    
    # Neural Knowledge Tracing
    CAN_VIEW_KNOWLEDGE_STATE = 'can_view_knowledge_state'
    CAN_ANALYZE_KNOWLEDGE_GAPS = 'can_analyze_knowledge_gaps'
    CAN_RESET_KNOWLEDGE_STATE = 'can_reset_knowledge_state'
    
    # Adaptive Content Generation
    CAN_GENERATE_PERSONALIZED_CONTENT = 'can_generate_personalized_content'
    CAN_CONFIGURE_ADAPTATION = 'can_configure_adaptation'
    CAN_OVERRIDE_AI_RECOMMENDATIONS = 'can_override_ai_recommendations'
    
    # Predictive Analytics
    CAN_VIEW_PREDICTIONS = 'can_view_predictions'
    CAN_EXPORT_PREDICTIONS = 'can_export_predictions'
    CAN_CONFIGURE_PREDICTION_MODELS = 'can_configure_prediction_models'
    CAN_TRAIN_MODELS = 'can_train_models'
    
    # Automated Interventions
    CAN_CREATE_AUTO_INTERVENTION = 'can_create_auto_intervention'
    CAN_SEND_AUTO_MESSAGES = 'can_send_auto_messages'
    CAN_CONFIGURE_INTERVENTION_RULES = 'can_configure_intervention_rules'
    
    # AI Teaching Assistant
    CAN_USE_AI_ASSISTANT = 'can_use_ai_assistant'
    CAN_TRAIN_AI_ASSISTANT = 'can_train_ai_assistant'
    CAN_EXPORT_AI_CONVERSATIONS = 'can_export_ai_conversations'
    
    # AI Essay Scoring
    CAN_VIEW_AI_ESSAY_SCORES = 'can_view_ai_essay_scores'
    CAN_OVERRIDE_AI_SCORES = 'can_override_ai_scores'
    CAN_CONFIGURE_SCORING_RUBRIC = 'can_configure_scoring_rubric'
    
    # AI Question Generation
    CAN_GENERATE_QUESTIONS = 'can_generate_questions'
    CAN_APPROVE_GENERATED_QUESTIONS = 'can_approve_generated_questions'
    
    # Model Management
    CAN_MANAGE_AI_MODELS = 'can_manage_ai_models'
    CAN_DEPLOY_MODELS = 'can_deploy_models'
    CAN_MONITOR_MODEL_PERFORMANCE = 'can_monitor_model_performance'
    
    ALL_AI_PERMISSIONS = [
        CAN_VIEW_KNOWLEDGE_STATE, CAN_ANALYZE_KNOWLEDGE_GAPS,
        CAN_RESET_KNOWLEDGE_STATE, CAN_GENERATE_PERSONALIZED_CONTENT,
        CAN_CONFIGURE_ADAPTATION, CAN_OVERRIDE_AI_RECOMMENDATIONS,
        CAN_VIEW_PREDICTIONS, CAN_EXPORT_PREDICTIONS,
        CAN_CONFIGURE_PREDICTION_MODELS, CAN_TRAIN_MODELS,
        CAN_CREATE_AUTO_INTERVENTION, CAN_SEND_AUTO_MESSAGES,
        CAN_CONFIGURE_INTERVENTION_RULES, CAN_USE_AI_ASSISTANT,
        CAN_TRAIN_AI_ASSISTANT, CAN_EXPORT_AI_CONVERSATIONS,
        CAN_VIEW_AI_ESSAY_SCORES, CAN_OVERRIDE_AI_SCORES,
        CAN_CONFIGURE_SCORING_RUBRIC, CAN_GENERATE_QUESTIONS,
        CAN_APPROVE_GENERATED_QUESTIONS, CAN_MANAGE_AI_MODELS,
        CAN_DEPLOY_MODELS, CAN_MONITOR_MODEL_PERFORMANCE,
    ]


class BlockchainPermissions:
    """Blockchain credential permissions"""
    
    # Certificate Management
    CAN_ISSUE_BLOCKCHAIN_CERTIFICATE = 'can_issue_blockchain_certificate'
    CAN_REVOKE_CERTIFICATE = 'can_revoke_certificate'
    CAN_VERIFY_CERTIFICATE = 'can_verify_certificate'
    CAN_DOWNLOAD_CERTIFICATE = 'can_download_certificate'
    CAN_SHARE_CERTIFICATE = 'can_share_certificate'
    
    # NFT Badges
    CAN_MINT_BADGE_NFT = 'can_mint_badge_nft'
    CAN_TRANSFER_NFT = 'can_transfer_nft'
    CAN_VIEW_NFT_GALLERY = 'can_view_nft_gallery'
    
    # Verifiable Credentials
    CAN_ISSUE_VERIFIABLE_CREDENTIAL = 'can_issue_verifiable_credential'
    CAN_VERIFY_CREDENTIAL = 'can_verify_credential'
    CAN_REVOKE_CREDENTIAL = 'can_revoke_credential'
    
    # Smart Contract Management
    CAN_DEPLOY_CONTRACT = 'can_deploy_contract'
    CAN_UPGRADE_CONTRACT = 'can_upgrade_contract'
    CAN_VIEW_CONTRACT_STATE = 'can_view_contract_state'
    
    # Wallet Management
    CAN_CONNECT_WALLET = 'can_connect_wallet'
    CAN_VIEW_TRANSACTIONS = 'can_view_transactions'
    CAN_EXPORT_WALLET = 'can_export_wallet'
    
    ALL_BLOCKCHAIN_PERMISSIONS = [
        CAN_ISSUE_BLOCKCHAIN_CERTIFICATE, CAN_REVOKE_CERTIFICATE,
        CAN_VERIFY_CERTIFICATE, CAN_DOWNLOAD_CERTIFICATE,
        CAN_SHARE_CERTIFICATE, CAN_MINT_BADGE_NFT, CAN_TRANSFER_NFT,
        CAN_VIEW_NFT_GALLERY, CAN_ISSUE_VERIFIABLE_CREDENTIAL,
        CAN_VERIFY_CREDENTIAL, CAN_REVOKE_CREDENTIAL,
        CAN_DEPLOY_CONTRACT, CAN_UPGRADE_CONTRACT,
        CAN_VIEW_CONTRACT_STATE, CAN_CONNECT_WALLET,
        CAN_VIEW_TRANSACTIONS, CAN_EXPORT_WALLET,
    ]


class VRARPermissions:
    """Virtual and Augmented Reality permissions"""
    
    # VR Sessions
    CAN_CREATE_VR_SESSION = 'can_create_vr_session'
    CAN_JOIN_VR_SESSION = 'can_join_vr_session'
    CAN_MODERATE_VR_SESSION = 'can_moderate_vr_session'
    CAN_RECORD_VR_SESSION = 'can_record_vr_session'
    
    # VR Content Management
    CAN_UPLOAD_VR_CONTENT = 'can_upload_vr_content'
    CAN_EDIT_VR_SCENE = 'can_edit_vr_scene'
    CAN_DELETE_VR_CONTENT = 'can_delete_vr_content'
    
    # VR Analytics
    CAN_VIEW_VR_TELEMETRY = 'can_view_vr_telemetry'
    CAN_EXPORT_VR_HEATMAP = 'can_export_vr_heatmap'
    CAN_ANALYZE_VR_PERFORMANCE = 'can_analyze_vr_performance'
    
    # AR Simulations
    CAN_CREATE_AR_SIMULATION = 'can_create_ar_simulation'
    CAN_USE_AR_SIMULATION = 'can_use_ar_simulation'
    CAN_DESIGN_AR_MARKERS = 'can_design_ar_markers'
    
    # 360° Video
    CAN_UPLOAD_360_VIDEO = 'can_upload_360_video'
    CAN_ADD_VIDEO_HOTSPOTS = 'can_add_video_hotspots'
    CAN_VIEW_360_VIDEO = 'can_view_360_video'
    
    # Hardware Management
    CAN_REGISTER_VR_DEVICE = 'can_register_vr_device'
    CAN_VIEW_DEVICE_HEALTH = 'can_view_device_health'
    
    ALL_VRAR_PERMISSIONS = [
        CAN_CREATE_VR_SESSION, CAN_JOIN_VR_SESSION,
        CAN_MODERATE_VR_SESSION, CAN_RECORD_VR_SESSION,
        CAN_UPLOAD_VR_CONTENT, CAN_EDIT_VR_SCENE,
        CAN_DELETE_VR_CONTENT, CAN_VIEW_VR_TELEMETRY,
        CAN_EXPORT_VR_HEATMAP, CAN_ANALYZE_VR_PERFORMANCE,
        CAN_CREATE_AR_SIMULATION, CAN_USE_AR_SIMULATION,
        CAN_DESIGN_AR_MARKERS, CAN_UPLOAD_360_VIDEO,
        CAN_ADD_VIDEO_HOTSPOTS, CAN_VIEW_360_VIDEO,
        CAN_REGISTER_VR_DEVICE, CAN_VIEW_DEVICE_HEALTH,
    ]


class AssessmentPermissions:
    """Advanced assessment and proctoring permissions"""
    
    # Quiz Management
    CAN_CREATE_QUIZ = 'can_create_quiz'
    CAN_EDIT_QUIZ = 'can_edit_quiz'
    CAN_DELETE_QUIZ = 'can_delete_quiz'
    CAN_SET_ADAPTIVE_QUIZ = 'can_set_adaptive_quiz'
    CAN_VIEW_QUIZ_ANALYTICS = 'can_view_quiz_analytics'
    
    # Advanced Question Types
    CAN_CREATE_MATCHING_QUESTIONS = 'can_create_matching_questions'
    CAN_CREATE_ORDERING_QUESTIONS = 'can_create_ordering_questions'
    CAN_CREATE_CODE_QUESTIONS = 'can_create_code_questions'
    CAN_CREATE_HOTSPOT_QUESTIONS = 'can_create_hotspot_questions'
    
    # Code Exercises
    CAN_CREATE_CODE_EXERCISE = 'can_create_code_exercise'
    CAN_EXECUTE_CODE = 'can_execute_code'
    CAN_VIEW_CODE_SUBMISSIONS = 'can_view_code_submissions'
    CAN_GRADE_CODE = 'can_grade_code'
    CAN_COLLABORATE_CODE = 'can_collaborate_code'
    
    # Proctoring
    CAN_ENABLE_PROCTORING = 'can_enable_proctoring'
    CAN_VIEW_PROCTORING_REPORTS = 'can_view_proctoring_reports'
    CAN_REVIEW_PROCTORING_FLAGS = 'can_review_proctoring_flags'
    CAN_OVERRIDE_PROCTORING = 'can_override_proctoring'
    CAN_CONFIGURE_PROCTORING = 'can_configure_proctoring'
    
    # Essay Scoring
    CAN_VIEW_AI_ESSAY_FEEDBACK = 'can_view_ai_essay_feedback'
    CAN_OVERRIDE_ESSAY_SCORE = 'can_override_essay_score'
    CAN_CONFIGURE_ESSAY_RUBRIC = 'can_configure_essay_rubric'
    
    # Group Assignments
    CAN_CREATE_GROUP_ASSIGNMENT = 'can_create_group_assignment'
    CAN_MANAGE_GROUPS = 'can_manage_groups'
    CAN_GRADE_GROUP = 'can_grade_group'
    
    ALL_ASSESSMENT_PERMISSIONS = [
        CAN_CREATE_QUIZ, CAN_EDIT_QUIZ, CAN_DELETE_QUIZ,
        CAN_SET_ADAPTIVE_QUIZ, CAN_VIEW_QUIZ_ANALYTICS,
        CAN_CREATE_MATCHING_QUESTIONS, CAN_CREATE_ORDERING_QUESTIONS,
        CAN_CREATE_CODE_QUESTIONS, CAN_CREATE_HOTSPOT_QUESTIONS,
        CAN_CREATE_CODE_EXERCISE, CAN_EXECUTE_CODE,
        CAN_VIEW_CODE_SUBMISSIONS, CAN_GRADE_CODE,
        CAN_COLLABORATE_CODE, CAN_ENABLE_PROCTORING,
        CAN_VIEW_PROCTORING_REPORTS, CAN_REVIEW_PROCTORING_FLAGS,
        CAN_OVERRIDE_PROCTORING, CAN_CONFIGURE_PROCTORING,
        CAN_VIEW_AI_ESSAY_FEEDBACK, CAN_OVERRIDE_ESSAY_SCORE,
        CAN_CONFIGURE_ESSAY_RUBRIC, CAN_CREATE_GROUP_ASSIGNMENT,
        CAN_MANAGE_GROUPS, CAN_GRADE_GROUP,
    ]


class AnalyticsPermissions:
    """Advanced analytics and BI permissions"""
    
    # Real-time Analytics
    CAN_VIEW_REALTIME_DASHBOARD = 'can_view_realtime_dashboard'
    CAN_EXPORT_REALTIME_DATA = 'can_export_realtime_data'
    CAN_CREATE_CUSTOM_WIDGET = 'can_create_custom_widget'
    
    # Predictive Analytics
    CAN_VIEW_PREDICTIVE_INSIGHTS = 'can_view_predictive_insights'
    CAN_CONFIGURE_PREDICTION_THRESHOLDS = 'can_configure_prediction_thresholds'
    
    # Custom Reports
    CAN_CREATE_CUSTOM_REPORT = 'can_create_custom_report'
    CAN_SCHEDULE_REPORTS = 'can_schedule_reports'
    CAN_SHARE_REPORTS = 'can_share_reports'
    CAN_EXPORT_REPORTS = 'can_export_reports'
    CAN_VIEW_AUDIT_REPORTS = 'can_view_audit_reports'
    
    # BI Integration
    CAN_CONNECT_BI_TOOL = 'can_connect_bi_tool'
    CAN_CREATE_BI_DATASET = 'can_create_bi_dataset'
    CAN_SCHEDULE_BI_REFRESH = 'can_schedule_bi_refresh'
    
    # Learning Analytics
    CAN_VIEW_LEARNING_ANALYTICS = 'can_view_learning_analytics'
    CAN_VIEW_ENGAGEMENT_METRICS = 'can_view_engagement_metrics'
    CAN_VIEW_COMPLETION_ANALYTICS = 'can_view_completion_analytics'
    CAN_COMPARE_COHORTS = 'can_compare_cohorts'
    
    ALL_ANALYTICS_PERMISSIONS = [
        CAN_VIEW_REALTIME_DASHBOARD, CAN_EXPORT_REALTIME_DATA,
        CAN_CREATE_CUSTOM_WIDGET, CAN_VIEW_PREDICTIVE_INSIGHTS,
        CAN_CONFIGURE_PREDICTION_THRESHOLDS, CAN_CREATE_CUSTOM_REPORT,
        CAN_SCHEDULE_REPORTS, CAN_SHARE_REPORTS, CAN_EXPORT_REPORTS,
        CAN_VIEW_AUDIT_REPORTS, CAN_CONNECT_BI_TOOL,
        CAN_CREATE_BI_DATASET, CAN_SCHEDULE_BI_REFRESH,
        CAN_VIEW_LEARNING_ANALYTICS, CAN_VIEW_ENGAGEMENT_METRICS,
        CAN_VIEW_COMPLETION_ANALYTICS, CAN_COMPARE_COHORTS,
    ]


class IntegrationPermissions:
    """Integration and API permissions"""
    
    # API Management
    CAN_CREATE_API_KEY = 'can_create_api_key'
    CAN_REVOKE_API_KEY = 'can_revoke_api_key'
    CAN_VIEW_API_LOGS = 'can_view_api_logs'
    CAN_CONFIGURE_RATE_LIMITS = 'can_configure_rate_limits'
    CAN_MANAGE_API_ENDPOINTS = 'can_manage_api_endpoints'
    
    # Webhooks
    CAN_CREATE_WEBHOOK = 'can_create_webhook'
    CAN_TEST_WEBHOOK = 'can_test_webhook'
    CAN_VIEW_WEBHOOK_LOGS = 'can_view_webhook_logs'
    
    # Third-party Integrations
    CAN_CONFIGURE_GOOGLE_INTEGRATION = 'can_configure_google_integration'
    CAN_CONFIGURE_TURNITIN = 'can_configure_turnitin'
    CAN_CONFIGURE_ZOOM = 'can_configure_zoom'
    CAN_CONFIGURE_PAYMENT_GATEWAY = 'can_configure_payment_gateway'
    CAN_CONFIGURE_HRMS = 'can_configure_hrms'
    
    # SCORM/xAPI
    CAN_UPLOAD_SCORM = 'can_upload_scorm'
    CAN_VIEW_XAPI_STATEMENTS = 'can_view_xapi_statements'
    CAN_EXPORT_XAPI = 'can_export_xapi'
    
    # LTI Integration
    CAN_CONFIGURE_LTI = 'can_configure_lti'
    CAN_LAUNCH_LTI = 'can_launch_lti'
    
    ALL_INTEGRATION_PERMISSIONS = [
        CAN_CREATE_API_KEY, CAN_REVOKE_API_KEY, CAN_VIEW_API_LOGS,
        CAN_CONFIGURE_RATE_LIMITS, CAN_MANAGE_API_ENDPOINTS,
        CAN_CREATE_WEBHOOK, CAN_TEST_WEBHOOK, CAN_VIEW_WEBHOOK_LOGS,
        CAN_CONFIGURE_GOOGLE_INTEGRATION, CAN_CONFIGURE_TURNITIN,
        CAN_CONFIGURE_ZOOM, CAN_CONFIGURE_PAYMENT_GATEWAY,
        CAN_CONFIGURE_HRMS, CAN_UPLOAD_SCORM, CAN_VIEW_XAPI_STATEMENTS,
        CAN_EXPORT_XAPI, CAN_CONFIGURE_LTI, CAN_LAUNCH_LTI,
    ]


class SecurityPermissions:
    """Security and compliance permissions"""
    
    # User Management
    CAN_MANAGE_USERS = 'can_manage_users'
    CAN_ASSIGN_ROLES = 'can_assign_roles'
    CAN_RESET_PASSWORDS = 'can_reset_passwords'
    CAN_IMPERSONATE_USER = 'can_impersonate_user'
    CAN_LOCK_ACCOUNTS = 'can_lock_accounts'
    
    # MFA/2FA
    CAN_ENFORCE_MFA = 'can_enforce_mfa'
    CAN_CONFIGURE_MFA = 'can_configure_mfa'
    CAN_BYPASS_MFA = 'can_bypass_mfa'
    
    # Audit & Compliance
    CAN_VIEW_AUDIT_TRAIL = 'can_view_audit_trail'
    CAN_EXPORT_AUDIT_LOGS = 'can_export_audit_logs'
    CAN_VIEW_COMPLIANCE_REPORTS = 'can_view_compliance_reports'
    CAN_CONFIGURE_RETENTION = 'can_configure_retention'
    
    # Data Privacy (GDPR)
    CAN_REQUEST_DATA_EXPORT = 'can_request_data_export'
    CAN_REQUEST_ACCOUNT_DELETION = 'can_request_account_deletion'
    CAN_ANONYMIZE_DATA = 'can_anonymize_data'
    CAN_MANAGE_CONSENT = 'can_manage_consent'
    
    # Security Policies
    CAN_CONFIGURE_SECURITY_POLICIES = 'can_configure_security_policies'
    CAN_VIEW_SECURITY_ALERTS = 'can_view_security_alerts'
    CAN_ACKNOWLEDGE_ALERTS = 'can_acknowledge_alerts'
    CAN_CONFIGURE_IP_WHITELIST = 'can_configure_ip_whitelist'
    
    # Encryption
    CAN_MANAGE_ENCRYPTION_KEYS = 'can_manage_encryption_keys'
    CAN_VIEW_ENCRYPTION_STATUS = 'can_view_encryption_status'
    
    ALL_SECURITY_PERMISSIONS = [
        CAN_MANAGE_USERS, CAN_ASSIGN_ROLES, CAN_RESET_PASSWORDS,
        CAN_IMPERSONATE_USER, CAN_LOCK_ACCOUNTS, CAN_ENFORCE_MFA,
        CAN_CONFIGURE_MFA, CAN_BYPASS_MFA, CAN_VIEW_AUDIT_TRAIL,
        CAN_EXPORT_AUDIT_LOGS, CAN_VIEW_COMPLIANCE_REPORTS,
        CAN_CONFIGURE_RETENTION, CAN_REQUEST_DATA_EXPORT,
        CAN_REQUEST_ACCOUNT_DELETION, CAN_ANONYMIZE_DATA,
        CAN_MANAGE_CONSENT, CAN_CONFIGURE_SECURITY_POLICIES,
        CAN_VIEW_SECURITY_ALERTS, CAN_ACKNOWLEDGE_ALERTS,
        CAN_CONFIGURE_IP_WHITELIST, CAN_MANAGE_ENCRYPTION_KEYS,
        CAN_VIEW_ENCRYPTION_STATUS,
    ]


class ContentPermissions:
    """Basic course content viewing and creation permissions"""
    
    # Course Viewing
    CAN_VIEW_COURSE = 'can_view_course'
    CAN_VIEW_MODULE = 'can_view_module'
    CAN_VIEW_LESSON = 'can_view_lesson'
    CAN_COMPLETE_LESSON = 'can_complete_lesson'
    CAN_VIEW_LEARNING_PATH = 'can_view_learning_path'
    
    # Content Creation
    CAN_CREATE_LESSON = 'can_create_lesson'
    CAN_EDIT_LESSON = 'can_edit_lesson'
    CAN_DELETE_LESSON = 'can_delete_lesson'
    CAN_UPLOAD_VIDEO = 'can_upload_video'
    CAN_UPLOAD_DOCUMENT = 'can_upload_document'
    CAN_UPLOAD_IMAGE = 'can_upload_image'
    CAN_EMBED_CONTENT = 'can_embed_content'
    CAN_CREATE_ANNOUNCEMENT = 'can_create_announcement'
    
    # Content Organization
    CAN_ORGANIZE_CONTENT = 'can_organize_content'
    CAN_ACCESS_CONTENT_LIBRARY = 'can_access_content_library'
    
    ALL_CONTENT_PERMISSIONS = [
        CAN_VIEW_COURSE, CAN_VIEW_MODULE, CAN_VIEW_LESSON,
        CAN_COMPLETE_LESSON, CAN_VIEW_LEARNING_PATH,
        CAN_CREATE_LESSON, CAN_EDIT_LESSON, CAN_DELETE_LESSON,
        CAN_UPLOAD_VIDEO, CAN_UPLOAD_DOCUMENT, CAN_UPLOAD_IMAGE,
        CAN_EMBED_CONTENT, CAN_CREATE_ANNOUNCEMENT,
        CAN_ORGANIZE_CONTENT, CAN_ACCESS_CONTENT_LIBRARY,
    ]


class DiscussionPermissions:
    """Discussion forum and collaboration permissions"""
    
    CAN_PARTICIPATE_DISCUSSION = 'can_participate_discussion'
    CAN_CREATE_DISCUSSION = 'can_create_discussion'
    CAN_MODERATE_DISCUSSIONS = 'can_moderate_discussions'
    CAN_DELETE_DISCUSSION_POST = 'can_delete_discussion_post'
    CAN_PIN_DISCUSSION = 'can_pin_discussion'
    CAN_LOCK_DISCUSSION = 'can_lock_discussion'
    CAN_VIEW_DISCUSSION_ANALYTICS = 'can_view_discussion_analytics'
    
    ALL_DISCUSSION_PERMISSIONS = [
        CAN_PARTICIPATE_DISCUSSION, CAN_CREATE_DISCUSSION,
        CAN_MODERATE_DISCUSSIONS, CAN_DELETE_DISCUSSION_POST,
        CAN_PIN_DISCUSSION, CAN_LOCK_DISCUSSION,
        CAN_VIEW_DISCUSSION_ANALYTICS,
    ]


class CollaborationPermissions:
    """Study groups and peer collaboration permissions"""
    
    CAN_CREATE_STUDY_GROUP = 'can_create_study_group'
    CAN_JOIN_STUDY_GROUP = 'can_join_study_group'
    CAN_LEAVE_STUDY_GROUP = 'can_leave_study_group'
    CAN_MANAGE_STUDY_GROUP = 'can_manage_study_group'
    CAN_REQUEST_PEER_REVIEW = 'can_request_peer_review'
    CAN_PROVIDE_PEER_REVIEW = 'can_provide_peer_review'
    CAN_VIEW_STUDY_GROUP_ANALYTICS = 'can_view_study_group_analytics'
    
    ALL_COLLABORATION_PERMISSIONS = [
        CAN_CREATE_STUDY_GROUP, CAN_JOIN_STUDY_GROUP,
        CAN_LEAVE_STUDY_GROUP, CAN_MANAGE_STUDY_GROUP,
        CAN_REQUEST_PEER_REVIEW, CAN_PROVIDE_PEER_REVIEW,
        CAN_VIEW_STUDY_GROUP_ANALYTICS,
    ]


class GradingPermissions:
    """Gradebook and assessment submission permissions"""
    
    CAN_VIEW_SUBMISSIONS = 'can_view_submissions'
    CAN_GRADE_SUBMISSION = 'can_grade_submission'
    CAN_RETURN_FOR_REVISION = 'can_return_for_revision'
    CAN_VIEW_GRADEBOOK = 'can_view_gradebook'
    CAN_EXPORT_GRADES = 'can_export_grades'
    CAN_BULK_GRADE = 'can_bulk_grade'
    CAN_ADJUST_GRADES = 'can_adjust_grades'
    CAN_VIEW_GRADE_STATISTICS = 'can_view_grade_statistics'
    
    ALL_GRADING_PERMISSIONS = [
        CAN_VIEW_SUBMISSIONS, CAN_GRADE_SUBMISSION,
        CAN_RETURN_FOR_REVISION, CAN_VIEW_GRADEBOOK,
        CAN_EXPORT_GRADES, CAN_BULK_GRADE,
        CAN_ADJUST_GRADES, CAN_VIEW_GRADE_STATISTICS,
    ]


class DepartmentManagementPermissions:
    """Department-level management permissions"""
    
    CAN_MANAGE_DEPARTMENT_USERS = 'can_manage_department_users'
    CAN_ASSIGN_INSTRUCTORS = 'can_assign_instructors'
    CAN_VIEW_DEPARTMENT_COURSES = 'can_view_department_courses'
    CAN_MANAGE_DEPARTMENT_COURSES = 'can_manage_department_courses'
    CAN_VIEW_DEPARTMENT_ANALYTICS = 'can_view_department_analytics'
    CAN_VIEW_DEPARTMENT_REPORTS = 'can_view_department_reports'
    CAN_VIEW_DEPARTMENT_BUDGET = 'can_view_department_budget'
    CAN_REQUEST_RESOURCES = 'can_request_resources'
    CAN_APPROVE_RESOURCE_REQUESTS = 'can_approve_resource_requests'
    CAN_EVALUATE_INSTRUCTORS = 'can_evaluate_instructors'
    CAN_VIEW_INSTRUCTOR_PERFORMANCE = 'can_view_instructor_performance'
    CAN_SCHEDULE_MEETINGS = 'can_schedule_meetings'
    CAN_MANAGE_DEPARTMENT_SETTINGS = 'can_manage_department_settings'
    
    ALL_DEPT_PERMISSIONS = [
        CAN_MANAGE_DEPARTMENT_USERS, CAN_ASSIGN_INSTRUCTORS,
        CAN_VIEW_DEPARTMENT_COURSES, CAN_MANAGE_DEPARTMENT_COURSES,
        CAN_VIEW_DEPARTMENT_ANALYTICS, CAN_VIEW_DEPARTMENT_REPORTS,
        CAN_VIEW_DEPARTMENT_BUDGET, CAN_REQUEST_RESOURCES,
        CAN_APPROVE_RESOURCE_REQUESTS, CAN_EVALUATE_INSTRUCTORS,
        CAN_VIEW_INSTRUCTOR_PERFORMANCE, CAN_SCHEDULE_MEETINGS,
        CAN_MANAGE_DEPARTMENT_SETTINGS,
    ]


class ApprovalWorkflowPermissions:
    """Enrollment and request approval permissions"""
    
    CAN_VIEW_ENROLLMENT_REQUESTS = 'can_view_enrollment_requests'
    CAN_APPROVE_ENROLLMENT = 'can_approve_enrollment'
    CAN_REJECT_ENROLLMENT = 'can_reject_enrollment'
    CAN_VIEW_PENDING_REQUESTS = 'can_view_pending_requests'
    CAN_ADD_APPROVAL_NOTES = 'can_add_approval_notes'
    CAN_VIEW_STUDENT_BASIC_INFO = 'can_view_student_basic_info'
    CAN_VIEW_ENROLLMENT_ANALYTICS = 'can_view_enrollment_analytics'
    CAN_VIEW_APPROVAL_HISTORY = 'can_view_approval_history'
    
    ALL_APPROVAL_PERMISSIONS = [
        CAN_VIEW_ENROLLMENT_REQUESTS, CAN_APPROVE_ENROLLMENT,
        CAN_REJECT_ENROLLMENT, CAN_VIEW_PENDING_REQUESTS,
        CAN_ADD_APPROVAL_NOTES, CAN_VIEW_STUDENT_BASIC_INFO,
        CAN_VIEW_ENROLLMENT_ANALYTICS, CAN_VIEW_APPROVAL_HISTORY,
    ]


class SystemAdminPermissions:
    """System-level administration and configuration permissions"""
    
    CAN_MANAGE_SYSTEM_SETTINGS = 'can_manage_system_settings'
    CAN_CONFIGURE_EMAIL = 'can_configure_email'
    CAN_CONFIGURE_STORAGE = 'can_configure_storage'
    CAN_VIEW_SYSTEM_HEALTH = 'can_view_system_health'
    CAN_MANAGE_BACKUP = 'can_manage_backup'
    CAN_RESTORE_BACKUP = 'can_restore_backup'
    CAN_CONFIGURE_AUTHENTICATION = 'can_configure_authentication'
    CAN_CONFIGURE_NOTIFICATIONS = 'can_configure_notifications'
    CAN_CONFIGURE_THEME = 'can_configure_theme'
    CAN_MANAGE_PLUGINS = 'can_manage_plugins'
    CAN_MANAGE_LICENSES = 'can_manage_licenses'
    CAN_VIEW_SYSTEM_LOGS = 'can_view_system_logs'
    
    ALL_SYSTEM_ADMIN_PERMISSIONS = [
        CAN_MANAGE_SYSTEM_SETTINGS, CAN_CONFIGURE_EMAIL,
        CAN_CONFIGURE_STORAGE, CAN_VIEW_SYSTEM_HEALTH,
        CAN_MANAGE_BACKUP, CAN_RESTORE_BACKUP,
        CAN_CONFIGURE_AUTHENTICATION, CAN_CONFIGURE_NOTIFICATIONS,
        CAN_CONFIGURE_THEME, CAN_MANAGE_PLUGINS,
        CAN_MANAGE_LICENSES, CAN_VIEW_SYSTEM_LOGS,
    ]


class MobileOfflinePermissions:
    """Mobile app and offline learning permissions"""
    
    CAN_USE_MOBILE_APP = 'can_use_mobile_app'
    CAN_DOWNLOAD_OFFLINE_CONTENT = 'can_download_offline_content'
    CAN_SYNC_OFFLINE_DATA = 'can_sync_offline_data'
    CAN_ACCESS_OFFLINE_MODE = 'can_access_offline_mode'
    CAN_INSTALL_MOBILE_APP = 'can_install_mobile_app'
    
    ALL_MOBILE_OFFLINE_PERMISSIONS = [
        CAN_USE_MOBILE_APP, CAN_DOWNLOAD_OFFLINE_CONTENT,
        CAN_SYNC_OFFLINE_DATA, CAN_ACCESS_OFFLINE_MODE,
        CAN_INSTALL_MOBILE_APP,
    ]


class StudentAssessmentPermissions:
    """Student-facing assessment permissions"""
    
    CAN_TAKE_QUIZ = 'can_take_quiz'
    CAN_SUBMIT_ASSIGNMENT = 'can_submit_assignment'
    CAN_VIEW_QUIZ_RESULTS = 'can_view_quiz_results'
    CAN_VIEW_OWN_GRADES = 'can_view_own_grades'
    CAN_RETAKE_QUIZ = 'can_retake_quiz'
    
    ALL_STUDENT_ASSESSMENT_PERMISSIONS = [
        CAN_TAKE_QUIZ, CAN_SUBMIT_ASSIGNMENT,
        CAN_VIEW_QUIZ_RESULTS, CAN_VIEW_OWN_GRADES,
        CAN_RETAKE_QUIZ,
    ]


class SuperuserOnlyPermissions:
    """System-level superuser permissions"""
    
    CAN_ACCESS_DJANGO_ADMIN = 'can_access_django_admin'
    CAN_MANAGE_SUPERUSERS = 'can_manage_superusers'
    CAN_MODIFY_SYSTEM_CODE = 'can_modify_system_code'
    CAN_ACCESS_SERVER_SHELL = 'can_access_server_shell'
    CAN_MANAGE_DATABASE_SCHEMA = 'can_manage_database_schema'
    CAN_CONFIGURE_DEPLOYMENT = 'can_configure_deployment'
    CAN_MANAGE_SSL_CERTIFICATES = 'can_manage_ssl_certificates'
    CAN_CONFIGURE_LOAD_BALANCING = 'can_configure_load_balancing'
    
    ALL_SUPERUSER_ONLY_PERMISSIONS = [
        CAN_ACCESS_DJANGO_ADMIN, CAN_MANAGE_SUPERUSERS,
        CAN_MODIFY_SYSTEM_CODE, CAN_ACCESS_SERVER_SHELL,
        CAN_MANAGE_DATABASE_SCHEMA, CAN_CONFIGURE_DEPLOYMENT,
        CAN_MANAGE_SSL_CERTIFICATES, CAN_CONFIGURE_LOAD_BALANCING,
    ]
