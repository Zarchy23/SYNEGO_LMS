import logging
from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .models import (
    Assignment,
    Certificate,
    Course,
    Enrollment,
    EnrollmentRequest,
    Notification,
    Quiz,
    Submission,
    User,
)
from .utils.certificate_gen import generate_certificate_pdf
from .utils.email import send_safe_email

logger = get_task_logger(__name__)
fallback_logger = logging.getLogger(__name__)


def _render_email(template, context, fallback_message):
    """Render an email template with safe fallback to plain content."""
    try:
        return render_to_string(template, context)
    except Exception as exc:
        fallback_logger.warning("Email template rendering failed for %s: %s", template, exc)
        return fallback_message


@shared_task
def send_async_email(subject, body, recipient):
    """Send a simple async email."""
    send_safe_email(
        subject=subject,
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
        recipient_list=[recipient],
    )
    return {"subject": subject, "recipient": recipient, "status": "sent"}


@shared_task
def send_welcome_email_task(user_id, temp_password=None, set_password_url=None):
    """Send welcome email asynchronously."""
    try:
        user = User.objects.get(id=user_id)
        login_url = getattr(settings, "LOGIN_URL", "/login/")

        context = {
            "user": user,
            "temp_password": temp_password,
            "set_password_url": set_password_url,
            "login_url": login_url,
        }
        plain = (
            "Welcome to Synego Institute!\n\n"
            f"Login URL: {login_url}\n"
            f"Username: {user.username}\n"
            + (f"Temporary Password: {temp_password}\n" if temp_password else "")
        )
        html = _render_email("lms/registration/welcome_email.html", context, plain)

        send_safe_email(
            subject=f"Welcome to Synego Institute, {user.first_name or user.username}!",
            message=plain,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            recipient_list=[user.email],
            html_message=html,
        )

        logger.info("Welcome email sent to %s", user.email)
        return True
    except Exception as exc:
        logger.error("Failed to send welcome email to %s: %s", user_id, exc)
        return False


@shared_task
def send_approval_notification_task(user_id, approver_id, request_id):
    """Send notification when enrollment request is approved."""
    try:
        user = User.objects.get(id=user_id)
        approver = User.objects.get(id=approver_id)
        enrollment_request = EnrollmentRequest.objects.get(id=request_id)
        login_url = getattr(settings, "LOGIN_URL", "/login/")

        context = {
            "user": user,
            "course": enrollment_request.course,
            "approver": approver,
            "login_url": login_url,
        }

        plain = (
            f"Your enrollment in {enrollment_request.course.title} has been approved.\n"
            f"Approved by: {approver.get_full_name() or approver.username}\n"
            f"Login: {login_url}"
        )
        html = _render_email("lms/registration/approval_request_email.html", context, plain)

        send_safe_email(
            subject=f"Enrollment approved: {enrollment_request.course.title}",
            message=plain,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            recipient_list=[user.email],
            html_message=html,
        )

        logger.info("Approval notification sent to %s", user.email)
        return True
    except Exception as exc:
        logger.error("Failed to send approval notification: %s", exc)
        return False


@shared_task
def send_grade_notification_task(submission_id):
    """Send notification when assignment is graded."""
    try:
        submission = Submission.objects.select_related("student", "assignment").get(id=submission_id)

        plain = (
            f"Grade posted for {submission.assignment.title}.\n"
            f"Grade: {submission.grade if submission.grade is not None else 'N/A'}"
        )
        context = {
            "submission": submission,
            "student": submission.student,
            "assignment": submission.assignment,
            "grade": submission.grade,
            "feedback": submission.feedback,
        }
        html = _render_email("lms/notifications/notification_email_base.html", context, plain)

        send_safe_email(
            subject=f"Grade Posted: {submission.assignment.title}",
            message=plain,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            recipient_list=[submission.student.email],
            html_message=html,
        )

        Notification.objects.create(
            recipient=submission.student,
            title=f"Grade Posted: {submission.assignment.title}",
            message=f"You received {submission.grade}% on {submission.assignment.title}",
            notification_type="grade",
            related_url=f"/submission/{submission.id}/",
        )

        logger.info("Grade notification sent to %s", submission.student.email)
        return True
    except Exception as exc:
        logger.error("Failed to send grade notification: %s", exc)
        return False


@shared_task
def send_deadline_reminder_task():
    """Send reminders for assignments due in the next 24 hours."""
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    assignments = Assignment.objects.filter(due_date__gt=now, due_date__lte=tomorrow)

    reminders_sent = 0
    for assignment in assignments:
        enrollments = Enrollment.objects.filter(course=assignment.course, status="active").select_related("student")

        for enrollment in enrollments:
            has_submitted = Submission.objects.filter(
                assignment=assignment,
                student=enrollment.student,
                status__in=["submitted", "graded", "under_review"],
            ).exists()

            if not has_submitted:
                plain = f"Reminder: {assignment.title} is due {assignment.due_date}."
                send_safe_email(
                    subject=f"Reminder: {assignment.title} is due soon",
                    message=plain,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
                    recipient_list=[enrollment.student.email],
                )

                Notification.objects.create(
                    recipient=enrollment.student,
                    title=f"Assignment Due Soon: {assignment.title}",
                    message=f"Your assignment is due on {assignment.due_date.strftime('%B %d, %Y %H:%M')}",
                    notification_type="reminder",
                    related_url=f"/assignment/{assignment.id}/",
                )
                reminders_sent += 1

    logger.info("Sent %s deadline reminders", reminders_sent)
    return reminders_sent


@shared_task
def generate_certificate_task(enrollment_id):
    """Generate certificate asynchronously when course is completed."""
    try:
        enrollment = Enrollment.objects.select_related("student", "course").get(id=enrollment_id)

        if Certificate.objects.filter(student=enrollment.student, course=enrollment.course).exists():
            logger.info("Certificate already exists for %s - %s", enrollment.student.email, enrollment.course.title)
            return False

        pdf_file, qr_code = generate_certificate_pdf(enrollment)

        certificate = Certificate.objects.create(
            student=enrollment.student,
            course=enrollment.course,
            pdf_file=pdf_file,
            qr_code=qr_code,
            final_grade=enrollment.get_final_grade(),
        )

        Notification.objects.create(
            recipient=enrollment.student,
            title=f"Certificate Issued: {enrollment.course.title}",
            message=f"Congratulations! Your certificate for {enrollment.course.title} is ready.",
            notification_type="certificate",
            related_url=f"/certificate/{certificate.certificate_id}/",
        )

        send_safe_email(
            subject=f"Certificate ready: {enrollment.course.title}",
            message=f"Congratulations on completing {enrollment.course.title}.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            recipient_list=[enrollment.student.email],
        )

        logger.info("Certificate generated for %s - %s", enrollment.student.email, enrollment.course.title)
        return True
    except Exception as exc:
        logger.error("Failed to generate certificate: %s", exc)
        return False


@shared_task
def check_course_completion_task(enrollment_id):
    """Check if course is complete and trigger certificate generation."""
    try:
        enrollment = Enrollment.objects.select_related("course").get(id=enrollment_id)
        total_chapters = enrollment.course.chapters.count()
        completed_chapters = len(enrollment.progress.get("completed_chapters", []))

        if total_chapters > 0 and completed_chapters >= total_chapters:
            course_quizzes = Quiz.objects.filter(chapter__course=enrollment.course)
            quiz_passes = set(enrollment.progress.get("quiz_passes", []))
            all_quizzes_passed = all(str(q.id) in quiz_passes for q in course_quizzes)

            if all_quizzes_passed or not course_quizzes.exists():
                enrollment.status = "completed"
                enrollment.completed_at = timezone.now()
                enrollment.save(update_fields=["status", "completed_at"])
                generate_certificate_task.delay(enrollment.id)
                logger.info("Course %s completed by %s", enrollment.course.title, enrollment.student.email)

        return True
    except Exception as exc:
        logger.error("Failed to check course completion: %s", exc)
        return False


@shared_task
def sync_google_classroom_task(user_id):
    """Sync Google Classroom courses for a user."""
    try:
        user = User.objects.get(id=user_id)
        if not user.google_access_token:
            logger.warning("No Google token for user %s", user.email)
            return False

        from lms.utils.google_client import GoogleClassroomClient

        client = GoogleClassroomClient(user)
        courses = client.list_courses()

        created_count = 0
        for course_data in courses:
            course, created = Course.objects.get_or_create(
                google_classroom_id=course_data["id"],
                defaults={
                    "title": course_data.get("name", "Imported Course"),
                    "description": course_data.get("description", ""),
                    "department": user.module,
                    "status": "draft",
                    "duration": "TBD",
                    "learning_objectives": "Imported from Google Classroom",
                    "difficulty": "beginner",
                    "estimated_hours": 1,
                    "code": f"GC-{course_data['id'][:8]}",
                },
            )
            if created:
                created_count += 1

        logger.info("Synced %s courses from Google Classroom for %s", created_count, user.email)
        return created_count
    except Exception as exc:
        logger.error("Failed to sync Google Classroom: %s", exc)
        return False


@shared_task
def push_grade_to_google_classroom_task(submission_id):
    """Push grade to Google Classroom."""
    try:
        submission = Submission.objects.select_related("assignment", "student", "assignment__course").get(id=submission_id)

        if not submission.assignment.google_classroom_id or not submission.assignment.course.google_classroom_id:
            logger.warning("Missing Google Classroom IDs for submission %s", submission_id)
            return False

        from lms.utils.google_client import GoogleClassroomClient

        client = GoogleClassroomClient(submission.student)
        client.update_submission_grade(
            course_id=submission.assignment.course.google_classroom_id,
            coursework_id=submission.assignment.google_classroom_id,
            student_id=submission.student.email,
            grade=submission.grade,
        )

        logger.info("Pushed grade %s to Google Classroom for %s", submission.grade, submission.student.email)
        return True
    except Exception as exc:
        logger.error("Failed to push grade to Google Classroom: %s", exc)
        return False


@shared_task
def submit_to_turnitin_task(submission_id):
    """Submit file to Turnitin for plagiarism check."""
    try:
        submission = Submission.objects.select_related("assignment", "student").get(id=submission_id)

        if not submission.assignment.enable_plagiarism_check:
            logger.info("Plagiarism check not enabled for assignment %s", submission.assignment.id)
            return False

        from lms.utils.turnitin_lti import TurnitinLTI

        client = TurnitinLTI()
        file_url = submission.submitted_file.url if submission.submitted_file else ""
        result = client.submit_file(
            submission_id=submission.id,
            file_url=file_url,
            student_name=submission.student.get_full_name() or submission.student.username,
            student_email=submission.student.email,
            assignment_title=submission.assignment.title,
        )

        if result.get("success"):
            submission.turnitin_submission_id = result.get("submission_id", "")
            submission.similarity_score = result.get("similarity_score")
            submission.turnitin_report_url = result.get("report_url", "")
            submission.save(update_fields=["turnitin_submission_id", "similarity_score", "turnitin_report_url"])
            logger.info("Submitted to Turnitin: %s", submission.id)
            return True

        logger.error("Turnitin submission failed: %s", result.get("error"))
        return False
    except Exception as exc:
        logger.error("Failed to submit to Turnitin: %s", exc)
        return False


@shared_task
def check_turnitin_report_task(submission_id):
    """Check if Turnitin report is ready."""
    try:
        submission = Submission.objects.select_related("assignment", "student", "assignment__course__department__head").get(id=submission_id)
        if not submission.turnitin_submission_id:
            return False

        from lms.utils.turnitin_lti import TurnitinLTI

        client = TurnitinLTI()
        result = client.get_report(submission.turnitin_submission_id)

        if result.get("ready"):
            submission.similarity_score = result.get("similarity_score")
            submission.turnitin_report_url = result.get("report_url", "")
            submission.save(update_fields=["similarity_score", "turnitin_report_url"])

            dept_head = submission.assignment.course.department.head
            if dept_head:
                Notification.objects.create(
                    recipient=dept_head,
                    title=f"Turnitin Report Ready: {submission.assignment.title}",
                    message=f"Plagiarism report is ready for {submission.student.get_full_name() or submission.student.username}",
                    notification_type="info",
                    related_url=f"/instructor/submission/{submission.id}/grade/",
                )

            logger.info("Turnitin report ready for submission %s", submission_id)
            return True

        check_turnitin_report_task.apply_async(args=[submission_id], countdown=30)
        return False
    except Exception as exc:
        logger.error("Failed to check Turnitin report: %s", exc)
        return False


@shared_task
def cleanup_inactive_users_task():
    """Delete inactive learners with no recent login."""
    cutoff_date = timezone.now() - timedelta(days=90)
    inactive_users = User.objects.filter(last_login__lt=cutoff_date, is_active=True, role="learner")
    count = inactive_users.count()
    inactive_users.delete()
    logger.info("Cleaned up %s inactive users", count)
    return count


@shared_task
def cleanup_expired_tokens_task():
    """Delete unapproved users with expired approval tokens."""
    cutoff_date = timezone.now() - timedelta(hours=48)
    expired_users = User.objects.filter(approval_token_created_at__lt=cutoff_date, is_approved=False)
    count = expired_users.count()
    expired_users.delete()
    logger.info("Cleaned up %s expired registration tokens", count)
    return count


@shared_task
def archive_old_notifications_task():
    """Archive notifications older than 30 days (hard delete in this implementation)."""
    cutoff_date = timezone.now() - timedelta(days=30)
    old_notifications = Notification.objects.filter(created_at__lt=cutoff_date)
    count = old_notifications.count()
    old_notifications.delete()
    logger.info("Archived %s old notifications", count)
    return count


@shared_task
def generate_daily_report_task():
    """Generate and email daily system report to admin address."""
    today = timezone.now().date()
    stats = {
        "date": str(today),
        "new_users": User.objects.filter(date_joined__date=today).count(),
        "new_enrollments": Enrollment.objects.filter(enrolled_at__date=today).count(),
        "new_submissions": Submission.objects.filter(submitted_at__date=today).count(),
        "certificates_issued": Certificate.objects.filter(issued_at__date=today).count(),
        "pending_approvals": EnrollmentRequest.objects.filter(status="pending").count(),
    }

    admin_email = getattr(settings, "ADMIN_EMAIL", getattr(settings, "DEFAULT_FROM_EMAIL", "admin@localhost"))
    message = (
        f"Daily Report ({today})\n"
        f"New users: {stats['new_users']}\n"
        f"New enrollments: {stats['new_enrollments']}\n"
        f"New submissions: {stats['new_submissions']}\n"
        f"Certificates issued: {stats['certificates_issued']}\n"
        f"Pending approvals: {stats['pending_approvals']}"
    )
    send_safe_email(
        subject=f"Daily Report - {today}",
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
        recipient_list=[admin_email],
    )
    logger.info("Daily report sent to %s", admin_email)
    return stats


@shared_task
def update_student_progress_task(student_id, course_id):
    """Update denormalized student progress cache."""
    try:
        from lms.models import StudentProgress

        enrollment = Enrollment.objects.get(student_id=student_id, course_id=course_id)
        progress_percent = enrollment.get_progress_percent()
        StudentProgress.objects.update_or_create(
            student_id=student_id,
            course_id=course_id,
            defaults={"overall_percent": progress_percent},
        )
        logger.info("Updated progress for student %s in course %s", student_id, course_id)
        return True
    except Exception as exc:
        logger.error("Failed to update progress: %s", exc)
        return False
