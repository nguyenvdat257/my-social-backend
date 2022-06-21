from .my_imports import *
from channels.testing import WebsocketCommunicator
from ..consumers import *
from asgiref.sync import sync_to_async
import pytest


class TestOtherSocket(MyTestCase):
    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_user_online(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator1_2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1_2.scope["user"] = self.profile_1.user
        communicator2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator2.scope["user"] = self.profile_2.user
        chatroom = await sync_to_async(ChatRoom.objects.create)()
        await sync_to_async(chatroom.profiles.add)(self.profile_1)
        await sync_to_async(chatroom.profiles.add)(self.profile_2)
        connected, subprotocol = await communicator1.connect()
        assert connected
        connected, subprotocol = await communicator2.connect()
        assert connected

        # when user 2 connect there is response in user 1
        response = await communicator1.receive_json_from()
        assert response['type'] == 'status_online'
        assert response['username'] == 'test_user2'

        # connect one more device user 1, no response in user 2
        connected, subprotocol = await communicator1_2.connect()
        assert connected
        assert await communicator2.receive_nothing() is True

        # disconnect both 2 device of user 1, there is response in user 2
        await communicator1.disconnect()
        assert await communicator2.receive_nothing() is True
        await communicator1_2.disconnect()
        response = await communicator2.receive_json_from()
        assert response['type'] == 'status_offline'
        assert response['username'] == 'test_user1'

        await communicator2.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_notification_create_comment_mention(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator2.scope["user"] = self.profile_2.user
        communicator3 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator3.scope["user"] = self.profile_3.user
        communicator4 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator4.scope["user"] = self.profile_4.user

        connected, _ = await communicator1.connect()
        assert connected
        connected, _ = await communicator2.connect()
        assert connected
        connected, _ = await communicator3.connect()
        assert connected
        connected, _ = await communicator4.connect()
        assert connected

        print('create data')
        await sync_to_async(Notification.objects.all().delete)()
        await sync_to_async(Comment.objects.create)(profile=self.profile_1, post=self.post_2, body='@test_user3 @test_user4 mention')

        # assert await communicator1.receive_nothing() is True
        # response = await communicator2.receive_json_from()
        # assert response['type'] == 'noti_alarm'
        response = await communicator3.receive_json_from()
        assert response['type'] == 'noti_alarm'
        response = await communicator4.receive_json_from()
        assert response['type'] == 'noti_alarm'

        await communicator1.disconnect()
        await communicator2.disconnect()
        await communicator3.disconnect()
        await communicator4.disconnect()


    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_noti_create_comment_no_mention(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator2.scope["user"] = self.profile_2.user

        connected, _ = await communicator1.connect()
        assert connected
        connected, _ = await communicator2.connect()
        assert connected

        print('create data')
        await sync_to_async(Notification.objects.all().delete)()
        await sync_to_async(Comment.objects.create)(profile=self.profile_1, post=self.post_2, body='comment post 2')

        assert await communicator1.receive_nothing() is True
        response = await communicator2.receive_json_from()
        assert response['type'] == 'noti_alarm'

        await communicator1.disconnect()
        await communicator2.disconnect()


    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_noti_post_like(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator2.scope["user"] = self.profile_2.user

        connected, _ = await communicator1.connect()
        assert connected
        connected, _ = await communicator2.connect()
        assert connected

        print('create data')
        await sync_to_async(Notification.objects.all().delete)()
        await sync_to_async(PostLike.objects.create)(profile=self.profile_1, post=self.post_2)

        assert await communicator1.receive_nothing() is True
        response = await communicator2.receive_json_from()
        assert response['type'] == 'noti_alarm'

        await communicator1.disconnect()
        await communicator2.disconnect()


    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_noti_comment_like(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator2.scope["user"] = self.profile_2.user

        connected, _ = await communicator1.connect()
        assert connected
        connected, _ = await communicator2.connect()
        assert connected

        print('create data')
        comment = await sync_to_async(Comment.objects.create)(profile=self.profile_2, post=self.post_3)
        await sync_to_async(Notification.objects.all().delete)()
        await sync_to_async(CommentLike.objects.create)(profile=self.profile_1, comment=comment)
    
        assert await communicator1.receive_nothing() is True
        response = await communicator2.receive_json_from()
        assert response['type'] == 'noti_alarm'

        await communicator1.disconnect()
        await communicator2.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_noti_following(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator3 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator3.scope["user"] = self.profile_3.user

        connected, _ = await communicator1.connect()
        assert connected
        connected, _ = await communicator3.connect()
        assert connected

        print('create data')
        await sync_to_async(Notification.objects.all().delete)()
        await sync_to_async(Follow.objects.create)(follower=self.profile_1, following=self.profile_3)

        assert await communicator1.receive_nothing() is True
        response = await communicator3.receive_json_from()
        assert response['type'] == 'noti_alarm'

        await communicator1.disconnect()
        await communicator3.disconnect()

    
    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_noti_new_post(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator2.scope["user"] = self.profile_2.user

        connected, _ = await communicator1.connect()
        assert connected
        connected, _ = await communicator2.connect()
        assert connected
        print('create data')
        await sync_to_async(Post.objects.create)(
                profile=self.profile_2,
                body="Post 2#hanoi #beach body",
                video=self.video_1,
                code='code2_new',
                likes_count=5,
            )
        assert await communicator2.receive_nothing() is True
        response = await communicator1.receive_json_from()
        assert response['type'] == 'new_post'

        await communicator1.disconnect()
        await communicator2.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_socket_noti_added_to_chatroom(self):
        communicator1 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator1.scope["user"] = self.profile_1.user
        communicator2 = WebsocketCommunicator(
            UserConsumer.as_asgi(), "/ws/user/")
        communicator2.scope["user"] = self.profile_2.user

        connected, _ = await communicator1.connect()
        assert connected
        connected, _ = await communicator2.connect()
        assert connected
        print('create data')
        chatroom = await sync_to_async(ChatRoom.objects.create)()
        await sync_to_async(ChatRoomProfile.objects.create)(chatroom=chatroom, profile=self.profile_1)

        assert await communicator2.receive_nothing() is True
        response = await communicator1.receive_json_from()
        assert response['type'] == 'added2chatroom'

        await communicator1.disconnect()
        await communicator2.disconnect()