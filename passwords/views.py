from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import PasswordEntry, AdditionalField, UserAdditionalData
from .forms import PasswordEntryForm, LoginForm, SignupForm


def signup_view(request):
    """User signup view"""
    if request.user.is_authenticated:
        return redirect('password_list')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Extract username from email (part before @)
            email = form.cleaned_data['email']
            username = email.split('@')[0]
            
            # Create Django User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=form.cleaned_data['password']
            )
            
            # Create UserAdditionalData
            UserAdditionalData.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                mobile_number=form.cleaned_data['mobile_number']
            )
            
            messages.success(request, 'Account created successfully! Please login with your credentials.')
            return redirect('login')
    else:
        form = SignupForm()
    
    return render(request, 'passwords/signup.html', {'form': form})


def login_view(request):
    """Master password login view"""
    if request.user.is_authenticated:
        return redirect('password_list')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('password_list')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'passwords/login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')


@login_required
def password_list(request):
    """Display all passwords for the current user grouped by app"""
    passwords = PasswordEntry.objects.filter(user=request.user).prefetch_related('additional_fields')
    
    # Group passwords by app name
    apps = {}
    for password in passwords:
        app_name = password.app_name
        if app_name not in apps:
            apps[app_name] = []
        
        # Decrypt password and additional fields for display
        password_data = {
            'id': password.id,
            'username': password.username,
            'password': password.get_password(),
            'url': password.url,
            'created_at': password.created_at,
            'additional_fields': []
        }
        
        for field in password.additional_fields.all():
            password_data['additional_fields'].append({
                'field_name': field.field_name,
                'field_value': field.get_field_value()
            })
        
        apps[app_name].append(password_data)
    
    return render(request, 'passwords/password_list.html', {'apps': apps})


@login_required
def add_password(request):
    """Add new password entry"""
    if request.method == 'POST':
        form = PasswordEntryForm(request.POST)
        if form.is_valid():
            password_entry = form.save(commit=False)
            password_entry.user = request.user
            
            # Encrypt the password before saving
            raw_password = form.cleaned_data['raw_password']
            password_entry.set_password(raw_password)
            password_entry.save()
            
            # Handle additional fields
            additional_fields = request.POST.get('additional_fields', '[]')
            try:
                fields_data = json.loads(additional_fields)
                for field_data in fields_data:
                    if field_data.get('field_name') and field_data.get('field_value'):
                        additional_field = AdditionalField(
                            password_entry=password_entry,
                            field_name=field_data['field_name']
                        )
                        print(field_data['field_value'])
                        additional_field.set_field_value(field_data['field_value'])
                        additional_field.save()
            except json.JSONDecodeError:
                pass
            
            messages.success(request, f'Password for {password_entry.app_name} added successfully!')
            return redirect('password_list')
    else:
        form = PasswordEntryForm()
    
    return render(request, 'passwords/add_password.html', {'form': form})


@login_required
def edit_password(request, password_id):
    """Edit existing password entry"""
    password_entry = get_object_or_404(PasswordEntry, id=password_id, user=request.user)
    
    if request.method == 'POST':
        form = PasswordEntryForm(request.POST, instance=password_entry)
        if form.is_valid():
            # Update basic fields
            password_entry = form.save(commit=False)
            
            # Update password if provided
            raw_password = form.cleaned_data.get('raw_password')
            if raw_password:
                password_entry.set_password(raw_password)
            
            password_entry.save()
            
            # Handle additional fields
            # First, delete existing additional fields
            password_entry.additional_fields.all().delete()
            
            # Add new additional fields
            additional_fields = request.POST.get('additional_fields', '[]')
            try:
                fields_data = json.loads(additional_fields)
                for field_data in fields_data:
                    if field_data.get('field_name') and field_data.get('field_value'):
                        additional_field = AdditionalField(
                            password_entry=password_entry,
                            field_name=field_data['field_name']
                        )
                        additional_field.set_field_value(field_data['field_value'])
                        additional_field.save()
            except json.JSONDecodeError:
                pass
            
            messages.success(request, f'Password for {password_entry.app_name} updated successfully!')
            return redirect('password_list')
    else:
        # Pre-populate form with existing data
        form = PasswordEntryForm(instance=password_entry)
        # Get existing additional fields
        additional_fields = []
        for field in password_entry.additional_fields.all():
            additional_fields.append({
                'field_name': field.field_name,
                'field_value': field.get_field_value()
            })
    
    return render(request, 'passwords/edit_password.html', {
        'form': form, 
        'password_entry': password_entry,
        'additional_fields': json.dumps(additional_fields)
    })


@login_required
def delete_password(request, password_id):
    """Delete password entry"""
    password_entry = get_object_or_404(PasswordEntry, id=password_id, user=request.user)
    
    if request.method == 'POST':
        app_name = password_entry.app_name
        password_entry.delete()
        messages.success(request, f'Password for {app_name} deleted successfully!')
        return redirect('password_list')
    
    return render(request, 'passwords/delete_password.html', {'password_entry': password_entry})


@login_required
@require_POST
def copy_password(request, password_id):
    """Return password for copying (AJAX endpoint)"""
    password_entry = get_object_or_404(PasswordEntry, id=password_id, user=request.user)
    return JsonResponse({'password': password_entry.get_password()})
