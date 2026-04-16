# lms/models/phase2_adaptive.py
"""
Phase 2B: Adaptive Learning – Student Mastery Tracking & Personalized Paths
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class KnowledgeConcept(models.Model):
    """Fine-grained learning concepts within a course"""
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='concepts')
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Knowledge relationships
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        help_text="Concepts that should be mastered first"
    )
    
    # Difficulty level
    difficulty = models.FloatField(
        default=0.5,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)
        ],
        help_text="0 (easy) to 1 (very hard)"
    )
    
    # Time estimate
    estimated_learning_time = models.IntegerField(
        default=30,
        help_text="Minutes to master this concept"
    )
    
    # AI embeddings for semantic similarity (for content recommendation)
    embedding_vector = models.JSONField(
        default=list,
        help_text="768-dimensional embedding for semantic search"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'name']
    
    def __str__(self):
        return f"{self.course.title} - {self.name}"


class ConceptLessonMapping(models.Model):
    """Map lessons to specific knowledge concepts"""
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='concepts')
    concept = models.ForeignKey(KnowledgeConcept, on_delete=models.CASCADE)
    
    # Importance: how critical is this concept to the lesson
    weight = models.FloatField(
        default=1.0,
        help_text="Importance weight (0-1)"
    )
    
    # Coverage: how much of lesson is about this concept
    coverage_percentage = models.FloatField(
        default=100.0,
        help_text="Lesson coverage of this concept"
    )
    
    class Meta:
        unique_together = [['lesson', 'concept']]
    
    def __str__(self):
        return f"{self.lesson.title} < > {self.concept.name}"


class StudentMastery(models.Model):
    """Track student mastery of each concept"""
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='mastery')
    concept = models.ForeignKey(KnowledgeConcept, on_delete=models.CASCADE)
    
    # Mastery level (0-100)
    mastery_score = models.FloatField(
        default=0.0,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(100.0)
        ]
    )
    
    # DKT State (Deep Knowledge Tracing)
    # 3 components: Knowledge, Slip, Guess
    knowledge_state = models.FloatField(default=0.0)  # Actual knowledge 0-1
    slip_probability = models.FloatField(default=0.1)  # P(wrong | knows)
    guess_probability = models.FloatField(default=0.2)  # P(right | doesn't know)
    
    # Engagement metrics
    attempts_count = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    
    # Time
    time_spent_minutes = models.PositiveIntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    
    # Forgetting curve
    forgetting_curve = models.JSONField(
        default=list,
        help_text="Time-series of mastery decay: [{days_elapsed, score}]"
    )
    
    class Meta:
        unique_together = [['student', 'concept']]
        indexes = [
            models.Index(fields=['student', 'mastery_score']),
            models.Index(fields=['concept']),
        ]
    
    def __str__(self):
        return f"{self.student.username} mastery of {self.concept.name}: {self.mastery_score:.1f}%"
    
    @property
    def is_mastered(self):
        """Consider concept mastered at 80%+ on knowledge_state"""
        return self.knowledge_state >= 0.8
    
    @property
    def needs_review(self):
        """Needs review if not practiced in 7 days"""
        from django.utils import timezone
        from datetime import timedelta
        return (timezone.now() - self.last_attempt) > timedelta(days=7)


class ItemResponseTheory(models.Model):
    """IRT parameters for adaptive difficulty"""
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='irt')
    
    # IRT parameters
    difficulty = models.FloatField(
        default=0.0,
        help_text="Item difficulty parameter (b)"
    )
    discrimination = models.FloatField(
        default=1.0,
        help_text="Item discrimination parameter (a)"
    )
    guessing = models.FloatField(
        default=0.2,
        help_text="Guessing parameter (c)"
    )
    
    # Calibration
    sample_size = models.IntegerField(default=0)
    is_calibrated = models.BooleanField(default=False)
    calibrated_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"IRT: {self.question.text[:50]}"


class AdaptivePath(models.Model):
    """Dynamic learning path based on student performance"""
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='adaptive_paths')
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    
    # Current status
    current_lesson = models.ForeignKey(
        'Lesson',
        null=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    
    # Recommendations
    recommended_next = models.ForeignKey(
        'Lesson',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="AI-recommended next lesson"
    )
    
    # Personalization
    remediation_lessons = models.JSONField(
        default=list,
        help_text="Lesson IDs for struggling students"
    )
    acceleration_lessons = models.JSONField(
        default=list,
        help_text="Advanced lessons for fast learners"
    )
    
    # Difficulty adjustment
    adaptive_difficulty = models.FloatField(
        default=0.5,
        help_text="0 (easy) to 1 (hard) - adjusts quiz difficulty"
    )
    
    # Performance prediction
    predicted_completion_date = models.DateField(null=True, blank=True)
    predicted_final_grade = models.FloatField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['student', 'course']]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} adaptive path"


class ConceptQuizSequence(models.Model):
    """Adaptive quiz sequencing based on mastery"""
    student = models.ForeignKey('User', on_delete=models.CASCADE)
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE)
    
    # Sequencing strategy
    strategy = models.CharField(
        max_length=50,
        choices=[
            ('linear', 'Linear - Fixed Order'),
            ('adaptive_difficulty', 'Adaptive Difficulty'),
            ('concept_based', 'Concept Mastery Based'),
            ('irt', 'Item Response Theory'),
        ],
        default='adaptive_difficulty'
    )
    
    # Question pool
    question_pool = models.JSONField(default=list)  # Available question IDs
    completed_questions = models.JSONField(default=list)  # Answered question IDs
    
    # Current status
    estimated_ability = models.FloatField(default=0.0)  # On IRT scale
    next_question_difficulty = models.FloatField(default=0.5)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} adaptive"


# Recommendation Engine

class ContentRecommendation(models.Model):
    """AI-powered content recommendations"""
    RECOMMENDATION_REASONS = (
        ('weakness', 'Address Known Weakness'),
        ('strength', 'Build on Strength'),
        ('prerequisite', 'Prerequisites for next topic'),
        ('similar_content', 'Similar to liked content'),
        ('trending', 'Trending in your cohort'),
        ('peer_review', 'Recommended by peers'),
    )
    
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='recommendations')
    recommended_lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=RECOMMENDATION_REASONS)
    
    # AI metrics
    confidence = models.FloatField(
        default=0.0,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)
        ],
        help_text="1 = very confident, 0 = not confident"
    )
    relevance_score = models.FloatField(default=0.0)
    
    # Tracking
    is_viewed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    was_helpful = models.BooleanField(null=True, default=None)
    
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-confidence', '-created_at']
    
    def __str__(self):
        return f"Rec: {self.student.username} - {self.recommended_lesson.title} ({self.get_reason_display()})"


class RelatedContent(models.Model):
    """Manually or automatically related content"""
    RELATION_TYPES = (
        ('prerequisite', 'Prerequisite - Must Learn First'),
        ('follow_up', 'Follow-up - Learn Next'),
        ('supplemental', 'Supplemental - Optional Extra Content'),
        ('alternative', 'Alternative Explanation'),
        ('deep_dive', 'Deep Dive - Advanced Version'),
        ('remedial', 'Remedial - Extra Help'),
    )
    
    source_lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name='related_from'
    )
    target_lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name='related_to'
    )
    relation_type = models.CharField(max_length=50, choices=RELATION_TYPES)
    
    # Auto vs manual
    is_auto_generated = models.BooleanField(default=False)
    confidence = models.FloatField(
        default=1.0,
        help_text="Confidence of relationship (for auto-generated)"
    )
    
    # Metadata
    description = models.TextField(blank=True)
    suggested_position = models.CharField(
        max_length=50,
        choices=[('before', 'Before'), ('after', 'After'), ('alongside', 'Alongside')],
        default='after'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['source_lesson', 'target_lesson']]
    
    def __str__(self):
        return f"{self.source_lesson.title} -{self.get_relation_type_display()}-> {self.target_lesson.title}"


# Learning Goals

class LearningGoal(models.Model):
    """Student-set learning goals"""
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='learning_goals')
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    
    # Goal definition
    goal_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_grade = models.FloatField(
        default=80.0,
        help_text="Target grade (0-100)"
    )
    
    # Timeline
    target_completion_date = models.DateField()
    weeks_available = models.IntegerField(default=12, help_text="Weeks left to complete goal")  # Calculated
    
    # Weekly commitment
    weekly_hours_target = models.FloatField(
        default=5.0,
        help_text="Target hours per week"
    )
    actual_weekly_hours = models.JSONField(
        default=list,
        help_text="Weekly tracking: [{week_start, hours}]"
    )
    
    # Progress
    is_achieved = models.BooleanField(default=False)
    current_progress = models.FloatField(default=0.0)  # 0-100
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.goal_title}"
    
    @property
    def is_on_track(self):
        """Check if student is on track to achieve goal"""
        from django.utils import timezone
        import math
        
        days_remaining = (self.target_completion_date - timezone.now().date()).days
        if days_remaining <= 0:
            return self.current_progress >= self.target_grade
        
        # Calculate daily progress needed
        progress_needed = self.target_grade - self.current_progress
        daily_progress_needed = progress_needed / days_remaining
        
        # Rough estimate: 1% progress per hour at recommended pace
        hours_needed = progress_needed
        hours_available = days_remaining / 7 * self.weekly_hours_target
        
        return hours_available >= hours_needed
