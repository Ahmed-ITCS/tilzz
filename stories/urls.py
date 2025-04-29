from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoryViewSet, EpisodeViewSet, VersionViewSet, PublicStoryViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'public-stories', PublicStoryViewSet, basename='public-story')

# Nested routers for episodes and versions
story_router = DefaultRouter()
story_router.register(r'episodes', EpisodeViewSet, basename='episode')

episode_router = DefaultRouter()
episode_router.register(r'versions', VersionViewSet, basename='version')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('stories/<int:story_pk>/', include(story_router.urls)),
    path('stories/<int:story_pk>/episodes/<int:episode_pk>/', include(episode_router.urls)),
]