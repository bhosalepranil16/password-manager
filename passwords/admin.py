from django.contrib import admin
from .models import PasswordEntry, AdditionalField


class AdditionalFieldInline(admin.TabularInline):
    model = AdditionalField
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PasswordEntry)
class PasswordEntryAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'username', 'user', 'url', 'created_at', 'updated_at')
    list_filter = ('app_name', 'user', 'created_at')
    search_fields = ('app_name', 'username', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AdditionalFieldInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'app_name', 'username', 'url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AdditionalField)
class AdditionalFieldAdmin(admin.ModelAdmin):
    list_display = ('password_entry', 'field_name', 'created_at')
    list_filter = ('field_name', 'created_at')
    search_fields = ('password_entry__app_name', 'field_name')
    readonly_fields = ('created_at', 'updated_at')
