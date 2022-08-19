import json
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync, sync_to_async
from django.db.models import signals
from django.dispatch import receiver
import channels.layers
from django.utils import timezone

from ..models import ChatRoomProfile, Notification, Profile, Post
from django.db.models import F


class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['user'].username
        self.group_name = 'user_%s' % self.username

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        user = self.scope['user']
        # profile = user.profile
        # prev_online_count = profile.online
        # profile.online = profile.online + 1
        # profile.save()
        # assert prev_online_count + 1 == profile.online
        await self.update_user_incr(user)
        profile = await database_sync_to_async(Profile.objects.get)(pk=user.profile.pk)

        if profile.online == 1:  # when there is first device online notify users
            chat_partners = await self.get_chat_partners(profile)
            for partner in chat_partners:
                partner_name = await self.get_username(partner)
                if partner_name == self.username:
                    continue
                await self.channel_layer.group_send(
                    'user_%s' % partner_name,
                    {
                        'type': 'status_online',
                        'username': self.username
                    }
                )
        await self.accept()

    async def disconnect(self, close_code):
        # Notify all chat partner offline status
        user = self.scope['user']
        await self.update_user_decr(user)
        profile = await database_sync_to_async(Profile.objects.get)(pk=user.profile.pk)
        if profile.online == 0:  # when there is no device online notify other users
            chat_partners = await self.get_chat_partners(profile)
            for partner in chat_partners:
                partner_name = await self.get_username(partner)
                if partner_name == self.username:
                    continue
                await self.channel_layer.group_send(
                    'user_%s' % partner_name,
                    {
                        'type': 'status_offline',
                        'username': self.username
                    }
                )
            profile.last_active = timezone.now()
            profile.save()
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    @database_sync_to_async
    def update_user_incr(self, user):
        return Profile.objects.filter(pk=user.profile.pk).update(online=F('online') + 1)

    @database_sync_to_async
    def update_user_decr(self, user):
        return Profile.objects.filter(pk=user.profile.pk).update(online=F('online') - 1)

    @database_sync_to_async
    def get_chat_partners(self, profile):
        chat_partners = set([profile for chat_room in profile.chatroom_set.prefetch_related(
            'profiles') for profile in chat_room.profiles.all()])
        return chat_partners

    @database_sync_to_async
    def get_username(self, profile):
        return profile.user.username

    async def status_online(self, event):
        await self.send(text_data=json.dumps({
            'type': event['type'],
            'username': event['username']
        }))

    async def status_offline(self, event):
        await self.send(text_data=json.dumps({
            'type': event['type'],
            'username': event['username']
        }))


    @staticmethod
    @receiver(signals.post_save, sender=Notification)
    def noti_created_observer(sender, instance, **kwargs):
        layer = channels.layers.get_channel_layer()
        async_to_sync(layer.group_send)('user_%s' % instance.receiver_profile.user.username, {
            'type': 'noti_alarm',
        })

    def noti_alarm(self, event):
        type = event['type']

        self.send(text_data=json.dumps({
            'type': type
        }))

    @staticmethod
    @receiver(signals.post_save, sender=Notification)
    def noti_created_observer(sender, instance, **kwargs):
        layer = channels.layers.get_channel_layer()
        async_to_sync(layer.group_send)('user_%s' % instance.receiver_profile.user.username, {
            'type': 'noti_alarm',
        })

    async def noti_alarm(self, event):
        type = event['type']

        await self.send(text_data=json.dumps({
            'type': type
        }))

    @staticmethod
    @receiver(signals.post_save, sender=Post)
    def post_created_observer(sender, instance, created, **kwargs):
        if created:
            followers = Profile.objects.filter(
                follower__following=instance.profile)
            layer = channels.layers.get_channel_layer()
            for follower in followers:
                async_to_sync(layer.group_send)('user_%s' % follower.user.username, {
                    'type': 'new_post',
                })

    def new_post(self, event):
        type = event['type']

        self.send(text_data=json.dumps({
            'type': type
        }))

