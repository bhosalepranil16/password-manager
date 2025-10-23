from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import PasswordEntry, UserAdditionalData
import re


class SignupForm(forms.Form):
    """Signup form for new users"""
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    mobile_number = forms.CharField(
        max_length=13,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91XXXXXXXXXX',
            'pattern': r'\+91[0-9]{10}'
        })
    )
    password = forms.CharField(
        label='Master Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong master password'
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long'
    )
    confirm_password = forms.CharField(
        label='Confirm Master Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your master password'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = email.split('@')[0] if email else ''
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with this email already exists.')
        
        return email
    
    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        
        # Validate mobile number format
        if not re.match(r'^\+91[0-9]{10}$', mobile):
            raise forms.ValidationError('Mobile number must be in format +91XXXXXXXXXX')
        
        return mobile
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class LoginForm(forms.Form):
    """Custom login form for master password"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Master Password'
        })
    )


class PasswordEntryForm(forms.ModelForm):
    """Form for creating and editing password entries"""
    raw_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        required=False,
        help_text='Leave empty when editing to keep current password'
    )
    
    class Meta:
        model = PasswordEntry
        fields = ['app_name', 'username', 'url']
        widgets = {
            'app_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'App Name (e.g., YONO, Gmail, Facebook)'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username or Email'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make raw_password required for new entries
        if not self.instance.pk:
            self.fields['raw_password'].required = True
            self.fields['raw_password'].help_text = ''
