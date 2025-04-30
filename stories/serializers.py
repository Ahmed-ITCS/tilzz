from rest_framework import serializers
from .models import Story, Episode, Version, Like, Favorite, QuarantineReport
from accounts.serializers import UserSerializer
from .models import StoryFollower

class StorySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'title', 'description', 'author', 'visibility',
            'status', 'created_at', 'updated_at', 'is_liked',
            'is_favorited', 'is_followed', 'likes_count'
        ]
        read_only_fields = ['author', 'status', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, story=obj).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, story=obj).exists()
        return False

    def get_is_followed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryFollower.objects.filter(user=request.user, story=obj).exists()
        return False

    def get_likes_count(self, obj):
        return Like.objects.filter(story=obj).count()

class EpisodeSerializer(serializers.ModelSerializer):
    has_next = serializers.SerializerMethodField()
    has_previous = serializers.SerializerMethodField()
    next_episode = serializers.SerializerMethodField()
    previous_episode = serializers.SerializerMethodField()
    versions_count = serializers.SerializerMethodField()
    next_version = serializers.SerializerMethodField()
    previous_version = serializers.SerializerMethodField()
    has_next_version = serializers.SerializerMethodField()
    has_previous_version = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = [
            'id', 'story', 'number', 'title', 'created_at', 'updated_at',
            'has_next', 'has_previous', 'next_episode', 'previous_episode',
            'versions_count', 'next_version', 'previous_version',
            'has_next_version', 'has_previous_version'
        ]

    def get_has_next(self, obj):
        return Episode.objects.filter(story=obj.story, number__gt=obj.number).exists()

    def get_has_previous(self, obj):
        return Episode.objects.filter(story=obj.story, number__lt=obj.number).exists()

    def get_next_episode(self, obj):
        next_episode = Episode.objects.filter(
            story=obj.story, 
            number__gt=obj.number
        ).order_by('number').first()
        return next_episode.id if next_episode else None

    def get_previous_episode(self, obj):
        prev_episode = Episode.objects.filter(
            story=obj.story, 
            number__lt=obj.number
        ).order_by('-number').first()
        return prev_episode.id if prev_episode else None

    def get_versions_count(self, obj):
        return Version.objects.filter(episode=obj).count()

    def get_has_next_version(self, obj):
        current_version = Version.objects.filter(episode=obj).order_by('-version_number').first()
        if current_version:
            return Version.objects.filter(
                episode=obj,
                version_number__gt=current_version.version_number
            ).exists()
        return False

    def get_has_previous_version(self, obj):
        current_version = Version.objects.filter(episode=obj).order_by('-version_number').first()
        if current_version:
            return Version.objects.filter(
                episode=obj,
                version_number__lt=current_version.version_number
            ).exists()
        return False

    def get_next_version(self, obj):
        current_version = Version.objects.filter(episode=obj).order_by('-version_number').first()
        if current_version:
            next_version = Version.objects.filter(
                episode=obj,
                version_number__gt=current_version.version_number
            ).order_by('version_number').first()
            return next_version.id if next_version else None
        return None

    def get_previous_version(self, obj):
        current_version = Version.objects.filter(episode=obj).order_by('-version_number').first()
        if current_version:
            prev_version = Version.objects.filter(
                episode=obj,
                version_number__lt=current_version.version_number
            ).order_by('-version_number').first()
            return prev_version.id if prev_version else None
        return None

class VersionSerializer(serializers.ModelSerializer):
    has_next = serializers.SerializerMethodField()
    has_previous = serializers.SerializerMethodField()
    next_version = serializers.SerializerMethodField()
    previous_version = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = [
            'id', 'episode', 'version_number', 'content', 'created_at', 
            'has_next', 'has_previous', 'next_version', 'previous_version'
        ]

    def get_has_next(self, obj):
        return Version.objects.filter(
            episode=obj.episode,
            version_number__gt=obj.version_number
        ).exists()

    def get_has_previous(self, obj):
        return Version.objects.filter(
            episode=obj.episode,
            version_number__lt=obj.version_number
        ).exists()

    def get_next_version(self, obj):
        next_version = Version.objects.filter(
            episode=obj.episode,
            version_number__gt=obj.version_number
        ).order_by('version_number').first()
        return next_version.id if next_version else None

    def get_previous_version(self, obj):
        prev_version = Version.objects.filter(
            episode=obj.episode,
            version_number__lt=obj.version_number
        ).order_by('-version_number').first()
        return prev_version.id if prev_version else None

class EpisodeCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(write_only=True)
    
    class Meta:
        model = Episode
        fields = ['title', 'number', 'content']
    
    def create(self, validated_data):
        content = validated_data.pop('content')
        story = self.context.get('story')
        current_version_number = self.context.get('current_version_number', 1)  # Gets version 3
        
        episode = Episode.objects.create(story=story, **validated_data)
        
        # Creates Episode 2 with Version 3
        Version.objects.create(
            episode=episode,
            content=content,
            version_number=current_version_number  # Uses version 3
        )
        
        return episode

class VersionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ['content']
    
    def create(self, validated_data):
        episode = self.context.get('episode')
        
        # Get the latest version number
        latest_version = episode.versions.order_by('-version_number').first()
        version_number = 1 if not latest_version else latest_version.version_number + 1
        
        return Version.objects.create(
            episode=episode,
            content=validated_data['content'],
            version_number=version_number
        )

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'story', 'created_at']
        read_only_fields = ['created_at']

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'story', 'created_at']
        read_only_fields = ['created_at']

class QuarantineReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuarantineReport
        fields = ['id', 'story', 'reason', 'created_at']
        read_only_fields = ['created_at']

class StoryFollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryFollower
        fields = ['story', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']


class StoryDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    episodes_count = serializers.SerializerMethodField()
    has_next = serializers.SerializerMethodField()
    has_previous = serializers.SerializerMethodField()
    next_story = serializers.SerializerMethodField()
    previous_story = serializers.SerializerMethodField()
    has_next_episode = serializers.SerializerMethodField()
    has_previous_episode = serializers.SerializerMethodField()
    next_episode_id = serializers.SerializerMethodField()
    previous_episode_id = serializers.SerializerMethodField()
    has_next_version = serializers.SerializerMethodField()
    has_previous_version = serializers.SerializerMethodField()
    next_version_id = serializers.SerializerMethodField()
    previous_version_id = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id', 'title', 'description', 'author', 'visibility',
            'status', 'created_at', 'updated_at', 'is_liked',
            'is_favorited', 'is_followed', 'likes_count', 'episodes_count',
            'has_next', 'has_previous', 'next_story', 'previous_story',
            'has_next_episode', 'has_previous_episode', 'next_episode_id', 'previous_episode_id',
            'has_next_version', 'has_previous_version', 'next_version_id', 'previous_version_id'
        ]
        read_only_fields = ['author', 'status', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, story=obj).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, story=obj).exists()
        return False

    def get_is_followed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryFollower.objects.filter(user=request.user, story=obj).exists()
        return False

    def get_likes_count(self, obj):
        return Like.objects.filter(story=obj).count()

    def get_episodes_count(self, obj):
        return Episode.objects.filter(story=obj).count()

    def get_has_next(self, obj):
        return Story.objects.filter(
            author=obj.author,
            created_at__gt=obj.created_at
        ).exists()

    def get_has_previous(self, obj):
        return Story.objects.filter(
            author=obj.author,
            created_at__lt=obj.created_at
        ).exists()

    def get_next_story(self, obj):
        next_story = Story.objects.filter(
            author=obj.author,
            created_at__gt=obj.created_at
        ).order_by('created_at').first()
        return next_story.id if next_story else None

    def get_previous_story(self, obj):
        prev_story = Story.objects.filter(
            author=obj.author,
            created_at__lt=obj.created_at
        ).order_by('-created_at').first()
        return prev_story.id if prev_story else None

    def get_has_next_episode(self, obj):
        current_episode = self.context.get('current_episode')
        if current_episode:
            return Episode.objects.filter(story=obj, number__gt=current_episode.number).exists()
        return False

    def get_has_previous_episode(self, obj):
        current_episode = self.context.get('current_episode')
        if current_episode:
            return Episode.objects.filter(story=obj, number__lt=current_episode.number).exists()
        return False

    def get_next_episode_id(self, obj):
        current_episode = self.context.get('current_episode')
        if current_episode:
            next_episode = Episode.objects.filter(
                story=obj,
                number__gt=current_episode.number
            ).order_by('number').first()
            return next_episode.id if next_episode else None
        return None

    def get_previous_episode_id(self, obj):
        current_episode = self.context.get('current_episode')
        if current_episode:
            prev_episode = Episode.objects.filter(
                story=obj,
                number__lt=current_episode.number
            ).order_by('-number').first()
            return prev_episode.id if prev_episode else None
        return None

    def get_has_next_version(self, obj):
        current_version = self.context.get('current_version')
        if current_version:
            return Version.objects.filter(
                episode__story=obj,
                version_number__gt=current_version.version_number
            ).exists()
        return False

    def get_has_previous_version(self, obj):
        current_version = self.context.get('current_version')
        if current_version:
            return Version.objects.filter(
                episode__story=obj,
                version_number__lt=current_version.version_number
            ).exists()
        return False

    def get_next_version_id(self, obj):
        current_version = self.context.get('current_version')
        if current_version:
            next_version = Version.objects.filter(
                episode__story=obj,
                version_number__gt=current_version.version_number
            ).order_by('version_number').first()
            return next_version.id if next_version else None
        return None

    def get_previous_version_id(self, obj):
        current_version = self.context.get('current_version')
        if current_version:
            prev_version = Version.objects.filter(
                episode__story=obj,
                version_number__lt=current_version.version_number
            ).order_by('-version_number').first()
            return prev_version.id if prev_version else None
        return None

# Add this after StorySerializer and before VersionSerializer

class StoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ['title', 'description', 'visibility']

    def create(self, validated_data):
        user = self.context['request'].user
        story = Story.objects.create(
            author=user,
            **validated_data
        )
        return story