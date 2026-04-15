from django.core.files.base import ContentFile


def generate_certificate_pdf(enrollment):
    """Generate placeholder certificate artifacts for async pipeline."""
    pdf_bytes = (
        f"Certificate for {enrollment.student.get_full_name() or enrollment.student.username}"
        f" in {enrollment.course.title}".encode("utf-8")
    )
    pdf_file = ContentFile(pdf_bytes, name=f"certificate_{enrollment.id}.pdf")

    qr_bytes = f"verify:{enrollment.id}".encode("utf-8")
    qr_file = ContentFile(qr_bytes, name=f"certificate_{enrollment.id}_qr.txt")
    return pdf_file, qr_file


def generate_certificate(enrollment):
    """Synchronous helper used by Enrollment.complete_course."""
    from lms.models import Certificate

    if Certificate.objects.filter(student=enrollment.student, course=enrollment.course).exists():
        return None

    pdf_file, qr_file = generate_certificate_pdf(enrollment)
    return Certificate.objects.create(
        student=enrollment.student,
        course=enrollment.course,
        pdf_file=pdf_file,
        qr_code=qr_file,
        final_grade=enrollment.get_final_grade(),
    )
