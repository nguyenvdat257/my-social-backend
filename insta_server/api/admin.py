import imp
from django.contrib import admin

# Register your models here.
from .models import *


class PostImageInline(admin.StackedInline):
    model = PostImage
    extra = 2


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 2


class StoryImageInline(admin.StackedInline):
    model = StoryImage
    extra = 2


class PostAdmin(admin.ModelAdmin):
    inlines = [PostImageInline, CommentInline]


class StoryAdmin(admin.ModelAdmin):
    inlines = [StoryImageInline]


admin.site.register(Profile)
admin.site.register(Post, PostAdmin)
admin.site.register(HashTag)
admin.site.register(PostSeen)
admin.site.register(PostImage)
admin.site.register(PostLike)
admin.site.register(SavedPost)
admin.site.register(Comment)
admin.site.register(CommentLike)
admin.site.register(RecentSearch)
admin.site.register(Notification)
admin.site.register(Story, StoryAdmin)
admin.site.register(StoryImage)
admin.site.register(ChatRoom)
admin.site.register(ChatRoomProfile)
admin.site.register(Chat)
admin.site.register(ChatSeen)
admin.site.register(ChatReaction)
