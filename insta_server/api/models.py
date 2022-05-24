import imp
from re import search
from tkinter import CASCADE
from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    avatar = models.ImageField(upload_to='images', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('C', 'Custom'),
        ('N', 'None'),
    )
    gender = models.CharField(max_length=1, blank=True,
                              null=True, choices=GENDER_CHOICES)

    def __str__(self):
        return self.user.username


class HashTag(models.Model):
    body = models.CharField(max_length=200)

    def __str__(self):
        return self.body


class Post(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    body = models.TextField(blank=True, null=True)
    video = models.FileField(blank=True, null=True, upload_to='videos')
    code = models.CharField(max_length=11, default='')
    POST_TYPES = (
        ('Public', 'Public'),
        ('Private', 'Private')
    )
    type = models.CharField(max_length=10, choices=POST_TYPES)
    hash_tags = models.ManyToManyField(HashTag)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.body[:15]


class PostSeen(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.profile) + ' seen ' + str(self.post)


class PostImage(models.Model):
    image = models.ImageField(upload_to='images')
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return 'post: ' + str(self.post) + ' image: ' + str(self.image.url[-15:])


class PostLike(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.profile) + ' likes ' + str(self.post)


class SavedPost(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile) + ' saved ' + str(self.post)


class Comment(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    reply_to_comment = models.ForeignKey(
        'self', blank=True, null=True, on_delete=models.RESTRICT)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.body[:15])


class CommentLike(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.profile) + ' likes ' + str(self.comment)


class RecentSearch(models.Model):
    current_profile = models.ForeignKey(
        Profile, related_name='current_profile', on_delete=models.CASCADE)
    search_profile = models.ForeignKey(
        Profile, blank=True, null=True, related_name='search_profile', on_delete=models.CASCADE)
    search_hashtag = models.ForeignKey(
        HashTag, blank=True, null=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.search_profile:
            return str(self.current_profile) + ' search ' + str(self.search_profile)[:15]
        else:
            return str(self.current_profile) + ' search ' + str(self.search_hashtag)[:15]

# class HashTagPost(models.Model):
#     post = models.ForeignKey(Post, on_delete=CASCADE)
#     hashtag = models.ForeignKey(HashTag, on_delete=CASCADE)


class Notification(models.Model):
    receiver_profile = models.ForeignKey(
        Profile, related_name='receiver_profile', on_delete=models.CASCADE)
    sender_profile = models.ForeignKey(
        Profile, related_name='sender_profile', on_delete=models.CASCADE, blank=True, null=True)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    NOTI_TYPES = (
        ('like_comment', 'like_comment'),
        ('mention_comment', 'mention_commnent'),
        ('following', 'following'),
        ('like_post', 'like_post'),
        ('comment_post', 'comment_post')
    )
    type = models.CharField(max_length=20, choices=NOTI_TYPES)
    user_seen = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.body[:15]


class Follow(models.Model):
    follower_profile = models.ForeignKey(
        Profile, related_name='follow_followers', on_delete=models.CASCADE)
    followee_profile = models.ForeignKey(
        Profile, related_name='follow_followees', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('follower_profile', 'followee_profile',)

    def __str__(self):
        return str(self.follower_profile) + " follows " + str(self.followee_profile)


class Story(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    body = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to="videos", blank=True, null=True)
    music = models.FileField(upload_to="music", blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.body[:15])


class StoryImage(models.Model):
    image = models.ImageField(upload_to='images')
    story = models.ForeignKey(Story, on_delete=models.CASCADE)

    def __str__(self):
        return 'Image of: ' + str(self.story)


class ChatRoom(models.Model):
    profiles = models.ManyToManyField(Profile, through='ChatRoomProfile')
    name = models.CharField(max_length=200, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ChatRoomProfile(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=True, null=True)
    mute = models.BooleanField(default=False)

    def __str__(self):
        return str(self.profile) + ' joins ' + str(self.chat_room)


class Chat(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    reply_to_chat = models.ForeignKey(
        'self', blank=True, null=True, on_delete=models.RESTRICT)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.body[:15]


class ChatSeen(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.profile) + ' seen ' + str(self.chat)


class ChatReaction(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    type = models.CharField(max_length=100)

    def __str__(self):
        return str(self.profile) + ' ' + self.type + ' ' + str(self.chat)
