# ============================================================================
# apps/maintenance/views.py
# ============================================================================

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import MaintenanceRequest
from .forms import MaintenanceRequestForm, MaintenanceStatusUpdateForm


class MaintenanceRequestListView(LoginRequiredMixin, ListView):
    """Display all maintenance requests with filtering."""
    
    model = MaintenanceRequest
    template_name = 'maintenance/maintenance_list.html'
    context_object_name = 'requests'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter requests by logged-in user's properties and status."""
        queryset = MaintenanceRequest.objects.filter(
            unit__property__owner=self.request.user
        ).select_related(
            'unit__property', 'submitted_by', 'assigned_to'
        ).order_by('-created_at')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority if provided
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter options and counts to template."""
        context = super().get_context_data(**kwargs)
        
        # Get all requests for counts
        all_requests = MaintenanceRequest.objects.filter(
            unit__property__owner=self.request.user
        )
        
        # Status counts
        context['pending_count'] = all_requests.filter(status='PENDING').count()
        context['in_progress_count'] = all_requests.filter(status='IN_PROGRESS').count()
        context['resolved_count'] = all_requests.filter(status='RESOLVED').count()
        
        # Current filters
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        
        return context


class MaintenanceRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Display single maintenance request details."""
    
    model = MaintenanceRequest
    template_name = 'maintenance/maintenance_detail.html'
    context_object_name = 'request'
    
    def test_func(self):
        """Only owner of the property can view."""
        request = self.get_object()
        return request.unit.property.owner == self.request.user
    
    def get_context_data(self, **kwargs):
        """Add status update form to context."""
        context = super().get_context_data(**kwargs)
        context['status_form'] = MaintenanceStatusUpdateForm(instance=self.object)
        return context


class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
    """Create new maintenance request."""

    model = MaintenanceRequest
    form_class = MaintenanceRequestForm
    template_name = 'maintenance/maintenance_form.html'

    # ❌ REMOVED get_form_kwargs entirely
    # The form doesn't accept 'user' — passing it causes the TypeError.
    # Unit filtering by tenant is a future enhancement; skip it for now.

    def form_valid(self, form):
        """Inject submitted_by from the logged-in user before saving."""
        form.instance.submitted_by = self.request.user

        # ✅ FIXED: 'OPEN' not 'PENDING' — match your model's STATUS_CHOICES
        form.instance.status = 'OPEN'

        messages.success(
            self.request,
            f'Maintenance request submitted for {form.instance.unit}.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('maintenance:detail', kwargs={'pk': self.object.pk})

class MaintenanceRequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update maintenance request (status change)."""
    
    model = MaintenanceRequest
    form_class = MaintenanceStatusUpdateForm
    template_name = 'maintenance/maintenance_form.html'
    
    def test_func(self):
        """Only property owner can update."""
        request = self.get_object()
        return request.unit.property.owner == self.request.user
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Request status updated to {form.instance.get_status_display()}.'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('maintenance:detail', kwargs={'pk': self.object.pk})


class MaintenanceRequestDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete maintenance request."""
    
    model = MaintenanceRequest
    template_name = 'maintenance/maintenance_confirm_delete.html'
    success_url = reverse_lazy('maintenance:list')
    
    def test_func(self):
        """Only property owner can delete."""
        request = self.get_object()
        return request.unit.property.owner == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(
            self.request,
            'Maintenance request deleted.'
        )
        return super().delete(request, *args, **kwargs)