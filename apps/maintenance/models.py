from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.
class MaintenanceRequest(models.Model):
    """ Represents a maintenance or repair request for a rental unit. """

    #CORE RELATIONSHIPS
    # - Unit (which unit has the issue)
    unit = models.ForeignKey('properties.Unit', on_delete=models.CASCADE, 
            related_name='maintenance_requests')
    
    # - Submitted by (tenant)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,  
        related_name='submitted_maintenance_requests', null=True, limit_choices_to={'role': 'TENANT'})
    
    # - Assigned to (manager)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
        related_name='assigned_maintenance_requests', null=True, 
        blank=True, limit_choices_to={'role': 'MANAGER'})
    
    #REQUEST DETAILS
    # - Title, description
    title = models.CharField(max_length=200, help_text="Brief title describing the issue")
    description = models.TextField(help_text="Detailed description of the maintenance issue")
    
    # - Priority (LOW, MEDIUM, HIGH, EMERGENCY)
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('EMERGENCY', 'Emergency'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # - Status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
# - Image upload (optional photo of problem)
    image = models.ImageField(upload_to='maintenance_images/%Y/%m/%d', blank=True, null=True)
# - Created/resolved timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the issue was resolved")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Maintenance Request"
        verbose_name_plural = "Maintenance Requests"

    def __str__(self):
        return f"{self.title} - {self.unit} - ({self.get_status_display()})"
    
    #Validation to ensure resolved_at is set when status is RESOLVED or CLOSED
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def clean(self):
        """
        Custom validation - called before saving.
        """
        super().clean()
        
        # Rule 1: If status is RESOLVED or CLOSED, must have resolved_at
        if self.status in ['RESOLVED', 'CLOSED']:
            if not self.resolved_at:
                # Auto-set resolved_at if not already set
                self.resolved_at = timezone.now()
        
        # Rule 2: If status is OPEN or IN_PROGRESS, resolved_at should be None
        if self.status in ['OPEN', 'IN_PROGRESS']:
            self.resolved_at = None
            # Clear resolved_at if status goes back to OPEN
            # (e.g., issue wasn't actually fixed)
    
    
    # ========================================================================
    # CUSTOM METHODS
    # ========================================================================
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-set resolved_at timestamp.
        """
        # Call validation
        self.full_clean()
        
        # Save the request
        super().save(*args, **kwargs)
    
    
    def is_open(self):
        """Check if request is still open (not started)"""
        return self.status == 'OPEN'
    
    
    def is_in_progress(self):
        """Check if request is currently being worked on"""
        return self.status == 'IN_PROGRESS'
    
    
    def is_resolved(self):
        """Check if request has been resolved"""
        return self.status in ['RESOLVED', 'CLOSED']
    
    
    def response_time_days(self):
        """
        Calculate how long request has been open (in days).
        Returns None if already resolved.
        """
        if self.is_resolved():
            return None
        
        delta = timezone.now() - self.created_at
        return delta.days
    
    
    def resolution_time(self):
        """
        Calculate total time from creation to resolution.
        Returns None if not yet resolved.
        """
        if not self.resolved_at:
            return None
        
        delta = self.resolved_at - self.created_at
        return delta.days
        # Returns number of days
        # Example: Created Jan 1, resolved Jan 5 → 4 days
    
    
    def is_overdue(self):
        """
        Check if request is taking too long based on priority.
        
        SLA (Service Level Agreement):
        - EMERGENCY: 24 hours
        - HIGH: 3 days
        - MEDIUM: 7 days
        - LOW: 14 days
        """
        if self.is_resolved():
            return False  # Already resolved, not overdue
        
        # Calculate how long request has been open
        hours_open = (timezone.now() - self.created_at).total_seconds() / 3600
        days_open = hours_open / 24
        
        # Check against SLA for each priority
        if self.priority == 'EMERGENCY':
            return hours_open > 24  # More than 24 hours
        elif self.priority == 'HIGH':
            return days_open > 3  # More than 3 days
        elif self.priority == 'MEDIUM':
            return days_open > 7  # More than 7 days
        elif self.priority == 'LOW':
            return days_open > 14  # More than 14 days
        
        return False
    
    
    def get_priority_color(self):
        """
        Return color code for priority (used in templates/admin).
        """
        colors = {
            'EMERGENCY': '#dc2626',  # Red
            'HIGH': '#f59e0b',       # Orange
            'MEDIUM': '#3b82f6',     # Blue
            'LOW': '#10b981',        # Green
        }
        return colors.get(self.priority, '#6b7280')  # Default gray
    
    
    def get_status_badge(self):
        """
        Return emoji badge for status (used in admin).
        """
        badges = {
            'OPEN': '🔵',           # Blue circle
            'IN_PROGRESS': '🟡',    # Yellow circle
            'RESOLVED': '🟢',       # Green circle
            'CLOSED': '⚫',         # Black circle
        }
        return badges.get(self.status, '⚪')  # Default white circle
    
    
    def days_since_created(self):
        """
        Calculate how many days since request was created.
        """
        delta = timezone.now() - self.created_at
        return delta.days
    
    
    def priority_display_with_emoji(self):
        """
        Return priority with emoji for admin display.
        """
        emojis = {
            'EMERGENCY': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
        }
        emoji = emojis.get(self.priority, '⚪')
        return f"{emoji} {self.get_priority_display()}"