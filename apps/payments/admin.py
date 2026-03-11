# ============================================================================
# IMPORTS
# ============================================================================

from django.contrib import admin
from .models import Payment


# ============================================================================
# PAYMENT ADMIN
# ============================================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for Payment model.
    Shows all payments with status, amounts, and late tracking.
    """
    
    # Columns shown in the payment list
    list_display = [
        'lease',
        'payment_month_display',
        'amount',
        'payment_date',
        'payment_method',
        'payment_status',
        'days_late',
        'reference_number',
        'created_at'
    ]
    # Shows: lease | month | amount | date paid | method | status | days late | reference | created
    
    # Filters in the right sidebar
    list_filter = [
        'payment_method',
        'payment_date',
        'payment_month',
        'lease__unit__property',
        'created_at'
    ]
    # Can filter by: payment method, dates, property
    
    # Search functionality
    search_fields = [
        'lease__unit__unit_number',
        'lease__unit__property__name',
        'lease__tenant__username',
        'lease__tenant__email',
        'reference_number'
    ]
    # Can search by: unit number, property name, tenant details, reference number
    
    # Fields shown when viewing/editing a payment
    fieldsets = (
        ('Lease Information', {
            'fields': ('lease', 'recorded_by')
        }),
        ('Payment Details', {
            'fields': (
                'amount',
                'payment_date',
                'payment_month',
                'payment_method',
                'reference_number'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    # Organized into 3 sections
    
    # Make timestamps read-only
    readonly_fields = ['created_at', 'updated_at']
    
    # Default ordering
    ordering = ['-payment_date']
    # Newest payments first
    
    # How many payments per page
    list_per_page = 45
    
    # Date hierarchy navigation
    date_hierarchy = 'payment_date'
    # Adds navigation: 2024 > March > Day
    
    # Custom display methods
    def payment_month_display(self, obj):
        """Display payment month in readable format"""
        return obj.payment_month.strftime('%B %Y')
        # January 2024, February 2024, etc.
    payment_month_display.short_description = 'Month'
    payment_month_display.admin_order_field = 'payment_month'
    
    def payment_status(self, obj):
        """Display payment status with color coding"""
        status = obj.payment_status()
        if 'Late' in status:
            return f'🔴 {status}'
        elif 'Early' in status:
            return f'🟢 {status}'
        else:
            return f'🟡 {status}'
    payment_status.short_description = 'Status'
# ```

# Save it.

# ---

# ## Step 9: Test Data for Payments

# Go to **Admin → Payments → Add Payment**

# ---

# ### **Payment 1: On-Time Payment**
# ```
# Lease: Sunset Apartments - Unit 204 - john_tenant (Active)
# Recorded by: [Your superuser]

# Amount: 180000.00
# Payment Date: 2024-01-01
# Payment Month: 2024-01-01
# Payment Method: Bank Transfer
# Reference Number: TXN20240101ABC123

# Notes: January rent - paid on time
# ```

# **Expected:** Status shows "On Time" 🟡

# ---

# ### **Payment 2: Late Payment**
# ```
# Lease: Sunset Apartments - Unit 204 - john_tenant (Active)
# Recorded by: [Your superuser]

# Amount: 180000.00
# Payment Date: 2024-02-10
# Payment Month: 2024-02-01
# Payment Method: Bank Transfer
# Reference Number: TXN20240210DEF456

# Notes: February rent - paid 9 days late
# ```

# **Expected:** Status shows "Late (9 days)" 🔴

# ---

# ### **Payment 3: Early Payment**
# ```
# Lease: Sunset Apartments - Unit 204 - john_tenant (Active)
# Recorded by: [Your superuser]

# Amount: 180000.00
# Payment Date: 2024-02-25
# Payment Month: 2024-03-01
# Payment Method: Mobile Money
# Reference Number: MPESA-2024-003789

# Notes: March rent - paid early
# ```

# **Expected:** Status shows "Early" 🟢

# ---

# ### **Payment 4: Cash Payment**
# ```
# Lease: Garden View Estate - Unit A-12 - sarah_tenant (Active)
# Recorded by: [Your superuser]

# Amount: 200000.00
# Payment Date: 2024-06-05
# Payment Month: 2024-06-01
# Payment Method: Cash
# Reference Number: RCPT-001

# Notes: June rent - cash payment
# ```

# **Expected:** Status shows "Late (4 days)" 🔴

# ---

# ### **Payment 5: Partial Payment with Late Fee**
# ```
# Lease: Garden View Estate - Unit B-05 - mike_tenant (Active)
# Recorded by: [Your superuser]

# Amount: 155000.00
# Payment Date: 2025-04-08
# Payment Month: 2025-04-01
# Payment Method: Bank Transfer
# Reference Number: TXN20250408GHI789

# Notes: April rent - partial payment ₦150,000 + ₦5,000 late fee (7 days late)
# ```

# **Expected:** Status shows "Late (7 days)" 🔴

# ---

# ## 🧪 Test Duplicate Prevention (MUST TRY THIS)

# **Try to create this payment (it SHOULD fail):**
# ```
# Lease: Sunset Apartments - Unit 204 - john_tenant (Active)
# Amount: 180000.00
# Payment Date: 2024-01-15
# Payment Month: 2024-01-01  [SAME as Payment 1!]
# Payment Method: Cash
# ```

# **Click Save.**

# **Expected Result:** ❌ **ERROR:**
# ```
# Payment with this Lease and Payment month already exists.
# ```

# **This proves duplicate prevention is working!** ✅

# ---

# ## 🧪 Test Invalid Month (Outside Lease Period)

# **Try to create this payment (it SHOULD fail):**
# ```
# Lease: Sunset Apartments - Unit 204 - john_tenant (Active)
#   [Remember: Lease runs Jan 1, 2024 to Jan 1, 2025]

# Amount: 180000.00
# Payment Date: 2025-03-01
# Payment Month: 2025-03-01  [AFTER lease ends!]
# Payment Method: Bank Transfer
# ```

# **Click Save.**

# **Expected Result:** ❌ **ERROR:**
# ```
# Payment month must be within lease period (2024-01-01 to 2025-01-01).