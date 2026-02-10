from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer,
    UpdateUserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)
from .permissions import IsAdmin, IsEditor, IsOwnerOrAdmin

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register', 'login']:
            return [permissions.AllowAny()]

        if self.action == 'destroy':
            return [IsAdmin()]

        if self.action == 'list':
            return [IsEditor()]
        
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [IsOwnerOrAdmin()]
        
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update'] and self.request.user.role == 'admin':
            return UpdateUserSerializer
        
        return UserSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to update this user.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Non-admins cannot change their own role
        if request.user.role != 'admin' and 'role' in request.data:
            return Response(
                {'error': 'You do not have permission to change roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to update this user.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Non-admins cannot change their own role
        if request.user.role != 'admin' and 'role' in request.data:
            return Response(
                {'error': 'You do not have permission to change roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)

    # ===== Custom Actions =====

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Role is forced to 'viewer' in serializer
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                raise Exception
        except Exception:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        })

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Wrong password.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        return Response({
            'message': 'Password changed successfully.',
            'token': token.key  # Return new token
        })
