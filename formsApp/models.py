from django.db import models
from django.conf import settings


class Form(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schema = models.JSONField(default=dict, help_text="JSON schema defining form fields")
    allow_excel_download = models.BooleanField(
        default=True,
        help_text="Allow admins to download form responses as Excel"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_forms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class FormResponse(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='form_responses'
    )
    response_data = models.JSONField(help_text="User's form submission data")
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.form.name} - {self.submitted_at}"
