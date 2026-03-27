# ============================================================================
# apps/maintenance/forms.py
# ============================================================================
# Handles creation and editing of maintenance requests
# ============================================================================

# apps/maintenance/forms.py

from django import forms
from .models import MaintenanceRequest


class MaintenanceRequestForm(forms.ModelForm):
    """
    Form for TENANTS to submit a new maintenance request.
    Only exposes fields the tenant should fill in.
    'submitted_by' is set automatically in the view, not here.
    """

    class Meta:
        model = MaintenanceRequest
        fields = ['unit', 'title', 'description', 'priority', 'image']
        # ↑ These are the ONLY fields on the model a tenant should touch

        widgets = {
            # Dropdown for unit selection
            'unit': forms.Select(attrs={
                'class': 'form-control',
            }),

            # Short text input for the issue title
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Leaking pipe in bathroom',
            }),

            # Large textarea for detailed description
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the issue in detail...',
            }),

            # Dropdown for priority level
            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),

            # File upload for optional photo
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }

        labels = {
            'unit': 'Affected Unit',
            'title': 'Issue Title',
            'description': 'Description',
            'priority': 'Priority Level',
            'image': 'Attach Photo (optional)',
        }

        help_texts = {
            'priority': 'Choose EMERGENCY only for urgent safety hazards.',
            'image': 'A photo helps the manager assess the issue faster.',
        }

    def clean_title(self):
        """
        Validation: Title must be at least 5 characters.
        Prevents vague titles like 'fix' or 'help'.
        """
        title = self.cleaned_data.get('title', '').strip()

        if len(title) < 5:
            raise forms.ValidationError(
                "Please provide a more descriptive title (at least 5 characters)."
            )

        return title

    def clean_description(self):
        """
        Validation: Description must be at least 20 characters.
        Forces tenants to give enough detail for the manager to act.
        """
        description = self.cleaned_data.get('description', '').strip()

        if len(description) < 20:
            raise forms.ValidationError(
                "Please describe the issue in more detail (at least 20 characters)."
            )

        return description


class MaintenanceStatusUpdateForm(forms.ModelForm):
    """
    Form for MANAGERS to update an existing maintenance request.
    Allows changing status, assigning a technician, and logging resolution time.
    'resolved_at' is exposed here so managers can manually correct it if needed
    (the model also auto-sets it in clean(), but manual override is useful).
    """

    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'assigned_to', 'resolved_at']
        # ↑ Managers only touch these three fields

        widgets = {
            # Dropdown for status update
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),

            # Dropdown filtered to MANAGER users only (limit_choices_to on model handles this)
            'assigned_to': forms.Select(attrs={
                'class': 'form-control',
            }),

            # Date-time picker for resolved timestamp
            'resolved_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',  # Renders native date-time picker in browser
            }),
        }

        labels = {
            'status': 'Update Status',
            'assigned_to': 'Assign To',
            'resolved_at': 'Resolved At',
        }

        help_texts = {
            'resolved_at': 'Leave blank — auto-filled when status is set to Resolved or Closed.',
        }

    def clean(self):
        """
        Cross-field validation for the status update form.
        Mirrors the logic in the model's clean() to give early form-level feedback.
        """
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        resolved_at = cleaned_data.get('resolved_at')

        # If marking as RESOLVED or CLOSED, resolved_at must exist
        # (the model will auto-set it, but warn the manager either way)
        if status in ['RESOLVED', 'CLOSED'] and not resolved_at:
            # Don't raise an error — the model's clean() will auto-set it.
            # This is just a soft reminder. You can make it strict if you prefer.
            pass

        # If moving BACK to OPEN or IN_PROGRESS, resolved_at should be cleared
        if status in ['OPEN', 'IN_PROGRESS'] and resolved_at:
            raise forms.ValidationError(
                "Resolved At should be empty when status is Open or In Progress. "
                "The system will clear it automatically."
            )

        return cleaned_data