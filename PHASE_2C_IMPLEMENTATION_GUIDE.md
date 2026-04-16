# PHASE 2C IMPLEMENTATION GUIDE

## Overview
Phase 2C adds advanced adaptive assessment capabilities, Item Response Theory (IRT) calibration, comprehensive learning analytics, and competency-based frameworks. The system dynamically adjusts assessment difficulty, measures student ability with precision, and provides actionable analytics for instructors and students.

**Timeline:** Weeks 5-6  
**Models:** 9 new models (200+ fields) + Phase 2A & 2B foundation  
**Features:** Adaptive testing, IRT calibration, learning analytics, competency frameworks  

---

## Models Overview

### 1. **AdaptiveAssessment**
Adaptive assessment adjusts difficulty based on student performance.

**Key Fields:**
- `min_difficulty`, `max_difficulty`: Difficulty range
- `starting_difficulty`: Initial difficulty level
- `pass_threshold` (0-1): Passing score
- `mastery_threshold` (0-1): Mastery indicator
- `branching_enabled`: Enables IRT-based branching

### 2. **AssessmentAttempt**
Individual student attempt at adaptive assessment.

**Key Fields:**
- `current_difficulty`: Current difficulty level
- `current_question_index`: Question position
- `questions_presented`: JSONField with question IDs and parameters
- `irt_ability`: IRT theta (student ability estimate)
- `irt_se`: Standard error of ability estimate
- `ability_estimate` (0-1): IRT-based ability on 0-1 scale

### 3. **AssessmentItem**
Individual assessment question with IRT calibration parameters.

**Key Fields:**
- `irt_discrimination` (a): How well item differentiates
- `irt_difficulty` (b): Difficulty on theta scale
- `irt_guessing` (c): Probability of guessing correctly
- `p_value`: CTT proportion correct
- `discrimination_index`: CTT item discrimination

### 4. **ItemResponse**
Individual item response for IRT analysis and calibration.

**Key Fields:**
- `is_correct`: Boolean correctness
- `response_time_ms`: Time to answer
- `ability_before`, `ability_after`: IRT ability estimates
- `information_gained`: Fisher information
- `student_confidence` (1-5): Self-rated confidence

### 5. **LearningAnalytics**
Comprehensive student learning analytics.

**Key Fields:**
- Performance: `average_score`, `highest_score`, `lowest_score`
- Engagement: `concepts_studied`, `concepts_mastered`
- Progress: `learning_velocity` (concepts/week)
- Risk: `at_risk`, `risk_score` (0-1)
- Efficiency: `learning_efficiency` (score per hour)

### 6. **PerformanceTrend**
Historical tracking for trend analysis and predictions.

**Key Fields:**
- Snapshot metrics: `average_score`, `assessment_count`, `mastery_count`
- Engagement: `session_frequency`, `active_days`
- Predictive: `risk_indicator` (0-1)

### 7. **CourseAnalytics**
Course-level aggregated analytics.

**Key Fields:**
- `completion_rate`, `dropout_rate`: Course metrics
- `difficult_concepts`: JSONField with low-mastery concepts
- `course_effectiveness_score`: Composite measure
- `learner_satisfaction`: Rating feedback

### 8. **CompetencyFramework**
Defines competencies and Bloom's taxonomy levels.

**Key Fields:**
- `bloom_level`: remember|understand|apply|analyze|evaluate|create
- `proficiency_levels`: JSONField with level thresholds
- `assessment_criteria`: How competency is assessed
- `related_concepts`: M2M with KnowledgeConcept

### 9. **StudentCompetency**
Track student's progress on competency framework.

**Key Fields:**
- `proficiency_level`: Current level name
- `proficiency_score` (0-1): Score on competency
- `evidenced_by`: JSONField with assessment evidence
- `first_demonstrated`, `last_demonstrated`: Timeline

---

## IRT (Item Response Theory) Implementation

### Item Characteristic Curve (ICC)
```python
def irt_probability(theta, a, b, c):
    """
    3PL IRT model: P(correct | theta) = c + (1-c) / (1 + exp(-a*(theta-b)))
    
    Args:
        theta: Student ability (-4 to +4 scale, 0=average)
        a: Discrimination (how well item differentiates)
        b: Difficulty (higher b = harder)
        c: Guessing (lower asymptote)
    
    Returns:
        Probability of correct response (0-1)
    """
    import math
    numerator = 1 - c
    denominator = 1 + math.exp(-a * (theta - b))
    return c + numerator / denominator
```

### Fisher Information
```python
def fisher_information(theta, a, c):
    """
    Information gained from item: I(theta) = a^2 * (P*Q) / (1-c)^2
    """
    P = irt_probability(theta, a, b, c)
    Q = 1 - P
    return (a**2 * P * Q) / ((1 - c)**2)
```

### Ability Estimation
```python
def estimate_ability(responses, items):
    """
    Maximum Likelihood Estimation (MLE) of student ability
    Can use Newton-Raphson method for iteration
    """
    # Initial estimate
    theta = 0.0
    
    # Newton-Raphson iteration
    for iteration in range(10):
        # Calculate likelihood derivative and second derivative
        likelihood_derivative = 0
        second_derivative = 0
        
        for response, item in zip(responses, items):
            P = irt_probability(theta, item.irt_discrimination, 
                               item.irt_difficulty, item.irt_guessing)
            Q = 1 - P
            a = item.irt_discrimination
            
            # Update derivatives
            likelihood_derivative += a * (response - P) / (P * Q)
            second_derivative -= a**2 * P * Q
        
        # Update theta
        if abs(second_derivative) > 0.001:
            theta = theta - likelihood_derivative / second_derivative
    
    return theta
```

---

## Implementation Steps

### Step 1: Create Assessment Service

**File:** `lms/services/assessment_service.py`

```python
from lms.models import AdaptiveAssessment, AssessmentAttempt, AssessmentItem, ItemResponse
import math

class AssessmentService:
    """Service for adaptive assessment"""
    
    @staticmethod
    def create_adaptive_assessment(lesson, title, concepts):
        """Create adaptive assessment for lesson"""
        assessment = AdaptiveAssessment.objects.create(
            lesson=lesson,
            course=lesson.section.module.course,
            title=title,
            min_difficulty=0.0,
            max_difficulty=1.0,
            starting_difficulty=0.5,
            pass_threshold=0.7,
            mastery_threshold=0.85
        )
        assessment.concepts_covered.set(concepts)
        return assessment
    
    @staticmethod
    def start_attempt(assessment, student):
        """Start new assessment attempt"""
        attempt = AssessmentAttempt.objects.create(
            assessment=assessment,
            student=student,
            current_difficulty=assessment.starting_difficulty,
            irt_ability=0.0,  # Start at average
            irt_se=1.0  # Start with high uncertainty
        )
        return attempt
    
    @staticmethod
    def select_next_question(attempt):
        """Select next question using IRT-based adaptive selection"""
        # Get items near current theta for maximum information
        ability = attempt.irt_ability
        se = attempt.irt_se
        
        # Select item closest to estimated ability (maximum information)
        items = AssessmentItem.objects.filter(
            assessment=attempt.assessment,
            irt_difficulty__gte=ability-0.5,
            irt_difficulty__lte=ability+0.5
        ).exclude(
            id__in=[q['id'] for q in attempt.questions_presented]
        ).order_by('?').first()
        
        return items
    
    @staticmethod
    def record_response(attempt, item, is_correct, response_time_ms, confidence=None):
        """Record item response and update ability estimate"""
        # Create response record
        response = ItemResponse.objects.create(
            attempt=attempt,
            item=item,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            student_confidence=confidence,
            ability_before=attempt.irt_ability,
            order=len(attempt.item_responses.all())
        )
        
        # Update ability estimate using IRT
        responses = attempt.item_responses.all().order_by('order')
        items = [r.item for r in responses]
        response_values = [r.is_correct for r in responses]
        
        new_ability = AssessmentService._estimate_ability_mle(response_values, items)
        attempt.irt_ability = new_ability
        
        # Update SE using Fisher information
        total_information = sum(
            AssessmentService._fisher_information(
                new_ability, item.irt_discrimination, item.irt_guessing
            ) for item in items
        )
        attempt.irt_se = 1.0 / math.sqrt(max(total_information, 0.01))
        
        response.ability_after = new_ability
        response.information_gained = total_information
        response.save()
        
        attempt.save()
        return response
    
    @staticmethod
    def _irt_probability(theta, a, b, c):
        """3PL IRT probability function"""
        try:
            numerator = 1 - c
            denominator = 1 + math.exp(-a * (theta - b))
            return c + numerator / denominator
        except:
            return 0.5
    
    @staticmethod
    def _fisher_information(theta, a, c):
        """Fisher information function"""
        P = AssessmentService._irt_probability(theta, a, 0, c)
        Q = 1 - P
        try:
            return (a**2 * P * Q) / ((1 - c)**2)
        except:
            return 0.1
    
    @staticmethod
    def _estimate_ability_mle(responses, items, iterations=10):
        """Maximum Likelihood Estimation of ability"""
        theta = 0.0
        
        for _ in range(iterations):
            likelihood_deriv = 0.0
            second_deriv = 0.0
            
            for response, item in zip(responses, items):
                P = AssessmentService._irt_probability(
                    theta, item.irt_discrimination, 
                    item.irt_difficulty, item.irt_guessing
                )
                Q = 1 - P
                a = item.irt_discrimination
                
                if P > 0.001 and Q > 0.001:
                    likelihood_deriv += a * (response - P) / (P * Q)
                    second_deriv -= a**2 * P * Q
            
            if abs(second_deriv) > 0.001:
                delta = likelihood_deriv / (-second_deriv)
                if abs(delta) < 0.01:
                    break
                theta = theta + delta
        
        return max(-4, min(4, theta))  # Clamp to [-4, 4]
```

### Step 2: Create Analytics Service

**File:** `lms/services/analytics_service.py`

```python
from django.db.models import Avg, Count, Q
from lms.models import (
    LearningAnalytics, PerformanceTrend, CourseAnalytics,
    AssessmentAttempt, DKTModel
)
from datetime import date, timedelta

class AnalyticsService:
    """Service for learning analytics and reporting"""
    
    @staticmethod
    def compute_student_analytics(student):
        """Compute comprehensive analytics for student"""
        analytics, _ = LearningAnalytics.objects.get_or_create(
            student=student
        )
        
        # Assessment metrics
        attempts = AssessmentAttempt.objects.filter(
            student=student,
            status__in=['completed', 'passed', 'failed']
        )
        
        if attempts.exists():
            analytics.total_assessments = attempts.count()
            analytics.average_score = attempts.aggregate(
                avg=Avg('score')
            )['avg'] or 0.0
            analytics.highest_score = attempts.aggregate(
                max=Max('score')
            )['max'] or 0.0
            analytics.lowest_score = attempts.aggregate(
                min=Min('score')
            )['min'] or 0.0
            
            # Learning velocity
            dkt_models = DKTModel.objects.filter(student=student)
            analytics.concepts_studied = dkt_models.count()
            analytics.concepts_mastered = dkt_models.filter(
                knowledge_state__gte=0.95
            ).count()
            
            # Risk assessment
            avg_k = dkt_models.aggregate(
                avg=Avg('knowledge_state')
            )['avg'] or 0.0
            analytics.risk_score = max(0, 1 - avg_k)
            analytics.at_risk = analytics.risk_score > 0.5
            
            # Engagement
            analytics.engagement_score = min(0.7, avg_k)
        
        analytics.save()
        return analytics
    
    @staticmethod
    def record_performance_trend(student):
        """Record daily performance snapshot"""
        analytics = LearningAnalytics.objects.get(student=student)
        
        trend = PerformanceTrend.objects.create(
            student=student,
            average_score=analytics.average_score,
            assessment_count=analytics.total_assessments,
            mastery_count=analytics.concepts_mastered,
            total_study_minutes=analytics.total_time_minutes,
            session_frequency=7,  # Would calculate from actual data
            login_count=1,
            active_days=7,  # Simplified
            risk_indicator=analytics.risk_score
        )
        return trend
    
    @staticmethod
    def compute_course_analytics(course):
        """Compute analytics for entire course"""
        analytics, _ = CourseAnalytics.objects.get_or_create(course=course)
        
        enrollments = course.enrollments.all()
        if enrollments.exists():
            analytics.total_enrollments = enrollments.count()
            analytics.active_students = enrollments.filter(
                status='active'
            ).count()
            
            # Completion rate
            completed = enrollments.filter(status='completed').count()
            analytics.completion_rate = completed / enrollments.count()
            
            # Concept difficulty
            concepts = KnowledgeConcept.objects.filter(course=course)
            difficult = []
            for concept in concepts:
                mastery_rate = DKTModel.objects.filter(
                    concept=concept
                ).aggregate(avg=Avg('knowledge_state'))['avg'] or 0.0
                
                if mastery_rate < 0.6:
                    difficult.append({
                        'concept_id': concept.id,
                        'mastery_rate': mastery_rate
                    })
            
            analytics.difficult_concepts = difficult
            analytics.course_effectiveness_score = sum(
                m['mastery_rate'] for m in difficult
            ) / max(1, len(difficult))
        
        analytics.save()
        return analytics
```

### Step 3: Testing IRT Calibration

**File:** `tests/test_irt.py`

```python
import math
from django.test import TestCase
from lms.services.assessment_service import AssessmentService

class IRTTestCase(TestCase):
    def test_irt_probability_curve(self):
        """Test ICC at various theta values"""
        # At difficulty point, should be around (1+c)/2
        P = AssessmentService._irt_probability(theta=0, a=1, b=0, c=0.2)
        self.assertAlmostEqual(P, 0.6, delta=0.01)
    
    def test_fisher_information(self):
        """Test information function"""
        I = AssessmentService._fisher_information(theta=0, a=1, c=0.2)
        self.assertGreater(I, 0)
        
        # At extreme theta, information should be lower
        I_extreme = AssessmentService._fisher_information(theta=4, a=1, c=0.2)
        self.assertLess(I_extreme, I)
    
    def test_mle_ability_estimation(self):
        """Test ability estimation"""
        from lms.models import AssessmentItem, Course, KnowledgeConcept
        
        # Create test data
        course = Course.objects.create(title='Test')
        concept = KnowledgeConcept.objects.create(course=course, name='Test')
        
        item1 = AssessmentItem.objects.create(
            assessment_id=1, concept=concept,
            irt_discrimination=1.0, irt_difficulty=0.0, irt_guessing=0.2
        )
        item2 = AssessmentItem.objects.create(
            assessment_id=1, concept=concept,
            irt_discrimination=1.0, irt_difficulty=0.5, irt_guessing=0.2
        )
        
        # Estimate ability from responses
        responses = [True, True, False]  # Got first two right, last wrong
        items = [item1, item2, item1]
        theta = AssessmentService._estimate_ability_mle(responses, items)
        
        # Should estimate positive but moderate ability
        self.assertGreater(theta, 0)
        self.assertLess(theta, 1.5)
```

### Step 4: Data Volume Considerations

**Queries requiring optimization:**

```python
# Worst case: M students × C assessments × I items = M*C*I responses
# With M=1000, C=100, I=30: 3M records

# Optimize with indexes:
from django.db import models

class ItemResponse(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['attempt', 'item']),
            models.Index(fields=['attempt', 'is_correct']),
            models.Index(fields=['item']),
        ]
```

---

## Competency Framework Integration

```python
# Create competency framework
framework = CompetencyFramework.objects.create(
    course=course,
    name='Problem Solving',
    bloom_level='analyze',
    proficiency_levels=[
        {'level': 'beginner', 'threshold': 0.3},
        {'level': 'proficient', 'threshold': 0.7},
        {'level': 'expert', 'threshold': 0.9},
    ],
    assessment_criteria='Solves complex multi-step problems'
)

# Track student competency
competency = StudentCompetency.objects.create(
    student=student,
    competency=framework,
    proficiency_level='proficient',
    proficiency_score=0.75,
    first_demonstrated=date.today(),
    last_demonstrated=date.today(),
    evidenced_by=[
        {'type': 'assessment_id', 'score': 0.8, 'date': '2026-04-15'}
    ]
)
```

---

## Deployment Checklist

- [ ] IRT calibration tested and validated
- [ ] Item pool with IRT parameters created
- [ ] Assessment service unit tests passing
- [ ] Analytics computation verified
- [ ] Database indexes created
- [ ] Admin interfaces customized
- [ ] Performance benchmarks met (<200ms per response)
- [ ] Analytics reporting functional
- [ ] Competency framework defined
- [ ] Background task scheduling configured

---

## Phase 2D: Advanced Features (Future)

- VR/AR Assessment Integration
- Blockchain Credentials
- Advanced Predictive Analytics
- Microservices Architecture
