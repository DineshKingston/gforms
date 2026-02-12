from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse

from .models import Form, FormResponse
from .serializers import FormSerializer, FormResponseSerializer
from .permissions import IsAdminOrReadOnly, CanSubmitForm, CanViewResponses
from .utils import upload_file_to_s3, generate_excel_export, has_file_fields, get_file_fields


class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanSubmitForm])
    def submit(self, request, pk=None):
        form = self.get_object()
        
        # Convert QueryDict to regular dict for multipart/form-data
        # This handles both JSON and multipart submissions
        if hasattr(request.data, 'dict'):
            # Multipart form data (QueryDict)
            response_data = dict(request.data)
            # QueryDict stores values as lists, get first value for each key
            response_data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                           for k, v in response_data.items()}
        else:
            # JSON data (dict)
            response_data = dict(request.data)
        
        # Check if form has file fields
        if has_file_fields(form.schema):
            file_field_names = get_file_fields(form.schema)
            
            # Process file uploads
            for field_name in file_field_names:
                if field_name in request.FILES:
                    try:
                        file = request.FILES[field_name]
                        # Upload to S3 and get URL
                        file_url = upload_file_to_s3(file, form.id, field_name)
                        # Store URL in response data
                        response_data[field_name] = file_url
                    except Exception as e:
                        return Response(
                            {'error': f'Failed to upload file for field {field_name}: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
        
        serializer_data = {
            'form': form.id,
            'response_data': response_data
        }
        
        serializer = FormResponseSerializer(data=serializer_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {
                    'message': 'Form submitted successfully',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, CanViewResponses])
    def responses(self, request, pk=None):
        form = self.get_object()
        responses = FormResponse.objects.filter(form=form)
        serializer = FormResponseSerializer(responses, many=True)
        
        return Response({
            'form': form.name,
            'total_responses': responses.count(),
            'responses': serializer.data
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, CanViewResponses], url_path='export-excel')
    def export_excel(self, request, pk=None):
        """
        Export form responses as Excel file.
        Only available if form has allow_excel_download enabled.
        """
        form = self.get_object()
        
        # Check if Excel download is allowed for this form
        if not form.allow_excel_download:
            return Response(
                {'error': 'Excel download is not enabled for this form'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all responses for this form
        responses = FormResponse.objects.filter(form=form).order_by('-submitted_at')
        
        if not responses.exists():
            return Response(
                {'error': 'No responses found for this form'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Generate Excel file
            excel_file = generate_excel_export(form, responses)
            
            # Create HTTP response with Excel file
            filename = f"{form.name.replace(' ', '_')}_responses.xlsx"
            response = HttpResponse(
                excel_file.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate Excel file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )