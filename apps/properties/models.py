# ============================================================================
# IMPORTS
# ============================================================================

import re

from django.db import models
from django.conf import settings
# settings.AUTH_USER_MODEL points to our custom User model
# Better than importing User directly (more flexible)
from urllib.parse import urlparse, parse_qs
import re



# ============================================================================
# PROPERTY MODEL
# ============================================================================

class Property(models.Model):
    """
    Represents a building or property that contains rental units.
    
    Business Rules:
    - Every property must have an owner (Landlord)
    - Property can optionally have a manager
    - Property contains multiple units
    - Property tracks basic info: name, address, description
    
    Examples:
    - "Sunset Apartments" (20 units)
    - "Downtown Plaza" (50 units)
    - "Family House" (1 unit - single house rental)
    """
    
    # ========================================================================
    # CORE FIELDS
    # ========================================================================
    
    name = models.CharField(
        max_length=200,
        help_text="Property name (e.g., 'Sunset Apartments')"
    )
    # The property's display name
    # max_length=200: Plenty of space for creative names
    # Will show in dropdowns, lists, reports
    
    address = models.CharField(
        max_length=300,
        help_text="Full street address"
    )
    # Physical location of the property
    # "123 Main Street, Apartment Complex A"
    # Used for: tenant info, maintenance visits, legal docs
    
    city = models.CharField(
        max_length=100
    )
    # City where property is located
    # Useful for: filtering by location, reports by city
    
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    # State/Province (optional)
    # blank=True: Form can be submitted without this
    # null=True: Database can store NULL
    # Optional because some countries don't use states
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Property description and amenities"
    )
    # Optional detailed description
    # "Modern apartment complex with pool, gym, parking"
    # TextField = unlimited length (unlike CharField)
    
    # ADD THIS NEW FIELD
    image = models.ImageField(
        upload_to='property_images/%Y/%m/%d',
        blank=True,
        null=True,
        help_text="Property photo"
    )

    # ADD THIS NEW FIELD
    video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="YouTube or Vimeo video URL (e.g., https://www.youtube.com/watch?v=...)"
    )
    # URLField = validates that it's a proper URL
    # User pastes YouTube/Vimeo link
    # We'll convert it to embeddable format in template


    
    
    # ========================================================================
    # OWNERSHIP & MANAGEMENT
    # ========================================================================
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_properties',
        limit_choices_to={'role': 'LANDLORD'}
    )
    # WHO OWNS THIS PROPERTY
    #
    # ForeignKey = "This property belongs to ONE user"
    # settings.AUTH_USER_MODEL = Points to our custom User model
    # on_delete=models.PROTECT = Can't delete user if they own properties
    #   (Must transfer ownership first - prevents data loss)
    #
    # related_name='owned_properties':
    #   Reverse relationship: user.owned_properties.all()
    #   Gets all properties owned by this landlord
    #
    # limit_choices_to={'role': 'LANDLORD'}:
    #   In admin/forms, dropdown only shows Landlords
    #   Prevents accidentally assigning Tenant as owner
    
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='managed_properties',
        limit_choices_to={'role': 'MANAGER'},
        blank=True,
        null=True
    )
    # WHO MANAGES THIS PROPERTY (OPTIONAL)
    #
    # on_delete=models.SET_NULL:
    #   If manager is deleted, property.manager becomes NULL
    #   Property still exists, just unassigned
    #   (Different from owner - losing manager is OK)
    #
    # related_name='managed_properties':
    #   manager.managed_properties.all()
    #   Gets all properties this manager oversees
    #
    # blank=True, null=True:
    #   Manager is optional
    #   Small landlords might manage their own properties
    
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    
    created_at = models.DateTimeField(auto_now_add=True)
    # When property was added to system
    # auto_now_add=True: Set automatically on creation, never changes
    
    updated_at = models.DateTimeField(auto_now=True)
    # When property was last modified
    # auto_now=True: Updates automatically on every save()
    
    
    # ========================================================================
    # META OPTIONS
    # ========================================================================
    
    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['name']
        # How properties appear in admin and queries
        # ordering = ['name']: Alphabetical by name
        # Could also use ['-created_at'] for newest first
    
    
    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================
    
    def __str__(self):
        return f"{self.name} - {self.city}"
        # How property appears when printed
        # Example: "Sunset Apartments - Lagos"
        # Shows in: admin panel, dropdowns, logs
    
    
    # ========================================================================
    # CUSTOM METHODS
    # ========================================================================
    
    def total_units(self):
        """Return total number of units in this property"""
        return self.units.count()
        # self.units is the reverse relationship from Unit model
        # .count() is efficient (SQL COUNT query, not loading all objects)
        # Used in: dashboards, reports
    
    def occupied_units(self):
        """Return number of occupied units"""
        return self.units.filter(is_occupied=True).count()
        # Filter units where is_occupied=True, then count
        # Used in: occupancy rate calculation
    
    def vacant_units(self):
        """Return number of vacant units"""
        return self.units.filter(is_occupied=False).count()
        # Opposite of occupied_units
        # Used in: showing available units to potential tenants
    
    def occupancy_rate(self):
        """Return occupancy rate as percentage"""
        total = self.total_units()
        if total == 0:
            return 0
        # Prevent division by zero
        # If property has no units yet, occupancy is 0%
        
        occupied = self.occupied_units()
        return round((occupied / total) * 100, 2)
        # (occupied / total) * 100 = percentage
        # round(..., 2) = 2 decimal places (e.g., 85.71%)
        # Used in: landlord dashboard, reports

    
    def get_video_embed_url(self):
        """
        Convert YouTube/Vimeo URL to embeddable format.

        Handles:
        - youtube.com/watch?v=ID
        - youtu.be/ID
        - youtube.com/shorts/ID
        - youtube.com/live/ID
        - vimeo.com/ID
        - vimeo.com/ID/HASH  (private/unlisted)

        Returns:
            str | None: Embeddable URL, or None if unsupported/missing.
        """
        if not self.video_url:
            return None

        try:
            parsed = urlparse(self.video_url)
        except ValueError:
            return None

        hostname = parsed.hostname or ""

        # ── YouTube ──────────────────────────────────────────────────────────────
        if hostname in ("www.youtube.com", "youtube.com"):
            # Standard: /watch?v=ID
            if parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [None])[0]

            # Short-form / live: /shorts/ID  or  /live/ID
            else:
                match = re.match(r"^/(?:shorts|live)/([^/?#]+)", parsed.path)
                video_id = match.group(1) if match else None

            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

        elif hostname == "youtu.be":
            # Short URL: youtu.be/ID
            video_id = parsed.path.lstrip("/").split("/")[0] or None
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

        # ── Vimeo ─────────────────────────────────────────────────────────────────
        elif hostname in ("www.vimeo.com", "vimeo.com"):
            # Matches /ID  and  /ID/HASH (private videos)
            match = re.match(r"^/(\d+)(/[a-f0-9]+)?", parsed.path)
            if match:
                video_id = match.group(1)
                private_hash = match.group(2) or ""
                return f"https://player.vimeo.com/video/{video_id}{private_hash}"

        return None


# ============================================================================
# UNIT MODEL
# ============================================================================

class Unit(models.Model):
    """
    Represents an individual rental unit within a property.

    Business Rules:
    - Every unit belongs to exactly one property
    - Each unit has a unique unit_number within its property
    - Unit tracks rent amount, bedrooms, bathrooms
    - is_occupied tracks current occupancy status
    - Unit can only be occupied by ONE active lease at a time

    Examples:
    - Apartment 204 in "Sunset Apartments"
    - House at "123 Main St" (single unit property)
    - Office Suite 5B in "Downtown Plaza"
    """

    # ========================================================================
    # RELATIONSHIP TO PROPERTY
    # ========================================================================

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='units'
    )
    # WHICH PROPERTY THIS UNIT BELONGS TO
    #
    # ForeignKey = "This unit belongs to ONE property"
    # on_delete=models.CASCADE:
    #   If property is deleted, delete all its units too
    #   Makes sense: if building is demolished, units don't exist
    #   (Different from PROTECT - units can't exist without property)
    #
    # related_name='units':
    #   Reverse relationship: property.units.all()
    #   Gets all units in this property
    #   Used in: property detail page, occupancy calculations


    # ========================================================================
    # UNIT IDENTIFICATION
    # ========================================================================

    unit_number = models.CharField(
        max_length=50,
        help_text="Unit identifier (e.g., '204', 'A-12', 'Ground Floor')"
    )
    # How the unit is identified within the property
    # Can be: numbers ("204"), letters ("A"), combinations ("2B")
    # max_length=50: Flexible enough for creative numbering schemes

    floor = models.IntegerField(
        blank=True,
        null=True,
        help_text="Floor number (0=Ground, 1=First, etc.)"
    )
    # Which floor the unit is on
    # Optional because: single houses don't have floors
    # IntegerField = whole numbers only
    # 0 = Ground floor, 1 = First floor, -1 = Basement


    # ========================================================================
    # UNIT SPECIFICATIONS
    # ========================================================================

    bedrooms = models.PositiveIntegerField(
        default=1,
        help_text="Number of bedrooms"
    )
    # How many bedrooms
    # PositiveIntegerField = can't be negative (makes sense!)
    # default=1: Studio/1-bedroom is most common
    # Used in: filtering ("show me 2-bedroom units")

    bathrooms = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=1.0,
        help_text="Number of bathrooms (e.g., 1.5, 2.0)"
    )
    # How many bathrooms
    # DecimalField allows: 1.0, 1.5, 2.0, 2.5 (half baths)
    # max_digits=3: Maximum 3 digits total
    # decimal_places=1: One decimal place (allows .5)
    # Examples: 1.5 (one full, one half bath)

    square_feet = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Unit size in square feet"
    )
    # How big the unit is (optional)
    # Used in: marketing, pricing comparisons
    # Optional because not all landlords track this


    # ========================================================================
    # FINANCIAL
    # ========================================================================

    rent_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monthly rent amount"
    )
    # HOW MUCH RENT THIS UNIT COSTS PER MONTH
    #
    # DecimalField for money (NEVER use FloatField for money!)
    # max_digits=10: Up to 10 digits total (e.g., 99,999,999.99)
    # decimal_places=2: Two decimals (cents/kobo)
    #
    # Why DecimalField not Float?
    # Float has rounding errors: 0.1 + 0.2 = 0.30000000000000004
    # Decimal is exact: 0.1 + 0.2 = 0.3 exactly
    # CRITICAL for financial calculations
    #
    # Examples: 85000.00, 120000.50


    # ========================================================================
    # OCCUPANCY STATUS
    # ========================================================================

    is_occupied = models.BooleanField(
        default=False,
        help_text="Is unit currently occupied?"
    )
    # IS SOMEONE CURRENTLY LIVING HERE?
    #
    # BooleanField = True or False
    # default=False: New units start vacant
    #
    # This gets updated automatically when:
    # - Lease is created → is_occupied = True
    # - Lease ends/terminated → is_occupied = False
    #
    # Used for:
    # - Showing available units to potential tenants
    # - Calculating occupancy rate
    # - Preventing double-booking (validation in Lease model)


    # ========================================================================
    # TIMESTAMPS
    # ========================================================================

    created_at = models.DateTimeField(auto_now_add=True)
    # When unit was added to system

    updated_at = models.DateTimeField(auto_now=True)
    # When unit info was last modified


    # ========================================================================
    # META OPTIONS
    # ========================================================================

    class Meta:
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'
        ordering = ['property', 'unit_number']
        # Order by property first, then unit number within property
        # Result: All units from Property A, then all from Property B

        unique_together = ['property', 'unit_number']
        # CRITICAL CONSTRAINT!
        # No two units in the SAME property can have the SAME unit_number
        #
        # Valid: Property A has Unit 204, Property B has Unit 204
        # Invalid: Property A has TWO units numbered 204
        #
        # Database enforces this - prevents duplicate unit numbers


    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================

    def __str__(self):
        return f"{self.property.name} - Unit {self.unit_number}"
        # How unit appears when printed
        # Example: "Sunset Apartments - Unit 204"
        # Shows property name AND unit number (clear identification)


    # ========================================================================
    # CUSTOM METHODS
    # ========================================================================

    def get_status_display(self):
        """Return human-readable occupancy status"""
        return "Occupied" if self.is_occupied else "Vacant"
        # Simple helper for templates
        # Instead of: {% if unit.is_occupied %}Occupied{% else %}Vacant{% endif %}
        # Use: {{ unit.get_status_display }}

    def current_lease(self):
        """Return the current active lease for this unit (if any)"""
        from apps.leases.models import Lease
        # Import here to avoid circular imports
        # (Lease model will import Unit, Unit imports Lease = circular)

        return self.leases.filter(
            status='ACTIVE'
        ).first()
        # self.leases = reverse relationship from Lease model (we'll build this in Phase 4)
        # filter(status='ACTIVE') = only active leases
        # .first() = get the first one (should only be one active lease)
        # Returns: Lease object or None
        #
        # Used in: Unit detail page to show current tenant

    def is_available(self):
        """Check if unit is available for rent"""
        return not self.is_occupied
        # Simple helper: available = not occupied
        # Could add more logic later:
        # - Check if under maintenance
        # - Check if reserved for incoming tenant
        # For now: simple True/False based on occupancy