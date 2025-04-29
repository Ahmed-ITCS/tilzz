from django.db import models
from accounts.models import User

class Story(models.Model):
    PUBLIC = 'public'
    PRIVATE = 'private'
    VISIBILITY_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    ]
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('quarantined', 'Quarantined'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    description = models.TextField()
    cover_image = models.ImageField(upload_to='story_covers/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    quarantine_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default=PUBLIC
    )
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Stories"

class Episode(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='episodes')
    title = models.CharField(max_length=255)
    number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.story.title} - Episode {self.number}: {self.title}"
    
    class Meta:
        unique_together = ('story', 'number')
        ordering = ['number']

class Version(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    version_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.episode} - Version {self.version_number}"
    
    class Meta:
        unique_together = ('episode', 'version_number')
        ordering = ['version_number']

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'story')
    
    def __str__(self):
        return f"{self.user.username} likes {self.story.title}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'story')
    
    def __str__(self):
        return f"{self.user.username} favorited {self.story.title}"

class QuarantineReport(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Report for {self.story.title} by {self.reported_by.username}"

class StoryFollower(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='followed_stories')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'user')
