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
from django.conf import settings
from versatileimagefield.serializers import VersatileImageFieldSerializer
from django.core.exceptions import ValidationError


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
    name = serializers.CharField(read_only=True, source='profile.name')
    email = serializers.CharField(read_only=True, source='profile.email')

    class Meta:
        model = User
        fields = '__all__'

    def is_valid(self, raise_exception=False):
        user_valid = super(UserSerializer, self).is_valid()
        profile_data = {}
        if 'name' in self.initial_data:
            profile_data['name'] = self.initial_data['name']
        if 'email' in self.initial_data:
            profile_data['email'] = self.initial_data['email']
        serializer = ProfileSerializer(data=profile_data, partial=True)
        profile_valid = serializer.is_valid()
        return user_valid and profile_valid, list(self.errors.keys()) + list(serializer.errors.keys())

    def create(self, validated_data):
        user = User.objects.create(username=self.initial_data['username'])
        user.set_password(self.initial_data['password'])
        user.save()
        profile = Profile.objects.create(
            user=user, name=self.initial_data['name'], email=self.initial_data['email'])
        profile.save()
        return user


class ProfileSerializer(DynamicFieldsModelSerializer):
    username = serializers.CharField(read_only=True, source='user.username')
    avatar = VersatileImageFieldSerializer(
        sizes=[
            ("thumbnail", "crop__100x100"),
            ("thumbnail_larger", "crop__200x200"),
        ],
        read_only=True,
    )
    num_posts = serializers.IntegerField(
        read_only=True, source='post_set.count')
    num_followings = serializers.IntegerField(
        read_only=True, source='follower.count')
    num_followers = serializers.IntegerField(
        read_only=True, source='following.count')
    is_follow = serializers.SerializerMethodField()

    def get_is_follow(self, obj):
        if 'profile' not in self.context:
            return False
        return Follow.objects.filter(follower=self.context['profile'], following=obj).exists()

    class Meta:
        model = Profile
        fields = '__all__'


class ProfileEditSerializer(ModelSerializer):
    username = serializers.CharField(read_only=True, source='user.username')
    avatar = VersatileImageFieldSerializer(
        sizes=[
            ("thumbnail", "crop__100x100"),
            ("thumbnail_larger", "crop__200x200"),
        ]
    )

    class Meta:
        model = Profile
        fields = '__all__'

    def is_valid(self, raise_exception=False):
        profile_valid = super(ProfileEditSerializer, self).is_valid()
        if self.context.get('new_username') and self.context['new_username'] != self.context['username']:
            user_data = {}
            user_data['username'] = self.context['new_username']
            serializer = UserSerializer(data=user_data, partial=True)
            user_valid = serializer.is_valid()[0]
            return user_valid and profile_valid, list(self.errors.keys()) + list(serializer.errors.keys())
        else:
            return profile_valid, list(self.errors.keys())

    def update(self, profile, validated_data):
        username = self.context.get('username')
        new_username = self.context.get('new_username')
        user = profile.user
        if new_username and new_username != username:
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
    avatar = VersatileImageFieldSerializer(
        sizes=[
            ("thumbnail", "crop__100x100"),
            ("thumbnail_larger", "crop__200x200"),
        ],
        read_only=True,
    )

    class Meta:
        model = Profile
        fields = ['name', 'username', 'avatar']


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
        fields = ['images', 'likes_count', 'comments_count', 'code', 'id']


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
            video_path = os.path.join(settings.MEDIA_ROOT, 'videos')
            video_path = os.path.join(
                video_path, 'temp_' + get_random_string(10))
            fs.save(video_path, validated_data['video'])
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
        post.save()
        return post


class CommentSerializer(ModelSerializer):
    username = serializers.CharField(
        read_only=True, source='profile.user.username')
    avatar = VersatileImageFieldSerializer(
        sizes=[
            ("thumbnail", "crop__100x100"),
        ],
        read_only=True,
        source='profile.avatar'
    )

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
    is_seen = serializers.SerializerMethodField()
    hour_ago = serializers.IntegerField()

    def get_is_seen(self, story):
        return StoryView.objects.filter(profile=self.context['current_profile'], story=story).exists()

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


class ProfileChatSerializer(ModelSerializer):
    username = serializers.CharField(read_only=True, source='user.username')
    avatar = VersatileImageFieldSerializer(
        sizes=[
            ("thumbnail", "crop__100x100"),
        ],
        read_only=True,
    )

    class Meta:
        model = Profile
        fields = ['name', 'username', 'avatar']


class ChatRoomSerializer(ModelSerializer):
    profiles = ProfileChatSerializer(many=True)
    chatroom_name = serializers.SerializerMethodField()
    is_mute = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    is_have_new_chat = serializers.SerializerMethodField()

    def get_chatroom_detail(self, chatroom):
        try:
            chatroom_profile = ChatRoomProfile.objects.get(
                chatroom=chatroom, profile=self.context['current_profile'])
            return chatroom_profile
        except:
            return None

    def get_chatroom_name(self, chatroom):
        chatroom_detail = self.get_chatroom_detail(chatroom)
        if chatroom_detail:
            return chatroom_detail.name
        return None

    def get_is_mute(self, chatroom):
        chatroom_detail = self.get_chatroom_detail(chatroom)
        if chatroom_detail:
            return chatroom_detail.is_mute
        return None

    def get_is_online(self, chatroom):
        profiles = chatroom.profiles.all()
        online_profile = [
            profile for profile in profiles if profile.online > 0]
        return len(online_profile) > 0

    def get_last_active(self, chatroom):
        profiles = chatroom.profiles.all()
        if len(profiles) == 2:
            partner_profile = profiles[0] if profiles[0] != self.context['current_profile'] else profiles[1]
            return partner_profile.last_active

    def get_last_message(self, chatroom):
        last_chat = chatroom.chat_set.last()
        if last_chat:
            return last_chat.body
        else:
            return None

    def get_is_have_new_chat(self, chatroom):
        chatroom_detail = self.get_chatroom_detail(chatroom)
        if chatroom_detail:
            last_chat = chatroom.chat_set.last()
            return last_chat != chatroom_detail.last_seen
        else:
            return False

    class Meta:
        model = ChatRoom
        fields = '__all__'

    def create(self, validated_data):
        new_chatroom = ChatRoom.objects.create()
        for profile in self.context['profiles']:
            chatroom_profile = ChatRoomProfile.objects.create(
                chatroom=new_chatroom, profile=profile)
            if profile == self.context['current_profile']:
                chatroom_profile.is_admin = True
                chatroom_profile.save()
        return new_chatroom

    def update(self, chatroom, validated_data):
        chatroom_profile = ChatRoomProfile.objects.get(
            profile=self.context['current_profile'], chatroom=chatroom)
        if 'chatroom_name' in self.context:
            chatroom_profile.name = self.context['chatroom_name']
        if 'is_mute' in self.context:
            chatroom_profile.is_mute = self.context['is_mute']
        chatroom_profile.save()
        existing_profiles = chatroom.profiles.all()
        if 'added_profiles' in self.context:
            for profile in self.context['added_profiles']:
                if profile not in existing_profiles:
                    ChatRoomProfile.objects.create(
                        chatroom=chatroom, profile=profile)
        if 'removed_profiles' in self.context:
            for profile in self.context['removed_profiles']:
                ChatRoomProfile.objects.filter(
                    chatroom=chatroom, profile=profile).delete()
        return chatroom


class ChatSerializer(ModelSerializer):
    profile = ProfileChatSerializer(read_only=True)
    reaction_count = serializers.IntegerField(
        read_only=True, source='chatreaction_set.count')
    reaction_types = serializers.SerializerMethodField()
    seen_profiles = serializers.SerializerMethodField()

    def get_reaction_types(self, chat):
        types = set(
            [reaction.type for reaction in chat.chatreaction_set.all()])
        if len(types) > 0:
            return list(types)
        return None

    def get_seen_profiles(self, chat):
        chatroom = chat.chatroom
        # filter profile who have last seen chat in this chat room equals to this chat
        profiles = Profile.objects.filter(
            chatroomprofile__chatroom=chatroom, chatroomprofile__last_seen=chat)
        if len(profiles) > 0:
            serializer = ProfileChatSerializer(profiles, many=True)
            return serializer.data
        return None

    class Meta:
        model = Chat
        fields = '__all__'
