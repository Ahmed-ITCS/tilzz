from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Q
from .models import Story, Episode, Version, Like, Favorite, QuarantineReport
from .serializers import (
    StorySerializer, StoryDetailSerializer, StoryCreateSerializer,
    EpisodeSerializer, EpisodeCreateSerializer,
    VersionSerializer, VersionCreateSerializer,
    LikeSerializer, FavoriteSerializer, QuarantineReportSerializer
)
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly

class PublicStoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for public story browsing (no authentication required)
    """
    queryset = Story.objects.filter(visibility=Story.PUBLIC, status='active').order_by('-created_at')
    serializer_class = StorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'author__username']
    ordering_fields = ['created_at', 'updated_at', 'title']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StoryDetailSerializer
        return StorySerializer

class StoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for authenticated story operations
    """
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'author__username']
    ordering_fields = ['created_at', 'updated_at', 'title']
    
    def get_queryset(self):
        user = self.request.user
        return Story.objects.filter(
            Q(visibility=Story.PUBLIC) | 
            Q(author=user) |
            Q(followers__user=user)
        ).distinct().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCreateSerializer
        elif self.action == 'retrieve':
            return StoryDetailSerializer
        return StorySerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        """Get stories from users that the current user follows"""
        followed_users = request.user.following.values_list('followed', flat=True)
        queryset = Story.objects.filter(
            Q(author__in=followed_users) | Q(author=request.user),
            status='active'
        ).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_stories(self, request):
        """Get stories created by the current user"""
        queryset = Story.objects.filter(author=request.user).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a story"""
        story = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, story=story)
        
        if created:
            return Response({'status': 'story liked'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'story already liked'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a story"""
        story = self.get_object()
        like = Like.objects.filter(user=request.user, story=story).first()
        
        if like:
            like.delete()
            return Response({'status': 'story unliked'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'story not liked'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """Add story to favorites"""
        story = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, story=story)
        
        if created:
            return Response({'status': 'story added to favorites'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'story already in favorites'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unfavorite(self, request, pk=None):
        """Remove story from favorites"""
        story = self.get_object()
        favorite = Favorite.objects.filter(user=request.user, story=story).first()
        
        if favorite:
            favorite.delete()
            return Response({'status': 'story removed from favorites'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'story not in favorites'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get user's favorite stories"""
        favorites = Favorite.objects.filter(user=request.user).values_list('story', flat=True)
        queryset = Story.objects.filter(id__in=favorites).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """Report a story for quarantine"""
        story = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response({'detail': 'Reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create report
        QuarantineReport.objects.create(
            story=story,
            reported_by=request.user,
            reason=reason
        )
        
        # Increment quarantine count
        story.quarantine_count += 1
        
        # If 3 or more reports, move to quarantine
        if story.quarantine_count >= 3:
            story.status = 'quarantined'
        
        story.save()
        
        return Response({'status': 'story reported'}, status=status.HTTP_201_CREATED)

class EpisodeViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    
    def get_queryset(self):
        story_id = self.kwargs.get('story_pk')
        return Episode.objects.filter(story_id=story_id).order_by('number')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EpisodeCreateSerializer
        return EpisodeSerializer
    
    def create(self, request, *args, **kwargs):
        story_id = self.kwargs.get('story_pk')
        try:
            story = Story.objects.get(pk=story_id)
            
            # Only check if story exists and is active
            if story.status != 'active':
                return Response(
                    {'detail': 'Cannot add episodes to inactive or quarantined stories'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(data=request.data, context={'story': story})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Story.DoesNotExist:
            return Response({'detail': 'Story not found'}, status=status.HTTP_404_NOT_FOUND)

class VersionViewSet(viewsets.ModelViewSet):
    serializer_class = VersionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    
    def get_queryset(self):
        episode_id = self.kwargs.get('episode_pk')
        return Version.objects.filter(episode_id=episode_id).order_by('version_number')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VersionCreateSerializer
        return VersionSerializer

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a story"""
        story = self.get_object()
        follower, created = StoryFollower.objects.get_or_create(
            story=story,
            user=request.user
        )
        
        if created:
            return Response({'status': 'story followed'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already following story'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """Unfollow a story"""
        story = self.get_object()
        follower = StoryFollower.objects.filter(story=story, user=request.user).first()
        
        if follower:
            follower.delete()
            return Response({'status': 'story unfollowed'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'not following story'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def followed_stories(self, request):
        """Get stories followed by the current user"""
        followed_stories = StoryFollower.objects.filter(user=request.user).values_list('story', flat=True)
        queryset = Story.objects.filter(id__in=followed_stories).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
