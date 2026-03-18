# ============================================================================
# IMPORTS
# ============================================================================

from django import forms
from django.db.models import Q
from .models import Lease, TenantProfile
from apps.users.models import User
from apps.properties.models import Unit


# ============================================================================
# LEASE FORM
# ============================================================================

class LeaseForm(forms.ModelForm):
    """
    Form for creating and editing leases.
    
    Key Features:
    1. Dynamic dropdowns (units, tenants loaded from database)
    2. Date validation (end > start, no overlaps)
    3. Conditional unit filtering (vacant only for new leases)
    4. Security (only show user's units and tenant users)
    
    This form is used in both LeaseCreateView and LeaseUpdateView.
    """
    
    class Meta:
        model = Lease
        fields = [
            'unit',           # Which unit to lease
            'tenant',         # Which tenant is leasing it
            'start_date',     # When lease starts
            'end_date',       # When lease ends
            'monthly_rent',   # How much rent per month
            'security_deposit',  # Upfront deposit
            'notes'           # Any special terms
        ]
        # We DON'T include 'created_by' or 'status' - those are auto-set
        
        # Custom widgets for better UX
        widgets = {
            'start_date': forms.DateInput(
                attrs={
                    'type': 'date',  # HTML5 date picker
                    'class': 'form-input'
                }
            ),
            'end_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-input'
                }
            ),
            'monthly_rent': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'step': '0.01',  # Allow decimals
                    'min': '0'       # Can't be negative
                }
            ),
            'security_deposit': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'step': '0.01',
                    'min': '0'
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-input',
                    'rows': 4
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Custom initialization to filter choices based on current user.
        
        This method runs BEFORE the form is displayed.
        It customizes the dropdown options based on who's logged in.
        
        Args:
            user: The logged-in user (landlord creating the lease)
            *args, **kwargs: Standard Django form arguments
        """
        # Extract the 'user' argument (passed from view)
        user = kwargs.pop('user', None)
        # kwargs.pop() removes 'user' from kwargs and returns its value
        # We must remove it because Django's form doesn't expect 'user'
        
        # Call parent __init__ to do standard form setup
        super().__init__(*args, **kwargs)
        
        # Only proceed if we have a user (should always be true)
        if user:
            # ================================================================
            # FILTER UNITS: Only show user's units
            # ================================================================
            
            # Get all units from properties owned by this user
            user_units = Unit.objects.filter(property__owner=user)
            # property__owner follows: Unit → Property → owner
            # Double underscore (__) means "follow relationship"
            
            # CONDITIONAL LOGIC: Create vs Edit
            if self.instance.pk:
                # self.instance.pk exists = EDITING existing lease
                # We need to show:
                # 1. The unit currently in this lease (even if occupied)
                # 2. Other vacant units (in case they want to change)
                
                self.fields['unit'].queryset = user_units.filter(
                    Q(pk=self.instance.unit.pk) |  # Current unit
                    Q(is_occupied=False)            # OR vacant units
                )
                # Q objects allow OR logic
                # Without Q: filter(a=1, b=2) means a=1 AND b=2
                # With Q: filter(Q(a=1) | Q(b=2)) means a=1 OR b=2
                
            else:
                # self.instance.pk is None = CREATING new lease
                # Show only vacant units
                self.fields['unit'].queryset = user_units.filter(
                    is_occupied=False
                )
            
            # ================================================================
            # FILTER TENANTS: Only show users with TENANT role
            # ================================================================
            
            self.fields['tenant'].queryset = User.objects.filter(
                role='TENANT'
            )
            # We don't want landlords or managers in the tenant dropdown!
            
            # Make the queryset distinct (no duplicates)
            self.fields['tenant'].queryset = self.fields['tenant'].queryset.distinct()
    
    def clean(self):
        """
        Custom validation that runs AFTER field-level validation.
        
        This is where we check business logic:
        1. End date must be after start date
        2. No overlapping leases for the same unit
        
        Django's validation flow:
        User submits form
            ↓
        Field validation (required, type, etc.)
            ↓
        clean() method ← WE ARE HERE
            ↓
        If valid: save()
        If invalid: show errors
        
        Returns:
            cleaned_data: Dictionary of validated field values
        
        Raises:
            forms.ValidationError: If validation fails
        """
        # Get the validated data from parent class
        cleaned_data = super().clean()
        # cleaned_data = {'unit': Unit object, 'tenant': User object, ...}
        
        # Extract individual fields
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        unit = cleaned_data.get('unit')
        
        # ================================================================
        # VALIDATION 1: End date must be after start date
        # ================================================================
        
        if start_date and end_date:
            # Both dates exist (not None)
            
            if end_date <= start_date:
                # End date is same or before start date
                # This makes no sense!
                
                raise forms.ValidationError(
                    "End date must be after start date."
                )
                # This error will appear at top of form
        
        # ================================================================
        # VALIDATION 2: No overlapping leases for same unit
        # ================================================================
        
        if unit and start_date and end_date:
            # All required data exists
            
            # Find other active leases for this unit
            overlapping_leases = Lease.objects.filter(
                unit=unit,           # Same unit
                status='ACTIVE'      # Only active leases
            )
            
            # If editing, exclude current lease from check
            if self.instance.pk:
                overlapping_leases = overlapping_leases.exclude(
                    pk=self.instance.pk
                )
                # Don't compare lease with itself!
            
            # Check each existing lease for overlap
            for lease in overlapping_leases:
                # Overlap detection logic:
                # Two date ranges overlap if:
                # - New lease starts BEFORE existing ends
                # - AND new lease ends AFTER existing starts
                
                if (start_date <= lease.end_date and 
                    end_date >= lease.start_date):
                    # OVERLAP DETECTED!
                    
                    raise forms.ValidationError(
                        f"This unit already has an active lease from "
                        f"{lease.start_date} to {lease.end_date}. "
                        f"Tenant: {lease.tenant.get_full_name() or lease.tenant.username}"
                    )
                    # Show helpful error with existing lease details
        
        # All validations passed!
        return cleaned_data
        # Django will now save the data