# ============================================================================
# apps/payments/views.py - FIXED VERSION
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
    DeleteView,
    TemplateView
)
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
import datetime
from datetime import timedelta  # FIX: Added missing import

from .models import Payment
from .forms import PaymentForm
from apps.leases.models import Lease


# ============================================================================
# VIEW 1: PaymentListView
# ============================================================================

class PaymentListView(LoginRequiredMixin, ListView):
    """
    Lists all payments for the logged-in landlord's properties.

    Features:
    - Filter by status (on time / late / early)
    - Filter by lease
    - Summary stats (total collected, total late, count)
    - Pagination (10 per page)
    - Security: only shows payments for user's properties
    """

    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10
    ordering = ['-payment_date']

    def get_queryset(self):
        """
        Returns the list of payments to display.
        Filters by ownership and optional status/lease filters.
        """
        user = self.request.user

        queryset = Payment.objects.filter(
            lease__unit__property__owner=user
        )

        # FIX: Removed undefined function reference
        # Late filtering is handled in get_context_data via database queries
        status_filter = self.request.GET.get('status')
        if status_filter == 'late':
            # Filter to late payments using F() expression
            queryset = queryset.filter(
                payment_date__gt=F('payment_month') + timedelta(days=5)
            )

        # Lease filter
        lease_id = self.request.GET.get('lease')
        if lease_id:
            queryset = queryset.filter(lease_id=lease_id)

        # Ordering
        queryset = queryset.order_by('-payment_date')

        # Performance optimization
        queryset = queryset.select_related(
            'lease',
            'lease__unit',
            'lease__unit__property',
            'lease__tenant',
            'recorded_by'
        )

        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds extra variables to the template context.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get ALL payments for this user (not just current page)
        all_payments = Payment.objects.filter(
            lease__unit__property__owner=user
        )

        # Total collected
        context['total_collected'] = all_payments.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # FIX: Use F() expressions for efficient late payment counting
        late_count = all_payments.filter(
            payment_date__gt=F('payment_month') + timedelta(days=5)
        ).count()

        on_time_count = all_payments.filter(
            payment_date__lte=F('payment_month') + timedelta(days=5),
            payment_date__gte=F('payment_month')
        ).count()

        early_count = all_payments.filter(
            payment_date__lt=F('payment_month')
        ).count()

        context['late_count'] = late_count
        context['on_time_count'] = on_time_count
        context['early_count'] = early_count
        context['total_payment_count'] = all_payments.count()

        # Filter state for UI
        context['current_status_filter'] = self.request.GET.get('status', 'all')

        # Lease filter dropdown
        context['user_leases'] = Lease.objects.filter(
            unit__property__owner=user
        ).select_related('unit', 'unit__property', 'tenant')

        context['selected_lease'] = self.request.GET.get('lease', '')

        return context


# ============================================================================
# VIEW 2: PaymentDetailView
# ============================================================================

class PaymentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Shows full details of a single payment.
    Security: Only the landlord who owns the property can view.
    """

    model = Payment
    template_name = 'payments/payment_detail_clean.html'
    context_object_name = 'payment'

    def test_func(self):
        """Check if user owns the property this payment belongs to."""
        payment = self.get_object()
        return payment.lease.unit.property.owner == self.request.user

    def get_context_data(self, **kwargs):
        """Adds extra info about the payment to the template."""
        context = super().get_context_data(**kwargs)
        payment = self.object

        # Add computed properties for the template
        context['is_late'] = payment.is_late()
        context['days_late'] = payment.days_late()
        context['late_fee'] = payment.late_fee_applicable()
        context['payment_status'] = payment.payment_status()

        return context


# ============================================================================
# VIEW 3: PaymentCreateView
# ============================================================================

class PaymentCreateView(LoginRequiredMixin, CreateView):
    """
    Form to record a new rent payment.

    Features:
    - Pre-select lease if ?lease=3 in URL
    - Auto-set recorded_by to current user
    - Auto-set payment_month from form's month/year dropdowns
    """

    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'

    def get_form_kwargs(self):
        """Passes current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-select lease if passed in URL."""
        initial = super().get_initial()
        lease_id = self.request.GET.get('lease')
        if lease_id:
            initial['lease'] = lease_id
        return initial

    def form_valid(self, form):
        """Called when form is valid. Sets auto fields and saves."""
        # Auto-set recorded_by
        form.instance.recorded_by = self.request.user

        # Set payment_month from custom month/year fields
        payment_month = form.cleaned_data.get('payment_month')
        if payment_month:
            form.instance.payment_month = payment_month

        # Success message
        tenant_name = (
            form.instance.lease.tenant.get_full_name()
            or form.instance.lease.tenant.username
        )

        messages.success(
            self.request,
            f'Payment of ₦{form.instance.amount:,.0f} recorded for '
            f'{tenant_name} — {form.instance.payment_month.strftime("%B %Y")}.'
        )

        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the newly created payment detail page."""
        return reverse('payment_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# VIEW 4: PaymentUpdateView
# ============================================================================

class PaymentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Edit an existing payment record.
    """

    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'

    def test_func(self):
        """Only property owner can edit payment records."""
        payment = self.get_object()
        return payment.lease.unit.property.owner == self.request.user

    def get_form_kwargs(self):
        """Pass current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Called when form is valid."""
        # Set payment_month from custom fields
        payment_month = form.cleaned_data.get('payment_month')
        if payment_month:
            form.instance.payment_month = payment_month

        # Success message
        messages.success(
            self.request,
            f'Payment for {form.instance.lease.tenant.get_full_name() or form.instance.lease.tenant.username} '
            f'has been updated.'
        )

        return super().form_valid(form)

    def get_success_url(self):
        """Redirect back to payment detail."""
        return reverse('payment_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# VIEW 5: PaymentDeleteView
# ============================================================================

class PaymentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Confirm and delete a payment record.
    """

    model = Payment
    template_name = 'payments/payment_confirm_delete.html'
    success_url = reverse_lazy('payment_list')

    def test_func(self):
        """Only the property owner can delete payment records."""
        payment = self.get_object()
        return payment.lease.unit.property.owner == self.request.user

    def form_valid(self, form):
        """Called when user confirms deletion."""
        payment = self.get_object()

        description = (
            f'₦{payment.amount:,.0f} payment for '
            f'{payment.payment_month.strftime("%B %Y")} '
            f'({payment.lease.tenant.get_full_name() or payment.lease.tenant.username})'
        )

        messages.success(
            self.request,
            f'Payment record deleted: {description}.'
        )

        return super().form_valid(form)


# ============================================================================
# VIEW 6: PaymentDashboardView
# ============================================================================

class PaymentDashboardView(LoginRequiredMixin, TemplateView):
    """
    Payment summary dashboard.

    Shows:
    - Total collected this month
    - Total collected this year
    - Overdue count (leases with no payment this month)
    - Recent payments
    - Monthly breakdown (last 6 months)
    """

    template_name = 'payments/payment_dashboard.html'

    def get_context_data(self, **kwargs):
        """Builds all the stats for the dashboard."""
        context = super().get_context_data(**kwargs)

        user = self.request.user
        today = timezone.now().date()

        # This month's dates
        this_month_start = today.replace(day=1)

        # All payments for this user
        all_payments = Payment.objects.filter(
            lease__unit__property__owner=user
        ).select_related('lease', 'lease__unit', 'lease__unit__property', 'lease__tenant')

        # This month's total
        this_month_payments = all_payments.filter(
            payment_month=this_month_start
        )

        this_month_total = this_month_payments.aggregate(
            total=Sum('amount')
        )['total'] or 0

        context['this_month_total'] = this_month_total
        context['this_month_count'] = this_month_payments.count()

        # This year's total
        this_year_payments = all_payments.filter(
            payment_date__year=today.year
        )

        this_year_total = this_year_payments.aggregate(
            total=Sum('amount')
        )['total'] or 0

        context['this_year_total'] = this_year_total

        # Overdue leases (active leases with no payment this month)
        active_leases = Lease.objects.filter(
            unit__property__owner=user,
            status='ACTIVE'
        ).select_related('unit', 'unit__property', 'tenant')

        paid_lease_ids = this_month_payments.values_list('lease_id', flat=True)
        overdue_leases = active_leases.exclude(pk__in=paid_lease_ids)

        context['overdue_leases'] = overdue_leases
        context['overdue_count'] = overdue_leases.count()

        # Recent payments (last 5)
        context['recent_payments'] = all_payments.order_by('-payment_date')[:5]

        # FIX: Simplified monthly breakdown (last 6 months)
        # Using simple date arithmetic instead of complex month math
        monthly_data = []
        
        for i in range(5, -1, -1):  # 5 months ago to current month
            # Calculate the month date
            if today.month - i <= 0:
                # Handle year boundary
                target_year = today.year - 1
                target_month = 12 + (today.month - i)
            else:
                target_year = today.year
                target_month = today.month - i
            
            month_date = datetime.date(target_year, target_month, 1)

            # Get payments for this month
            month_total = all_payments.filter(
                payment_month=month_date
            ).aggregate(total=Sum('amount'))['total'] or 0

            monthly_data.append({
                'month': month_date.strftime('%b %Y'),
                'total': month_total,
                'month_date': month_date,
            })

        context['monthly_data'] = monthly_data

        return context