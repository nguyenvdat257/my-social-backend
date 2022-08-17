from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import *
import re

# used when sending notification


def get_mention_usernames(body):
    usernames = list(set(re.findall(r"@(\w+)", body)))
    return usernames


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        # instance holds the new comment (reply), but you also have to fetch
        # original comment and the user who created it
        mentioned_usernames = get_mention_usernames(instance.body)
        comment_profile = instance.profile
        for username in mentioned_usernames:
            mentioned_profile = Profile.objects.get(user__username=username)
            if comment_profile != mentioned_profile:
                Notification.objects.create(receiver_profile=mentioned_profile,
                                            sender_profile=comment_profile,
                                            comment=instance,
                                            post=instance.post,
                                            type="mention_comment")
        post_profile = instance.post.profile
        # if the comment is not reply comment then notify post author
        if post_profile != comment_profile and not instance.reply_to:
            if post_profile.user.username not in mentioned_usernames:
                Notification.objects.create(receiver_profile=post_profile,
                                            sender_profile=comment_profile,
                                            comment=instance,
                                            post=instance.post,
                                            type="comment_post")


@receiver(post_save, sender=PostLike)
def create_post_like_notification(sender, instance, created, **kwargs):
    if created:
        post_profile = instance.post.profile
        like_profile = instance.profile
        if post_profile != like_profile:
            Notification.objects.create(receiver_profile=post_profile,
                                        sender_profile=like_profile,
                                        post=instance.post,
                                        type="like_post")


@receiver(post_save, sender=CommentLike)
def create_comment_like_notification(sender, instance, created, **kwargs):
    if created:
        comment_profile = instance.comment.profile
        like_profile = instance.profile
        if comment_profile != like_profile:
            Notification.objects.create(receiver_profile=comment_profile,
                                        sender_profile=like_profile,
                                        comment=instance.comment,
                                        post=instance.comment.post,
                                        type="like_comment")


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        follower = instance.follower
        following = instance.following
        Notification.objects.create(receiver_profile=following,
                                    sender_profile=follower,
                                    type="following")
