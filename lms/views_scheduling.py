# lms/views_scheduling.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
from django import forms
import calendar

from .models import (
    Course, ClassSession,
    SessionAttendance, CalendarEvent, CourseAdvertisement, CourseReminder,
    CourseIntake, IntakeEnrollment
)

User = get_user_model()

# ============================================================
# CALENDAR VIEWS
# ============================================================

@login_required
def calendar_view(request):
    """Interactive calendar showing all course schedules and events"""
    
    # Get current month/year
    today = timezone.now()
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)
    
    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = today.year
        month = today.month
    
    # Calculate calendar dates
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Get days in month
    days_in_month = last_day.day
    first_weekday = first_day.weekday()
    
    # Build calendar grid
    calendar_days = []
    week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Previous month days - calculate the last day of previous month
    if month > 1:
        prev_month_first = datetime(year, month - 1, 1)
    else:
        prev_month_first = datetime(year - 1, 12, 1)
    
    # Get the last day of previous month
    prev_month_last_date = prev_month_first.replace(day=1) - timedelta(days=1)
    prev_month_last_day = prev_month_last_date.day
    
    # Calculate which days from previous month to show
    prev_month_days_to_show = first_weekday
    start_day = prev_month_last_day - first_weekday + 1
    
    for day_num in range(start_day, prev_month_last_day + 1):
        cal_date = prev_month_last_date.replace(day=day_num)
        calendar_days.append({
            'date': cal_date,
            'current_month': False,
            'events': [],
            'is_today': False
        })
    
    # Current month days
    for day in range(1, days_in_month + 1):
        current_date = datetime(year, month, day)
        calendar_days.append({
            'date': current_date,
            'current_month': True,
            'events': [],
            'is_today': current_date.date() == today.date()
        })
    
    # Next month days - fill remaining grid slots
    remaining_days = 42 - len(calendar_days)
    # Get next month info using calendar.monthrange to determine correct month length
    if month < 12:
        next_month_year, next_month_num = year, month + 1
    else:
        next_month_year, next_month_num = year + 1, 1
    
    # Only add up to remaining days or days available in next month, whichever is smaller
    for day_num in range(1, min(remaining_days + 1, 32)):  # 31 is max days in any month
        try:
            cal_date = datetime(next_month_year, next_month_num, day_num)
            calendar_days.append({
                'date': cal_date,
                'current_month': False,
                'events': []
            })
        except ValueError:
            # Day doesn't exist in next month (e.g., Feb 30), stop adding
            break
    
    # Fetch events for the month range
    start_range = datetime(year, month, 1)
    if month < 12:
        end_range = datetime(year, month + 1, 1)
    else:
        end_range = datetime(year + 1, 1, 1)
    
    # Course intakes
    course_intakes = CourseIntake.objects.filter(
        Q(course_start_date__gte=start_range, course_start_date__lt=end_range) |
        Q(course_end_date__gte=start_range, course_end_date__lt=end_range),
        status__in=['open', 'upcoming', 'in_progress']
    ).select_related('course')
    
    # Calendar events
    calendar_events = CalendarEvent.objects.filter(
        Q(start_date__gte=start_range, start_date__lt=end_range) |
        Q(end_date__gte=start_range, end_date__lt=end_range),
        is_active=True
    )
    
    # Class sessions
    class_sessions = ClassSession.objects.filter(
        start_time__gte=start_range,
        start_time__lt=end_range,
        is_cancelled=False
    ).select_related('intake__course')
    
    # Organize events by date
    for day in calendar_days:
        date_obj = day['date'].date()
        
        # Add course intakes
        for intake in course_intakes:
            if intake.course_start_date.date() == date_obj:
                day['events'].append({
                    'type': 'course_start',
                    'title': f"📚 {intake.course.title} starts",
                    'description': intake.description[:100],
                    'color': 'green'
                })
        
        # Add class sessions
        for session in class_sessions:
            if session.start_time.date() == date_obj:
                day['events'].append({
                    'type': 'class',
                    'title': f"📖 {session.title}",
                    'description': session.description[:100],
                    'time': session.start_time.strftime('%H:%M'),
                    'color': 'blue'
                })
        
        # Add calendar events
        for event in calendar_events:
            if event.start_date.date() == date_obj:
                day['events'].append({
                    'type': 'event',
                    'title': f"🎉 {event.title}",
                    'description': event.description[:100],
                    'color': 'purple'
                })
    
    # Upcoming deadlines
    upcoming_sessions = ClassSession.objects.filter(
        start_time__gte=timezone.now(),
        is_cancelled=False
    ).select_related('intake__course').order_by('start_time')[:10]
    
    # Instructor's intakes (for instructors)
    my_schedules = None
    if hasattr(request.user, 'role') and request.user.role == 'instructor':
        my_schedules = CourseIntake.objects.filter(
            created_by=request.user,
            status__in=['open', 'upcoming', 'in_progress']
        ).order_by('course_start_date')[:5]
    
    context = {
        'calendar_days': calendar_days,
        'week_days': week_days,
        'year': year,
        'month': month,
        'prev_month': (month - 1) if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': (month + 1) if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'month_name': first_day.strftime('%B %Y'),
        'upcoming_sessions': upcoming_sessions,
        'my_schedules': my_schedules,
    }
    
    return render(request, 'lms/calendar/calendar.html', context)


# ============================================================
# COURSE ADVERTISING / PROMOTION VIEWS
# ============================================================

@login_required
def create_course_schedule(request):
    """Create a new course schedule (instructor/admin)"""
    
    if not hasattr(request.user, 'role') or request.user.role not in ['admin', 'instructor', 'dept_head']:
        messages.error(request, "You don't have permission to create course schedules.")
        return redirect('lms:dashboard')
    
    class CourseIntakeForm(forms.ModelForm):
        class Meta:
            model = CourseIntake
            fields = [
                'course', 'title', 'description', 'start_date', 'end_date',
                'schedule_type', 'max_capacity', 'session_duration_hours',
                'sessions_per_week', 'delivery_mode', 'venue', 'meeting_link',
                'regular_price', 'early_bird_price', 'early_bird_deadline',
                'requirements', 'what_to_expect', 'is_featured'
            ]
            widgets = {
                'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                'early_bird_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                'description': forms.Textarea(attrs={'rows': 4}),
                'requirements': forms.Textarea(attrs={'rows': 3}),
                'what_to_expect': forms.Textarea(attrs={'rows': 3}),
            }
    
    if request.method == 'POST':
        form = CourseIntakeForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.status = 'published'
            schedule.save()
            
            messages.success(request, f"Course schedule '{schedule.title}' created successfully!")
            return redirect('lms:course_schedule_detail', schedule_id=schedule.id)
    else:
        form = CourseIntakeForm()
    
    context = {'form': form}
    return render(request, 'lms/instructor/create_schedule.html', context)


@login_required
def create_advertisement(request, schedule_id):
    """Create an advertisement for a course schedule"""
    
    schedule = get_object_or_404(CourseIntake, id=schedule_id)
    
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.error(request, "Only administrators can create advertisements.")
        return redirect('lms:course_schedule_detail', schedule_id=schedule.id)
    
    if request.method == 'POST':
        ad = CourseAdvertisement.objects.create(
            intake=schedule,
            ad_type=request.POST.get('ad_type'),
            title=request.POST.get('title'),
            headline=request.POST.get('headline'),
            description=request.POST.get('description'),
            discount_percentage=request.POST.get('discount_percentage'),
            promo_code=request.POST.get('promo_code'),
            offer_valid_until=request.POST.get('offer_valid_until'),
            target_audience=request.POST.get('target_audience'),
            priority=request.POST.get('priority', 0),
        )
        
        if request.FILES.get('banner_image'):
            ad.banner_image = request.FILES['banner_image']
            ad.save()
        
        messages.success(request, f"Advertisement '{ad.title}' created successfully!")
        return redirect('lms:course_schedule_detail', schedule_id=schedule.id)
    
    context = {'schedule': schedule}
    return render(request, 'lms/instructor/create_advertisement.html', context)


# ============================================================
# PUBLIC COURSE LISTINGS WITH SCHEDULES
# ============================================================

def upcoming_courses(request):
    """Public page showing upcoming course schedules"""
    
    # Filtering
    department_id = request.GET.get('department')
    delivery_mode = request.GET.get('delivery_mode')
    month = request.GET.get('month')
    
    schedules = CourseIntake.objects.filter(
        course_start_date__gte=timezone.now(),
        status__in=['open', 'upcoming']
    ).select_related('course__department')
    
    if department_id:
        schedules = schedules.filter(course__department_id=department_id)
    
    if delivery_mode:
        schedules = schedules.filter(delivery_mode=delivery_mode)
    
    if month:
        schedules = schedules.filter(course_start_date__month=month)
    
    # Featured courses
    featured_schedules = schedules.filter(is_featured=True)[:6]
    
    # Get departments for filter
    departments = Course.objects.values_list('department', flat=True).distinct()
    departments = [{'id': d} for d in departments if d]
    
    # Pagination
    paginator = Paginator(schedules, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'featured_schedules': featured_schedules,
        'delivery_modes': CourseIntake.DELIVERY_CHOICES,
        'departments': departments,
        'selected_department': department_id,
        'selected_delivery_mode': delivery_mode,
        'selected_month': month,
    }
    return render(request, 'lms/courses/upcoming_courses.html', context)


def course_schedule_detail(request, schedule_id):
    """Detailed view of a course schedule for registration"""
    
    # Allow viewing schedules in any status (view will show appropriate message based on status)
    schedule = get_object_or_404(CourseIntake, id=schedule_id, is_visible=True)
    
    # Check if user is already enrolled
    is_enrolled = False
    enrollment = None
    
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'learner':
        try:
            enrollment = IntakeEnrollment.objects.get(
                intake=schedule,
                student=request.user
            )
            is_enrolled = True
        except IntakeEnrollment.DoesNotExist:
            pass
    
    # Get sessions for this schedule
    sessions = schedule.sessions.filter(is_cancelled=False).order_by('start_time')
    
    context = {
        'schedule': schedule,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'sessions': sessions,
        'available_spots': schedule.available_spots,
    }
    return render(request, 'lms/courses/schedule_detail.html', context)


# ============================================================
# ENROLLMENT & REGISTRATION
# ============================================================

@login_required
def enroll_in_schedule(request, schedule_id):
    """Enroll a student in a specific course schedule"""
    
    schedule = get_object_or_404(CourseIntake, id=schedule_id, is_visible=True)
    
    # Check if the intake is open for registration
    if schedule.status != 'open':
        messages.error(request, f"Registration for this course is currently {schedule.get_status_display().lower()}. Please try again later.")
        return redirect('lms:course_schedule_detail', schedule_id=schedule.id)
    
    if not hasattr(request.user, 'role') or request.user.role != 'learner':
        messages.error(request, "Only learners can enroll in courses.")
        return redirect('lms:course_schedule_detail', schedule_id=schedule.id)
    
    # Check if already enrolled
    if IntakeEnrollment.objects.filter(intake=schedule, student=request.user).exists():
        messages.warning(request, "You are already enrolled in this course schedule.")
        return redirect('lms:course_schedule_detail', schedule_id=schedule.id)
    
    # Check capacity
    if schedule.available_spots <= 0:
        # Add to waitlist
        IntakeEnrollment.objects.create(
            intake=schedule,
            student=request.user,
            status='waitlisted',
            price_paid=0
        )
        messages.info(request, "This course is full. You have been added to the waitlist.")
    else:
        # Regular enrollment
        enrollment = IntakeEnrollment.objects.create(
            intake=schedule,
            student=request.user,
            status='enrolled',
            price_paid=schedule.current_price
        )
        
        # Create calendar events for student
        for session in schedule.sessions.all():
            SessionAttendance.objects.get_or_create(
                session=session,
                student=request.user,
                enrollment=enrollment
            )
        
        messages.success(request, f"You have successfully enrolled in {schedule.title}!")
    
    return redirect('lms:my_schedule')


@login_required
def my_schedule(request):
    """Student's personal schedule showing all enrolled courses"""
    
    enrollments = IntakeEnrollment.objects.filter(
        student=request.user,
        status__in=['enrolled', 'waitlisted']
    ).select_related('intake__course')
    
    # Get all sessions for enrolled courses
    upcoming_sessions = ClassSession.objects.filter(
        intake__enrollments__student=request.user,
        start_time__gte=timezone.now(),
        is_cancelled=False
    ).order_by('start_time')[:20]
    
    # Attendance summary
    total_sessions = SessionAttendance.objects.filter(
        student=request.user
    ).count()
    
    attended_sessions = SessionAttendance.objects.filter(
        student=request.user,
        status__in=['present', 'online']
    ).count()
    
    attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    context = {
        'enrollments': enrollments,
        'upcoming_sessions': upcoming_sessions,
        'attendance_rate': attendance_rate,
        'attendance_remaining': 283 - (attendance_rate / 100 * 283),
    }
    return render(request, 'lms/student/my_schedule.html', context)


# ============================================================
# INSTRUCTOR CLASS MANAGEMENT
# ============================================================

@login_required
def manage_class_sessions(request, schedule_id):
    """Manage individual class sessions (instructor)"""
    
    intake = get_object_or_404(CourseIntake, id=schedule_id)
    
    if not hasattr(request.user, 'role') or (request.user.role not in ['admin', 'instructor'] and intake.created_by != request.user):
        messages.error(request, "You don't have permission to manage this schedule.")
        return redirect('lms:dashboard')
    
    if request.method == 'POST':
        # Add new session
        session = ClassSession.objects.create(
            schedule=schedule,
            title=request.POST.get('title'),
            session_type=request.POST.get('session_type'),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
            description=request.POST.get('description'),
            meeting_link=request.POST.get('meeting_link'),
        )
        
        messages.success(request, f"Session '{session.title}' added successfully!")
        return redirect('lms:manage_class_sessions', schedule_id=schedule.id)
    
    sessions = schedule.sessions.all().order_by('start_time')
    
    context = {
        'schedule': schedule,
        'sessions': sessions,
    }
    return render(request, 'lms/instructor/manage_sessions.html', context)


@login_required
def take_attendance(request, session_id):
    """Mark attendance for a class session"""
    
    session = get_object_or_404(ClassSession, id=session_id)
    schedule = session.schedule
    
    if not hasattr(request.user, 'role') or (request.user.role not in ['admin', 'instructor'] and schedule.created_by != request.user):
        messages.error(request, "You don't have permission to take attendance.")
        return redirect('lms:dashboard')
    
    enrollments = IntakeEnrollment.objects.filter(
        schedule=schedule,
        status='enrolled'
    ).select_related('student')
    
    if request.method == 'POST':
        for enrollment in enrollments:
            status = request.POST.get(f'attendance_{enrollment.id}')
            if status:
                attendance, created = SessionAttendance.objects.get_or_create(
                    session=session,
                    student=enrollment.student,
                    schedule_enrollment=enrollment,
                    defaults={'status': status, 'marked_by': request.user}
                )
                if not created:
                    attendance.status = status
                    attendance.marked_by = request.user
                    attendance.marked_at = timezone.now()
                    attendance.save()
        
        session.attendance_taken = True
        session.save()
        
        messages.success(request, "Attendance saved successfully!")
        return redirect('lms:manage_class_sessions', schedule_id=schedule.id)


# ============================================================
# CourseIntake ADMIN/INSTRUCTOR MANAGEMENT VIEWS
# ============================================================

from django.contrib.admin.views.decorators import staff_member_required
from .models import CourseIntake, IntakeEnrollment

@staff_member_required
def manage_intakes(request):
    """View all course intakes for management"""
    
    # Get all intakes, ordered by start date
    intakes = CourseIntake.objects.select_related('course', 'instructor').all()
    
    # Filtering
    status = request.GET.get('status')
    if status:
        intakes = intakes.filter(status=status)
    
    course_id = request.GET.get('course')
    if course_id:
        intakes = intakes.filter(course_id=course_id)
    
    # Pagination
    paginator = Paginator(intakes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    courses = Course.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'courses': courses,
        'status_choices': CourseIntake.STATUS_CHOICES,
        'selected_status': status,
        'selected_course': course_id,
    }
    return render(request, 'lms/admin/manage_intakes.html', context)


@staff_member_required
def create_intake(request, course_id=None):
    """Create a new course intake/schedule"""
    
    if course_id:
        course = get_object_or_404(Course, id=course_id)
    else:
        course = None
    
    if request.method == 'POST':
        # Get form data
        course_id = request.POST.get('course')
        course = get_object_or_404(Course, id=course_id)
        
        intake = CourseIntake.objects.create(
            course=course,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            registration_start_date=request.POST.get('registration_start_date'),
            registration_end_date=request.POST.get('registration_end_date'),
            course_start_date=request.POST.get('course_start_date'),
            course_end_date=request.POST.get('course_end_date'),
            weekday=request.POST.get('weekday'),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
            duration_weeks=int(request.POST.get('duration_weeks', 0)),
            total_hours=int(request.POST.get('total_hours', 0)),
            max_students=int(request.POST.get('max_students', 30)),
            delivery_mode=request.POST.get('delivery_mode'),
            venue=request.POST.get('venue', ''),
            meeting_link=request.POST.get('meeting_link', ''),
            regular_price=request.POST.get('regular_price', 0),
            early_bird_price=request.POST.get('early_bird_price') or None,
            early_bird_deadline=request.POST.get('early_bird_deadline') or None,
            is_featured=request.POST.get('is_featured') == 'on',
            instructor_id=request.POST.get('instructor') or None,
            created_by=request.user,
        )
        
        messages.success(request, f'Course intake "{intake.title}" created successfully!')
        return redirect('lms:manage_intakes')
    
    courses = Course.objects.filter(is_active=True)
    instructors = User.objects.filter(groups__name__in=['instructor', 'admin'])
    
    context = {
        'course': course,
        'courses': courses,
        'instructors': instructors,
        'weekdays': CourseIntake.WEEKDAY_CHOICES,
        'delivery_modes': CourseIntake.DELIVERY_CHOICES,
        'status_choices': CourseIntake.STATUS_CHOICES,
    }
    return render(request, 'lms/admin/create_intake.html', context)


@staff_member_required
def edit_intake(request, intake_id):
    """Edit an existing course intake"""
    
    intake = get_object_or_404(CourseIntake, id=intake_id)
    
    if request.method == 'POST':
        # Update intake fields
        intake.title = request.POST.get('title')
        intake.description = request.POST.get('description', '')
        intake.registration_start_date = request.POST.get('registration_start_date')
        intake.registration_end_date = request.POST.get('registration_end_date')
        intake.course_start_date = request.POST.get('course_start_date')
        intake.course_end_date = request.POST.get('course_end_date')
        intake.weekday = request.POST.get('weekday')
        intake.start_time = request.POST.get('start_time')
        intake.end_time = request.POST.get('end_time')
        intake.duration_weeks = int(request.POST.get('duration_weeks', 0))
        intake.total_hours = int(request.POST.get('total_hours', 0))
        intake.max_students = int(request.POST.get('max_students', 30))
        intake.delivery_mode = request.POST.get('delivery_mode')
        intake.venue = request.POST.get('venue', '')
        intake.meeting_link = request.POST.get('meeting_link', '')
        intake.regular_price = request.POST.get('regular_price', 0)
        intake.early_bird_price = request.POST.get('early_bird_price') or None
        intake.early_bird_deadline = request.POST.get('early_bird_deadline') or None
        intake.is_featured = request.POST.get('is_featured') == 'on'
        intake.status = request.POST.get('status')
        intake.instructor_id = request.POST.get('instructor') or None
        
        intake.save()
        
        messages.success(request, f'Course intake "{intake.title}" updated successfully!')
        return redirect('lms:manage_intakes')
    
    instructors = User.objects.filter(groups__name__in=['instructor', 'admin'])
    
    context = {
        'intake': intake,
        'instructors': instructors,
        'weekdays': CourseIntake.WEEKDAY_CHOICES,
        'delivery_modes': CourseIntake.DELIVERY_CHOICES,
        'status_choices': CourseIntake.STATUS_CHOICES,
    }
    return render(request, 'lms/admin/edit_intake.html', context)


@staff_member_required
def delete_intake(request, intake_id):
    """Delete a course intake"""
    
    intake = get_object_or_404(CourseIntake, id=intake_id)
    
    if request.method == 'POST':
        intake_title = intake.title
        intake.delete()
        messages.success(request, f'Course intake "{intake_title}" deleted successfully!')
        return redirect('lms:manage_intakes')
    
    context = {'intake': intake}
    return render(request, 'lms/admin/delete_intake_confirm.html', context)


@staff_member_required
def duplicate_intake(request, intake_id):
    """Duplicate an existing intake (for creating next session)"""
    
    original = get_object_or_404(CourseIntake, id=intake_id)
    
    # Create copy with new dates (add 3 months approximate)
    new_start = original.course_start_date + timedelta(days=90)
    new_end = original.course_end_date + timedelta(days=90)
    
    new_intake = CourseIntake.objects.create(
        course=original.course,
        title=f"{original.course.title} - {new_start.strftime('%B %Y')}",
        description=original.description,
        registration_start_date=new_start - timedelta(days=30),
        registration_end_date=new_start - timedelta(days=7),
        course_start_date=new_start,
        course_end_date=new_end,
        weekday=original.weekday,
        start_time=original.start_time,
        end_time=original.end_time,
        duration_weeks=original.duration_weeks,
        total_hours=original.total_hours,
        max_students=original.max_students,
        delivery_mode=original.delivery_mode,
        venue=original.venue,
        meeting_link=original.meeting_link,
        regular_price=original.regular_price,
        early_bird_price=original.early_bird_price,
        early_bird_deadline=original.early_bird_deadline,
        instructor=original.instructor,
        created_by=request.user,
    )
    
    messages.success(request, f'Course intake duplicated! New intake: "{new_intake.title}"')
    return redirect('lms:edit_intake', intake_id=new_intake.id)


def intake_detail(request, intake_id):
    """Public intake detail page"""
    
    intake = get_object_or_404(CourseIntake, id=intake_id, is_visible=True)
    
    context = {
        'intake': intake,
        'course': intake.course,
        'sessions': intake.sessions.all(),
        'enrollments': intake.enrollments.filter(status='enrolled').count(),
    }
    return render(request, 'lms/intake_detail.html', context)


def upcoming_courses(request):
    """List of upcoming course intakes"""
    
    # Get visible, upcoming intakes
    intakes = CourseIntake.objects.filter(
        is_visible=True,
        course_start_date__gte=timezone.now()
    ).select_related('course', 'instructor').order_by('course_start_date')
    
    # Filtering
    delivery_mode = request.GET.get('delivery')
    if delivery_mode:
        intakes = intakes.filter(delivery_mode=delivery_mode)
    
    search = request.GET.get('q')
    if search:
        intakes = intakes.filter(
            Q(course__title__icontains=search) |
            Q(title__icontains=search) |
            Q(course__description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(intakes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'delivery_choices': CourseIntake.DELIVERY_CHOICES,
        'selected_delivery': delivery_mode,
        'search_query': search,
    }
    return render(request, 'lms/upcoming_courses.html', context)
    
    # Get existing attendance records
    attendance_records = {
        att.student_id: att for att in SessionAttendance.objects.filter(session=session)
    }
    
    context = {
        'session': session,
        'schedule': schedule,
        'enrollments': enrollments,
        'attendance_records': attendance_records,
    }
    return render(request, 'lms/instructor/take_attendance.html', context)
