from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import User, Organization, Follow
from .serializers import (
    UserSerializer, UserSignupSerializer, UserLoginSerializer,
    OrganizationSerializer, FollowSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['signup', 'login']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'], serializer_class=UserSignupSerializer)
    def signup(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], serializer_class=UserLoginSerializer)
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        if request.user.is_authenticated:
            request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)
    
    def create(self, request, *args, **kwargs):
        try:
            user_to_follow = User.objects.get(pk=request.data.get('followed'))
            if user_to_follow == request.user:
                return Response(
                    {'detail': 'You cannot follow yourself'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            follow, created = Follow.objects.get_or_create(
                follower=request.user,
                followed=user_to_follow
            )
            
            if not created:
                return Response(
                    {'detail': 'You are already following this user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                FollowSerializer(follow).data,
                status=status.HTTP_201_CREATED
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def unfollow(self, request, pk=None):
        try:
            user_to_unfollow = User.objects.get(pk=pk)
            follow = Follow.objects.filter(
                follower=request.user,
                followed=user_to_unfollow
            ).first()
            
            if not follow:
                return Response(
                    {'detail': 'You are not following this user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Organization.objects.all()
        elif user.role == 'subadmin':
            return Organization.objects.filter(admin=user)
        return Organization.objects.filter(members=user)
