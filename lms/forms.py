from django import forms
from django.contrib.auth import get_user_model
from .models import Certification, CertificationProvider, ExamRegistration

User = get_user_model()


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)


# ============================================================
# CERTIFICATION FORMS
# ============================================================

class ExamRegistrationForm(forms.ModelForm):
    """Form for students to register for certification exams"""
    
    class Meta:
        model = ExamRegistration
        fields = ['exam_date', 'exam_location', 'exam_language']
        widgets = {
            'exam_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'required': True
            }),
            'exam_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Testing center location',
                'required': True
            }),
            'exam_language': forms.Select(attrs={
                'class': 'form-select',
                'choices': [('English', 'English'), ('French', 'French'), ('Spanish', 'Spanish')]
            }),
        }
    
    def clean_exam_date(self):
        exam_date = self.cleaned_data.get('exam_date')
        if exam_date:
            from django.utils import timezone
            if exam_date <= timezone.now():
                raise forms.ValidationError('Exam date must be in the future.')
        return exam_date


class ExamPaymentForm(forms.Form):
    """Form for handling exam registration payment"""
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'readonly': True
        })
    )
    reference_number = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Payment reference/receipt number'
        }),
        required=False
    )


class CertificationProviderForm(forms.ModelForm):
    """Admin form for managing certification providers"""
    
    class Meta:
        model = CertificationProvider
        fields = ['name', 'short_name', 'provider_type', 'logo', 'website', 'description',
                  'partnership_status', 'partnership_start_date', 'partnership_end_date',
                  'contact_person', 'contact_email', 'contact_phone',
                  'api_endpoint', 'api_key', 'api_secret', 'webhook_url',
                  'is_active', 'requires_voucher', 'voucher_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'provider_type': forms.Select(attrs={'class': 'form-select'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'partnership_status': forms.Select(attrs={'class': 'form-select'}),
            'partnership_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'partnership_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'api_endpoint': forms.URLInput(attrs={'class': 'form-control'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'api_secret': forms.PasswordInput(attrs={'class': 'form-control'}),
            'webhook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'voucher_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_voucher': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CertificationForm(forms.ModelForm):
    """Admin form for managing certifications"""
    
    class Meta:
        model = Certification
        fields = ['provider', 'code', 'title', 'full_title', 'description', 'difficulty',
                  'exam_code', 'exam_duration_minutes', 'number_of_questions',
                  'passing_score', 'passing_percentage', 'validity_years',
                  'renewal_requirements', 'continuing_education_units',
                  'synego_course', 'exam_voucher_price', 'training_material_price',
                  'logo', 'featured_image', 'is_active', 'is_featured']
        widgets = {
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'full_title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'exam_code': forms.TextInput(attrs={'class': 'form-control'}),
            'exam_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'number_of_questions': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'validity_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'renewal_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'continuing_education_units': forms.NumberInput(attrs={'class': 'form-control'}),
            'synego_course': forms.Select(attrs={'class': 'form-select'}),
            'exam_voucher_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'training_material_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

