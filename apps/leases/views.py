# ============================================================================
# IMPORTS
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Lease, TenantProfile
from .forms import LeaseForm
from apps.properties.models import Unit


# ============================================================================
# STEP 2: LEASE LIST VIEW
# ============================================================================

class LeaseListView(LoginRequiredMixin, ListView):
    """
    Display list of all leases for the logged-in landlord.
    
    Features:
    1. Shows only leases for user's properties
    2. Filters by status (Active/Expired/Terminated)
    3. Displays with pagination (10 per page)
    4. Calculates statistics (total leases, active, expired)
    
    URL: /leases/
    Template: templates/leases/lease_list.html
    """
    
    model = Lease
    # Which model to query
    
    template_name = 'leases/lease_list.html'
    # Which template to render
    
    context_object_name = 'leases'
    # Variable name in template (instead of 'object_list')
    # Now we can use {{ leases }} in template
    
    paginate_by = 10
    # Show 10 leases per page
    # Django automatically handles pagination
    
    ordering = ['-created_at']
    # Order by most recent first
    # '-' means descending (newest first)
    # Without '-' would be ascending (oldest first)
    
    def get_queryset(self):
        """
        Filter leases to show only those for user's properties.
        
        This is a SECURITY measure!
        Without this, landlords would see ALL leases (including competitors).
        
        Flow:
        1. Get all leases
        2. Filter to only leases for units in user's properties
        3. Apply status filter if requested
        
        Returns:
            QuerySet of Lease objects owned by current user
        """
        # Get the logged-in user
        user = self.request.user
        # self.request.user = currently authenticated user
        
        # Filter leases to only those for user's properties
        queryset = Lease.objects.filter(
            unit__property__owner=user
        )
        # unit__property__owner follows relationships:
        # Lease → unit (ForeignKey)
        #     → property (ForeignKey)
        #         → owner (ForeignKey)
        # Result: Only leases where the property owner is current user
        
        # Check if user wants to filter by status
        status = self.request.GET.get('status')
        # self.request.GET = URL parameters
        # Example: /leases/?status=ACTIVE
        # status = 'ACTIVE'
        
        if status:
            # User requested specific status filter
            queryset = queryset.filter(status=status)
            # Further filter the queryset
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add extra data to template context.
        
        Default context (from ListView):
        - leases: List of Lease objects
        - is_paginated: True if more than paginate_by items
        - page_obj: Current page object
        
        We add:
        - total_leases: Count of all user's leases
        - active_leases: Count of active leases
        - expired_leases: Count of expired leases
        - terminated_leases: Count of terminated leases
        - current_filter: Which filter is active (for UI)
        
        Returns:
            Dictionary with all context data for template
        """
        # Get default context from parent class
        context = super().get_context_data(**kwargs)
        # context = {'leases': [...], 'is_paginated': True, ...}
        
        # Get base queryset (all user's leases, before filtering)
        user = self.request.user
        all_user_leases = Lease.objects.filter(
            unit__property__owner=user
        )
        
        # Calculate statistics
        context['total_leases'] = all_user_leases.count()
        # .count() = efficient way to count (doesn't load all objects)
        
        context['active_leases'] = all_user_leases.filter(
            status='ACTIVE'
        ).count()
        
        context['expired_leases'] = all_user_leases.filter(
            status='EXPIRED'
        ).count()
        
        context['terminated_leases'] = all_user_leases.filter(
            status='TERMINATED'
        ).count()
        
        # Add current filter for UI (to highlight active tab)
        context['current_filter'] = self.request.GET.get('status', 'all')
        # Default to 'all' if no filter specified
        
        return context
        # Template can now access all these variables


# ============================================================================
# HOW GET_QUERYSET AND GET_CONTEXT_DATA WORK TOGETHER
# ============================================================================
#
# Django's ListView flow:
#
# 1. User visits /leases/?status=ACTIVE
#
# 2. Django calls get_queryset()
#    - Returns: Only ACTIVE leases for current user
#    - Stored as 'leases' in context
#
# 3. Django calls get_context_data()
#    - Receives: context = {'leases': [active leases]}
#    - Adds: statistics, filters
#    - Returns: context with all data
#
# 4. Django renders template
#    - Passes: All context data
#    - Template uses: {{ leases }}, {{ total_leases }}, etc.
#
# ============================================================================

# ============================================================================
# STEP 3: LEASE DETAIL VIEW
# ============================================================================

class LeaseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display details of a single lease.
    
    Shows:
    1. Lease information (dates, rent, status)
    2. Property and unit details
    3. Tenant information and profile
    4. Payment history for this lease
    5. Days remaining, status badges
    
    Security:
    - Only owner of property can view
    - Uses test_func() to verify ownership
    
    URL: /leases/5/
    Template: templates/leases/lease_detail.html
    """
    
    model = Lease
    template_name = 'leases/lease_detail.html'
    context_object_name = 'lease'
    # Template uses {{ lease }} to access the object
    
    def test_func(self):
        """
        Check if user owns the property this lease belongs to.
        
        This is a PERMISSION check.
        Called by UserPassesTestMixin before allowing access.
        
        Flow:
        1. User visits /leases/5/
        2. Django gets Lease with pk=5
        3. Django calls test_func()
        4. If returns True: Show page
        5. If returns False: Show 403 Forbidden
        
        Returns:
            True if user owns the property, False otherwise
        """
        # Get the lease being viewed
        lease = self.get_object()
        # self.get_object() = DetailView method that gets object by pk from URL
        
        # Check ownership through relationship chain
        return lease.unit.property.owner == self.request.user
        # lease → unit → property → owner
        # Compare owner with logged-in user
        
        # Example:
        # lease.unit.property.owner = User(id=5, username='landlord1')
        # self.request.user = User(id=5, username='landlord1')
        # Result: True (same user, access granted)
    
    def get_context_data(self, **kwargs):
        """
        Add related data to template context.
        
        Default context (from DetailView):
        - lease: The Lease object
        - object: Same Lease object (alternative name)
        
        We add:
        - payments: All payments for this lease
        - total_paid: Sum of all payments
        - amount_due: Rent still owed
        - tenant_profile: Tenant's profile (if exists)
        
        Returns:
            Dictionary with all context data
        """
        context = super().get_context_data(**kwargs)
        lease = self.object
        # self.object = the lease being viewed (set by DetailView)
        
        # ================================================================
        # GET PAYMENT HISTORY
        # ================================================================
        
        # Get all payments for this lease
        payments = lease.payments.all().order_by('-payment_date')
        # lease.payments = reverse relationship
        # Payment model has: lease = ForeignKey(Lease, related_name='payments')
        # So: lease.payments.all() gets all Payment objects for this lease
        # order_by('-payment_date') = newest payments first
        
        context['payments'] = payments
        
        # Calculate total amount paid
        from django.db.models import Sum
        total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        # aggregate(Sum('amount')) returns: {'amount__sum': 150000}
        # We extract the value and default to 0 if None
        
        context['total_paid'] = total_paid
        
        # Calculate how much rent is still owed
        # This is simplified - real calculation would be more complex
        # (number of months × monthly rent - total paid)
        from django.utils import timezone
        today = timezone.now().date()
        
        if lease.start_date <= today <= lease.end_date:
            # Lease is active, calculate months elapsed
            months_elapsed = (
                (today.year - lease.start_date.year) * 12 +
                (today.month - lease.start_date.month) + 1
            )
            expected_payment = lease.monthly_rent * months_elapsed
            amount_due = max(0, expected_payment - total_paid)
            # max(0, ...) ensures we don't show negative
        else:
            amount_due = 0
        
        context['amount_due'] = amount_due
        
        # ================================================================
        # GET TENANT PROFILE
        # ================================================================
        
        try:
            # Try to get tenant's profile
            tenant_profile = TenantProfile.objects.get(user=lease.tenant)
            context['tenant_profile'] = tenant_profile
        except TenantProfile.DoesNotExist:
            # Tenant doesn't have a profile yet
            context['tenant_profile'] = None
        
        return context


# ============================================================================
# REVERSE RELATIONSHIPS EXPLAINED
# ============================================================================
#
# Forward relationship (following ForeignKey):
#   lease.unit → Gets the Unit object
#   lease.tenant → Gets the User object
#
# Reverse relationship (going backwards):
#   lease.payments.all() → Gets all Payment objects
#   
# How reverse relationships work:
#
# 1. Payment model has:
#    lease = ForeignKey(Lease, related_name='payments')
#
# 2. This creates reverse relationship:
#    Lease.payments → Manager to access related Payment objects
#
# 3. Usage:
#    lease.payments.all() → All payments for this lease
#    lease.payments.filter(payment_date__year=2024) → Payments from 2024
#    lease.payments.count() → Count of payments
#
# ============================================================================

# ============================================================================
# STEP 4: LEASE CREATE VIEW
# ============================================================================

class LeaseCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new lease agreement.
    
    Features:
    1. Shows form with dynamic unit/tenant dropdowns
    2. Auto-sets created_by to current user
    3. Validates dates and prevents overlaps
    4. Updates unit occupancy when lease is active
    5. Shows success message
    
    Security:
    - Only shows user's vacant units in dropdown
    - Only shows tenant users in tenant dropdown
    
    URL: /leases/create/
    Template: templates/leases/lease_form.html
    """
    
    model = Lease
    form_class = LeaseForm
    # Use our custom form (not auto-generated)
    # This gives us dynamic choices and validation
    
    template_name = 'leases/lease_form.html'
    
    def get_form_kwargs(self):
        """
        Pass the current user to the form.
        
        Why?
        The form needs to know WHO is creating the lease
        so it can filter units (only show their properties).
        
        Flow:
        1. View calls get_form_kwargs()
        2. We add 'user' to kwargs
        3. Django creates form with kwargs
        4. Form's __init__ receives 'user' parameter
        5. Form filters choices based on user
        
        Returns:
            Dictionary with form initialization arguments
        """
        kwargs = super().get_form_kwargs()
        # Get default kwargs from parent
        # kwargs = {'instance': None, 'data': None, ...}
        
        kwargs['user'] = self.request.user
        # Add current user to kwargs
        # Now kwargs = {..., 'user': User object}
        
        return kwargs
        # Form receives this and uses it in __init__
    
    def form_valid(self, form):
        """
        Called when form data is valid (passes all validation).
        
        We use this to:
        1. Auto-set created_by field
        2. Update unit occupancy if lease is active
        3. Show success message
        
        Args:
            form: The validated LeaseForm
        
        Returns:
            HttpResponse: Redirect to success_url
        """
        # Auto-set who created this lease
        form.instance.created_by = self.request.user
        # form.instance = the Lease object being created
        # Not saved to database yet
        
        # Show success message
        messages.success(
            self.request,
            f'Lease created successfully for {form.instance.tenant.get_full_name() or form.instance.tenant.username}!'
        )
        
        # Save the lease and redirect
        return super().form_valid(form)
        # This calls form.save() which:
        # 1. Saves Lease to database
        # 2. Triggers Lease.save() method (which updates unit.is_occupied)
        # 3. Redirects to success_url
    
    def get_success_url(self):
        """
        Where to redirect after successful creation.
        
        We redirect to the lease detail page so user can
        see the newly created lease.
        
        Returns:
            URL string
        """
        return reverse('lease_detail', kwargs={'pk': self.object.pk})
        # self.object = the lease that was just created
        # reverse() converts URL name to actual URL
        # Example: reverse('lease_detail', kwargs={'pk': 5})
        #          → '/leases/5/'


# ============================================================================
# FORM KWARGS FLOW
# ============================================================================
#
# Understanding get_form_kwargs():
#
# 1. User visits /leases/create/
#
# 2. Django calls LeaseCreateView.get_form_kwargs()
#    Returns: {'user': User(id=5)}
#
# 3. Django creates form:
#    form = LeaseForm(user=User(id=5))
#
# 4. LeaseForm.__init__ receives user parameter:
#    def __init__(self, *args, **kwargs):
#        user = kwargs.pop('user', None)  ← Gets User(id=5)
#
# 5. Form uses user to filter choices:
#    self.fields['unit'].queryset = Unit.objects.filter(
#        property__owner=user  ← Uses the user we passed
#    )
#
# This is how the view and form communicate!
#
# ============================================================================


# ============================================================================
# STEP 5: LEASE UPDATE VIEW
# ============================================================================

class LeaseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Edit an existing lease.
    
    Features:
    1. Pre-fills form with current lease data
    2. Allows changing unit, tenant, dates, rent
    3. Re-validates dates and overlaps
    4. Updates unit occupancy if needed
    
    Security:
    - Only property owner can edit
    - Form shows current unit + other vacant units
    
    URL: /leases/5/edit/
    Template: templates/leases/lease_form.html (same as create)
    """
    
    model = Lease
    form_class = LeaseForm
    template_name = 'leases/lease_form.html'
    # Same template as create
    # Template can detect edit vs create using: {% if object %}
    
    def test_func(self):
        """
        Check if user owns the property before allowing edit.
        
        This prevents users from editing other landlords' leases.
        
        Returns:
            True if user owns property, False otherwise
        """
        lease = self.get_object()
        # Get the lease being edited (from URL pk)
        
        return lease.unit.property.owner == self.request.user
        # Follow relationship chain to check ownership
    
    def get_form_kwargs(self):
        """
        Pass current user to form.
        
        Same as CreateView - form needs user to filter choices.
        
        Returns:
            Dictionary with form kwargs including 'user'
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        # Form will now show:
        # - Current unit + user's vacant units
        # - All tenant users
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        
        Note: We DON'T change created_by (that stays the original creator)
        We just show success message.
        
        Args:
            form: Validated LeaseForm
        
        Returns:
            HttpResponse: Redirect to success_url
        """
        messages.success(
            self.request,
            f'Lease for {form.instance.tenant.get_full_name() or form.instance.tenant.username} has been updated.'
        )
        
        return super().form_valid(form)
        # Saves changes and redirects
    
    def get_success_url(self):
        """
        Redirect back to lease detail after editing.
        
        Returns:
            URL to lease detail page
        """
        return reverse('lease_detail', kwargs={'pk': self.object.pk})
        # Go back to the lease we just edited


# ============================================================================
# CREATE vs UPDATE DIFFERENCES
# ============================================================================
#
# LeaseCreateView:
# - self.object doesn't exist yet
# - form.instance.pk is None
# - Form shows only vacant units
# - Sets created_by field
#
# LeaseUpdateView:
# - self.object exists (the lease being edited)
# - form.instance.pk has a value
# - Form shows current unit + vacant units (Q objects in form)
# - Doesn't change created_by (preserves original creator)
#
# Both views:
# - Use same LeaseForm (smart form adapts based on instance.pk)
# - Use same template (template detects create vs edit)
# - Pass user to form via get_form_kwargs()
# - Show success messages
#
# ============================================================================

# ============================================================================
# LEASE DELETE VIEW
# ============================================================================

class LeaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Terminate/delete a lease.

    We use 'terminate' language in the UI (not 'delete') because
    leases are legal records — landlords understand termination better.

    What this does:
    1. Checks user owns the property (test_func)
    2. On confirmation, deletes the lease from the database
    3. Updates unit.is_occupied = False (unit becomes vacant again)
    4. Shows success message and redirects to lease list

    URL: /leases/5/delete/
    Template: templates/leases/lease_confirm_delete.html
    """

    model = Lease
    template_name = 'leases/lease_confirm_delete.html'
    success_url = reverse_lazy('lease_list')
    # reverse_lazy() instead of reverse() because success_url is evaluated
    # at class definition time, before URLs are fully loaded.
    # reverse() would crash here — reverse_lazy() waits until it's needed.

    def test_func(self):
        """
        Only the property owner can delete a lease.
        Same ownership check as Detail and Update views.
        """
        lease = self.get_object()
        return lease.unit.property.owner == self.request.user

    def form_valid(self, form):
        """
        Soft delete — mark as TERMINATED instead of wiping from database.

        Why not hard delete?
        1. Payment model has on_delete=PROTECT on its lease ForeignKey
        → Django blocks deletion if payments exist
        2. Leases are legal/financial records — losing them loses history
        3. Terminated leases should appear in stats and audit trail

        Flow:
            User confirms → status = TERMINATED → unit freed → redirect
        """
        lease = self.get_object()

        # Change status to TERMINATED
        lease.status = Lease.TERMINATED
        # Calling lease.save() triggers the custom save() in models.py
        # which sets unit.is_occupied = False automatically
        lease.save()

        messages.success(
            self.request,
            f'Lease for {lease.tenant.get_full_name() or lease.tenant.username} '
            f'on {lease.unit.unit_number} has been terminated.'
        )

        return redirect(self.success_url)
        # redirect() instead of super().form_valid() because we're no longer
        # calling .delete() — super() would try to delete the object