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
from .models import Property, Unit


# ============================================================================
# STEP 1: PROPERTY LIST VIEW
# ============================================================================

class PropertyListView(LoginRequiredMixin, ListView):
    """
    Display list of properties owned by the logged-in user.
    
    Inherits from:
    - LoginRequiredMixin: Requires user to be logged in
    - ListView: Django's built-in view for displaying lists
    
    What it does:
    1. Gets all properties from database
    2. Filters to show only current user's properties
    3. Passes them to template
    4. Handles pagination automatically
    
    Template receives:
    - object_list: List of Property objects
    - property_list: Same list (Django creates both)
    """
    
    model = Property
    # Which model to query
    
    template_name = 'properties/property_list.html'
    # Which template to render
    
    context_object_name = 'properties'
    # Name to use in template (instead of 'object_list')
    # Template can now use {{ properties }} instead of {{ object_list }}
    
    paginate_by = 10
    # Show 10 properties per page
    # Django handles pagination automatically
    
    ordering = ['name']
    # Order properties alphabetically by name
    
    def get_queryset(self):
        """
        Filter properties to show only those owned by current user.
        
        Without this: User sees ALL properties (security issue!)
        With this: User sees only THEIR properties
        
        Returns:
            QuerySet of Property objects owned by current user
        """
        return Property.objects.filter(owner=self.request.user)
        # self.request.user = currently logged-in user
        # filter(owner=...) = SQL WHERE clause
    
    def get_context_data(self, **kwargs):
        """
        Add extra data to pass to template.
        
        Default context (from ListView):
        - properties: List of Property objects
        
        We add:
        - total_properties: Count of user's properties
        - total_units: Count of all units across all properties
        - occupied_units: Count of occupied units
        """
        # Get the default context first
        context = super().get_context_data(**kwargs)
        # super() calls ListView's get_context_data()
        # This gives us the basic 'properties' variable
        
        # Add custom statistics
        user_properties = Property.objects.filter(owner=self.request.user)
        
        context['total_properties'] = user_properties.count()
        # How many properties user owns
        
        context['total_units'] = Unit.objects.filter(
            property__owner=self.request.user
        ).count()
        # Total units across all user's properties
        # property__owner = follow relationship from Unit → Property → owner
        
        context['occupied_units'] = Unit.objects.filter(
            property__owner=self.request.user,
            is_occupied=True
        ).count()
        # How many units are currently occupied
        # Add vacant units calculation
        context['vacant_units'] = context['total_units'] - context['occupied_units']
        
        return context


# ============================================================================
# STEP 2: PROPERTY DETAIL VIEW
# ============================================================================

class PropertyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display details of a single property with all its units.
    
    Inherits from:
    - LoginRequiredMixin: Must be logged in
    - UserPassesTestMixin: Additional permission check (must own property)
    - DetailView: Shows single object
    
    What it does:
    1. Gets one property by ID (from URL)
    2. Checks if user owns it (test_func)
    3. Gets all units for that property
    4. Calculates stats (occupancy rate, etc.)
    5. Passes everything to template
    
    Template receives:
    - object: The Property object
    - property: Same Property object
    - units: All units in this property
    - stats: Occupancy statistics
    """
    
    model = Property
    template_name = 'properties/property_detail.html'
    context_object_name = 'property'
    
    def test_func(self):
        """
        Check if current user owns this property.
        
        Called by UserPassesTestMixin before allowing access.
        
        Returns:
            True: User owns property → Allow access
            False: User doesn't own → Redirect with error (403 Forbidden)
        """
        property = self.get_object()
        # self.get_object() gets the Property from URL
        # Example: /properties/5/ → Gets Property with pk=5
        
        return property.owner == self.request.user
        # Check: Is property.owner same as logged-in user?
        # Example: property.owner = User(id=5), self.request.user = User(id=5) → True
    
    def get_context_data(self, **kwargs):
        """
        Add units and statistics to template context.
        
        Default context (from DetailView):
        - object: The Property object
        - property: Same Property object
        
        We add:
        - units: All units in this property
        - total_units: Count of units
        - occupied_units: Count of occupied units
        - vacant_units: Count of vacant units
        - occupancy_rate: Percentage occupied
        """
        context = super().get_context_data(**kwargs)
        property = self.object
        # self.object = the Property we're viewing
        
        # Get all units for this property
        context['units'] = property.units.all()
        # property.units = reverse relationship from Property to Unit
        # Remember: Unit has ForeignKey(Property, related_name='units')
        # So property.units.all() gets all units for this property
        
        # Add statistics (using methods we created in Property model)
        context['total_units'] = property.total_units()
        context['occupied_units'] = property.occupied_units()
        context['vacant_units'] = property.vacant_units()
        context['occupancy_rate'] = property.occupancy_rate()
        
        return context


# ============================================================================
# STEP 3: PROPERTY CREATE VIEW
# ============================================================================

class PropertyCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new property.
    
    Inherits from:
    - LoginRequiredMixin: Must be logged in
    - CreateView: Handles form display and saving
    
    What it does:
    1. Shows empty form to user (GET request)
    2. User fills out form
    3. Validates data (POST request)
    4. Auto-sets owner to current user
    5. Saves to database
    6. Shows success message
    7. Redirects to property list
    
    Template receives:
    - form: PropertyForm object (automatically created)
    """
    
    model = Property
    template_name = 'properties/property_form.html'
    
    fields = ['name', 'address', 'city', 'state', 'description', 'image', 'video_url', 'manager']
    # Which fields to show in the form
    # Notice: 'owner' is NOT here (we set it automatically)
    # 'created_at' and 'updated_at' are auto-generated
    
    def form_valid(self, form):
        """
        Called when form data is valid (after validation).
        
        We use this to:
        1. Set owner to current user (before saving)
        2. Show success message
        3. Save and redirect
        
        Args:
            form: The validated form with cleaned data
        
        Returns:
            HttpResponse: Redirect to success_url
        """
        # Set owner to logged-in user
        form.instance.owner = self.request.user
        # form.instance = the Property object being created
        # It's created but not saved yet
        # We modify it before saving
        
        # Show success message
        messages.success(
            self.request,
            f'Property "{form.instance.name}" has been created successfully!'
        )
        # form.instance.name = the name user entered in the form
        
        # Save and redirect
        return super().form_valid(form)
        # Calls CreateView's form_valid() which:
        # 1. Saves the object to database
        # 2. Redirects to success_url
    
    def get_success_url(self):
        """
        Where to redirect after successful creation.
        
        Returns:
            URL to property detail page of newly created property
        """
        return reverse('property_detail', kwargs={'pk': self.object.pk})
        # self.object = the Property that was just created
        # self.object.pk = its primary key (ID)
        # reverse('property_detail', kwargs={'pk': 5}) → /properties/5/
        
        # Alternative: Redirect to property list
        # return reverse('property_list')


# ============================================================================
# STEP 4: PROPERTY UPDATE VIEW
# ============================================================================

class PropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Edit an existing property.
    
    Inherits from:
    - LoginRequiredMixin: Must be logged in
    - UserPassesTestMixin: Must own the property
    - UpdateView: Handles editing existing objects
    
    What it does:
    1. Gets property by ID from URL
    2. Checks if user owns it
    3. Shows form pre-filled with current data (GET)
    4. User edits and submits (POST)
    5. Validates changes
    6. Saves updates
    7. Shows success message
    8. Redirects to property detail
    
    Template receives:
    - form: PropertyForm pre-filled with current data
    - object: The Property being edited
    - property: Same Property object
    """
    
    model = Property
    template_name = 'properties/property_form.html'
    # Same template as create (form looks the same)
    # Template can check if object exists to show "Edit" vs "Create" title
    
    fields = ['name', 'address', 'city', 'state', 'description', 'image', 'video_url', 'manager']
    # Same fields as create
    
    def test_func(self):
        """
        Check if user owns this property before allowing edit.
        
        Returns:
            True: User owns property → Can edit
            False: User doesn't own → 403 Forbidden
        """
        property = self.get_object()
        return property.owner == self.request.user
    
    def form_valid(self, form):
        """
        Called when edited form is valid.
        
        Show success message and save changes.
        """
        messages.success(
            self.request,
            f'Property "{form.instance.name}" has been updated successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        """
        Redirect back to property detail after editing.
        """
        return reverse('property_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# STEP 5: PROPERTY DELETE VIEW
# ============================================================================

class PropertyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete a property.
    
    Inherits from:
    - LoginRequiredMixin: Must be logged in
    - UserPassesTestMixin: Must own the property
    - DeleteView: Handles deletion with confirmation
    
    What it does:
    1. Gets property by ID
    2. Checks if user owns it
    3. Shows confirmation page (GET) - "Are you sure?"
    4. User confirms (POST)
    5. Deletes property from database
    6. Shows success message
    7. Redirects to property list
    
    Template receives:
    - object: The Property to be deleted
    - property: Same Property object
    
    IMPORTANT: Because Property has CASCADE relationship with Units,
    deleting a property also deletes all its units!
    """
    
    model = Property
    template_name = 'properties/property_confirm_delete.html'
    success_url = reverse_lazy('property_list')
    # reverse_lazy because this is a class attribute
    # Evaluated when URL is actually needed, not when class loads
    
    def test_func(self):
        """
        Check if user owns this property before allowing deletion.
        
        Returns:
            True: User owns property → Can delete
            False: User doesn't own → 403 Forbidden
        """
        property = self.get_object()
        return property.owner == self.request.user
    
    def delete(self, request, *args, **kwargs):
        """
        Called when user confirms deletion.
        
        Show success message before deleting.
        """
        property = self.get_object()
        property_name = property.name
        # Save name before deleting (can't access after deletion)

        # Call parent delete (this deletes the object)
        response = super().delete(request, *args, **kwargs)
        
        messages.success(
            self.request,
            f'Property "{property_name}" has been deleted successfully.'
        )
        
        return response

# ============================================================================
# UNIT VIEWS
# ============================================================================

class UnitCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a new unit for a specific property.
    
    🆕 NEW CONCEPT: Parent-Child Creation
    
    URL pattern: /properties/5/units/create/
    - '5' is the property_pk (property ID)
    - We extract it from URL
    - Auto-set unit.property to that property
    
    Flow:
    1. User clicks "Add Unit" on property detail page
    2. URL includes property_pk: /properties/5/units/create/
    3. View extracts property_pk from URL
    4. Form shows (property is pre-set, user fills other fields)
    5. When saved, unit is automatically linked to that property
    
    This ensures units are always created for the correct property.
    """
    
    model = Unit
    template_name = 'properties/unit_form.html'
    fields = ['unit_number', 'floor', 'bedrooms', 'bathrooms', 'square_feet', 'rent_amount']
    # Notice: 'property' is NOT in fields (we set it from URL)
    # 'is_occupied' defaults to False (new units start vacant)
    
    def test_func(self):
        """
        Check if user owns the property they're adding a unit to.
        
        🆕 Getting property from URL:
        - self.kwargs['property_pk'] = property ID from URL
        - get_object_or_404 = get property or show 404 if not found
        """
        property_pk = self.kwargs.get('property_pk')
        # self.kwargs = dictionary of URL parameters
        # Example URL: /properties/5/units/create/
        # self.kwargs = {'property_pk': '5'}
        
        property = get_object_or_404(Property, pk=property_pk)
        # Get the property or show 404 if doesn't exist
        
        return property.owner == self.request.user
        # Check: Does logged-in user own this property?
    
    def form_valid(self, form):
        """
        Auto-set the property before saving the unit.
        
        🆕 Setting related object from URL parameter:
        """
        # Get property from URL
        property_pk = self.kwargs.get('property_pk')
        property = get_object_or_404(Property, pk=property_pk)
        
        # Set property on the unit
        form.instance.property = property
        # form.instance = the Unit object being created
        # Now: unit.property = the property from URL
        
        # Show success message
        messages.success(
            self.request,
            f'Unit {form.instance.unit_number} has been added to {property.name}.'
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        """
        Redirect back to property detail page after creating unit.
        """
        return reverse('property_detail', kwargs={'pk': self.kwargs.get('property_pk')})
        # Redirect to the property we just added a unit to
    
    def get_context_data(self, **kwargs):
        """
        Pass property info to template.
        
        Template needs to know which property we're adding a unit to
        (to show in the page title).
        """
        context = super().get_context_data(**kwargs)
        property_pk = self.kwargs.get('property_pk')
        context['property'] = get_object_or_404(Property, pk=property_pk)
        return context


class UnitUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Edit an existing unit.
    
    Similar to PropertyUpdateView, but checks if user owns the PROPERTY
    (not the unit directly, since units don't have an owner field).
    """
    
    model = Unit
    template_name = 'properties/unit_form.html'
    fields = ['unit_number', 'floor', 'bedrooms', 'bathrooms', 'square_feet', 'rent_amount', 'is_occupied']
    # Same fields as create, plus 'is_occupied' (can manually toggle)
    
    def test_func(self):
        """
        Check if user owns the property this unit belongs to.
        
        🆕 Permission check through relationship:
        unit.property.owner = the landlord who owns this property
        """
        unit = self.get_object()
        return unit.property.owner == self.request.user
        # Follow relationship: Unit → Property → owner
        # Check if that owner is the current user
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Unit {form.instance.unit_number} has been updated.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        """
        Redirect to property detail page after editing.
        """
        return reverse('property_detail', kwargs={'pk': self.object.property.pk})
        # self.object = the unit we just edited
        # self.object.property = the property this unit belongs to
        # self.object.property.pk = that property's ID


class UnitDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete a unit.
    
    🆕 Dynamic success_url:
    Can't use class attribute because we need the property_pk
    (which comes from the object being deleted).
    """
    
    model = Unit
    template_name = 'properties/unit_confirm_delete.html'
    
    def test_func(self):
        """
        Check if user owns the property this unit belongs to.
        """
        unit = self.get_object()
        return unit.property.owner == self.request.user
    
    def get_success_url(self):
        """
        🆕 Get property_pk from the unit BEFORE deleting it.
        
        Why not use class attribute 'success_url'?
        - We need to know which property the unit belongs to
        - After deletion, the unit no longer exists
        - So we grab property.pk BEFORE calling delete()
        """
        return reverse('property_detail', kwargs={'pk': self.object.property.pk})
        # self.object = the unit about to be deleted
        # Grab property.pk before it's deleted
    
    def delete(self, request, *args, **kwargs):
        """
        Show success message before deleting.
        """
        unit = self.get_object()
        unit_number = unit.unit_number
        property_name = unit.property.name

        # Call parent delete (this deletes the object)
        response = super().delete(request, *args, **kwargs)
        
        messages.success(
            self.request,
            f'Unit {unit_number} has been removed from {property_name}.'
        )
        
        return response