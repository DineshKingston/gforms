from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Form, FormResponse
from .serializers import FormSerializer, FormResponseSerializer
from .permissions import IsAdminOrReadOnly, CanSubmitForm, CanViewResponses


class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanSubmitForm])
    def submit(self, request, pk=None):
        form = self.get_object()
        response_data = {
            'form': form.id,
            'response_data': request.data
        }
        
        serializer = FormResponseSerializer(data=response_data)
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