# ============================================================================
# apps/maintenance/urls.py
# ============================================================================

from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.MaintenanceRequestListView.as_view(), name='list'),
    path('create/', views.MaintenanceRequestCreateView.as_view(), name='create'),
    path('<int:pk>/', views.MaintenanceRequestDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.MaintenanceRequestUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.MaintenanceRequestDeleteView.as_view(), name='delete'),
]