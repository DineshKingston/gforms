from rest_framework import serializers
from .models import Form, FormResponse


class FormSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.email')
    
    class Meta:
        model = Form
        fields = ['id', 'name', 'description', 'schema', 'allow_excel_download', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate_schema(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Schema must be a JSON object")
        
        if 'fields' not in value:
            raise serializers.ValidationError("Schema must contain 'fields' key")
        
        if not isinstance(value['fields'], list):
            raise serializers.ValidationError("'fields' must be a list")
        
        valid_field_types = ['text', 'email', 'number', 'textarea', 'select', 'checkbox', 'radio', 'date', 'file']
        
        for field in value['fields']:
            if not isinstance(field, dict):
                raise serializers.ValidationError("Each field must be a JSON object")
            
            if 'name' not in field or 'type' not in field:
                raise serializers.ValidationError("Each field must have 'name' and 'type'")
            
            if field['type'] not in valid_field_types:
                raise serializers.ValidationError(
                    f"Invalid field type '{field['type']}'. Valid types are: {', '.join(valid_field_types)}"
                )
            
            if 'required' not in field:
                field['required'] = False
        
        return value


class FormResponseSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    form_name = serializers.ReadOnlyField(source='form.name')
    
    class Meta:
        model = FormResponse
        fields = ['id', 'form', 'form_name', 'user', 'response_data', 'submitted_at']
        read_only_fields = ['user', 'submitted_at']
    
    def validate(self, data):
        form = data.get('form')
        response_data = data.get('response_data', {})
        
        if not form:
            raise serializers.ValidationError("Form is required")
        
        schema = form.schema
        fields = schema.get('fields', [])
        
        # Check required fields
        for field in fields:
            field_name = field.get('name')
            is_required = field.get('required', False)
            
            if is_required and field_name not in response_data:
                raise serializers.ValidationError(
                    f"Field '{field_name}' is required"
                )

            if field_name in response_data:
                value = response_data[field_name]
                field_type = field.get('type')

                if field_type == 'email' and value:
                    if '@' not in str(value):
                        raise serializers.ValidationError(
                            f"Field '{field_name}' must be a valid email"
                        )
        
        return data
