# ============================================================================
# IMPORTS
# ============================================================================

from django.contrib import admin
from .models import MaintenanceRequest


# ============================================================================
# MAINTENANCE REQUEST ADMIN
# ============================================================================

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for MaintenanceRequest model.
    Shows all maintenance requests with priority, status, and overdue tracking.
    """
    
    # Columns shown in the list
    list_display = [
        'title',
        'unit',
        'submitted_by',
        'priority_display',
        'status_display',
        'assigned_to',
        'days_since_created',
        'is_overdue',
        'created_at'
    ]
    
    # Filters in sidebar
    list_filter = [
        'priority',
        'status',
        'unit__property',
        'assigned_to',
        'created_at'
    ]
    
    # Search functionality
    search_fields = [
        'title',
        'description',
        'unit__unit_number',
        'unit__property__name',
        'submitted_by__username',
        'submitted_by__email'
    ]
    
    # Fields when viewing/editing
    fieldsets = (
        ('Request Information', {
            'fields': ('unit', 'submitted_by', 'assigned_to')
        }),
        ('Issue Details', {
            'fields': ('title', 'description', 'image', 'priority', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ['created_at', 'updated_at']
    
    # Default ordering
    ordering = ['-created_at']
    
    # Pagination
    list_per_page = 30
    
    # Date hierarchy
    date_hierarchy = 'created_at'
    
    # Bulk actions
    actions = ['mark_as_in_progress', 'mark_as_resolved', 'mark_as_closed']
    
    # Custom display methods
    def priority_display(self, obj):
        """Display priority with emoji"""
        return obj.priority_display_with_emoji()
    priority_display.short_description = 'Priority'
    priority_display.admin_order_field = 'priority'
    
    def status_display(self, obj):
        """Display status with emoji"""
        badge = obj.get_status_badge()
        return f"{badge} {obj.get_status_display()}"
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    # Bulk action methods
    def mark_as_in_progress(self, request, queryset):
        """Mark selected requests as In Progress"""
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f'{updated} request(s) marked as In Progress.')
    mark_as_in_progress.short_description = "Mark as In Progress"
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected requests as Resolved"""
        from django.utils import timezone
        for req in queryset:
            req.status = 'RESOLVED'
            req.resolved_at = timezone.now()
            req.save()
        self.message_user(request, f'{queryset.count()} request(s) marked as Resolved.')
    mark_as_resolved.short_description = "Mark as Resolved"
    
    def mark_as_closed(self, request, queryset):
        """Mark selected requests as Closed"""
        from django.utils import timezone
        for req in queryset:
            req.status = 'CLOSED'
            if not req.resolved_at:
                req.resolved_at = timezone.now()
            req.save()
        self.message_user(request, f'{queryset.count()} request(s) marked as Closed.')
    mark_as_closed.short_description = "Mark as Closed"
