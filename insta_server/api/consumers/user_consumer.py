import json
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.db.models import signals
from django.dispatch import receiver
import channels.layers
from django.utils import timezone

from ..models import Notification, Profile
from django.db.models import F


class UserConsumer(WebsocketConsumer):
    def connect(self):
        self.username = self.scope['user'].username
        self.group_name = 'user_%s' % self.username

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        user = self.scope['user']
        self.update_user_incr(user)
        profile = Profile.objects.get(pk=user.profile.pk)
        if profile.online == 1: # when there is first device online notify users
            chat_partners = set([profile for chat_room in profile.chatroom_set.prefetch_related(
                'profiles') for profile in chat_room.profiles.all()])

            for partner in chat_partners:
                if partner.user.username == self.username:
                    continue
                async_to_sync(self.channel_layer.group_send)(
                    'user_%s' % partner.user.username,
                    {
                        'type': 'status_online',
                        'username': self.username
                    }
            )
        self.accept()

    def disconnect(self, close_code):
        # Notify all chat partner offline status
        user = self.scope['user']
        self.update_user_decr(user)
        profile = Profile.objects.get(pk=user.profile.pk)
        if profile.online == 0: # when there is no device online notify other users
            chat_partners = set([profile for chat_room in profile.chatroom_set.prefetch_related(
                'profiles') for profile in chat_room.profiles.all()])
            for partner in chat_partners:
                if partner.user.username == self.username:
                    continue
                async_to_sync(self.channel_layer.group_send)(
                    'user_%s' % partner.user.username,
                    {
                        'type': 'status_offline',
                        'username': self.username
                    }
                )
            profile.last_active = timezone.now()
            profile.save()
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def status_online(self, event):
        self.send(text_data=json.dumps({
            'type': event['type'],
            'username': event['username']
        }))

    def status_offline(self, event):
        self.send(text_data=json.dumps({
            'type': event['type'],
            'username': event['username']
        }))

    def update_user_incr(self, user):
        return Profile.objects.filter(pk=user.profile.pk).update(online=F('online') + 1)

    def update_user_decr(self, user):
        return Profile.objects.filter(pk=user.profile.pk).update(online=F('online') - 1)

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
