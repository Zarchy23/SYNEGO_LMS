# lms/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

# Namespace for the app
app_name = 'lms'

urlpatterns = [
    # -------------------------------------------------------------------
    # Home & Public Pages
    # -------------------------------------------------------------------
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
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
    path('dashboard/department/', views.department_head_dashboard, name='department_head_dashboard'),
    
    # -------------------------------------------------------------------
    # Department Views
    # -------------------------------------------------------------------
    path('departments/', views.department_list, name='department_list'),
    path('departments/<slug:slug>/', views.department_detail, name='department_detail'),
    
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
    path('admin-panel/departments/', views.admin_departments, name='admin_departments'),
    path('admin-panel/departments/add/', views.admin_add_department, name='admin_add_department'),
    path('admin-panel/departments/<int:dept_id>/edit/', 
         views.admin_edit_department, 
         name='admin_edit_department'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/reports/download/<str:report_type>/', 
         views.download_report, 
         name='download_report'),
    path('admin-panel/system-logs/', views.admin_system_logs, name='admin_system_logs'),

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
]

# -------------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------------
handler400 = 'lms.views.bad_request'
handler403 = 'lms.views.permission_denied'
handler404 = 'lms.views.page_not_found'
handler500 = 'lms.views.server_error'