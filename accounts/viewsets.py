from rest_framework import viewsets
from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication


class RegisterUserViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = []
    authentication_classes = []
    
    def create (self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def login(self,request):
        user = User.objects.get(re)
        return Response(self.serializer_class(user).data, status=status.HTTP_200_OK)
    
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    def list(self, request):
        return self.retrieve(request, pk=request.user.id)
    