class TurnitinLTI:
	"""Turnitin LTI helper stub used by async tasks."""

	def submit_file(self, submission_id, file_url, student_name, student_email, assignment_title):
		return {
			"success": True,
			"submission_id": f"tti-{submission_id}",
			"similarity_score": None,
			"report_url": "",
			"error": "",
		}

	def get_report(self, turnitin_submission_id):
		return {
			"ready": False,
			"similarity_score": None,
			"report_url": "",
		}
