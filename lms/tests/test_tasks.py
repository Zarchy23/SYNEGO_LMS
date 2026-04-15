from django.test import TestCase

from lms.tasks import send_async_email


class TaskTests(TestCase):
	def test_send_async_email_returns_status_dict(self):
		result = send_async_email("Subject", "Body", "noreply@example.com")
		self.assertIn("status", result)

