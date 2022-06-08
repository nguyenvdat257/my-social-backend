from pip import main
from pytz import timezone
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
import re
import cv2
import os


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        user = User.objects.create(username=validated_data['username'])
        user.set_password(validated_data['password'])
        user.save()
        profile = Profile.objects.create(user=user, name=self.context['name'], email=self.context['email'])
        profile.save()
        return user


class ProfileSerializer(DynamicFieldsModelSerializer):
    username = serializers.CharField(read_only=True, source='user.username')
    num_posts = serializers.IntegerField(read_only=True, source='num_posts')
    num_followings = serializers.IntegerField(
        read_only=True, source='num_followings')
    num_followers = serializers.IntegerField(
        read_only=True, source='num_followers')
    is_follow = serializers.SerializerMethodField()

    def get_is_follow(self, obj):
        if 'profile' not in self.context:
            return False
        return Follow.objects.filter(follower=self.context['profile'], following=obj).exists()

    class Meta:
        model = Profile
        fields = '__all__'

    def update(self, profile, validated_data):
        username = self.context.get('username')
        new_username = self.context.get('new_username')
        user = User.objects.get(username=username)
        user_data = {'username': new_username}
        user_serializer = UserSerializer(
            instance=user, data=user_data, partial=True)

        if user_serializer.is_valid():
            user_serializer.save()
        for (key, value) in validated_data.items():
            setattr(profile, key, value)
        profile.save()
        return profile


class ProfileLightSerializer(ModelSerializer):
    username = serializers.CharField(read_only=True, source='user.username')
    is_follow = serializers.SerializerMethodField()

    def get_is_follow(self, obj):
        if 'profile' not in self.context:
            return False
        return Follow.objects.filter(follower=self.context['profile'], following=obj).exists()

    class Meta:
        model = Profile
        fields = ['name', 'username', 'avatar', 'is_follow']


class HashtagSerializer(ModelSerializer):
    body = serializers.CharField()

    class Meta:
        model = HashTag
        fields = '__all__'

    def create(self, validated_data):
        post = self.context.get('post')
        hashtag, created = HashTag.objects.get_or_create(**validated_data)
        post.hash_tags.add(hashtag)
        return hashtag


class PostImageSerializer(ModelSerializer):
    class Meta:
        model = PostImage
        fields = '__all__'


class PostLightSerializer(ModelSerializer):
    images = PostImageSerializer(source='postimage_set', many=True)

    class Meta:
        model = Post
        fields = ['images', 'likes_count', 'comments_count', 'code']


class PostSerializer(DynamicFieldsModelSerializer):
    hash_tags = HashtagSerializer(many=True)
    images = PostImageSerializer(source='postimage_set', many=True)
    profile_info = ProfileLightSerializer(source='profile', read_only=True)

    class Meta:
        model = Post
        fields = '__all__'

    def get_hashtag(self, body):
        hashtags = list(set(re.findall(r"#(\w+)", body)))
        return hashtags

    def create(self, validated_data):
        code = get_random_string(length=11)
        while Post.objects.filter(code=code).exists():
            code = get_random_string(length=11)
        validated_data.update({'code': code})
        new_post = Post.objects.create(**validated_data)

        # add hashtags
        hashtags = self.get_hashtag(validated_data['body'])
        new_hashtags_data = [{'body': hashtag}
                             for hashtag in hashtags]
        hashtag_serializer = HashtagSerializer(
            data=new_hashtags_data, many=True, context={'post': new_post})
        if hashtag_serializer.is_valid():
            hashtag_serializer.save()

        # add images
        images_data = [{'post': new_post.id, 'image': image, 'order': order}
                       for order, image in enumerate(self.context.get('images'))]
        image_serializer = PostImageSerializer(data=images_data, many=True)
        if image_serializer.is_valid():
            image_serializer.save()

        # add video thumbnail
        if validated_data.get('video'):
            fs = FileSystemStorage()
            filename = fs.save('videos/temp.mp4', validated_data['video'])
            uploaded_file_url = fs.url(filename)
            video_path = 'insta_server' + uploaded_file_url
            vidcap = cv2.VideoCapture(video_path)
            success, image = vidcap.read()
            if success:
                ret, buf = cv2.imencode('.jpg', image)
                new_post.video_thumbnail.save(
                    name='video_thumbnail.jpg', content=ContentFile(buf.tobytes()))
                vidcap.release()
                os.remove(video_path)

        return new_post

    def update(self, post, validated_data):
        post.hash_tags.clear()
        hashtags = self.get_hashtag(validated_data['body'])
        new_hashtags_data = [{'body': hashtag}
                             for hashtag in hashtags]
        hashtag_serializer = HashtagSerializer(
            data=new_hashtags_data, many=True, context={'post': post})
        if hashtag_serializer.is_valid():
            hashtag_serializer.save()
        post.body = validated_data['body']
        return post


class CommentSerializer(ModelSerializer):
    username = serializers.CharField(
        read_only=True, source='profile.user.username')
    avatar = serializers.ImageField(read_only=True, source='profile.avatar')

    class Meta:
        model = Comment
        fields = '__all__'

    def create(self, validated_data):
        new_comment = Comment.objects.create(**validated_data)
        return new_comment


class StoryImageSerializer(ModelSerializer):
    class Meta:
        model = StoryImage
        fields = '__all__'


class StorySerializer(ModelSerializer):
    images = StoryImageSerializer(source='storyimage_set', many=True)
    profile_info = ProfileLightSerializer(source='profile', read_only=True)
    hour_ago = serializers.IntegerField()

    class Meta:
        model = Story
        exclude = ('view_profiles', 'like_profiles')

    def create(self, validated_data):
        new_story = Story.objects.create(**validated_data)

        # add images
        images_data = [{'story': new_story.id, 'image': image}
                       for image in self.context.get('images')]
        image_serializer = StoryImageSerializer(data=images_data, many=True)
        if image_serializer.is_valid():
            image_serializer.save()
        return new_story

class NotificationSerializer(ModelSerializer):
    post = PostLightSerializer()
    comment = CommentSerializer()
    class Meta:
        model = Notification
        fields = '__all__'
    
