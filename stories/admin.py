from django.contrib import admin
from .models import Story, Episode, Version, Like, Favorite, QuarantineReport

class VersionInline(admin.TabularInline):
    model = Version
    extra = 1

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1

class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'quarantine_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    inlines = [EpisodeInline]

class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'story', 'number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'story__title')
    inlines = [VersionInline]

admin.site.register(Story, StoryAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Version)
admin.site.register(Like)
admin.site.register(Favorite)
admin.site.register(QuarantineReport)
