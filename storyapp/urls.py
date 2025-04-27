from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from accounts.views import UserViewSet, FollowViewSet, OrganizationViewSet
from stories.views import PublicStoryViewSet, StoryViewSet, EpisodeViewSet, VersionViewSet
from admin_panel.views import (
    AdminUserViewSet, SubAdminUserViewSet, AdminOrganizationViewSet,
    QuarantinedStoryViewSet
)

# Create routers
router = DefaultRouter()

# Public endpoints (no authentication required)
router.register(r'public/stories', PublicStoryViewSet)

# User endpoints
router.register(r'users', UserViewSet, basename='user')
router.register(r'follows', FollowViewSet, basename='follow')
router.register(r'organizations', OrganizationViewSet, basename='user-organization')  # Added unique basename

# Story endpoints
router.register(r'stories', StoryViewSet, basename='user-story')

# Admin panel endpoints
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
router.register(r'admin/subadmin/users', SubAdminUserViewSet, basename='subadmin-user')
router.register(r'admin/organizations', AdminOrganizationViewSet, basename='admin-organization')
router.register(r'admin/quarantined-stories', QuarantinedStoryViewSet, basename='quarantined-story')  # Added unique basename

# Nested routes for episodes and versions
story_router = DefaultRouter()
story_router.register(r'episodes', EpisodeViewSet, basename='episode')

episode_router = DefaultRouter()
episode_router.register(r'versions', VersionViewSet, basename='version')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/stories/<int:story_pk>/', include(story_router.urls)),
    path('api/stories/<int:story_pk>/episodes/<int:episode_pk>/', include(episode_router.urls)),
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
