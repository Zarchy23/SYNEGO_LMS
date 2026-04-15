from django.core.mail import send_mail


def send_safe_email(subject, message, from_email, recipient_list, html_message=None):
	"""Send email with fail-safe behavior for development and async tasks."""
	try:
		send_mail(
			subject=subject,
			message=message,
			from_email=from_email,
			recipient_list=recipient_list,
			html_message=html_message,
			fail_silently=False,
		)
		return True
	except Exception:
		return False
