from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from accounts.models import Organization
from stories.models import Story, QuarantineReport
from accounts.serializers import UserSerializer, OrganizationSerializer
from stories.serializers import StorySerializer, QuarantineReportSerializer

User = get_user_model()

class AdminPermission(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access admin panel.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.user.role == 'admin')

class SubAdminPermission(permissions.BasePermission):
    """
    Custom permission to allow admin and subadmin users to access certain views.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.user.role in ['admin', 'subadmin'])

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermission]
    
    @action(detail=True, methods=['post'])
    def make_subadmin(self, request, pk=None):
        user = self.get_object()
        organization_id = request.data.get('organization_id')
        
        if not organization_id:
            return Response(
                {'detail': 'Organization ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            organization = Organization.objects.get(pk=organization_id)
            
            # Make user a subadmin
            user.role = 'subadmin'
            user.organization = organization
            user.save()
            
            return Response(UserSerializer(user).data)
        except Organization.DoesNotExist:
            return Response(
                {'detail': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def assign_to_organization(self, request, pk=None):
        user = self.get_object()
        organization_id = request.data.get('organization_id')
        
        if not organization_id:
            return Response(
                {'detail': 'Organization ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            organization = Organization.objects.get(pk=organization_id)
            
            # Assign user to organization
            user.organization = organization
            user.save()
            
            return Response(UserSerializer(user).data)
        except Organization.DoesNotExist:
            return Response(
                {'detail': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class SubAdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, SubAdminPermission]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return User.objects.all()
        elif user.role == 'subadmin' and user.organization:
            return User.objects.filter(organization=user.organization)
        return User.objects.none()
    
    @action(detail=True, methods=['post'])
    def add_to_organization(self, request, pk=None):
        if request.user.role != 'subadmin' or not request.user.organization:
            return Response(
                {'detail': 'You do not have permission to add users to an organization'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        # Add user to subadmin's organization
        user.organization = request.user.organization
        user.save()
        
        return Response(UserSerializer(user).data)

class AdminOrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermission]

class QuarantinedStoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.filter(status='quarantined')
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated, AdminPermission]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        story = self.get_object()
        story.status = 'approved'
        story.quarantine_count = 0
        story.save()
        
        return Response({'status': 'story approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        story = self.get_object()
        story.status = 'rejected'
        story.save()
        
        return Response({'status': 'story rejected'})
    
    @action(detail=True, methods=['get'])
    def reports(self, request, pk=None):
        story = self.get_object()
        reports = QuarantineReport.objects.filter(story=story)
        serializer = QuarantineReportSerializer(reports, many=True)
        
        return Response(serializer.data)
