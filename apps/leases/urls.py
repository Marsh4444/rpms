# ============================================================================
# apps/leases/urls.py
# ============================================================================

from django.urls import path
from . import views

urlpatterns = [

    # ------------------------------------------------------------------
    # LIST  →  /leases/
    # ------------------------------------------------------------------
    path(
        '',
        views.LeaseListView.as_view(),
        name='lease_list'
    ),

    # ------------------------------------------------------------------
    # CREATE  →  /leases/create/
    # ------------------------------------------------------------------
    path(
        'create/',
        views.LeaseCreateView.as_view(),
        name='lease_create'
    ),

    # ------------------------------------------------------------------
    # DETAIL  →  /leases/5/
    # ------------------------------------------------------------------
    path(
        '<int:pk>/',
        views.LeaseDetailView.as_view(),
        name='lease_detail'
    ),

    # ------------------------------------------------------------------
    # UPDATE  →  /leases/5/edit/
    # ------------------------------------------------------------------
    path(
        '<int:pk>/edit/',
        views.LeaseUpdateView.as_view(),
        name='lease_update'
    ),

    # ------------------------------------------------------------------
    # DELETE  →  /leases/5/delete/
    # (LeaseDeleteView still to be built in Phase 9 Step 6+)
    # ------------------------------------------------------------------
    path(
        '<int:pk>/delete/',
        views.LeaseDeleteView.as_view(),
        name='lease_delete'
    ),

]