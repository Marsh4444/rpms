# ============================================================================
# IMPORTS
# ============================================================================

from django.contrib import admin
from .models import Property, Unit


# ============================================================================
# PROPERTY ADMIN
# ============================================================================

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Admin interface for Property model.
    Shows landlord all their properties with key info.
    """

    # Columns shown in the property list
    list_display = [
        'name',
        'city',
        'owner',
        'manager',
        'total_units',
        'occupied_units',
        'occupancy_rate',
        'created_at'
    ]
    # Shows: name | city | owner | manager | units | occupied | rate | created

    # Filters in the right sidebar
    list_filter = ['city', 'owner', 'manager', 'created_at']
    # Can filter by: city, owner (landlord), manager, creation date

    # Search functionality
    search_fields = ['name', 'address', 'city', 'owner__username']
    # Can search by: property name, address, city, owner's username
    # owner__username = searches in related User model

    # Fields shown when viewing/editing a property
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'city', 'state', 'description')
        }),
        ('Ownership & Management', {
            'fields': ('owner', 'manager')
        }),
    )
    # Organized into collapsible sections
    # Section 1: Basic info (name, address, etc.)
    # Section 2: Who owns/manages it

    # Make these fields read-only (calculated, not editable)
    readonly_fields = ['created_at', 'updated_at']

    # Default ordering in the list
    ordering = ['name']
    # Alphabetical by property name

    # How many properties to show per page
    list_per_page = 20


# ============================================================================
# UNIT ADMIN
# ============================================================================

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    """
    Admin interface for Unit model.
    Shows all units with occupancy status and rent info.
    """

    # Columns shown in the unit list
    list_display = [
        'property',
        'unit_number',
        'floor',
        'bedrooms',
        'bathrooms',
        'rent_amount',
        'is_occupied',
        'get_status_display'
    ]
    # Shows: property | unit# | floor | beds | baths | rent | occupied | status

    # Filters in the right sidebar
    list_filter = [
        'property',
        'is_occupied',
        'bedrooms',
        'bathrooms',
        'created_at'
    ]
    # Can filter by: which property, occupied status, bedroom count, etc.

    # Search functionality
    search_fields = [
        'unit_number',
        'property__name',
        'property__city'
    ]
    # Can search by: unit number, property name, property city
    # property__name = searches in related Property model

    # Fields shown when viewing/editing a unit
    fieldsets = (
        ('Property', {
            'fields': ('property',)
        }),
        ('Unit Identification', {
            'fields': ('unit_number', 'floor')
        }),
        ('Specifications', {
            'fields': ('bedrooms', 'bathrooms', 'square_feet')
        }),
        ('Financial', {
            'fields': ('rent_amount',)
        }),
        ('Status', {
            'fields': ('is_occupied',)
        }),
    )
    # Organized into 5 sections for clarity

    # Make these fields read-only
    readonly_fields = ['created_at', 'updated_at']

    # Default ordering
    ordering = ['property', 'unit_number']
    # Group by property, then by unit number within each property

    # How many units to show per page
    list_per_page = 50
    # More than properties (properties have many units)