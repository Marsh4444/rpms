# ============================================================================
# IMPORTS
# ============================================================================

from django.contrib.auth.models import AbstractUser
# AbstractUser is Django's built-in User model with all the standard fields
# We inherit from it to add our custom fields

from django.db import models
# Django's model class - gives us database functionality


# ============================================================================
# CUSTOM USER MODEL
# ============================================================================

class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    
    Why custom user?
    - Allows us to add fields later without breaking everything
    - Industry best practice
    - Must be done BEFORE first migration
    
    Inherited fields from AbstractUser:
    - username
    - email
    - password (hashed)
    - first_name
    - last_name
    - is_staff (can access admin)
    - is_active (account enabled)
    - is_superuser (full permissions)
    - date_joined
    - last_login
    """
    
    # ========================================================================
    # ROLE CHOICES
    # ========================================================================
    
    LANDLORD = 'LANDLORD'
    MANAGER = 'MANAGER'
    TENANT = 'TENANT'
    
    ROLE_CHOICES = [
        (LANDLORD, 'Landlord'),  # Full control
        (MANAGER, 'Manager'),    # Operations
        (TENANT, 'Tenant'),      # Self-service
    ]
    # These are the 3 roles in our system
    # Stored as 'LANDLORD', 'MANAGER', 'TENANT' in database
    # Displayed as 'Landlord', 'Manager', 'Tenant' to users
    
    
    # ========================================================================
    # CUSTOM FIELDS
    # ========================================================================
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=TENANT,
    )
    # Role field - determines what user can do
    # max_length=20: Maximum 20 characters
    # choices=ROLE_CHOICES: Must be one of the 3 roles above
    # default=TENANT: If not specified, user is a tenant
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    # Optional phone number
    # blank=True: Form can be submitted without this field
    # null=True: Database can store NULL (no value)
    
    profile_picture = models.ImageField(
        upload_to='profile_pictures/%Y/%m/%d',
        blank=True,
        null=True,
    )
    # Optional profile picture
    # upload_to='profile_pictures/': Files saved to media/profile_pictures/
    # Requires Pillow (already installed)
    
    
    # ========================================================================
    # META OPTIONS
    # ========================================================================
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        # How users appear in admin
        # ordering = ['-date_joined']: Newest users first (- means descending)
    
    
    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
        # How the user appears when printed
        # Example: "john_doe (Landlord)"
        # get_role_display() converts 'LANDLORD' to 'Landlord'
    
    
    # ========================================================================
    # CUSTOM METHODS
    # ========================================================================
    
    def is_landlord(self):
        """Check if user is a landlord"""
        return self.role == self.LANDLORD
    
    def is_manager(self):
        """Check if user is a manager"""
        return self.role == self.MANAGER
    
    def is_tenant(self):
        """Check if user is a tenant"""
        return self.role == self.TENANT
    
    # These methods make it easy to check roles in views:
    # if request.user.is_landlord():
    #     # Show landlord dashboard