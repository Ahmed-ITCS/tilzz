from rest_framework import serializers
from .models import Story, Episode, Version, Like, Favorite, QuarantineReport
from accounts.serializers import UserSerializer

class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ['id', 'content', 'version_number', 'created_at']

class EpisodeSerializer(serializers.ModelSerializer):
    versions = VersionSerializer(many=True, read_only=True)
    has_next_version = serializers.SerializerMethodField()
    has_previous_version = serializers.SerializerMethodField()
    
    class Meta:
        model = Episode
        fields = ['id', 'title', 'number', 'created_at', 'updated_at', 'versions', 'has_next_version', 'has_previous_version']
    
    def get_has_next_version(self, obj):
        latest_version = obj.versions.order_by('-version_number').first()
        if not latest_version:
            return False
        return obj.versions.filter(version_number__gt=latest_version.version_number).exists()
    
    def get_has_previous_version(self, obj):
        latest_version = obj.versions.order_by('-version_number').first()
        if not latest_version or latest_version.version_number <= 1:
            return False
        return obj.versions.filter(version_number__lt=latest_version.version_number).exists()

class StorySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    episodes_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = ['id', 'title', 'author', 'description', 'cover_image', 'status', 
                  'created_at', 'updated_at', 'episodes_count', 'likes_count', 
                  'is_liked', 'is_favorited']
        read_only_fields = ['author', 'status', 'created_at', 'updated_at']
    
    def get_episodes_count(self, obj):
        return obj.episodes.count()
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False

class StoryDetailSerializer(StorySerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    
    class Meta(StorySerializer.Meta):
        fields = StorySerializer.Meta.fields + ['episodes']

class StoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ['title', 'description', 'cover_image']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class EpisodeCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(write_only=True)
    
    class Meta:
        model = Episode
        fields = ['title', 'number', 'content']
    
    def create(self, validated_data):
        content = validated_data.pop('content')
        story = self.context.get('story')
        
        episode = Episode.objects.create(story=story, **validated_data)
        
        # Create the first version
        Version.objects.create(
            episode=episode,
            content=content,
            version_number=1
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