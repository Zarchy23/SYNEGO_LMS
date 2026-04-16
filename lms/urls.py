# lms/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from . import views_enterprise_admin
from . import views_enterprise_instructor
from . import views_enterprise_learner
from . import views_enterprise_dept_head

# Namespace for the app
app_name = 'lms'

urlpatterns = [
    # -------------------------------------------------------------------
    # Home & Public Pages
    # -------------------------------------------------------------------
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('featured-courses/', views.featured_courses, name='featured_courses'),
    
    # -------------------------------------------------------------------
    # Authentication & Registration
    # -------------------------------------------------------------------
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.self_register, name='register'),
    path('register/success/', views.registration_success, name='registration_success'),
    path('approve/<uuid:token>/', views.approve_registration, name='approve_registration'),
    path('reject/<uuid:token>/', views.reject_registration, name='reject_registration'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='lms/registration/password_reset_form.html',
             email_template_name='lms/registration/password_reset_email.html'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='lms/registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='lms/registration/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='lms/registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Set password (for admin-created accounts)
    path('set-password/<uuid:token>/', views.set_password, name='set_password'),
    
    # -------------------------------------------------------------------
    # User Profile & Dashboard
    # -------------------------------------------------------------------
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/department/', views.module_head_dashboard, name='module_head_dashboard'),
    
    # -------------------------------------------------------------------
    # Module Views
    # -------------------------------------------------------------------
    path('modules/', views.module_list, name='module_list'),
    path('modules/<slug:slug>/', views.module_detail, name='module_detail'),
    
    # -------------------------------------------------------------------
    # Course Views
    # -------------------------------------------------------------------
    path('courses/', views.course_list, name='course_list'),
    path('my-courses/', views.my_enrolled_courses, name='my_enrolled_courses'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<slug:slug>/unenroll/', views.unenroll_course, name='unenroll_course'),
    
    # Chapter Views
    path('courses/<slug:course_slug>/chapter/<int:chapter_id>/', 
         views.chapter_detail, 
         name='chapter_detail'),
    path('courses/<slug:course_slug>/chapter/<int:chapter_id>/complete/', 
         views.mark_chapter_complete, 
         name='mark_chapter_complete'),
    
    # Quiz Views
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    path('quiz/<int:quiz_id>/retake/', views.retake_quiz, name='retake_quiz'),
    
    # -------------------------------------------------------------------
    # Assignment & Submission Views (Student)
    # -------------------------------------------------------------------
    path('assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/', views.view_submission, name='view_submission'),
    path('submission/<int:submission_id>/edit/', views.edit_submission, name='edit_submission'),
    
    # -------------------------------------------------------------------
    # Grading Views (Instructor)
    # -------------------------------------------------------------------
    path('instructor/assignments/', views.instructor_assignments, name='instructor_assignments'),
    path('instructor/assignment/<int:assignment_id>/submissions/', 
         views.submission_list, 
         name='submission_list'),
    path('instructor/submission/<int:submission_id>/grade/', 
         views.grade_submission, 
         name='grade_submission'),
    path('instructor/submission/<int:submission_id>/return/', 
         views.return_submission, 
         name='return_submission'),
    path('instructor/assignment/<int:assignment_id>/analytics/', 
         views.assignment_analytics, 
         name='assignment_analytics'),
    
    # -------------------------------------------------------------------
    # Assignment Creation (Instructor)
    # -------------------------------------------------------------------
    path('api/course/<slug:course_slug>/chapters/', 
         views.api_course_chapters, 
         name='api_course_chapters'),
    path('instructor/create-assignment/', 
         views.create_assignment, 
         name='create_assignment_new'),
    path('instructor/course/<slug:course_slug>/create-assignment/', 
         views.create_assignment, 
         name='create_assignment'),
    path('instructor/assignment/<int:assignment_id>/edit/', 
         views.edit_assignment, 
         name='edit_assignment'),
    path('instructor/assignment/<int:assignment_id>/delete/', 
         views.delete_assignment, 
         name='delete_assignment'),
    
    # -------------------------------------------------------------------
    # Course Management (Instructor)
    # -------------------------------------------------------------------
# Course Management (Instructor) - TODO: Implement
    # path('instructor/courses/', views.instructor_courses, name='instructor_courses'),
    # path('instructor/course/<slug:slug>/manage/', 
    #      views.manage_course, 
    #      name='manage_course'),
# path('instructor/course/<slug:slug>/add-chapter/', 
    #     views.add_chapter, 
    #     name='add_chapter'),
# path('instructor/chapter/<int:chapter_id>/edit/', 
    #     views.edit_chapter, 
    #     name='edit_chapter'),
# path('instructor/chapter/<int:chapter_id>/delete/', 
    #     views.delete_chapter, 
    #     name='delete_chapter'),
# path('instructor/course/<slug:slug>/create-quiz/', 
    #     views.create_quiz, 
    #     name='create_quiz'),
# path('instructor/quiz/<int:quiz_id>/edit/', 
    #     views.edit_quiz, 
    #     name='edit_quiz'),
# path('instructor/quiz/<int:quiz_id>/add-questions/', 
    #     views.add_quiz_questions, 
    #     name='add_quiz_questions'),
    
    # -------------------------------------------------------------------
    # Admin Views
    # -------------------------------------------------------------------
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/add/', views.admin_add_student, name='admin_add_student'),
    path('admin-panel/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/enrollment-requests/', 
         views.admin_enrollment_requests, 
         name='admin_enrollment_requests'),
    path('admin-panel/enrollment-requests/<int:request_id>/process/', 
         views.admin_process_request, 
         name='admin_process_request'),
    path('admin-panel/modules/', views.admin_modules, name='admin_modules'),
    path('admin-panel/modules/add/', views.admin_add_module, name='admin_add_module'),
    path('admin-panel/modules/<int:module_id>/edit/', 
         views.admin_edit_module, 
         name='admin_edit_module'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/reports/download/<str:report_type>/', 
         views.download_report, 
         name='download_report'),
    path('admin-panel/system-logs/', views.admin_system_logs, name='admin_system_logs'),
    path('admin-panel/system-settings/', views.admin_system_settings, name='admin_system_settings'),

     # Course Material Management (Admin)
     path('admin-panel/course/<slug:course_slug>/manage/', views.manage_course, name='manage_course'),
     path('admin-panel/course/<slug:course_slug>/add-material/', views.add_course_material, name='add_course_material'),
     path('admin-panel/course/<slug:course_slug>/add-chapter/', views.admin_add_chapter, name='admin_add_chapter'),
     path('admin-panel/course/<slug:course_slug>/add-assignment/', views.admin_add_assignment, name='admin_add_assignment'),
     path('admin-panel/course/<slug:course_slug>/add-quiz/', views.admin_add_quiz, name='admin_add_quiz'),
     path('admin-panel/course/<slug:course_slug>/add-quiz/<int:chapter_id>/', views.admin_add_quiz, name='admin_add_quiz_with_chapter'),
     path('admin-panel/quiz/<int:quiz_id>/add-questions/', views.admin_add_quiz_questions, name='admin_add_quiz_questions'),
     path('admin-panel/chapter/<int:chapter_id>/edit/', views.admin_edit_chapter, name='admin_edit_chapter'),
     path('admin-panel/chapter/<int:chapter_id>/delete/', views.admin_delete_chapter, name='admin_delete_chapter'),
     path('admin-panel/assignment/<int:assignment_id>/edit/', views.admin_edit_assignment, name='admin_edit_assignment'),
     path('admin-panel/assignment/<int:assignment_id>/delete/', views.admin_delete_assignment, name='admin_delete_assignment'),
     path('admin-panel/quiz/<int:quiz_id>/edit/', views.admin_edit_quiz, name='admin_edit_quiz'),
     path('admin-panel/quiz/<int:quiz_id>/delete/', views.admin_delete_quiz, name='admin_delete_quiz'),
     path('admin-panel/question/<int:question_id>/edit/', views.admin_edit_question, name='admin_edit_question'),
     path('admin-panel/question/<int:question_id>/delete/', views.admin_delete_question, name='admin_delete_question'),
    
    # -------------------------------------------------------------------
    # Bulk Operations (Admin)
    # -------------------------------------------------------------------
    path('admin-panel/bulk-enroll/download-template/', views.download_bulk_enroll_template, name='download_bulk_enroll_template'),
    path('admin-panel/bulk-enroll/', views.bulk_enroll_students, name='bulk_enroll_students'),
    path('admin-panel/bulk-upload/', views.bulk_upload_courses, name='bulk_upload_courses'),
    
    # -------------------------------------------------------------------
    # Certificate Views
    # -------------------------------------------------------------------
    path('certificate/<str:certificate_id>/', views.view_certificate, name='view_certificate'),
    path('certificate/<str:certificate_id>/download/', views.download_certificate, name='download_certificate'),
    path('certificate/verify/<str:certificate_id>/', views.verify_certificate, name='verify_certificate'),
    
    # -------------------------------------------------------------------
    # Google Integration
    # -------------------------------------------------------------------
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('google/sync-classroom/', views.sync_google_classroom, name='sync_google_classroom'),
    path('google/create-doc/<int:assignment_id>/', views.create_google_doc, name='create_google_doc'),
    
    # -------------------------------------------------------------------
    # Turnitin Integration
    # -------------------------------------------------------------------
    path('turnitin/launch/<int:submission_id>/', views.turnitin_launch, name='turnitin_launch'),
    path('turnitin/callback/', views.turnitin_callback, name='turnitin_callback'),
    path('turnitin/report/<int:submission_id>/', views.turnitin_report, name='turnitin_report'),
    
    # -------------------------------------------------------------------
    # API Endpoints (AJAX)
    # -------------------------------------------------------------------
    path('api/get-chapter-progress/', views.api_chapter_progress, name='api_chapter_progress'),
    path('api/update-progress/', views.api_update_progress, name='api_update_progress'),
    path('api/notification/mark-read/', views.api_mark_notification_read, name='api_mark_notification_read'),
    path('api/get-notifications/', views.api_get_notifications, name='api_get_notifications'),
    
    # -------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------
    path('search/', views.search, name='search'),
    
    # -------------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------------
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # -------------------------------------------------------------------
    # Progress Tracking
    # -------------------------------------------------------------------
    path('progress/', views.my_progress, name='my_progress'),
    path('progress/<slug:course_slug>/', views.course_progress, name='course_progress'),
    
    # -------------------------------------------------------------------
    # Grades
    # -------------------------------------------------------------------
    path('grades/', views.my_grades, name='my_grades'),
    path('grades/<slug:course_slug>/', views.course_grades, name='course_grades'),
    
    # -------------------------------------------------------------------
    # Help & Support
    # -------------------------------------------------------------------
    path('help/', views.help_center, name='help_center'),
    path('help/<slug:topic>/', views.help_topic, name='help_topic'),
    path('support/ticket/', views.create_support_ticket, name='create_support_ticket'),
    
    # ===================================================================
    # ENTERPRISE ADMIN FEATURES
    # ===================================================================
    
    # AI Administration
    path('admin/ai/models/', views_enterprise_admin.ai_models_view, name='ai_models'),
    path('admin/ai/config/', views_enterprise_admin.ai_model_config_view, name='ai_config'),
    path('admin/ai/performance/', views_enterprise_admin.ai_performance_view, name='ai_performance'),
    
    # Blockchain
    path('admin/blockchain/contracts/', views_enterprise_admin.smart_contracts_view, name='smart_contracts'),
    path('admin/blockchain/registry/', views_enterprise_admin.contract_registry_view, name='contract_registry'),
    
    # Integrations & API
    path('admin/api/management/', views_enterprise_admin.api_management_view, name='api_management'),
    path('admin/integrations/third-party/', views_enterprise_admin.third_party_services_view, name='third_party_services'),
    path('admin/integrations/webhooks/', views_enterprise_admin.webhooks_view, name='webhooks'),
    
    # Security & Compliance
    path('admin/security/authentication/', views_enterprise_admin.authentication_config_view, name='authentication'),
    path('admin/security/encryption/', views_enterprise_admin.encryption_keys_view, name='encryption'),
    path('admin/security/audit-trail/', views_enterprise_admin.audit_trail_view, name='audit_trail'),
    path('admin/security/compliance/', views_enterprise_admin.compliance_view, name='compliance'),
    
    # System Configuration
    path('admin/config/email/', views_enterprise_admin.email_config_view, name='email_config'),
    path('admin/config/storage-backup/', views_enterprise_admin.storage_backup_view, name='storage_backup'),
    path('admin/config/theme/', views_enterprise_admin.theme_customization_view, name='theme'),
    path('admin/config/plugins/', views_enterprise_admin.plugins_view, name='plugins'),
    path('admin/config/licenses/', views_enterprise_admin.licenses_view, name='licenses'),
    
    # Enterprise Analytics
    path('admin/analytics/bi/', views_enterprise_admin.bi_integration_view, name='bi_integration'),
    path('admin/analytics/reports/', views_enterprise_admin.report_scheduling_view, name='report_scheduling'),
    path('admin/analytics/health/', views_enterprise_admin.system_health_view, name='system_health'),
    
    # ===================================================================
    # ENTERPRISE INSTRUCTOR FEATURES
    # ===================================================================
    
    # AI Content Tools
    path('instructor/ai/generate-questions/', views_enterprise_instructor.generate_questions_view, name='generate_questions'),
    path('instructor/ai/adaptive-learning/', views_enterprise_instructor.adaptive_learning_view, name='adaptive_learning'),
    path('instructor/ai/essay-scoring/', views_enterprise_instructor.ai_essay_scoring_view, name='ai_essay_scoring'),
    
    # VR/AR Content Creation
    path('instructor/vr/create-session/', views_enterprise_instructor.create_vr_session_view, name='create_vr_session'),
    path('instructor/ar/create-simulation/', views_enterprise_instructor.create_ar_simulation_view, name='create_ar_simulation'),
    
    # Advanced Assessment
    path('instructor/assessment/code-exercises/', views_enterprise_instructor.code_exercises_view, name='code_exercises'),
    path('instructor/assessment/proctoring/', views_enterprise_instructor.proctoring_view, name='proctoring'),
    
    # Blockchain & Credentials
    path('instructor/credentials/issue-certificates/', views_enterprise_instructor.issue_certificates_view, name='issue_certificates'),
    path('instructor/credentials/mint-badges/', views_enterprise_instructor.mint_badges_view, name='mint_badges'),
    
    # Teaching Analytics
    path('instructor/analytics/engagement/', views_enterprise_instructor.engagement_dashboard_view, name='engagement_dashboard'),
    path('instructor/analytics/at-risk-students/', views_enterprise_instructor.at_risk_students_view, name='at_risk_students'),
    path('instructor/analytics/reports/', views_enterprise_instructor.reports_export_view, name='reports_export'),
    
    # ===================================================================
    # ENTERPRISE LEARNER FEATURES
    # ===================================================================
    
    # AI Learning
    path('learner/ai/knowledge-state/', views_enterprise_learner.knowledge_state_view, name='knowledge_state'),
    path('learner/ai/recommendations/', views_enterprise_learner.ai_recommendations_view, name='ai_recommendations'),
    path('learner/ai/assistant/', views_enterprise_learner.ai_assistant_view, name='ai_assistant'),
    
    # VR/AR Experiences
    path('learner/vr/sessions/', views_enterprise_learner.vr_sessions_view, name='vr_sessions'),
    path('learner/ar/simulations/', views_enterprise_learner.ar_simulations_view, name='ar_simulations'),
    
    # Collaboration
    path('learner/collaboration/study-groups/', views_enterprise_learner.study_groups_view, name='study_groups'),
    path('learner/collaboration/peer-reviews/', views_enterprise_learner.peer_reviews_view, name='peer_reviews'),
    
    # Blockchain & Credentials
    path('learner/credentials/certificates/', views_enterprise_learner.verified_certificates_view, name='verified_certificates'),
    path('learner/credentials/badges/', views_enterprise_learner.nft_badges_view, name='nft_badges'),
    path('learner/credentials/wallet/', views_enterprise_learner.my_wallet_view, name='my_wallet'),
    
    # Personal Analytics
    path('learner/analytics/learning-analytics/', views_enterprise_learner.learning_analytics_view, name='learning_analytics'),
    path('learner/analytics/predictions/', views_enterprise_learner.predictions_view, name='predictions'),
    
    # ===================================================================
    # MODULE HEAD FEATURES
    # ===================================================================
    
    # Course Quality & AI
    path('dept-head/quality/reviews/', views_enterprise_dept_head.quality_reviews_view, name='quality_reviews'),
    path('dept-head/quality/ai-recommendations/', views_enterprise_dept_head.ai_recommendations_view, name='module_ai_recommendations'),
    
    # Staff Management
    path('dept-head/staff/evaluations/', views_enterprise_dept_head.instructor_evaluations_view, name='instructor_evaluations'),
    path('dept-head/staff/performance/', views_enterprise_dept_head.instructor_performance_view, name='instructor_performance'),
    path('dept-head/staff/schedule-meetings/', views_enterprise_dept_head.schedule_meetings_view, name='schedule_meetings'),
    
    # Budget & Resources
    path('dept-head/budget/overview/', views_enterprise_dept_head.budget_overview_view, name='budget_overview'),
    path('dept-head/budget/request-resources/', views_enterprise_dept_head.request_resources_view, name='request_resources'),
    path('dept-head/budget/approve-requests/', views_enterprise_dept_head.approve_requests_view, name='approve_requests'),
    
    # Analytics
    path('dept-head/analytics/cohort-comparison/', views_enterprise_dept_head.cohort_comparison_view, name='cohort_comparison'),
    path('dept-head/analytics/cross-course/', views_enterprise_dept_head.cross_course_analytics_view, name='cross_course_analytics'),
]

# -------------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------------
handler400 = 'lms.views.bad_request'
handler403 = 'lms.views.permission_denied'
handler404 = 'lms.views.page_not_found'
handler500 = 'lms.views.server_error'