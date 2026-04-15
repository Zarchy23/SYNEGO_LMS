class GoogleClassroomClient:
	"""Lightweight client stub for Google Classroom integration flows."""

	def __init__(self, user):
		self.user = user

	def list_courses(self):
		"""Return classroom courses for the current user."""
		return []

	def update_submission_grade(self, course_id, coursework_id, student_id, grade):
		"""Push grade to Google Classroom (stub)."""
		return {
			"success": True,
			"course_id": course_id,
			"coursework_id": coursework_id,
			"student_id": student_id,
			"grade": grade,
		}
