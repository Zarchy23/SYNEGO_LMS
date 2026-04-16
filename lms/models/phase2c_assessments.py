# lms/models/phase2c_assessments.py
"""
Phase 2C: Advanced Assessments - Adaptive Testing, Analytics & Reporting
Sophisticated assessment and analytics capabilities with Item Response Theory
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
import json


class AdaptiveAssessment(models.Model):
    """
    Adaptive assessment that adjusts difficulty based on student performance
    """
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='adaptive_assessments')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='adaptive_assessments')
    
    # Title and description
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Assessment settings
    min_difficulty = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Easiest difficulty level"
    )
    max_difficulty = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Hardest difficulty level"
    )
    starting_difficulty = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Adaptive parameters
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    max_questions = models.PositiveIntegerField(default=20)
    
    # Pass threshold
    pass_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Score needed to pass (0-1)"
    )
    
    # Mastery requirement
    mastery_threshold = models.FloatField(
        default=0.85,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Score indicating mastery (0-1)"
    )
    
    # Branching logic
    branching_enabled = models.BooleanField(default=True)
    
    # Content specifications
    concepts_covered = models.ManyToManyField('KnowledgeConcept', related_name='adaptive_assessments')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.lesson.title})"


class AssessmentAttempt(models.Model):
    """
    Individual student attempt at an adaptive assessment
    """
    assessment = models.ForeignKey('AdaptiveAssessment', on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='assessment_attempts')
    
    # Attempt tracking
    attempt_number = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    
    # Current state
    current_difficulty = models.FloatField(default=0.5)
    current_question_index = models.PositiveIntegerField(default=0)
    
    # Questions and answers
    questions_presented = models.JSONField(
        default=list,
        help_text="List of question IDs presented: [{'id': 1, 'difficulty': 0.5}, ...]"
    )
    answers_given = models.JSONField(
        default=dict,
        help_text="Student answers: {'question_id': {'answer': 'A', 'correct': True, 'time_ms': 5000}, ...}"
    )
    
    # Scoring
    raw_score = models.FloatField(default=0.0)
    ability_estimate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="IRT-based ability estimate (theta)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        default='in_progress',
        choices=(
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('abandoned', 'Abandoned'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        )
    )
    
    # Result
    score = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    passed = models.BooleanField(null=True)
    mastery_achieved = models.BooleanField(default=False)
    
    # Item Response Theory metrics
    irt_ability = models.FloatField(default=0.0, help_text="Student ability theta")
    irt_se = models.FloatField(default=1.0, help_text="Standard error of ability estimate")
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['student', 'assessment']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.assessment.title} (Attempt {self.attempt_number})"


class AssessmentItem(models.Model):
    """
    Individual assessment question with IRT parameters
    """
    assessment = models.ForeignKey('AdaptiveAssessment', on_delete=models.CASCADE, related_name='items')
    concept = models.ForeignKey('KnowledgeConcept', on_delete=models.CASCADE, related_name='assessment_items')
    
    # Item content
    question_text = models.TextField()
    item_type = models.CharField(
        max_length=20,
        default='multiple_choice',
        choices=(
            ('multiple_choice', 'Multiple Choice'),
            ('true_false', 'True/False'),
            ('short_answer', 'Short Answer'),
            ('matching', 'Matching'),
        )
    )
    
    # IRT Parameters (a=discrimination, b=difficulty, c=guessing)
    irt_discrimination = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(3.0)],
        help_text="IRT discrimination parameter (a): how well item differentiates"
    )
    irt_difficulty = models.FloatField(
        default=0.0,
        help_text="IRT difficulty parameter (b): difficulty on theta scale"
    )
    irt_guessing = models.FloatField(
        default=0.25,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="IRT guessing parameter (c): probability of guessing correctly"
    )
    
    # Item pool
    is_pool_item = models.BooleanField(default=False)
    pool_category = models.CharField(max_length=100, blank=True)
    
    # Metadata
    difficulty_level = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    time_estimate_seconds = models.PositiveIntegerField(default=60)
    
    # Performance tracking
    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['assessment', 'question_text']]
        indexes = [
            models.Index(fields=['concept']),
            models.Index(fields=['difficulty_level']),
        ]
    
    def __str__(self):
        return f"{self.question_text[:50]}... ({self.item_type})"
    
    @property
    def p_value(self):
        """Classical test theory: proportion of students answering correctly"""
        if self.total_attempts == 0:
            return 0
        return self.correct_attempts / self.total_attempts
    
    @property
    def discrimination_index(self):
        """CTT discrimination index"""
        if self.total_attempts < 2:
            return 0
        # Simplified: could be enhanced with high/low group comparison
        return (self.p_value - 0.5) * 2  # -1 to 1 scale


class ItemResponse(models.Model):
    """
    Individual item response from student during assessment attempt
    Used for IRT calibration and item analysis
    """
    attempt = models.ForeignKey('AssessmentAttempt', on_delete=models.CASCADE, related_name='item_responses')
    item = models.ForeignKey('AssessmentItem', on_delete=models.CASCADE, related_name='responses')
    
    # Response
    answer_text = models.TextField()
    is_correct = models.BooleanField()
    
    # Timing
    response_time_ms = models.PositiveIntegerField(default=0)
    time_to_first_keystroke = models.PositiveIntegerField(null=True, blank=True)
    
    # Item response theory
    ability_before = models.FloatField(
        default=0.0,
        help_text="Student ability estimate before this item"
    )
    ability_after = models.FloatField(
        default=0.0,
        help_text="Student ability estimate after this item"
    )
    information_gained = models.FloatField(
        default=0.0,
        help_text="Fisher information gained from this item"
    )
    
    # Confidence
    student_confidence = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Student confidence (1-5)"
    )
    
    order = models.PositiveIntegerField(help_text="Order presented in attempt")
    
    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['attempt', 'item']),
            models.Index(fields=['is_correct']),
        ]
    
    def __str__(self):
        return f"{self.attempt.student.username} - Item {self.item.id} - {'Correct' if self.is_correct else 'Incorrect'}"


class LearningAnalytics(models.Model):
    """
    Comprehensive analytics for a student's learning journey
    Updated periodically from assessment and progress data
    """
    student = models.OneToOneField('User', on_delete=models.CASCADE, related_name='learning_analytics')
    
    # Overall metrics
    total_assessments = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    highest_score = models.FloatField(default=0.0)
    lowest_score = models.FloatField(default=0.0)
    
    # Time metrics
    total_time_minutes = models.PositiveIntegerField(default=0)
    average_session_length = models.PositiveIntegerField(default=0)  # minutes
    
    # Engagement
    concepts_studied = models.PositiveIntegerField(default=0)
    concepts_mastered = models.PositiveIntegerField(default=0)
    
    # Progress
    learning_velocity = models.FloatField(
        default=0.0,
        help_text="Rate of mastery gain (concepts/week)"
    )
    
    # Predictor: time to completion
    estimated_time_to_goal_completion_hours = models.FloatField(default=0.0)
    
    # Performance trajectory
    performance_trend = models.CharField(
        max_length=20,
        default='stable',
        choices=(
            ('improving', 'Improving'),
            ('stable', 'Stable'),
            ('declining', 'Declining'),
        )
    )
    
    # Risk indicators
    at_risk = models.BooleanField(default=False)
    risk_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="0=no risk, 1=highest risk"
    )
    
    # Engagement level
    engagement_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Learning efficiency
    learning_efficiency = models.FloatField(
        default=0.0,
        help_text="Score gained per hour of study"
    )
    
    # Last computed
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analytics: {self.student.username}"


class PerformanceTrend(models.Model):
    """
    Historical tracking of performance metrics for trend analysis
    """
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='performance_trends')
    
    # Timestamp
    recorded_date = models.DateField(auto_now_add=True)
    
    # Metrics snapshot
    average_score = models.FloatField()
    assessment_count = models.PositiveIntegerField()
    mastery_count = models.PositiveIntegerField()
    
    # Time metrics
    total_study_minutes = models.PositiveIntegerField()
    session_frequency = models.PositiveIntegerField(help_text="Sessions per week")
    
    # Engagement
    login_count = models.PositiveIntegerField()
    active_days = models.PositiveIntegerField()  # Days with activity
    
    # Predictive metrics
    risk_indicator = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    class Meta:
        ordering = ['recorded_date']
        unique_together = [['student', 'recorded_date']]
        indexes = [
            models.Index(fields=['student', 'recorded_date']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.recorded_date}"


class CourseAnalytics(models.Model):
    """
    Course-level analytics aggregated from student performance
    """
    course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='analytics')
    
    # Enrollment metrics
    total_enrollments = models.PositiveIntegerField(default=0)
    active_students = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Performance
    average_student_score = models.FloatField(default=0.0)
    median_student_score = models.FloatField(default=0.0)
    
    # Concepts difficulty analysis
    difficult_concepts = models.JSONField(
        default=list,
        help_text="Concepts with low mastery rates: [{'concept_id': 1, 'mastery_rate': 0.3}, ...]"
    )
    
    # Learning patterns
    average_time_to_completion_hours = models.FloatField(default=0.0)
    dropout_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Effectiveness
    course_effectiveness_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Composite effectiveness measure"
    )
    
    # Quality indicators
    learner_satisfaction = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics: {self.course.title}"


class CompetencyFramework(models.Model):
    """
    Defines competencies and their relationships for curriculum design
    """
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='competency_frameworks')
    
    # Competency definition
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Bloom's taxonomy level
    bloom_level = models.CharField(
        max_length=20,
        choices=(
            ('remember', 'Remember'),
            ('understand', 'Understand'),
            ('apply', 'Apply'),
            ('analyze', 'Analyze'),
            ('evaluate', 'Evaluate'),
            ('create', 'Create'),
        )
    )
    
    # Competency mapping
    related_concepts = models.ManyToManyField('KnowledgeConcept', related_name='competencies')
    
    # Mastery definition
    proficiency_levels = models.JSONField(
        help_text="Proficiency levels: [{'level': 'beginner', 'threshold': 0.3}, {'level': 'proficient', 'threshold': 0.7}, ...]"
    )
    
    # Assessment criteria
    assessment_criteria = models.TextField(help_text="How competency will be assessed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['course', 'name']]
    
    def __str__(self):
        return f"{self.course.title} - {self.name}"


class StudentCompetency(models.Model):
    """
    Track student's competency level across framework
    """
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='student_competencies')
    competency = models.ForeignKey('CompetencyFramework', on_delete=models.CASCADE, related_name='student_competencies')
    
    # Level
    proficiency_level = models.CharField(max_length=50)
    proficiency_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Validation
    evidenced_by = models.JSONField(
        help_text="Evidence of competency: [{'type': 'assessment_id', 'score': 0.9, 'date': '2026-04-15'}, ...]"
    )
    
    # Timeline
    first_demonstrated = models.DateField()
    last_demonstrated = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['student', 'competency']]
    
    def __str__(self):
        return f"{self.student.username} - {self.competency.name} ({self.proficiency_level})"
