import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from ..models import ChatRoom, Chat, ChatReaction, ChatRoomProfile, Profile


class ChatConsumer(AsyncWebsocketConsumer):
    @sync_to_async
    def get_data(self, chatroom):
        return self.scope['user'].profile, [profile for profile in chatroom.profiles.all()]

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'chat_%s' % self.room_id

        # Join room group
        try:
            # allow connect only if user in chatroom
            self.chatroom = await sync_to_async(ChatRoom.objects.get)(pk=self.room_id)
            self.profile, chatroom_profiles = await self.get_data(self.chatroom)
            self.chatroom_detail = await sync_to_async(ChatRoomProfile.objects.get)(chatroom=self.chatroom, profile=self.profile)
            if self.profile in chatroom_profiles:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
            else:
                await self.close()
        except:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        username = text_data_json['username']
        type = text_data_json['type']

        sender_profile = await sync_to_async(Profile.objects.get)(user__username=username)
        send_obj = {'type': type, 'username': username}
        if type == 'message':
            message = text_data_json['message']
            reply_to = text_data_json.get('reply_to')
            await sync_to_async(Chat.objects.create)(
                profile=sender_profile, chatroom=self.chatroom, body=message, reply_to=reply_to)
            send_obj.update({'message': message, 'reply_to': reply_to})
        elif type == 'reaction':
            reply_to = text_data_json['reply_to']
            reaction_type = text_data_json['reaction_type']
            await sync_to_async(ChatReaction.objects.create)(profile=sender_profile, reply_to_id=reply_to, type=reaction_type)
            send_obj.update(
                {'reaction_type': reaction_type, 'reply_to': reply_to})
        elif type == 'seen':
            last_seen = text_data_json['last_seen']
            await self.update_last_seen(sender_profile, last_seen)
            send_obj.update({'last_seen': last_seen})
        elif type == 'typing':
            pass

            # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, send_obj
        )

    @sync_to_async
    def update_last_seen(self, profile, last_seen):
        ChatRoomProfile.objects.filter(
            profile=profile, chatroom=self.chatroom).update(last_seen=last_seen)

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
