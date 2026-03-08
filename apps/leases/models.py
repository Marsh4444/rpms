# ============================================================================
# IMPORTS
# ============================================================================

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
# timezone for date/time handling with timezone awareness


# ============================================================================
# TENANT PROFILE MODEL
# ============================================================================

class TenantProfile(models.Model):
    """
    Extended information for users with TENANT role.

    Why separate from User model?
    - Not all users are tenants (landlords/managers don't need this)
    - Keeps User model clean
    - Only created when user becomes a tenant

    Contains:
    - Emergency contact information
    - ID/documentation
    - Additional tenant-specific data
    """

    # ========================================================================
    # USER RELATIONSHIP
    # ========================================================================

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_profile'
    )
    # WHICH USER THIS PROFILE BELONGS TO
    #
    # OneToOneField = "Each user has ONE profile, each profile has ONE user"
    # Different from ForeignKey (one-to-many)
    #
    # on_delete=models.CASCADE:
    #   If user is deleted, delete their tenant profile too
    #   Makes sense: profile can't exist without the user
    #
    # related_name='tenant_profile':
    #   Reverse relationship: user.tenant_profile
    #   Access profile from user: tenant_user.tenant_profile.emergency_contact


    # ========================================================================
    # EMERGENCY CONTACT
    # ========================================================================

    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Full name of emergency contact"
    )
    # Who to contact if tenant has emergency
    # Optional but recommended

    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number of emergency contact"
    )
    # How to reach emergency contact

    emergency_contact_relationship = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Relationship to tenant (e.g., 'Mother', 'Brother')"
    )
    # Who they are to the tenant
    # Examples: "Mother", "Brother", "Friend"


    # ========================================================================
    # DOCUMENTATION
    # ========================================================================

    id_document = models.FileField(
        upload_to='tenant_documents/',
        blank=True,
        null=True,
        help_text="ID card, passport, or driver's license"
    )
    # Scanned copy of tenant's ID
    # FileField accepts any file type (PDF, image, etc.)
    # upload_to='tenant_documents/': Files saved to media/tenant_documents/
    # Optional but many landlords require this


    # ========================================================================
    # TIMESTAMPS
    # ========================================================================

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # ========================================================================
    # META OPTIONS
    # ========================================================================

    class Meta:
        verbose_name = 'Tenant Profile'
        verbose_name_plural = 'Tenant Profiles'
        ordering = ['-created_at']


    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================

    def __str__(self):
        return f"Profile for {self.user.username}"
        # Example: "Profile for john_doe"


# ============================================================================
# LEASE MODEL
# ============================================================================

class Lease(models.Model):
    """
    Represents a rental agreement between landlord and tenant.

    Critical Business Rules:
    1. No overlapping leases on the same unit
    2. Unit becomes occupied when lease is active
    3. Unit becomes vacant when lease ends
    4. Lease must have start and end date
    5. Rent amount from lease, not just unit default

    Lifecycle:
    - ACTIVE: Currently valid, tenant living there
    - EXPIRED: End date passed, tenant should move out
    - TERMINATED: Ended early by landlord or tenant
    """

    # ========================================================================
    # STATUS CHOICES
    # ========================================================================

    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'
    TERMINATED = 'TERMINATED'

    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (EXPIRED, 'Expired'),
        (TERMINATED, 'Terminated'),
    ]
    # Lease can be in one of three states


    # ========================================================================
    # CORE RELATIONSHIPS
    # ========================================================================

    unit = models.ForeignKey(
        'properties.Unit',
        on_delete=models.PROTECT,
        related_name='leases'
    )
    # WHICH UNIT IS BEING RENTED
    #
    # 'properties.Unit' = string reference to avoid circular imports
    # on_delete=models.PROTECT:
    #   Can't delete unit if it has leases
    #   Must terminate/delete leases first
    #   Prevents accidental data loss
    #
    # related_name='leases':
    #   unit.leases.all() = all leases for this unit (past and present)

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='leases',
        limit_choices_to={'role': 'TENANT'}
    )
    # WHO IS RENTING THE UNIT
    #
    # on_delete=models.PROTECT:
    #   Can't delete tenant if they have leases
    #   Financial/legal records must be preserved
    #
    # limit_choices_to={'role': 'TENANT'}:
    #   Only show users with TENANT role in dropdown
    #   Prevents assigning landlord as tenant

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_leases',
        null=True,
        blank=True
    )
    # WHO CREATED THIS LEASE (landlord or manager)
    # Audit trail - know who created the lease
    # on_delete=models.SET_NULL: If user deleted, lease remains but creator = NULL


    # ========================================================================
    # LEASE TERMS
    # ========================================================================

    start_date = models.DateField(
        help_text="Lease start date"
    )
    # When tenant can move in
    # DateField = date only (no time)
    # REQUIRED field - every lease must have start date

    end_date = models.DateField(
        help_text="Lease end date"
    )
    # When tenant must move out
    # REQUIRED field - every lease must have end date
    # Used to detect expired leases

    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monthly rent amount for this lease"
    )
    # HOW MUCH RENT FOR THIS LEASE
    #
    # Why not just use unit.rent_amount?
    # - Rent can be negotiated (different from unit default)
    # - Rent might increase mid-tenancy
    # - Historical record (unit.rent_amount might change)
    #
    # Decimal for exact money calculations

    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Security deposit amount"
    )
    # Upfront deposit (usually 1-2 months rent)
    # Refunded when tenant moves out (if no damages)
    # default=0.00: Optional, some leases don't require deposit


    # ========================================================================
    # STATUS & METADATA
    # ========================================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )
    # Current state of the lease
    # default=ACTIVE: New leases start as active

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or terms"
    )
    # Optional additional information
    # "Pet allowed with $50/month pet rent"
    # "Includes parking space #24"


    # ========================================================================
    # TIMESTAMPS
    # ========================================================================

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # ========================================================================
    # META OPTIONS
    # ========================================================================

    class Meta:
        verbose_name = 'Lease'
        verbose_name_plural = 'Leases'
        ordering = ['-start_date']
        # Newest leases first


    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================

    def __str__(self):
        return f"{self.unit} - {self.tenant.username} ({self.get_status_display()})"
        # Example: "Sunset Apartments - Unit 204 - john_doe (Active)"


    # ========================================================================
    # VALIDATION
    # ========================================================================

    def clean(self):
        """
        Custom validation - called before saving.
        Enforces business rules.
        """
        super().clean()

        # Rule 1: Start date must be before end date
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': 'End date must be after start date.'
                })

        # Rule 2: No overlapping leases on the same unit
        if self.unit:
            # Get all ACTIVE leases for this unit
            overlapping_leases = Lease.objects.filter(
                unit=self.unit,
                status=self.ACTIVE
            ).exclude(pk=self.pk)
            # exclude(pk=self.pk) = don't check against yourself when editing

            for lease in overlapping_leases:
                # Check if dates overlap
                if (self.start_date <= lease.end_date and
                    self.end_date >= lease.start_date):
                    raise ValidationError({
                        'unit': f'This unit already has an active lease from {lease.start_date} to {lease.end_date}.'
                    })


    # ========================================================================
    # CUSTOM METHODS
    # ========================================================================

    def save(self, *args, **kwargs):
        """
        Override save to update unit occupancy status.
        """
        # Call validation
        self.full_clean()

        # Save the lease
        super().save(*args, **kwargs)

        # Update unit occupancy status
        if self.status == self.ACTIVE:
            # Active lease = unit is occupied
            self.unit.is_occupied = True
            self.unit.save()
        elif self.status in [self.EXPIRED, self.TERMINATED]:
            # Expired or terminated = unit is vacant
            self.unit.is_occupied = False
            self.unit.save()

    def is_active(self):
        """Check if lease is currently active"""
        return self.status == self.ACTIVE

    def days_remaining(self):
        """Calculate days until lease ends"""
        if self.status != self.ACTIVE:
            return 0

        today = timezone.now().date()
        if self.end_date > today:
            return (self.end_date - today).days
        return 0
        # Returns: number of days until end_date
        # Used in: tenant dashboard "Your lease expires in 45 days"

    def is_expired(self):
        """Check if lease has passed its end date"""
        today = timezone.now().date()
        return self.end_date < today and self.status == self.ACTIVE
        # If end_date passed and still ACTIVE = should be marked EXPIRED
        # This can be automated with a daily cron job