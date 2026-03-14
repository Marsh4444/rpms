# ============================================================================
# IMPORTS
# ============================================================================

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


# ============================================================================
# USER REGISTRATION FORM
# ============================================================================

class UserRegistrationForm(UserCreationForm):
    """
    Custom registration form that extends Django's UserCreationForm.
    
    Adds:
    - Email field (required)
    - First name and last name fields
    - Role selection (Landlord/Manager/Tenant)
    
    Inherits from UserCreationForm:
    - Username field
    - Password1 and Password2 fields
    - Password validation
    """
    
    # Email field (required)
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.'
    )
    # EmailField validates email format automatically
    # required=True means form won't validate without it
    
    # First name (optional)
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text='Optional. Your first name.'
    )
    
    # Last name (optional)
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text='Optional. Your last name.'
    )
    
    # Role selection (required)
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        help_text='Required. Select your role in the system.'
    )
    # ChoiceField creates a dropdown
    # User.ROLE_CHOICES comes from our User model:
    #   [('LANDLORD', 'Landlord'), ('MANAGER', 'Manager'), ('TENANT', 'Tenant')]
    
    class Meta:
        """
        Meta options for the form.
        
        Tells Django:
        - Which model this form is for
        - Which fields to include
        - What order to show them
        """
        model = User
        # This form creates/edits User objects
        
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'password1',
            'password2',
        ]
        # Order matters - this is the order fields appear in the form
        # password1 = "Password"
        # password2 = "Confirm Password"
        # These come from UserCreationForm parent class
    
    def clean_email(self):
        """
        Validate that email is unique.
        
        Django calls this automatically when validating the form.
        Method name pattern: clean_<field_name>
        """
        email = self.cleaned_data.get('email')
        # cleaned_data = data that passed initial validation
        
        # Check if email already exists in database
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
            # ValidationError stops form submission and shows error message
        
        return email
        # Return the cleaned value if validation passed
    
    def save(self, commit=True):
        """
        Override save method to set email on the user.
        
        Why override?
        - UserCreationForm doesn't save email by default
        - We need to explicitly set it
        """
        user = super().save(commit=False)
        # Call parent save() with commit=False
        # Creates User object but doesn't save to database yet
        
        # Set email from cleaned data
        user.email = self.cleaned_data['email']
        
        # Set first_name and last_name if provided
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        if commit:
            # Save to database if commit=True
            user.save()
        
        return user
        # Return the User object