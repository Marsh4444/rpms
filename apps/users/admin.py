# ============================================================================
# IMPORTS
# ============================================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# BaseUserAdmin is Django's built-in admin for User models
# We inherit from it to customize for our User model

from .models import User


# ============================================================================
# CUSTOM USER ADMIN
# ============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    Extends Django's UserAdmin with our custom fields.
    """
    
    # Fields to display in the user list
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    # Shows: username | email | role | staff status | active status
    
    # Filters in the right sidebar
    list_filter = ['role', 'is_staff', 'is_active', 'date_joined']
    # Can filter by: role, staff, active, join date
    
    list_editable = ('is_staff', 'is_active', 'role')

    # Search functionality
    search_fields = ['username', 'email', 'first_name', 'last_name']
    # Can search by: username, email, first/last name
    
    # Fields to show when editing a user
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone_number', 'profile_picture')
        }),
    )
    # BaseUserAdmin.fieldsets = Django's default fields
    # + ('Custom Fields', {...}) = adds our custom fields section
    
    # Fields to show when creating a new user
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone_number', 'profile_picture')
        }),
    )