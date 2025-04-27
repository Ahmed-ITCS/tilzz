from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a story to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the author
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'story'):
            return obj.story.author == request.user
        elif hasattr(obj, 'episode'):
            return obj.episode.story.author == request.user
        
        return False

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit but anyone to view.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and (request.user.is_superuser or request.user.role in ['admin', 'subadmin'])