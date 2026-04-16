# lms/models/phase2b_adaptive.py
"""
Phase 2B: Advanced Adaptive Learning - Deep Knowledge Tracing & Personalization Services
Extends Phase 2A with sophisticated recommendation algorithms and mastery tracking
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta
import json


class DKTModel(models.Model):
    """
    Deep Knowledge Tracing Parameters per student-concept pair
    Tracks hidden knowledge state using Bayesian networks
    """
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='dkt_models')
    concept = models.ForeignKey('KnowledgeConcept', on_delete=models.CASCADE, related_name='dkt_models')
    
    # Hidden knowledge state (0-1: probability student knows concept)
    knowledge_state = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Bayesian estimate: P(knows concept)"
    )
    
    # Slip probability - P(wrong | student knows)
    slip = models.FloatField(
        default=0.1,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability student makes mistake despite knowing"
    )
    
    # Guess probability - P(right | student doesn't know)
    guess = models.FloatField(
        default=0.25,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability student guesses correctly"
    )
    
    # Learning rate - P(learns | doesn't know)
    learn = models.FloatField(
        default=0.25,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability student learns from attempt"
    )
    
    # Forget rate - P(forgets | knows)
    forget = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability student forgets material over time"
    )
    
    # Attempt tracking
    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    
    # Last update
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['student', 'concept']]
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['student', 'concept']),
            models.Index(fields=['knowledge_state']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.concept.name} (P(K)={self.knowledge_state:.2f})"
    
    @property
    def mastery_threshold(self):
        """Student is considered to have mastered if knowledge_state >= 0.95"""
        return self.knowledge_state >= 0.95
    
    def update_dkt(self, correct: bool):
        """
        Bayesian update of knowledge state based on attempt result
        Uses BKT (Bayesian Knowledge Tracing) algorithm
        """
        self.total_attempts += 1
        
        if correct:
            self.correct_attempts += 1
            # P(L|X_t, K_t) = P(X_t|L) * P(K_t) / P(X_t)
            numerator = (1 - self.slip) * self.knowledge_state + self.guess * (1 - self.knowledge_state)
            self.knowledge_state = numerator
        else:
            # P(L|X_t, K_t) = P(X_t|L) * P(K_t) / P(X_t)
            numerator = self.slip * self.knowledge_state + (1 - self.guess) * (1 - self.knowledge_state)
            self.knowledge_state = numerator
        
        # Update knowledge with learning rate
        self.knowledge_state = self.knowledge_state + (1 - self.knowledge_state) * self.learn
        self.save()


class LearnerProfile(models.Model):
    """
    Comprehensive learner profile capturing learning style, pace, preferences
    """
    LEARNING_STYLE_CHOICES = (
        ('visual', 'Visual Learner'),
        ('auditory', 'Auditory Learner'),
        ('kinesthetic', 'Kinesthetic Learner'),
        ('mixed', 'Mixed Learning Style'),
    )
    
    PACE_CHOICES = (
        ('slow', 'Slow Learner'),
        ('moderate', 'Moderate Pace'),
        ('fast', 'Fast Learner'),
        ('variable', 'Variable Pace'),
    )
    
    student = models.OneToOneField('User', on_delete=models.CASCADE, related_name='learner_profile')
    
    # Learning characteristics
    learning_style = models.CharField(max_length=20, choices=LEARNING_STYLE_CHOICES, default='mixed')
    preferred_pace = models.CharField(max_length=20, choices=PACE_CHOICES, default='moderate')
    
    # Time preferences
    preferred_study_hours = models.JSONField(
        default=dict,
        help_text="e.g., {'monday': ['09:00-11:00', '14:00-16:00']}"
    )
    preferred_session_length_minutes = models.PositiveIntegerField(default=60)
    
    # Content preferences
    prefers_video = models.BooleanField(default=True)
    prefers_text = models.BooleanField(default=True)
    prefers_interactive = models.BooleanField(default=True)
    
    # Difficulty preference
    prefer_challenging = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile: {self.student.username}"


class RecommendationEngine(models.Model):
    """
    Stores recommendation algorithm parameters and historical recommendations
    """
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='recommendation_engines')
    
    # Algorithm weights
    dkt_weight = models.FloatField(default=0.4, help_text="Weight for DKT predictions")
    collaboration_weight = models.FloatField(default=0.2, help_text="Weight for peer recommendations")
    content_weight = models.FloatField(default=0.2, help_text="Weight for content similarity")
    diversity_weight = models.FloatField(default=0.2, help_text="Weight for content diversity")
    
    # Personalization parameters
    exploration_vs_exploitation = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Epsilon-greedy parameter: 0=exploit, 1=explore"
    )
    
    # Last update
    last_trained = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['student']]
    
    def __str__(self):
        return f"Recommender: {self.student.username}"
    
    @property
    def is_stale(self):
        """Recommender needs retraining if not updated in 7 days"""
        if not self.last_trained:
            return True
        return (datetime.now() - self.last_trained).days > 7


class PeerInfluence(models.Model):
    """
    Captures peer learning dynamics and collaboration patterns
    """
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='peer_influences_as_student')
    peer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='peer_influences_as_peer')
    concept = models.ForeignKey('KnowledgeConcept', on_delete=models.CASCADE, related_name='peer_influences')
    
    # Similarity metrics
    mastery_similarity = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How similar are their mastery levels? (1=identical)"
    )
    
    # Interaction frequency
    collaboration_count = models.PositiveIntegerField(default=0)
    last_collaborated = models.DateTimeField(null=True, blank=True)
    
    # Influence score (0-1: how much peer helps learning)
    influence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    class Meta:
        unique_together = [['student', 'peer', 'concept']]
        indexes = [
            models.Index(fields=['student', 'concept']),
            models.Index(fields=['influence_score']),
        ]
    
    def __str__(self):
        return f"{self.student.username} ← {self.peer.username} ({self.concept.name})"


class SequenceRecommendation(models.Model):
    """
    Recommended lesson sequence for optimal learning path
    Generated by adaptive algorithms based on DKT state
    """
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sequence_recommendations')
    goal = models.ForeignKey('LearningGoal', on_delete=models.CASCADE, related_name='sequence_recommendations', null=True, blank=True)
    
    # Sequence metadata
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Lessons in sequence (ordered list)
    lesson_sequence = models.JSONField(
        help_text="List of lesson IDs in recommended order: [{'id': 1, 'reason': 'prerequisite'}, ...]"
    )
    
    # Confidence in recommendation
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How confident is the algorithm in this sequence?"
    )
    
    # Algorithm used
    algorithm = models.CharField(
        max_length=50,
        default='dkt_collaborative',
        help_text="e.g., 'dkt_only', 'collaborative', 'hybrid'"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    completion_status = models.CharField(
        max_length=20,
        default='not_started',
        choices=(
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('abandoned', 'Abandoned'),
        )
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['completion_status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.title}"


class LearningPathVariable(models.Model):
    """
    Individual variable tracking within a learning path
    Captures temporal aspects of learning
    """
    learning_path = models.ForeignKey('LearningPath', on_delete=models.CASCADE, related_name='variables')
    
    # Variable name and type
    name = models.CharField(max_length=100)
    variable_type = models.CharField(
        max_length=50,
        choices=(
            ('mastery', 'Mastery Level'),
            ('engagement', 'Engagement'),
            ('pace', 'Learning Pace'),
            ('retention', 'Information Retention'),
            ('confidence', 'Student Confidence'),
        )
    )
    
    # Current value and history
    current_value = models.FloatField()
    value_history = models.JSONField(
        default=list,
        help_text="List of historical values: [{'value': 0.8, 'timestamp': '2026-04-15T10:00:00'}]"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['learning_path', 'name']]
    
    def __str__(self):
        return f"{self.learning_path.title} - {self.name}"
    
    def add_value(self, value: float):
        """Add new value to history"""
        self.value_history.append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        self.current_value = value
        self.save()


class InterventionStrategy(models.Model):
    """
    Intervention strategies triggered when student struggles
    """
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='intervention_strategies')
    concept = models.ForeignKey('KnowledgeConcept', on_delete=models.CASCADE, related_name='intervention_strategies')
    
    # Intervention details
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Type of intervention
    intervention_type = models.CharField(
        max_length=50,
        choices=(
            ('simplify', 'Simplify Content'),
            ('video_explanation', 'Additional Video'),
            ('peer_help', 'Peer Tutoring'),
            ('practice', 'Extra Practice'),
            ('interactive', 'Interactive Activity'),
            ('feedback', 'Detailed Feedback'),
        )
    )
    
    # Recommended actions
    recommended_actions = models.JSONField(
        help_text="List of recommended actions: [{'action': 'show_video', 'video_id': 123}, ...]"
    )
    
    # Trigger condition
    trigger_threshold = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Trigger when mastery drops below this (e.g., 0.3)"
    )
    
    # Tracking
    triggered_count = models.PositiveIntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    effectiveness_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How effective was this intervention? (0-1)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['student', 'concept', 'intervention_type']]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.name}"


class StudentCohort(models.Model):
    """
    Groups students with similar learning patterns for collaborative learning
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Cohort criteria
    criteria = models.JSONField(
        help_text="Grouping criteria: {'learning_style': 'visual', 'pace': 'moderate'}"
    )
    
    # Members
    members = models.ManyToManyField('User', related_name='student_cohorts')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.members.count()
