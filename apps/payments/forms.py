# ============================================================================
# apps/payments/forms.py - FIXED VERSION
# ============================================================================

from django import forms
from .models import Payment
from apps.leases.models import Lease
from django.db.models import Q
import datetime
from datetime import timedelta


class PaymentForm(forms.ModelForm):
    """
    Form for recording a new rent payment.

    Features:
    1. Lease dropdown filtered to current user's leases only (security)
    2. payment_month uses separate month/year selectors (better UX)
    3. Validates no duplicate payments for same lease+month
    4. Validates amount is positive
    5. Payment month auto-set to first day of selected month
    """

    # =========================================================================
    # CUSTOM FIELDS (month/year dropdowns for payment_month)
    # =========================================================================

    MONTH_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]

    current_year = datetime.date.today().year
    YEAR_CHOICES = [(y, str(y)) for y in range(current_year - 2, current_year + 3)]

    payment_month_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        label='Payment Month',
    )

    payment_month_year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        label='Payment Year',
    )

    # =========================================================================
    # META CLASS
    # =========================================================================

    class Meta:
        model = Payment
        fields = [
            'lease',
            'amount',
            'payment_date',
            'payment_method',
            'reference_number',
            'notes',
        ]

        widgets = {
            'payment_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-input',
                }
            ),

            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'step': '0.01',
                    'min': '0',
                    'placeholder': 'e.g. 150000',
                }
            ),

            'reference_number': forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'e.g. TXN20240105ABC123',
                }
            ),

            'notes': forms.Textarea(
                attrs={
                    'class': 'form-input',
                    'rows': 3,
                    'placeholder': 'Partial payment, late fee included, etc...',
                }
            ),
        }

    # =========================================================================
    # __init__ METHOD
    # =========================================================================

    def __init__(self, *args, **kwargs):
        """
        Custom initialization to filter lease choices and set initial values.
        
        Args:
            user: The logged-in landlord (passed from view)
            *args, **kwargs: Standard form arguments
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter lease dropdown to user's leases only
        if user:
            self.fields['lease'].queryset = Lease.objects.filter(
                unit__property__owner=user
            ).filter(
                Q(status='ACTIVE') | Q(status='EXPIRED')
            ).select_related('unit', 'unit__property', 'tenant')

        # Pre-select current month/year for new payments
        if not self.instance.pk:
            today = datetime.date.today()
            self.fields['payment_month_month'].initial = today.month
            self.fields['payment_month_year'].initial = today.year
            self.fields['payment_date'].initial = today

        else:
            # Editing existing payment - pre-fill month/year
            existing_month = self.instance.payment_month
            if existing_month:
                self.fields['payment_month_month'].initial = existing_month.month
                self.fields['payment_month_year'].initial = existing_month.year

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    def clean_amount(self):
        """
        Validate that payment amount is positive.
        
        CRITICAL FIX: Prevents negative or zero amounts.
        """
        amount = self.cleaned_data.get('amount')
        
        if amount is not None and amount <= 0:
            raise forms.ValidationError(
                "Payment amount must be greater than zero."
            )
        
        return amount

    def clean(self):
        """
        Cross-field validation.
        
        Validates:
        1. Builds payment_month from month/year dropdowns
        2. No duplicate payment for same lease+month
        3. Payment date within lease period
        4. Payment month within lease period (with grace)
        """
        cleaned_data = super().clean()

        # ── Build payment_month from month/year ──────────────────────────────
        month = cleaned_data.get('payment_month_month')
        year = cleaned_data.get('payment_month_year')

        if month and year:
            try:
                payment_month = datetime.date(int(year), int(month), 1)
                cleaned_data['payment_month'] = payment_month
            except ValueError:
                raise forms.ValidationError("Invalid payment month/year combination.")

        # ── Validate no duplicate payment ────────────────────────────────────
        lease = cleaned_data.get('lease')
        payment_month = cleaned_data.get('payment_month')

        if lease and payment_month:
            duplicate_check = Payment.objects.filter(
                lease=lease,
                payment_month=payment_month
            )

            if self.instance.pk:
                duplicate_check = duplicate_check.exclude(pk=self.instance.pk)

            if duplicate_check.exists():
                raise forms.ValidationError(
                    f"A payment for {payment_month.strftime('%B %Y')} "
                    f"already exists for this lease."
                )

        # ── Validate payment_date within lease period ────────────────────────
        payment_date = cleaned_data.get('payment_date')

        if lease and payment_date:
            if payment_date < lease.start_date:
                raise forms.ValidationError(
                    f"Payment date cannot be before the lease start date "
                    f"({lease.start_date})."
                )

        # ── NEW: Validate payment_month within lease period (with grace) ─────
        if lease and payment_month:
            # Payment month can't be before lease starts
            if payment_month < lease.start_date.replace(day=1):
                raise forms.ValidationError(
                    f"Payment month cannot be before lease start "
                    f"({lease.start_date.strftime('%B %Y')})."
                )
            
            # Allow payment_month up to 1 month after lease ends
            # (for final payment or late payment grace period)
            one_month_after_end = lease.end_date + timedelta(days=31)
            if payment_month > one_month_after_end.replace(day=1):
                raise forms.ValidationError(
                    f"Payment month too far after lease end date. "
                    f"Lease ended {lease.end_date.strftime('%B %Y')}."
                )

        return cleaned_data