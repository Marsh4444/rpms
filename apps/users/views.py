# ============================================================================
# IMPORTS
# ============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import UserRegistrationForm
from .models import User


# ============================================================================
# HOME VIEW
# ============================================================================

def home(request):
    """
    Display the landing page.
    
    If user is already logged in, redirect to dashboard.
    Otherwise, show the home page with features.
    """
    #if request.user.is_authenticated:
        # TODO: uncomment when dashboard is built (Phase 12)
        # User is logged in, send to dashboard
        # (We'll build dashboards in Phase 12, for now just show a message)
        #return redirect('dashboard')  # Temporary - will change to dashboard later
    
    # User not logged in, show home page
    return render(request, 'home.html')


# ============================================================================
# LOGIN VIEW
# ============================================================================

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Handle user login.
    
    GET: Display login form
    POST: Process login credentials
    
    Flow:
    1. User enters username and password
    2. Django checks if credentials are valid
    3. If valid: Log user in and redirect
    4. If invalid: Show error message
    """
    
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('home')
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        # Get username and password from form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate user
        user = authenticate(request, username=username, password=password)
        # authenticate() returns User object if valid, None if invalid
        
        if user is not None:
            # Credentials are valid - log the user in
            login(request, user)
            # login() creates a session for the user
            
            # Show success message
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next page (or home if no next page)
            next_page = request.GET.get('next', 'home')
            # 'next' parameter used when login is required to access a page
            # Example: Trying to access /properties/ without login
            #   → Redirects to /login/?next=/properties/
            #   → After login, redirects back to /properties/
            
            return redirect(next_page)
        else:
            # Credentials are invalid
            messages.error(request, 'Invalid username or password.')
            # Error message will display in the template
    
    # Handle GET request (show form)
    # Also handles POST with errors (re-display form)
    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


# ============================================================================
# REGISTER VIEW
# ============================================================================

@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Handle user registration.
    
    GET: Display registration form
    POST: Create new user account
    
    Flow:
    1. User fills out registration form
    2. Django validates data (username unique, passwords match, etc.)
    3. If valid: Create user, log them in, redirect
    4. If invalid: Show error messages
    """
    
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        messages.info(request, 'You are already registered and logged in.')
        return redirect('home')
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        # Create form with submitted data
        form = UserRegistrationForm(request.POST)
        # UserRegistrationForm is our custom form (we'll create it next)
        
        if form.is_valid():
            # All validation passed
            # form.is_valid() checks:
            # - Username not already taken
            # - Email is valid format
            # - Passwords match
            # - Password meets Django's requirements
            
            # Create the user (but don't save to database yet)
            user = form.save(commit=False)
            # commit=False means "create User object but don't save yet"
            # Why? So we can modify it before saving
            
            # Set the role from the form
            user.role = form.cleaned_data.get('role')
            # cleaned_data = validated and cleaned form data
            
            # Now save to database
            user.save()
            
            # Log the user in immediately after registration
            login(request, user)
            # Good UX: Don't make them login after registering
            
            # Show success message
            messages.success(
                request, 
                f'Welcome to RPMS, {user.username}! Your account has been created.'
            )
            
            # Redirect to home (or dashboard when we build it)
            return redirect('home')
        else:
            # Form validation failed
            # Errors will be displayed in the template via {{ form.errors }}
            messages.error(request, 'Please correct the errors below.')
    else:
        # Handle GET request (show empty form)
        form = UserRegistrationForm()
    
    # Render the registration page
    return render(request, 'registration/register.html', {'form': form})


# ============================================================================
# LOGOUT VIEW
# ============================================================================

def logout_view(request):
    """
    Handle user logout.
    
    Flow:
    1. User clicks "Logout" link
    2. Django destroys the session
    3. Redirect to home page
    """
    
    # Log the user out
    logout(request)
    # logout() destroys the session (user is no longer authenticated)
    
    # Show success message
    messages.success(request, 'You have been logged out successfully.')
    
    # Redirect to home page
    return redirect('home')

# ADD THESE NEW VIEWS

@login_required
def profile_view(request):
    """
    Display user's profile.
    """
    return render(request, 'users/profile.html', {'user': request.user})


@login_required
def profile_edit_view(request):
    """
    Edit user's profile.
    """
    if request.method == 'POST':
        # Update user fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.phone_number = request.POST.get('phone_number', '')
        request.user.bio = request.POST.get('bio', '')
        request.user.company_name = request.POST.get('company_name', '')
        request.user.address = request.POST.get('address', '')
        request.user.city = request.POST.get('city', '')
        request.user.state = request.POST.get('state', '')
        request.user.website = request.POST.get('website', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            request.user.profile_picture = request.FILES['profile_picture']
        
        # Handle profile picture removal
        if request.POST.get('profile_picture-clear'):
            request.user.profile_picture = None
        
        request.user.save()
        
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('profile')
    
    return render(request, 'users/profile_edit.html', {'user': request.user})