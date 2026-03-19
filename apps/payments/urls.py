from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.PaymentDashboardView.as_view(), name='payment_dashboard'),
    path('', views.PaymentListView.as_view(), name='payment_list'),
    path(
        'create/',
        views.PaymentCreateView.as_view(),
        name='payment_create'),
    path(
        '<int:pk>/',
        views.PaymentDetailView.as_view(),
        name='payment_detail'
    ),
    path(
        '<int:pk>/edit/',
        views.PaymentUpdateView.as_view(),
        name='payment_update'
    ),
    path(
        '<int:pk>/delete/',
        views.PaymentDeleteView.as_view(),
        name='payment_delete'
    ),

]