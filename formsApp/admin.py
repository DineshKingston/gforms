from django.contrib import admin
from .models import Form, FormResponse


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ['form', 'user', 'submitted_at']
    list_filter = ['submitted_at', 'form']
    search_fields = ['user__email', 'form__name']
    readonly_fields = ['submitted_at']
