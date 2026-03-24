# ============================================================================
# IMPORTS
# ============================================================================

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


# ============================================================================
# PAYMENT MODEL
# ============================================================================

class Payment(models.Model):
    """
    Represents a single rent payment made by a tenant.
    
    Critical Business Rules:
    1. NO duplicate payments for same lease + same month
    2. Payment month must be within lease period
    3. Track payment method and reference number
    4. Detect late payments automatically
    
    Examples:
    - Tenant pays ₦180,000 on Jan 5 for January rent
    - Tenant pays ₦180,000 on Jan 28 for February rent (early!)
    - Tenant pays ₦180,000 on Mar 15 for March rent (late)
    """
    
    # ========================================================================
    # PAYMENT METHOD CHOICES
    # ========================================================================
    
    CASH = 'CASH'
    BANK_TRANSFER = 'BANK_TRANSFER'
    MOBILE_MONEY = 'MOBILE_MONEY'
    CHEQUE = 'CHEQUE'
    
    PAYMENT_METHOD_CHOICES = [
        (CASH, 'Cash'),
        (BANK_TRANSFER, 'Bank Transfer'),
        (MOBILE_MONEY, 'Mobile Money'),
        (CHEQUE, 'Cheque'),
    ]
    # How the tenant paid
    # Used for: financial reports, tracking payment channels
    
    
    # ========================================================================
    # CORE RELATIONSHIPS
    # ========================================================================
    
    lease = models.ForeignKey(
        'leases.Lease',
        on_delete=models.PROTECT,
        related_name='payments'
    )
    # WHICH LEASE THIS PAYMENT IS FOR
    #
    # 'leases.Lease' = string reference to avoid circular imports
    # on_delete=models.PROTECT:
    #   Can't delete lease if it has payment records
    #   Financial records must be preserved (legal requirement!)
    #
    # related_name='payments':
    #   lease.payments.all() = all payments for this lease
    #   Used in: tenant payment history, landlord income reports
    
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='recorded_payments',
        null=True,
        blank=True
    )
    # WHO RECORDED THIS PAYMENT (landlord or manager)
    # Audit trail - know who entered the payment
    # on_delete=models.SET_NULL: If user deleted, payment remains but recorder = NULL
    # Optional: automated payments might not have a recorder
    
    
    # ========================================================================
    # PAYMENT DETAILS
    # ========================================================================
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount paid"
    )
    # HOW MUCH WAS PAID
    #
    # DecimalField for money - NEVER FloatField!
    # Why? Float has rounding errors:
    #   0.1 + 0.2 = 0.30000000000000004 (wrong!)
    #   Decimal: 0.1 + 0.2 = 0.3 (exact!)
    #
    # max_digits=10: Up to 10 digits total (99,999,999.99)
    # decimal_places=2: Two decimals (kobo/cents)
    #
    # Why allow amount ≠ lease.monthly_rent?
    # - Partial payments (tenant pays ₦100,000 of ₦180,000)
    # - Late fees added (₦180,000 + ₦5,000 late fee = ₦185,000)
    # - Discounts (landlord gives ₦10,000 discount)
    
    payment_date = models.DateField(
        help_text="Date when payment was made"
    )
    # WHEN THE PAYMENT WAS ACTUALLY MADE
    #
    # DateField = date only (no time)
    # This is the ACTUAL date money was received
    #
    # Examples:
    # - January rent paid on Jan 5 → payment_date = 2024-01-05
    # - February rent paid early on Jan 28 → payment_date = 2024-01-28
    #
    # Used for: calculating if payment was late
    
    payment_month = models.DateField(
        help_text="Month this payment covers (first day of month)"
    )
    # WHICH MONTH THIS PAYMENT IS FOR
    #
    # THIS IS THE CRITICAL FIELD FOR DUPLICATE PREVENTION!
    #
    # Always store as FIRST DAY of the month:
    # - January 2024 → 2024-01-01
    # - February 2024 → 2024-02-01
    # - March 2024 → 2024-03-01
    #
    # Why first day?
    # - Standardized format (always same day)
    # - Easy to compare (all January payments have same date)
    # - Database unique constraint works correctly
    #
    # Example:
    # Payment made on Jan 5 for January → payment_month = 2024-01-01
    # Payment made on Jan 28 for February → payment_month = 2024-02-01
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=BANK_TRANSFER
    )
    # HOW TENANT PAID
    # default=BANK_TRANSFER: Most common method
    # Used in: reports (how many cash vs bank payments?)
    
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Transaction reference or receipt number"
    )
    # PROOF OF PAYMENT
    #
    # Examples:
    # - Bank transfer: "TXN20240105ABC123"
    # - Mobile money: "MPESA-2024-001234"
    # - Cash: "RCPT-001" (manual receipt)
    #
    # Optional but recommended
    # Used for: verifying payment, resolving disputes
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this payment"
    )
    # OPTIONAL NOTES
    #
    # Examples:
    # - "Partial payment - remaining ₦80,000 to be paid by 15th"
    # - "Includes ₦5,000 late fee"
    # - "Early payment discount applied"
    
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    
    created_at = models.DateTimeField(auto_now_add=True)
    # When payment record was created in system
    
    updated_at = models.DateTimeField(auto_now=True)
    # When payment record was last modified
    
    
    # ========================================================================
    # META OPTIONS
    # ========================================================================
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']
        # Newest payments first
        
        constraints = [
            models.UniqueConstraint(
                fields=['lease', 'payment_month'],
                name='unique_lease_payment_month'
            )
        ]
        # THIS IS THE DUPLICATE PREVENTION!
        #
        # UniqueConstraint enforces at DATABASE level:
        # - Can't have TWO payments with same lease + same payment_month
        # - Database will reject the second one
        #
        # Example (ALLOWED):
        # Payment 1: lease=John's lease, payment_month=2024-01-01 ✅
        # Payment 2: lease=John's lease, payment_month=2024-02-01 ✅ (different month)
        # Payment 3: lease=Sarah's lease, payment_month=2024-01-01 ✅ (different lease)
        #
        # Example (BLOCKED):
        # Payment 1: lease=John's lease, payment_month=2024-01-01 ✅
        # Payment 2: lease=John's lease, payment_month=2024-01-01 ❌ DUPLICATE!
        #
        # This is STRONGER than model validation because:
        # - Database enforces it (can't bypass)
        # - Works even with raw SQL
        # - Prevents race conditions (two payments at exact same time)
    
    
    # ========================================================================
    # STRING REPRESENTATION
    # ========================================================================
    
    def __str__(self):
        return f"{self.lease.unit} - {self.lease.tenant.username} - {self.payment_month.strftime('%B %Y')}"
        # Example: "Sunset Apartments - Unit 204 - john_doe - January 2024"
        # strftime('%B %Y') = "January 2024" (month name + year)
    
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def clean(self):
        """
        Custom validation - called before saving.
        Enforces business rules.
        """
        super().clean()
        
        # Rule 1: payment_month must be within lease period
        if self.lease and self.payment_month:
            # Convert payment_month to first day of month (in case it's not)
            payment_month_start = self.payment_month.replace(day=1)
            
            # Check if payment_month is within lease start/end dates
            # We compare MONTHS, not exact dates
            lease_start_month = self.lease.start_date.replace(day=1)
            lease_end_month = self.lease.end_date.replace(day=1)
            
            if payment_month_start < lease_start_month or payment_month_start > lease_end_month:
                raise ValidationError({
                    'payment_month': f'Payment month must be within lease period ({self.lease.start_date} to {self.lease.end_date}).'
                })
        
        # Rule 2: Amount must be positive
        if self.amount and self.amount <= 0:
            raise ValidationError({
                'amount': 'Payment amount must be greater than zero.'
            })
    
    
   # ========================================================================
    # PAYMENT STATUS METHODS (FIXED - USE 5-DAY GRACE PERIOD)
    # ========================================================================
    
    GRACE_PERIOD_DAYS = 5
    
    def expected_payment_date(self):
        """Calculate when payment should be made (with grace period)."""
        from datetime import timedelta
        return self.payment_month + timedelta(days=self.GRACE_PERIOD_DAYS)
    
    def is_late(self):
        """Check if payment was made after the grace period."""
        return self.payment_date > self.expected_payment_date()
    
    def days_late(self):
        """Calculate how many days late the payment was."""
        if not self.is_late():
            return 0
        
        expected = self.expected_payment_date()
        delta = self.payment_date - expected
        return delta.days
    
    def late_fee_applicable(self):
        """Calculate late fee if applicable."""
        from decimal import Decimal
        if not self.is_late():
            return Decimal('0.00')
        return Decimal('0.00')
    
    def payment_status(self):
        """Get human-readable payment status."""
        if self.is_late():
            days = self.days_late()
            return f"Late ({days} day{'s' if days != 1 else ''})"
        elif self.payment_date < self.payment_month:
            return "Early"
        else:
            return "On Time"