from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from lms.permissions import IsAdmin, require_roles


class PermissionTests(TestCase):
	def test_require_roles_denies_invalid_role(self):
		user = SimpleNamespace(is_authenticated=True, role="learner")
		with self.assertRaises(PermissionDenied):
			require_roles(user, ["admin"])

	def test_is_admin_permission_true_for_admin(self):
		request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role="admin"))
		self.assertTrue(IsAdmin().has_permission(request, None))

