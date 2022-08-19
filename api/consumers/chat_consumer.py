import json
import profile
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync, sync_to_async
from django.db.models import signals
from django.dispatch import receiver
import channels.layers

from ..serializers import ChatSerializer
from ..models import ChatRoom, Chat, ChatReaction, ChatRoomProfile, Profile


class ChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_data(self, chatroom):
        ids = self.scope['user'].profile, [
            profile for profile in chatroom.profiles.all()]
        return ids

    @database_sync_to_async
    def get_chatroom_ids(self, profile):
        ids = [chatroom.id for chatroom in profile.chatroom_set.all()]
        return ids

    @database_sync_to_async
    def get_profile(self, user):
        return user.profile

    @database_sync_to_async
    def serialize_chat(self, chat):
        return ChatSerializer(chat).data

    async def connect(self):
        self.username = self.scope['user'].username
        self.group_name = 'user_chat%s' % self.username

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        # self.profile = await sync_to_async(lambda: self.scope['user'].profile)()
        self.profile = await self.get_profile(self.scope['user'])
        try:
            chatroom_ids = await self.get_chatroom_ids(self.profile)
            for id in chatroom_ids:
                room_group_name = 'chatroom_%s' % id
                await self.channel_layer.group_add(
                    room_group_name,
                    self.channel_name
                )
            await self.accept()
        except:
            await self.close()

    async def disconnect(self, close_code):
        chatroom_ids = await self.get_chatroom_ids(self.profile)
        for id in chatroom_ids:
            room_group_name = 'chatroom_%s' % id
            await self.channel_layer.group_discard(
                room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        chatroom_id = text_data_json['chatroom_id']
        username = text_data_json['username']
        type = text_data_json['type']

        sender_profile = await database_sync_to_async(Profile.objects.get)(user__username=username)

        send_obj = {'type': type}
        if type == 'message':
            message = text_data_json['message']
            reply_to = text_data_json.get('reply_to')
            chat = await database_sync_to_async(Chat.objects.create)(
                profile=sender_profile, chatroom_id=chatroom_id, body=message, reply_to=reply_to)
            chat_data = await self.serialize_chat(chat)
            send_obj.update({'chat': chat_data})
        elif type == 'reaction':
            reply_to = text_data_json['reply_to']
            reaction_type = text_data_json['reaction_type']
            await database_sync_to_async(ChatReaction.objects.create)(profile=sender_profile, reply_to_id=reply_to, type=reaction_type)
            send_obj.update(
                {'reaction_type': reaction_type, 'reply_to': reply_to})
        elif type == 'seen':
            last_seen_id = text_data_json['last_seen_id']
            await self.update_last_seen(sender_profile, chatroom_id, last_seen_id)
            send_obj.update({'chatroom_id': chatroom_id,
                            'username': username, 'last_seen_id': last_seen_id})
        elif type == 'typing' or type == 'untyping':
            send_obj = {'type': type,
                        'chatroom_id': chatroom_id, 'username': username}
        elif type == 'chatroom_added':
            room_group_name = 'chatroom_%s' % chatroom_id
            await self.channel_layer.group_add(
                room_group_name,
                self.channel_name
            )
            return

            # Send message to room group
        room_group_name = 'chatroom_%s' % chatroom_id
        await self.channel_layer.group_send(
            room_group_name, send_obj
        )

    @database_sync_to_async
    def update_last_seen(self, profile, chatroom_id, last_seen_id):
        ChatRoomProfile.objects.filter(
            profile=profile, chatroom_id=chatroom_id).update(last_seen_id=last_seen_id)

    @staticmethod
    @receiver(signals.post_save, sender=ChatRoomProfile)
    def added2chatroom_observer(sender, instance, created, **kwargs):
        if created:
            username = instance.profile.user.username
            layer = channels.layers.get_channel_layer()
            async_to_sync(layer.group_send)('user_chat%s' % username, {
                'type': 'chatroom_added',
                'username': username,
                'chatroom_id': instance.chatroom.id
            })

    async def chatroom_added(self, event):
        type = event['type']
        await self.send(text_data=json.dumps({
            'type': type,
            'username': event['username'],
            'chatroom_id': event['chatroom_id']
        }))

    async def message(self, event):
        await self.send(text_data=json.dumps(
            event
        ))

    async def reaction(self, event):
        await self.send(text_data=json.dumps(
            event
        ))

    async def seen(self, event):
        await self.send(text_data=json.dumps(
            event
        ))

    async def typing(self, event):
        await self.send(text_data=json.dumps(
            event
        ))

    async def untyping(self, event):
        await self.send(text_data=json.dumps(
            event
        ))
