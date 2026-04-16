# PHASE 2B IMPLEMENTATION GUIDE

## Overview
Phase 2B adds Deep Knowledge Tracing (DKT), sophisticated personalization, and advanced recommendation algorithms to Synego LMS. Students receive personalized learning paths, interventions tailored to their learning patterns, and recommendations based on their mastery state and peer learning dynamics.

**Timeline:** Weeks 3-4  
**Models:** 8 new models (147 fields) + Phase 2A foundation  
**Features:** DKT algorithm, personalized paths, peer learning, intervention strategies  

---

## Models Overview

### 1. **DKTModel**
Implements Bayesian Knowledge Tracing (BKT) per student-concept pair.

**Key Fields:**
- `knowledge_state` (0-1): Hidden knowledge probability
- `slip` (0-1): P(wrong | knows)
- `guess` (0-1): P(right | doesn't know)
- `learn` (0-1): P(learns from attempt)
- `forget` (0-1): P(forgets over time)
- `total_attempts`, `correct_attempts`: Attempt tracking

**Methods:**
```python
dkt.update_dkt(correct: bool)
# Updates knowledge_state using Bayesian algorithm
```

### 2. **LearnerProfile**
Comprehensive learner modeling capturing learning style and preferences.

**Key Fields:**
- `learning_style`: visual|auditory|kinesthetic|mixed
- `preferred_pace`: slow|moderate|fast|variable
- `preferred_study_hours`: JSONField with time preferences
- Content preferences: `prefers_video`, `prefers_text`, `prefers_interactive`

### 3. **RecommendationEngine**
Configurable algorithm weights for personalized recommendations.

**Key Fields:**
- Algorithm weights: `dkt_weight`, `collaboration_weight`, `content_weight`, `diversity_weight`
- `exploration_vs_exploitation`: Epsilon-greedy parameter (0=exploit, 1=explore)
- `last_trained`: Retraining trigger

### 4. **PeerInfluence**
Captures peer learning dynamics and collaboration patterns.

**Key Fields:**
- `mastery_similarity` (0-1): How similar their mastery levels
- `influence_score` (0-1): How much peer helps learning
- `collaboration_count`: Interaction frequency
- `last_collaborated`: Timestamp

### 5. **SequenceRecommendation**
Recommended lesson sequence for optimal learning path.

**Key Fields:**
- `lesson_sequence`: JSONField with ordered lesson IDs
- `confidence_score` (0-1): Algorithm confidence
- `algorithm`: e.g., 'dkt_only', 'collaborative', 'hybrid'
- `completion_status`: not_started|in_progress|completed|abandoned

### 6. **LearningPathVariable**
Individual variable tracking within learning paths (for analytics).

**Key Fields:**
- `variable_type`: mastery|engagement|pace|retention|confidence
- `current_value`: Current metric value
- `value_history`: JSONField with temporal tracking

### 7. **InterventionStrategy**
Triggered interventions when students struggle.

**Key Fields:**
- `intervention_type`: simplify|video_explanation|peer_help|practice|interactive|feedback
- `trigger_threshold` (0-1): When to trigger
- `effectiveness_score` (0-1): How effective was intervention
- `recommended_actions`: JSONField with action list

### 8. **StudentCohort**
Groups students with similar learning patterns.

**Key Fields:**
- `criteria`: JSONField with grouping criteria
- `members`: M2M relationship with Users

---

## Implementation Steps

### Step 1: Understand DKT Algorithm
The BKT update formula:
```
P(K_{t+1}) = P(K_t) + (1 - P(K_t)) * L

Where:
- P(K_t) = prior knowledge probability
- L = P(learns | doesn't know) = learn parameter
- If correct: P(K_t) is updated with (1-slip) * P(K_t) + guess * (1-P(K_t))
- If wrong: P(K_t) is updated with slip * P(K_t) + (1-guess) * (1-P(K_t))
```

### Step 2: Create DKT Service Layer

**File:** `lms/services/dkt_service.py`

```python
from lms.models import DKTModel, StudentMastery, AssessmentAttempt, ItemResponse

class DKTService:
    """Service for Deep Knowledge Tracing"""
    
    @staticmethod
    def initialize_dkt_for_student_concept(student, concept):
        """Initialize DKT for new student-concept pair"""
        dkt, created = DKTModel.objects.get_or_create(
            student=student,
            concept=concept,
            defaults={
                'knowledge_state': 0.0,
                'slip': 0.1,
                'guess': 0.25,
                'learn': 0.25,
                'forget': 0.0
            }
        )
        return dkt
    
    @staticmethod
    def update_from_assessment(attempt: 'AssessmentAttempt'):
        """Update DKT from assessment attempt results"""
        for item_response in attempt.item_responses.all():
            concept = item_response.item.concept
            dkt = DKTService.initialize_dkt_for_student_concept(
                attempt.student, concept
            )
            dkt.update_dkt(correct=item_response.is_correct)
            # Update StudentMastery with new knowledge state
            mastery, _ = StudentMastery.objects.get_or_create(
                student=attempt.student,
                concept=concept
            )
            mastery.knowledge_state = dkt.knowledge_state
            mastery.save()
```

### Step 3: Create Personalization Service

**File:** `lms/services/personalization_service.py`

```python
from lms.models import (
    LearnerProfile, RecommendationEngine, DKTModel, 
    PeerInfluence, SequenceRecommendation
)

class PersonalizationService:
    """Service for personalized recommendations"""
    
    @staticmethod
    def get_or_create_learner_profile(student):
        """Get or create learner profile"""
        profile, created = LearnerProfile.objects.get_or_create(
            student=student
        )
        return profile
    
    @staticmethod
    def recommend_sequence(student, concepts, algorithm='hybrid'):
        """Generate personalized lesson sequence"""
        # 1. Get student's DKT state
        dkt_scores = DKTModel.objects.filter(
            student=student, concept__in=concepts
        ).values()
        
        # 2. Get collaborative data (similar peers)
        peers = PeerInfluence.objects.filter(
            student=student
        ).order_by('-influence_score')[:10]
        
        # 3. Generate sequence based on gaps and prerequisites
        sequence = []
        for concept in sorted(concepts, key=lambda c: dkt_scores.get(concept, 0.0)):
            lessons = concept.lessons.filter(is_active=True)
            for lesson in lessons:
                sequence.append({'id': lesson.id, 'reason': 'prerequisite'})
        
        # 4. Create recommendation record
        recommendation = SequenceRecommendation.objects.create(
            student=student,
            title=f"Personalized Path - {algorithm}",
            lesson_sequence=sequence,
            algorithm=algorithm,
            confidence_score=0.85
        )
        
        return recommendation
```

### Step 4: Create Intervention Service

**File:** `lms/services/intervention_service.py`

```python
class InterventionService:
    """Service for intelligent interventions"""
    
    @staticmethod
    def check_and_trigger_interventions(student):
        """Check if interventions need to be triggered"""
        from lms.models import DKTModel, InterventionStrategy
        
        # Get all DKT models where knowledge_state is below threshold
        dtks = DKTModel.objects.filter(
            student=student,
            knowledge_state__lt=0.3  # Struggling
        )
        
        for dkt in dtks:
            # Find relevant interventions
            strategies = InterventionStrategy.objects.filter(
                student=student,
                concept=dkt.concept,
                trigger_threshold__gte=dkt.knowledge_state
            )
            
            # Recommend highest-effectiveness intervention
            for strategy in strategies:
                strategy.triggered_count += 1
                strategy.last_triggered = now()
                strategy.save()
                # Would send notification to student
```

### Step 5: Database Design Considerations

**Indexes:**
- `DKTModel`: (student, concept), knowledge_state
- `PeerInfluence`: (student, concept), influence_score
- `SequenceRecommendation`: (student, is_active), completion_status
- `InterventionStrategy`: (student, concept, trigger_threshold)

**Queries to optimize:**
```python
# Get all struggling concepts
DKTModel.objects.filter(
    student=student,
    knowledge_state__lt=0.3
).select_related('concept')

# Get peer recommendations  
PeerInfluence.objects.filter(
    student=student,
    influence_score__gte=0.5
).select_related('peer', 'concept')
```

### Step 6: Admin Customization

In `lms/admin/phase2b_admin.py`:

```python
@admin.register(DKTModel)
class DKTModelAdmin(admin.ModelAdmin):
    list_display = ('student', 'concept', 'mastery_percentage', 'attempt_count', 'last_updated')
    list_filter = ('concept__course', 'mastery_threshold')
    search_fields = ('student__username', 'concept__name')
    readonly_fields = ('last_updated',)

@admin.register(SequenceRecommendation)
class SequenceRecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'algorithm', 'confidence_score', 'completion_status')
    list_filter = ('algorithm', 'completion_status')
    search_fields = ('student__username', 'title')
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_dkt.py
from django.test import TestCase
from lms.models import User, Course, KnowledgeConcept, DKTModel
from lms.services.dkt_service import DKTService

class DKTTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='test')
        self.course = Course.objects.create(title='Test Course')
        self.concept = KnowledgeConcept.objects.create(
            course=self.course, name='Algebra'
        )
    
    def test_dkt_initialization(self):
        dkt = DKTService.initialize_dkt_for_student_concept(
            self.student, self.concept
        )
        self.assertEqual(dkt.knowledge_state, 0.0)
        self.assertEqual(dkt.slip, 0.1)
    
    def test_dkt_update_correct(self):
        dkt = DKTService.initialize_dkt_for_student_concept(
            self.student, self.concept
        )
        initial_state = dkt.knowledge_state
        dkt.update_dkt(correct=True)
        self.assertGreater(dkt.knowledge_state, initial_state)
    
    def test_dkt_update_incorrect(self):
        dkt = DKTModel.objects.create(
            student=self.student,
            concept=self.concept,
            knowledge_state=0.8
        )
        initial_state = dkt.knowledge_state
        dkt.update_dkt(correct=False)
        self.assertLess(dkt.knowledge_state, initial_state)
```

---

## Performance Considerations

### 1. **Query Performance**
- Batch DKT updates in background tasks
- Cache learner profiles (TTL: 1 hour)
- Use `select_related()` for foreign keys

### 2. **Computation**
- Run recommendation generation as async tasks
- Batch process peer influence calculations
- Use Celery for background task queue

### 3. **Data Volume**
- Partition DKTModel table by student for large datasets
- Archive old InterventionStrategy records
- Aggregate PerformanceTrend data daily

---

## Deployment Checklist

- [ ] Database migrations applied
- [ ] DKT service tests passing
- [ ] Personalization service configured
- [ ] Intervention triggers tested
- [ ] Admin interface functional
- [ ] Performance benchmarks met (<100ms avg query)
- [ ] Background tasks scheduled
- [ ] Monitoring/alerts configured

---

## Next Phase (Phase 2C)

Phase 2C extends with advanced assessments, adaptive testing, and comprehensive analytics built on the DKT foundation.
