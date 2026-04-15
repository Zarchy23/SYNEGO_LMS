from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from lms.models import Assignment, Chapter, Course, Department, Question, Quiz


CHAPTER_1_CONTENT = """
<h2>Introduction to Engineering Surveying</h2>
<p>Welcome to Engineering Surveying. This chapter introduces core concepts and why surveying is essential in civil engineering projects.</p>
<h3>Learning Objectives</h3>
<ul>
    <li>Define engineering surveying and its purpose</li>
    <li>Identify major survey types and use cases</li>
    <li>Understand key terms used in fieldwork</li>
</ul>
<h3>Key Concepts</h3>
<ul>
    <li>Benchmark, leveling, traverse, contour line</li>
    <li>Azimuth and bearing basics</li>
    <li>Surveying as foundation for roads, buildings, drainage, and bridges</li>
</ul>
<h3>Summary</h3>
<p>Surveying is the first and most critical step in construction planning and execution.</p>
"""

CHAPTER_2_CONTENT = """
<h2>Surveying Instruments and Equipment</h2>
<p>This chapter covers practical field equipment used by surveyors.</p>
<h3>Essential Instruments</h3>
<ul>
    <li>Total Station (angles + EDM + coordinate calculations)</li>
    <li>GPS/GNSS Receiver (RTK and static workflows)</li>
    <li>Automatic Level (elevation measurement)</li>
    <li>Theodolite (precise angle measurement)</li>
</ul>
<h3>Care and Maintenance</h3>
<ul>
    <li>Store in protective cases</li>
    <li>Handle optics with lens paper only</li>
    <li>Perform regular calibration checks</li>
</ul>
"""

CHAPTER_3_CONTENT = """
<h2>Leveling and Height Measurement</h2>
<p>Learn to measure elevation differences accurately for engineering design and construction.</p>
<h3>Core Formulas</h3>
<p><strong>HI = BM Elevation + Backsight</strong></p>
<p><strong>RL = HI - Foresight</strong></p>
<h3>Leveling Types</h3>
<ul>
    <li>Differential leveling</li>
    <li>Profile leveling</li>
    <li>Cross-section leveling</li>
    <li>Reciprocal leveling</li>
</ul>
<h3>Practical Focus</h3>
<p>Field setup, reading sequence, calculations, and closure/error checks.</p>
"""

CHAPTER_4_CONTENT = """
<h2>Distance Measurement and Traversing</h2>
<p>This chapter introduces traversing workflows, coordinate computation, and error adjustment.</p>
<h3>Distance Methods</h3>
<ul>
    <li>Tape measurement</li>
    <li>EDM/Total Station</li>
    <li>GPS/GNSS</li>
</ul>
<h3>Traverse Basics</h3>
<ul>
    <li>Closed and open traverse types</li>
    <li>Latitude and departure</li>
    <li>Coordinate calculations (Easting/Northing)</li>
    <li>Bowditch adjustment rule</li>
</ul>
"""

QUIZ_QUESTIONS = [
    {
        "text": "What is the most commonly used instrument for modern surveying?",
        "question_type": "mcq",
        "options": ["Theodolite", "Automatic Level", "Total Station", "GPS"],
        "correct_answer": "Total Station",
        "points": 10,
    },
    {
        "text": "A backsight reading is taken on an unknown point.",
        "question_type": "tf",
        "options": ["True", "False"],
        "correct_answer": "False",
        "points": 10,
    },
    {
        "text": "What does HI stand for in leveling calculations?",
        "question_type": "mcq",
        "options": ["Horizontal Index", "Height of Instrument", "Height Indicator", "Horizontal Indicator"],
        "correct_answer": "Height of Instrument",
        "points": 10,
    },
    {
        "text": "Calculate the Reduced Level if HI = 105.500 m and FS = 2.350 m.",
        "question_type": "short",
        "options": [],
        "correct_answer": "103.150 m",
        "points": 10,
    },
    {
        "text": "GPS provides more accurate distance measurements than a total station for short distances.",
        "question_type": "tf",
        "options": ["True", "False"],
        "correct_answer": "False",
        "points": 10,
    },
    {
        "text": "Which type of survey is used to map terrain features?",
        "question_type": "mcq",
        "options": ["Boundary Survey", "Topographic Survey", "Construction Survey", "Hydrographic Survey"],
        "correct_answer": "Topographic Survey",
        "points": 10,
    },
    {
        "text": "What is the formula for calculating Height of Instrument (HI)?",
        "question_type": "short",
        "options": [],
        "correct_answer": "HI = BM Elevation + Backsight Reading",
        "points": 10,
    },
    {
        "text": "In a closed traverse, the sum of latitudes should equal:",
        "question_type": "mcq",
        "options": ["0", "360", "180", "Perimeter"],
        "correct_answer": "0",
        "points": 10,
    },
    {
        "text": "A benchmark is a temporary reference point.",
        "question_type": "tf",
        "options": ["True", "False"],
        "correct_answer": "False",
        "points": 10,
    },
    {
        "text": "Convert bearing N45°W to azimuth.",
        "question_type": "short",
        "options": [],
        "correct_answer": "315°",
        "points": 10,
    },
]


class Command(BaseCommand):
    help = "Seed sample Engineering Surveying materials (chapters, quiz, questions, assignment)."

    def handle(self, *args, **options):
        department, _ = Department.objects.get_or_create(
            code="CEI",
            defaults={
                "name": "Department of Civil Engineering and Infrastructure",
                "description": "Supports technical construction operations in surveying, road works, and materials testing.",
                "mission": "Build practical civil engineering skills for infrastructure delivery.",
                "vision": "Be a leading training center for civil engineering practice.",
                "infrastructure": "Survey kits, lab equipment, practical field setup.",
                "resources": "Total station, GPS tools, leveling instruments.",
                "status": "active",
            },
        )

        course = Course.objects.filter(code="CEI-8E6928").first()
        if not course:
            course = Course.objects.filter(title__iexact="Engineering Surveying").first()

        if not course:
            course = Course.objects.create(
                department=department,
                code="CEI-8E6928",
                title="Engineering Surveying",
                description="Core surveying principles and practical field methods for civil engineering applications.",
                learning_objectives="Understand surveying concepts, instruments, leveling, traversing, and practical workflows.",
                prerequisites="Basic mathematics and technical drawing fundamentals.",
                duration="6 - 12 months",
                estimated_hours=120,
                difficulty="intermediate",
                status="published",
                is_active=True,
            )
        else:
            course.department = department
            course.duration = "6 - 12 months"
            course.difficulty = "intermediate"
            course.status = "published"
            course.is_active = True
            course.save()

        chapters_data = [
            {
                "order": 1,
                "title": "Introduction to Engineering Surveying",
                "chapter_type": "lesson",
                "content": CHAPTER_1_CONTENT,
                "estimated_minutes": 45,
                "video_url": "https://www.youtube.com/embed/2b1l4UeLq6M",
            },
            {
                "order": 2,
                "title": "Surveying Instruments and Equipment",
                "chapter_type": "lesson",
                "content": CHAPTER_2_CONTENT,
                "estimated_minutes": 60,
                "video_url": "https://www.youtube.com/embed/3gUfBcLrMlQ",
            },
            {
                "order": 3,
                "title": "Leveling and Height Measurement",
                "chapter_type": "lesson",
                "content": CHAPTER_3_CONTENT,
                "estimated_minutes": 50,
                "video_url": "https://www.youtube.com/embed/4K5dZM4n_v4",
            },
            {
                "order": 4,
                "title": "Distance Measurement and Traversing",
                "chapter_type": "lesson",
                "content": CHAPTER_4_CONTENT,
                "estimated_minutes": 55,
                "video_url": "",
            },
            {
                "order": 5,
                "title": "Engineering Surveying Quiz",
                "chapter_type": "quiz",
                "content": "Test your knowledge of surveying fundamentals.",
                "estimated_minutes": 30,
                "video_url": "",
            },
        ]

        chapter_map = {}
        for item in chapters_data:
            chapter, _ = Chapter.objects.update_or_create(
                course=course,
                order=item["order"],
                defaults={
                    "title": item["title"],
                    "chapter_type": item["chapter_type"],
                    "content": item["content"],
                    "estimated_minutes": item["estimated_minutes"],
                    "video_url": item["video_url"],
                },
            )
            chapter_map[item["order"]] = chapter

        quiz_chapter = chapter_map[5]
        quiz, _ = Quiz.objects.update_or_create(
            chapter=quiz_chapter,
            defaults={
                "title": "Engineering Surveying Fundamentals Quiz",
                "description": "Assessment on fundamentals of surveying concepts and calculations.",
                "pass_score": 70,
                "time_limit_minutes": 30,
                "attempts_allowed": 2,
                "shuffle_questions": True,
                "show_answers_after_submit": True,
            },
        )

        for idx, q in enumerate(QUIZ_QUESTIONS, start=1):
            Question.objects.update_or_create(
                quiz=quiz,
                order=idx,
                defaults={
                    "text": q["text"],
                    "question_type": q["question_type"],
                    "options": q["options"],
                    "correct_answer": q["correct_answer"],
                    "points": q["points"],
                },
            )

        Assignment.objects.update_or_create(
            course=course,
            title="Field Survey Practical - Campus Building Layout",
            defaults={
                "chapter": chapter_map[4],
                "description": (
                    "Conduct a closed traverse survey around a designated building and produce a scaled map. "
                    "Include field observations, calculations, closure adjustment, area calculation, and reporting."
                ),
                "assignment_type": "individual",
                "due_date": timezone.now() + timedelta(days=14),
                "soft_deadline": timezone.now() + timedelta(days=17),
                "late_penalty_percent": 10,
                "total_points": 100,
                "rubric": {
                    "criteria": [
                        {"name": "Field data accuracy", "max_score": 30},
                        {"name": "Calculations correctness", "max_score": 30},
                        {"name": "Map quality", "max_score": 20},
                        {"name": "Report quality", "max_score": 20},
                    ]
                },
                "enable_plagiarism_check": True,
                "max_file_size_mb": 50,
                "allowed_file_types": ".pdf,.doc,.docx,.txt",
            },
        )

        self.stdout.write(self.style.SUCCESS("Engineering Surveying sample materials seeded successfully."))
        self.stdout.write(self.style.SUCCESS(f"Course: {course.code} - {course.title}"))
