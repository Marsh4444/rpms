# ============================================================================
# IMPORTS
# ============================================================================

from django.contrib import admin
from .models import TenantProfile, Lease


# ============================================================================
# TENANT PROFILE ADMIN
# ============================================================================

@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for TenantProfile model.
    Shows tenant extended information.
    """
    
    # Columns shown in the tenant profile list
    list_display = [
        'user',
        'emergency_contact_name',
        'emergency_contact_phone',
        'created_at'
    ]
    # Shows: user | emergency contact | phone | created date
    
    # Filters in the right sidebar
    list_filter = ['created_at']
    # Can filter by: creation date
    
    # Search functionality
    search_fields = [
        'user__username',
        'user__email',
        'emergency_contact_name',
        'emergency_contact_phone'
    ]
    # Can search by: username, email, emergency contact details
    # user__username = searches in related User model
    
    # Fields shown when viewing/editing a tenant profile
    fieldsets = (
        ('Tenant', {
            'fields': ('user',)
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone',
                'emergency_contact_relationship'
            )
        }),
        ('Documentation', {
            'fields': ('id_document',)
        }),
    )
    # Organized into 3 sections:
    # 1. Which user this profile belongs to
    # 2. Emergency contact info
    # 3. ID documents
    
    # Make timestamps read-only
    readonly_fields = ['created_at', 'updated_at']
    
    # Default ordering
    ordering = ['-created_at']
    # Newest profiles first
    
    # How many profiles per page
    list_per_page = 25


# ============================================================================
# LEASE ADMIN
# ============================================================================

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    """
    Admin interface for Lease model.
    Shows all leases with status, dates, and financial info.
    """
    
    # Columns shown in the lease list
    list_display = [
        'unit',
        'tenant',
        'start_date',
        'end_date',
        'monthly_rent',
        'status',
        'days_remaining',
        'created_at'
    ]
    # Shows: unit | tenant | start | end | rent | status | days left | created
    
    # Filters in the right sidebar
    list_filter = [
        'status',
        'start_date',
        'end_date',
        'created_at',
        'unit__property'
    ]
    # Can filter by: status, dates, which property
    # unit__property = filter by the property the unit belongs to
    
    # Search functionality
    search_fields = [
        'unit__unit_number',
        'unit__property__name',
        'tenant__username',
        'tenant__email',
        'tenant__first_name',
        'tenant__last_name'
    ]
    # Can search by:
    # - Unit number
    # - Property name (through unit)
    # - Tenant username/email/name
    
    # Fields shown when viewing/editing a lease
    fieldsets = (
        ('Lease Details', {
            'fields': ('unit', 'tenant', 'created_by')
        }),
        ('Lease Terms', {
            'fields': (
                'start_date',
                'end_date',
                'monthly_rent',
                'security_deposit'
            )
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
    )
    # Organized into 3 sections:
    # 1. Unit, tenant, who created it
    # 2. Dates and financial terms
    # 3. Current status and notes
    
    # Make timestamps read-only
    readonly_fields = ['created_at', 'updated_at']
    
    # Default ordering
    ordering = ['-start_date']
    # Newest leases first (by start date)
    
    # How many leases per page
    list_per_page = 30
    
    # Date hierarchy navigation (useful for filtering by year/month)
    date_hierarchy = 'start_date'
    # Adds navigation: 2025 > March > Day
    # Makes it easy to find leases from specific time periods
    
    # Actions that can be performed on multiple leases at once
    actions = ['mark_as_terminated', 'mark_as_expired']
    
    def mark_as_terminated(self, request, queryset):
        """
        Admin action to terminate selected leases.
        """
        updated = queryset.update(status=Lease.TERMINATED)
        # Update all selected leases to TERMINATED status
        
        # Update unit occupancy for each lease
        for lease in queryset:
            lease.unit.is_occupied = False
            lease.unit.save()
        
        self.message_user(
            request,
            f'{updated} lease(s) marked as terminated.'
        )
        # Show success message to admin
    
    mark_as_terminated.short_description = "Mark selected leases as Terminated"
    # Text shown in the actions dropdown
    
    def mark_as_expired(self, request, queryset):
        """
        Admin action to mark selected leases as expired.
        """
        updated = queryset.update(status=Lease.EXPIRED)
        
        # Update unit occupancy
        for lease in queryset:
            lease.unit.is_occupied = False
            lease.unit.save()
        
        self.message_user(
            request,
            f'{updated} lease(s) marked as expired.'
        )
    
    mark_as_expired.short_description = "Mark selected leases as Expired"