from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings
import json
import base64


class UserAdditionalData(models.Model):
    """Additional user data with one-to-one relationship to User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, help_text="User's first name")
    last_name = models.CharField(max_length=50, help_text="User's last name")
    mobile_number = models.CharField(max_length=13, help_text="13-digit mobile number (+91XXXXXXXXXX)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"
    
    class Meta:
        verbose_name = "User Additional Data"
        verbose_name_plural = "User Additional Data"


class PasswordEntry(models.Model):
    """Main password entry model with mandatory and optional fields"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=100, help_text="Name of the application")
    username = models.CharField(max_length=100, help_text="Username for the application")
    password = models.TextField(help_text="Encrypted password")
    url = models.URLField(blank=True, null=True, help_text="Optional URL for the application")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['app_name', 'username']
        unique_together = ['user', 'app_name', 'username']
    
    def __str__(self):
        return f"{self.app_name} - {self.username}"
    
    def set_password(self, raw_password):
        """Encrypt and store the password"""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        self.password = fernet.encrypt(raw_password.encode()).decode()
    
    def get_password(self):
        """Decrypt and return the password"""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        return fernet.decrypt(self.password.encode()).decode()
    
    def _get_encryption_key(self):
        """Generate encryption key based on user and secret key"""
        # In production, use a more sophisticated key derivation
        secret_key = getattr(settings, 'PASSWORD_ENCRYPTION_KEY', 'default-secret-key')
        user_key = f"{secret_key}-{self.user.id}".encode()
        return base64.urlsafe_b64encode(user_key.ljust(32)[:32])


class AdditionalField(models.Model):
    """Model for storing additional custom fields for password entries"""
    password_entry = models.ForeignKey(PasswordEntry, on_delete=models.CASCADE, related_name='additional_fields')
    field_name = models.CharField(max_length=50, help_text="Name of the custom field (e.g., 'mpin', 'profile_password')")
    field_value = models.TextField(help_text="Encrypted value of the custom field")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['password_entry', 'field_name']
    
    def __str__(self):
        return f"{self.password_entry.app_name} - {self.field_name}"
    
    def set_field_value(self, raw_value):
        """Encrypt and store the field value"""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        self.field_value = fernet.encrypt(raw_value.encode()).decode()
    
    def get_field_value(self):
        """Decrypt and return the field value"""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        decoded_value = fernet.decrypt(self.field_value.encode()).decode()
        return decoded_value

    def _get_encryption_key(self):
        """Generate encryption key based on user and secret key"""
        secret_key = getattr(settings, 'PASSWORD_ENCRYPTION_KEY', 'default-secret-key')
        user_key = f"{secret_key}-{self.password_entry.user.id}".encode()
        return base64.urlsafe_b64encode(user_key.ljust(32)[:32])
