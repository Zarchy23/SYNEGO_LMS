#!/usr/bin/env python
import re

files_to_update = {
    'lms/views_enterprise_admin.py': {
        'ai_model_config_view': 'ai_administration.html',
        'ai_performance_view': 'ai_administration.html',
        'smart_contracts_view': 'blockchain.html',
        'contract_registry_view': 'blockchain.html',
        'api_management_view': 'api_gateway.html',
        'third_party_services_view': 'integrations.html',
        'webhooks_view': 'integrations.html',
        'authentication_config_view': 'authentication_management.html',
        'encryption_keys_view': 'security_compliance.html',
        'audit_trail_view': 'audit_logs.html',
        'compliance_view': 'security_compliance.html',
        'email_config_view': 'configuration.html',
        'storage_backup_view': 'backup_recovery.html',
        'theme_customization_view': 'custom_branding.html',
        'plugins_view': 'integrations.html',
        'licenses_view': 'integrations.html',
        'bi_integration_view': 'advanced_analytics.html',
        'report_scheduling_view': 'report_generation.html',
        'system_health_view': 'system_health.html',
    },
    'lms/views_enterprise_instructor.py': {
        'generate_questions_view': 'instructor_ai_tools.html',
        'adaptive_learning_view': 'instructor_ai_tools.html',
        'ai_essay_scoring_view': 'instructor_ai_tools.html',
        'create_vr_session_view': 'instructor_vrar_creation.html',
        'create_ar_simulation_view': 'instructor_vrar_creation.html',
        'code_exercises_view': 'instructor_assessment_tools.html',
        'proctoring_view': 'instructor_assessment_tools.html',
        'issue_certificates_view': 'instructor_credentials.html',
        'mint_badges_view': 'instructor_credentials.html',
        'engagement_dashboard_view': 'instructor_analytics.html',
        'at_risk_students_view': 'instructor_analytics.html',
        'reports_export_view': 'instructor_analytics.html',
    },
    'lms/views_enterprise_learner.py': {
        'knowledge_state_view': 'learner_ai_assistant.html',
        'ai_recommendations_view': 'learner_ai_assistant.html',
        'ai_assistant_view': 'learner_ai_assistant.html',
        'vr_sessions_view': 'learner_vrar_experiences.html',
        'ar_simulations_view': 'learner_vrar_simulations.html',
        'study_groups_view': 'learner_collaboration.html',
        'peer_reviews_view': 'learner_collaboration.html',
        'verified_certificates_view': 'learner_credentials.html',
        'nft_badges_view': 'learner_credentials.html',
        'my_wallet_view': 'learner_credentials.html',
        'learning_analytics_view': 'learner_analytics.html',
        'predictions_view': 'learner_performance_analytics.html',
    },
    'lms/views_enterprise_dept_head.py': {
        'quality_reviews_view': 'dept_head_course_quality.html',
        'ai_recommendations_view': 'dept_head_course_quality.html',
        'instructor_evaluations_view': 'dept_head_staff_management.html',
        'instructor_performance_view': 'dept_head_staff_management.html',
        'schedule_meetings_view': 'dept_head_staff_management.html',
        'budget_overview_view': 'dept_head_budget_resources.html',
        'request_resources_view': 'dept_head_budget_resources.html',
        'approve_requests_view': 'dept_head_approvals.html',
        'cohort_comparison_view': 'dept_head_insights.html',
        'cross_course_analytics_view': 'dept_head_insights.html',
    }
}

for file_path, replacements in files_to_update.items():
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace all placeholder references with feature templates
        content = content.replace("'lms/enterprise_placeholder.html'", "'lms/features/TEMPLATE.html'")
        
        # Now replace TEMPLATE with the correct feature template for each function
        for func_name, template in replacements.items():
            # Find the function definition and its return statement
            pattern = f"def {func_name}\\(.*?\\):\n(.*?)return render\\(request, 'lms/features/TEMPLATE.html', context\\)"
            replacement = f"def {func_name}(\\1return render(request, 'lms/features/{template}', context)"
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Updated {file_path}")
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
    except Exception as e:
        print(f"✗ Error updating {file_path}: {e}")

print("\nAll files updated!")
