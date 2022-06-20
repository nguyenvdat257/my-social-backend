from .my_imports import *
from channels.testing import WebsocketCommunicator
from ..consumers import *
from asgiref.sync import sync_to_async
import pytest


class TestChatSocket(MyTestCase):
    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_add_message(self):
        print('create data')
        chatroom = await sync_to_async(ChatRoom.objects.create)()
        await sync_to_async(chatroom.profiles.add)(self.profile_1)
        await sync_to_async(chatroom.profiles.add)(self.profile_2)
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/chat/%s/" % chatroom.id)
        communicator1.scope.update({"user": self.profile_1.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/user/%s/" % chatroom.id)
        communicator2.scope.update({"user": self.profile_2.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        communicator3 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/user/%s/" % chatroom.id)
        communicator3.scope.update({"user": self.profile_3.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id + 100}}})
        communicator4 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/user/%s/" % chatroom.id)
        communicator4.scope.update({"user": self.profile_4.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        connected, subprotocol = await communicator1.connect()
        assert connected
        connected, subprotocol = await communicator2.connect()
        assert connected
        connected, subprotocol = await communicator3.connect()
        # user 3 connect different room
        assert connected is False
        connected, subprotocol = await communicator4.connect()
        # user 4 connect same room but not member of room
        assert connected is False

        await communicator2.send_json_to({'type': 'message', 'message': 'chat from user 2', 'username': 'test_user2'})
        response = await communicator1.receive_json_from()
        assert response['message'] == 'chat from user 2'
        assert response['username'] == 'test_user2'
        response = await communicator2.receive_json_from()
        assert response['message'] == 'chat from user 2'
        assert response['username'] == 'test_user2'

        chats = await sync_to_async(Chat.objects.all)()
        chats = await sync_to_async(list)(chats)
        assert len(chats)
        assert chats[0].profile_id == self.profile_2.id
        assert chats[0].reply_to_id == None
        assert chats[0].body == 'chat from user 2'

        await communicator1.disconnect()
        await communicator2.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_chat_reaction(self):
        print('create data')
        chatroom = await sync_to_async(ChatRoom.objects.create)()
        await sync_to_async(chatroom.profiles.add)(self.profile_1)
        await sync_to_async(chatroom.profiles.add)(self.profile_2)
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/chat/%s/" % chatroom.id)
        communicator1.scope.update({"user": self.profile_1.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/user/%s/" % chatroom.id)
        communicator2.scope.update({"user": self.profile_2.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        
        connected, subprotocol = await communicator1.connect()
        assert connected
        connected, subprotocol = await communicator2.connect()
        assert connected
        chat_1 = await sync_to_async(Chat.objects.create)(
            profile=self.profile_1, chatroom=chatroom, body='chat 1')
        # user 2 like chat 1
        await communicator2.send_json_to(
            {'type': 'reaction', 
            'reaction_type': 'like', 
            'username': 'test_user2',
            'reply_to': chat_1.id})
        response = await communicator1.receive_json_from()
        assert response['reaction_type'] == 'like'
        assert response['username'] == 'test_user2'
        response = await communicator2.receive_json_from()
        assert response['reaction_type'] == 'like'
        assert response['username'] == 'test_user2'

        chat_reactions = await sync_to_async(ChatReaction.objects.all)()
        chat_reactions = await sync_to_async(list)(chat_reactions)
        assert len(chat_reactions) == 1
        assert chat_reactions[0].type == 'like'
        assert chat_reactions[0].profile_id == self.profile_2.id
        assert chat_reactions[0].reply_to_id == chat_1.id

        await communicator1.disconnect()
        await communicator2.disconnect()
        
    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_chat_seen(self):
        print('create data')
        chatroom = await sync_to_async(ChatRoom.objects.create)()
        await sync_to_async(chatroom.profiles.add)(self.profile_1)
        await sync_to_async(chatroom.profiles.add)(self.profile_2)
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/chat/%s/" % chatroom.id)
        communicator1.scope.update({"user": self.profile_1.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/user/%s/" % chatroom.id)
        communicator2.scope.update({"user": self.profile_2.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        
        connected, subprotocol = await communicator1.connect()
        assert connected
        connected, subprotocol = await communicator2.connect()
        assert connected
        chat_1 = await sync_to_async(Chat.objects.create)(
            profile=self.profile_1, chatroom=chatroom, body='chat 1')
        # user 2 seen chat 1
        await communicator2.send_json_to(
            {'type': 'seen', 
            'last_seen': chat_1.id,
            'username': 'test_user2'
            })
        response = await communicator1.receive_json_from()
        assert response['last_seen'] == chat_1.id
        assert response['username'] == 'test_user2'
        response = await communicator2.receive_json_from()
        assert response['last_seen'] == chat_1.id
        assert response['username'] == 'test_user2'

        chat_details = await sync_to_async(ChatRoomProfile.objects.filter)(profile=self.profile_2, chatroom=chatroom)
        chat_details = await sync_to_async(list)(chat_details)
        assert len(chat_details) == 1
        assert chat_details[0].last_seen_id == chat_1.id

        await communicator1.disconnect()
        await communicator2.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_chat_typing(self):
        print('create data')
        chatroom = await sync_to_async(ChatRoom.objects.create)()
        await sync_to_async(chatroom.profiles.add)(self.profile_1)
        await sync_to_async(chatroom.profiles.add)(self.profile_2)
        communicator1 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/chat/%s/" % chatroom.id)
        communicator1.scope.update({"user": self.profile_1.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        communicator2 = WebsocketCommunicator(
            ChatConsumer.as_asgi(), "/ws/user/%s/" % chatroom.id)
        communicator2.scope.update({"user": self.profile_2.user, 'url_route': {
                                   'kwargs': {'room_id': chatroom.id}}})
        
        connected, subprotocol = await communicator1.connect()
        assert connected
        connected, subprotocol = await communicator2.connect()
        assert connected
        chat_1 = await sync_to_async(Chat.objects.create)(
            profile=self.profile_1, chatroom=chatroom, body='chat 1')
        # user 2 seen chat 1
        await communicator2.send_json_to(
            {'type': 'typing', 
            'username': 'test_user2'
            })
        response = await communicator1.receive_json_from()
        assert response['type'] == 'typing'
        assert response['username'] == 'test_user2'
        response = await communicator2.receive_json_from()
        assert response['type'] == 'typing'
        assert response['username'] == 'test_user2'


        await communicator1.disconnect()
        await communicator2.disconnect()