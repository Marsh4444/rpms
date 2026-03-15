# ============================================================================
# IMPORTS
# ============================================================================

from django.urls import path
from . import views


# ============================================================================
# URL PATTERNS
# ============================================================================

urlpatterns = [
    # ========================================================================
    # PROPERTY URLs
    # ========================================================================
    
    # Property List
    path('', views.PropertyListView.as_view(), name='property_list'),
    # URL: /properties/
    # View: PropertyListView
    # Shows all properties owned by logged-in user
    # Example: http://localhost:8000/properties/
    
    # Property Detail
    path('<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    # URL: /properties/5/
    # <int:pk> = capture integer as 'pk' parameter
    # pk = primary key (property ID)
    # View receives: self.kwargs = {'pk': 5}
    # Example: http://localhost:8000/properties/5/
    
    # Property Create
    path('create/', views.PropertyCreateView.as_view(), name='property_create'),
    # URL: /properties/create/
    # View: PropertyCreateView
    # Shows form to create new property
    # Example: http://localhost:8000/properties/create/
    
    # Property Update
    path('<int:pk>/edit/', views.PropertyUpdateView.as_view(), name='property_update'),
    # URL: /properties/5/edit/
    # View receives: self.kwargs = {'pk': 5}
    # Shows form pre-filled with property data
    # Example: http://localhost:8000/properties/5/edit/
    
    # Property Delete
    path('<int:pk>/delete/', views.PropertyDeleteView.as_view(), name='property_delete'),
    # URL: /properties/5/delete/
    # View receives: self.kwargs = {'pk': 5}
    # Shows confirmation page before deletion
    # Example: http://localhost:8000/properties/5/delete/
    
    
    # ========================================================================
    # UNIT URLs
    # ========================================================================
    
    # Unit Create (nested under property)
    path('<int:property_pk>/units/create/', views.UnitCreateView.as_view(), name='unit_create'),
    # URL: /properties/5/units/create/
    # <int:property_pk> = capture property ID
    # View receives: self.kwargs = {'property_pk': 5}
    # Shows form to create unit for property with ID 5
    # Example: http://localhost:8000/properties/5/units/create/
    #
    # 🆕 NEW CONCEPT: Nested URLs
    # Unit create URL is "nested" under property
    # This shows the relationship: units belong to properties
    
    # Unit Update
    path('units/<int:pk>/edit/', views.UnitUpdateView.as_view(), name='unit_update'),
    # URL: /properties/units/10/edit/
    # <int:pk> = unit ID (not property ID!)
    # View receives: self.kwargs = {'pk': 10}
    # Shows form to edit unit with ID 10
    # Example: http://localhost:8000/properties/units/10/edit/
    #
    # Why not nested under property?
    # /properties/5/units/10/edit/ would be redundant
    # Unit already knows its property (through ForeignKey)
    # Simpler URL is better
    
    # Unit Delete
    path('units/<int:pk>/delete/', views.UnitDeleteView.as_view(), name='unit_delete'),
    # URL: /properties/units/10/delete/
    # View receives: self.kwargs = {'pk': 10}
    # Shows confirmation to delete unit with ID 10
    # Example: http://localhost:8000/properties/units/10/delete/
]


# ============================================================================
# URL PATTERN EXPLANATION
# ============================================================================
#
# How Django matches URLs:
#
# User visits: http://localhost:8000/properties/5/
#
# 1. Django looks at config/urls.py
#    Finds: path('properties/', include('apps.properties.urls'))
#    
# 2. Strips 'properties/' from URL, leaving '5/'
#    
# 3. Looks in apps/properties/urls.py for '5/'
#    Finds: path('<int:pk>/', ...)
#    
# 4. Matches! <int:pk> captures '5' as an integer
#    self.kwargs = {'pk': 5}
#    
# 5. Calls PropertyDetailView.as_view()
#    
# 6. View gets property with pk=5 and renders template
#
# ============================================================================


# ============================================================================
# URL NAMING CONVENTION
# ============================================================================
#
# We use descriptive names that follow Django conventions:
#
# Pattern: <model>_<action>
#
# Examples:
# - property_list    → List all properties
# - property_detail  → View one property
# - property_create  → Create new property
# - property_update  → Edit existing property
# - property_delete  → Delete property
# - unit_create      → Create new unit
# - unit_update      → Edit existing unit
# - unit_delete      → Delete unit
#
# These names are used in templates:
# {% url 'property_list' %}           → /properties/
# {% url 'property_detail' pk=5 %}    → /properties/5/
# {% url 'property_update' pk=5 %}    → /properties/5/edit/
# {% url 'unit_create' property_pk=5 %} → /properties/5/units/create/
#
# ============================================================================


# ============================================================================
# ORDER MATTERS!
# ============================================================================
#
# Django matches URLs from TOP to BOTTOM.
# First match wins!
#
# ❌ WRONG ORDER:
# path('<int:pk>/', ...)      # Matches first!
# path('create/', ...)        # Never reached!
#
# Why? 
# - User visits /properties/create/
# - Django tries <int:pk>/ first
# - 'create' is not an integer, but Django tries to match anyway
# - Pattern might fail or behave unexpectedly
#
# ✅ CORRECT ORDER (what we have):
# path('', ...)               # Most specific first
# path('create/', ...)        # Static URLs before dynamic
# path('<int:pk>/', ...)      # Dynamic URLs last
#
# This ensures:
# - /properties/create/ → Matches 'create/' pattern ✅
# - /properties/5/      → Matches '<int:pk>/' pattern ✅
#
# ============================================================================