# lms/models/__init__.py
"""
LMS Models Package
Organizes models into: base (Phase 1), phase2_hierarchy, phase2_adaptive, phase2b_adaptive, phase2c_assessments
"""

# Helper functions from base.py
from .base import (
    generate_certificate_id,
    validate_json_structure,
)

# Phase 1: Core Models (base.py)
from .base import (
    User,
    Module,
    Course,
    Chapter,
    Quiz,
    Question,
    QuizAttempt,
    Assignment,
    Submission,
    Enrollment,
    EnrollmentRequest,
    Certificate,
    CourseReview,
    Notification,
    SystemLog,
    StudentProgress,
)

# Phase 2A: Course Hierarchy Models (phase2_hierarchy.py)
from .phase2_hierarchy import (
    CourseModule,
    Section,
    Lesson,
    LessonResource,
    Prerequisite,
    LearningPath,
    LearningPathEnrollment,
    ModuleProgress,
    LessonProgress,
    LessonNote,
)

# Phase 2A: Adaptive Learning Models (phase2_adaptive.py)
from .phase2_adaptive import (
    KnowledgeConcept,
    ConceptLessonMapping,
    StudentMastery,
    ItemResponseTheory,
    AdaptivePath,
    ConceptQuizSequence,
    ContentRecommendation,
    RelatedContent,
    LearningGoal,
)

# Phase 2B: Advanced Adaptive Learning with DKT (phase2b_adaptive.py)
from .phase2b_adaptive import (
    DKTModel,
    LearnerProfile,
    RecommendationEngine,
    PeerInfluence,
    SequenceRecommendation,
    LearningPathVariable,
    InterventionStrategy,
    StudentCohort,
)

# Phase 2C: Advanced Assessments (phase2c_assessments.py)
from .phase2c_assessments import (
    AdaptiveAssessment,
    AssessmentAttempt,
    AssessmentItem,
    ItemResponse,
    LearningAnalytics,
    PerformanceTrend,
    CourseAnalytics,
    CompetencyFramework,
    StudentCompetency,
)

__all__ = [
    # Helper functions
    'generate_certificate_id',
    'validate_json_structure',
    # Phase 1
    'User',
    'Department',
    'Course',
    'Chapter',
    'Quiz',
    'Question',
    'QuizAttempt',
    'Assignment',
    'Submission',
    'Enrollment',
    'EnrollmentRequest',
    'Certificate',
    'CourseReview',
    'Notification',
    'SystemLog',
    'StudentProgress',
    # Phase 2A Hierarchy
    'Module',
    'Section',
    'Lesson',
    'LessonResource',
    'Prerequisite',
    'LearningPath',
    'LearningPathEnrollment',
    'ModuleProgress',
    'LessonProgress',
    'LessonNote',
    # Phase 2A Adaptive
    'KnowledgeConcept',
    'ConceptLessonMapping',
    'StudentMastery',
    'ItemResponseTheory',
    'AdaptivePath',
    'ConceptQuizSequence',
    'ContentRecommendation',
    'RelatedContent',
    'LearningGoal',
    # Phase 2B Advanced Adaptive
    'DKTModel',
    'LearnerProfile',
    'RecommendationEngine',
    'PeerInfluence',
    'SequenceRecommendation',
    'LearningPathVariable',
    'InterventionStrategy',
    'StudentCohort',
    # Phase 2C Assessments
    'AdaptiveAssessment',
    'AssessmentAttempt',
    'AssessmentItem',
    'ItemResponse',
    'LearningAnalytics',
    'PerformanceTrend',
    'CourseAnalytics',
    'CompetencyFramework',
    'StudentCompetency',
]
