"""
Views for Certification Management
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
import json

from .models import (
    Certification, CertificationProvider, ExamRegistration,
    StudentCertification, PartnerIntegrationLog, Course
)
from .forms import (
    ExamRegistrationForm, ExamPaymentForm, CertificationProviderForm,
    CertificationForm
)
from .permission_decorators import admin_required


# ============================================================
# STUDENT VIEWS
# ============================================================

@login_required
def certification_catalog(request):
    """Display certification catalog for students"""
    
    # Get all active certifications
    certifications = Certification.objects.filter(
        is_active=True,
        provider__is_active=True,
        provider__partnership_status='active'
    ).select_related('provider').order_by('-is_featured', 'title')
    
    # Filter by provider if specified
    provider_id = request.GET.get('provider')
    if provider_id:
        certifications = certifications.filter(provider_id=provider_id)
    
    # Filter by difficulty
    difficulty = request.GET.get('difficulty')
    if difficulty:
        certifications = certifications.filter(difficulty=difficulty)
    
    # Filter by search query
    query = request.GET.get('q')
    if query:
        certifications = certifications.filter(
            Q(title__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Get user's registered certifications
    user_registrations = ExamRegistration.objects.filter(
        student=request.user
    ).values_list('certification_id', flat=True)
    
    # Pagination
    paginator = Paginator(certifications, 12)
    page = request.GET.get('page', 1)
    certifications_page = paginator.get_page(page)
    
    # Get providers for filter
    providers = CertificationProvider.objects.filter(
        is_active=True,
        partnership_status='active'
    ).order_by('name')
    
    context = {
        'certifications': certifications_page,
        'providers': providers,
        'user_registrations': user_registrations,
        'selected_provider': provider_id,
        'selected_difficulty': difficulty,
        'search_query': query,
        'difficulty_choices': Certification.DIFFICULTY_CHOICES,
        'page_title': 'Certification Catalog',
    }
    
    return render(request, 'lms/certifications/catalog.html', context)


@login_required
def certification_detail(request, certification_id):
    """Display certification detail"""
    
    certification = get_object_or_404(
        Certification.objects.select_related('provider', 'synego_course'),
        id=certification_id,
        is_active=True
    )
    
    # Check if user has already registered
    user_registration = ExamRegistration.objects.filter(
        student=request.user,
        certification=certification
    ).first()
    
    # Get related certifications
    related_certs = Certification.objects.filter(
        provider=certification.provider,
        is_active=True
    ).exclude(id=certification_id)[:3]
    
    context = {
        'certification': certification,
        'user_registration': user_registration,
        'related_certifications': related_certs,
        'page_title': certification.title,
    }
    
    return render(request, 'lms/certifications/detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def register_for_exam(request, certification_id):
    """Register for certification exam"""
    
    certification = get_object_or_404(Certification, id=certification_id, is_active=True)
    
    # Check if already registered
    existing_registration = ExamRegistration.objects.filter(
        student=request.user,
        certification=certification,
        status__in=['registered', 'exam_scheduled', 'exam_completed', 'passed', 'certificate_issued']
    ).exists()
    
    if existing_registration:
        messages.warning(request, 'You have already registered for this certification.')
        return redirect('lms:certification_detail', certification_id=certification_id)
    
    if request.method == 'POST':
        form = ExamRegistrationForm(request.POST)
        
        if form.is_valid():
            registration = form.save(commit=False)
            registration.student = request.user
            registration.certification = certification
            registration.status = 'pending_payment'
            
            # If no voucher required, mark as registered
            if not certification.provider.requires_voucher:
                registration.status = 'registered'
                registration.save()
                messages.success(request, 'Successfully registered for exam!')
                return redirect('lms:exam_payment', registration_id=registration.id)
            
            registration.save()
            
            # Redirect to payment
            return redirect('lms:exam_payment', registration_id=registration.id)
    else:
        initial_date = timezone.now()
        form = ExamRegistrationForm(initial={'exam_date': initial_date})
    
    context = {
        'form': form,
        'certification': certification,
        'page_title': f'Register for {certification.title}',
    }
    
    return render(request, 'lms/certifications/register.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def exam_payment(request, registration_id):
    """Handle exam payment"""
    
    registration = get_object_or_404(
        ExamRegistration,
        id=registration_id,
        student=request.user,
        status='pending_payment'
    )
    
    if request.method == 'POST':
        form = ExamPaymentForm(request.POST)
        
        if form.is_valid():
            payment_method = form.cleaned_data.get('payment_method')
            reference = form.cleaned_data.get('reference_number')
            
            registration.payment_method = payment_method
            registration.payment_reference = reference
            registration.amount_paid = registration.certification.exam_voucher_price
            registration.payment_date = timezone.now()
            registration.status = 'payment_verified'
            registration.save()
            
            # Log the payment
            PartnerIntegrationLog.objects.create(
                provider=registration.certification.provider,
                endpoint='payment_processing',
                method='POST',
                request_data={
                    'student': request.user.username,
                    'certification': registration.certification.code,
                    'payment_method': payment_method,
                    'amount': str(registration.amount_paid)
                },
                response_data={'status': 'success'},
                status_code=200,
                success=True
            )
            
            messages.success(request, 'Payment verified! Your voucher code will be issued soon.')
            return redirect('lms:my_certifications')
    else:
        payment_amount = registration.certification.exam_voucher_price
        form = ExamPaymentForm(initial={'amount': payment_amount})
    
    context = {
        'form': form,
        'registration': registration,
        'amount': registration.certification.exam_voucher_price,
        'page_title': 'Process Payment',
    }
    
    return render(request, 'lms/certifications/payment.html', context)


@login_required
def my_certifications(request):
    """Display user's certifications and registrations"""
    
    # Get exam registrations
    registrations = ExamRegistration.objects.filter(
        student=request.user
    ).select_related('certification', 'certification__provider').order_by('-registration_date')
    
    # Get earned certifications
    earned_certs = StudentCertification.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('certification', 'certification__provider').order_by('-issue_date')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        registrations = registrations.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(registrations, 10)
    page = request.GET.get('page', 1)
    registrations_page = paginator.get_page(page)
    
    context = {
        'registrations': registrations_page,
        'earned_certifications': earned_certs,
        'all_registrations': registrations,
        'status_filter': status_filter,
        'status_choices': ExamRegistration.STATUS_CHOICES,
        'page_title': 'My Certifications',
    }
    
    return render(request, 'lms/certifications/my_certifications.html', context)


# ============================================================
# ADMIN VIEWS
# ============================================================

@admin_required
def list_providers(request):
    """List certification providers"""
    
    providers = CertificationProvider.objects.all().annotate(
        certification_count=Count('certifications')
    ).order_by('-is_active', 'name')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        providers = providers.filter(partnership_status=status)
    
    # Search
    query = request.GET.get('q')
    if query:
        providers = providers.filter(
            Q(name__icontains=query) |
            Q(short_name__icontains=query)
        )
    
    paginator = Paginator(providers, 20)
    page = request.GET.get('page', 1)
    providers_page = paginator.get_page(page)
    
    context = {
        'providers': providers_page,
        'search_query': query,
        'status_filter': status,
        'page_title': 'Certification Providers',
    }
    
    return render(request, 'lms/admin/certifications/providers.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def create_provider(request):
    """Create certification provider"""
    
    if request.method == 'POST':
        form = CertificationProviderForm(request.POST, request.FILES)
        
        if form.is_valid():
            provider = form.save()
            messages.success(request, f'Provider "{provider.name}" created successfully!')
            return redirect('lms:list_providers')
    else:
        form = CertificationProviderForm()
    
    context = {
        'form': form,
        'page_title': 'Add Certification Provider',
    }
    
    return render(request, 'lms/admin/certifications/provider_form.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def edit_provider(request, provider_id):
    """Edit certification provider"""
    
    provider = get_object_or_404(CertificationProvider, id=provider_id)
    
    if request.method == 'POST':
        form = CertificationProviderForm(request.POST, request.FILES, instance=provider)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Provider "{provider.name}" updated successfully!')
            return redirect('lms:list_providers')
    else:
        form = CertificationProviderForm(instance=provider)
    
    context = {
        'form': form,
        'provider': provider,
        'page_title': f'Edit {provider.name}',
    }
    
    return render(request, 'lms/admin/certifications/provider_form.html', context)


@admin_required
def list_certifications(request):
    """List certifications"""
    
    certifications = Certification.objects.select_related('provider', 'synego_course').order_by(
        '-is_featured', '-is_active', 'title'
    )
    
    # Filter
    provider_id = request.GET.get('provider')
    if provider_id:
        certifications = certifications.filter(provider_id=provider_id)
    
    difficulty = request.GET.get('difficulty')
    if difficulty:
        certifications = certifications.filter(difficulty=difficulty)
    
    query = request.GET.get('q')
    if query:
        certifications = certifications.filter(
            Q(title__icontains=query) |
            Q(code__icontains=query)
        )
    
    paginator = Paginator(certifications, 20)
    page = request.GET.get('page', 1)
    certs_page = paginator.get_page(page)
    
    providers = CertificationProvider.objects.all().order_by('name')
    
    context = {
        'certifications': certs_page,
        'providers': providers,
        'search_query': query,
        'difficulty_choices': Certification.DIFFICULTY_CHOICES,
        'page_title': 'Certifications',
    }
    
    return render(request, 'lms/admin/certifications/list.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def create_certification(request):
    """Create certification"""
    
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES)
        
        if form.is_valid():
            cert = form.save()
            messages.success(request, f'Certification "{cert.title}" created successfully!')
            return redirect('lms:list_certifications')
    else:
        form = CertificationForm()
    
    context = {
        'form': form,
        'page_title': 'Add Certification',
    }
    
    return render(request, 'lms/admin/certifications/form.html', context)


@admin_required
@require_http_methods(["GET", "POST"])
def edit_certification(request, certification_id):
    """Edit certification"""
    
    certification = get_object_or_404(Certification, id=certification_id)
    
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES, instance=certification)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Certification "{certification.title}" updated successfully!')
            return redirect('lms:list_certifications')
    else:
        form = CertificationForm(instance=certification)
    
    context = {
        'form': form,
        'certification': certification,
        'page_title': f'Edit {certification.title}',
    }
    
    return render(request, 'lms/admin/certifications/form.html', context)


@require_http_methods(["POST"])
def certification_webhook(request, provider_id):
    """Certification webhook endpoint for provider result notifications"""
    
    provider = get_object_or_404(CertificationProvider, id=provider_id)
    
    try:
        payload = json.loads(request.body)
        
        # Log the webhook call
        PartnerIntegrationLog.objects.create(
            provider=provider,
            endpoint=request.path,
            method='POST',
            request_data=payload,
            status_code=200,
            success=True
        )
        
        # Process results if provided
        if 'exam_results' in payload:
            results = payload['exam_results']
            registration = ExamRegistration.objects.filter(
                provider_reference=results.get('registration_id')
            ).first()
            
            if registration:
                registration.exam_score = results.get('score')
                registration.exam_percentage = results.get('percentage')
                registration.passed = results.get('passed', False)
                registration.results_received_at = timezone.now()
                registration.results_details = results
                registration.status = 'exam_completed'
                
                if registration.passed:
                    registration.status = 'passed'
                
                registration.save()
                
                # Send notification to student
                from .utils import send_notification
                message = f"Your exam results are ready! You {'passed' if registration.passed else 'did not pass'} with {registration.exam_percentage}%."
                send_notification(
                    registration.student,
                    f'{registration.certification.title} Results',
                    message,
                    'success' if registration.passed else 'warning'
                )
        
        return JsonResponse({'status': 'received', 'success': True})
    
    except Exception as e:
        PartnerIntegrationLog.objects.create(
            provider=provider,
            endpoint=request.path,
            method='POST',
            status_code=400,
            success=False,
            error_message=str(e)
        )
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

