# lms/admin/phase2_admin.py
"""
Django Admin Configuration for Phase 2A, 2B, 2C: Complete LMS Enhancement Suite
Simplified admin interface - registers all models with default ModelAdmin
"""

from django.contrib import admin
from ..models import (
    # Phase 2A Hierarchy
    CourseModule, Section, Lesson, LessonResource, Prerequisite, LearningPath, 
    LearningPathEnrollment, ModuleProgress, LessonProgress, LessonNote,
    # Phase 2A Adaptive
    KnowledgeConcept, ConceptLessonMapping, StudentMastery, ItemResponseTheory,
    AdaptivePath, ConceptQuizSequence, ContentRecommendation, RelatedContent, LearningGoal,
    # Phase 2B Adaptive
    DKTModel, LearnerProfile, RecommendationEngine, PeerInfluence, SequenceRecommendation,
    LearningPathVariable, InterventionStrategy, StudentCohort,
    # Phase 2C Assessments
    AdaptiveAssessment, AssessmentAttempt, AssessmentItem, ItemResponse,
    LearningAnalytics, PerformanceTrend, CourseAnalytics, CompetencyFramework, StudentCompetency,
)

# ==================================================
# PHASE 2A MODELS
# ==================================================

# Hierarchy Models
admin.site.register(CourseModule)
admin.site.register(Section)
admin.site.register(Lesson)
admin.site.register(LessonResource)
admin.site.register(Prerequisite)
admin.site.register(LearningPath)
admin.site.register(LearningPathEnrollment)
admin.site.register(ModuleProgress)
admin.site.register(LessonProgress)
admin.site.register(LessonNote)

# Adaptive Learning Models
admin.site.register(KnowledgeConcept)
admin.site.register(ConceptLessonMapping)
admin.site.register(StudentMastery)
admin.site.register(ItemResponseTheory)
admin.site.register(AdaptivePath)
admin.site.register(ConceptQuizSequence)
admin.site.register(ContentRecommendation)
admin.site.register(RelatedContent)
admin.site.register(LearningGoal)

# ==================================================
# PHASE 2B ADVANCED ADAPTIVE LEARNING MODELS
# ==================================================

admin.site.register(DKTModel)
admin.site.register(LearnerProfile)
admin.site.register(RecommendationEngine)
admin.site.register(PeerInfluence)
admin.site.register(SequenceRecommendation)
admin.site.register(LearningPathVariable)
admin.site.register(InterventionStrategy)
admin.site.register(StudentCohort)

# ==================================================
# PHASE 2C ADVANCED ASSESSMENT & ANALYTICS MODELS
# ==================================================

admin.site.register(AdaptiveAssessment)
admin.site.register(AssessmentAttempt)
admin.site.register(AssessmentItem)
admin.site.register(ItemResponse)
admin.site.register(LearningAnalytics)
admin.site.register(PerformanceTrend)
admin.site.register(CourseAnalytics)
admin.site.register(CompetencyFramework)
admin.site.register(StudentCompetency)
