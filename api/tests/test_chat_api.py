from .my_imports import *
from django.utils.dateparse import parse_datetime


class ChatTestCase(MyTestCase):
    def test_chat_create_chat_room(self):
        chat_dict = {
            'usernames': ['test_user1', 'test_user2', 'test_user3']
        }
        self.client.post('/chatroom/', chat_dict)
        chat_room = ChatRoom.objects.all()
        self.assertEqual(len(chat_room), 1)
        chat_room = chat_room[0]
        profiles = chat_room.profiles.all()
        self.assertEqual(len(profiles), 3)
        self.assertTrue(self.profile_1 in profiles)
        self.assertTrue(self.profile_2 in profiles)
        self.assertTrue(self.profile_3 in profiles)

    def test_chat_update_name_and_mute(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom_profile = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_1)
        chatroom_profile.is_admin = True
        chatroom_profile.save()

        # chat room name and mute
        chat_dict = {
            'chatroom_name': 'our chat room',
            'is_mute': True,
        }
        resp = self.client.put('/chatroom/%s/' % chatroom.id, chat_dict)
        data = resp.json()
        self.assertEqual(data['chatroom_name'], chat_dict['chatroom_name'])
        self.assertEqual(data['is_mute'], chat_dict['is_mute'])

    def test_chat_add_user(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom_profile = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_1)
        chatroom_profile.is_admin = True
        chatroom_profile.save()
        chat_dict = {
            'added_usernames': ['test_user3', 'test_user4'],
        }
        resp = self.client.put('/chatroom/%s/' % chatroom.id, chat_dict)
        data = resp.json()
        data_usernames = [profile['username'] for profile in data['profiles']]
        self.assertEqual(len(data_usernames), 4)
        self.assertTrue('test_user1' in data_usernames)
        self.assertTrue('test_user2' in data_usernames)
        self.assertTrue('test_user3' in data_usernames)
        self.assertTrue('test_user4' in data_usernames)
        self.assertTrue(chatroom in self.profile_1.chatroom_set.all())
        self.assertTrue(chatroom in self.profile_2.chatroom_set.all())
        self.assertTrue(chatroom in self.profile_3.chatroom_set.all())
        self.assertTrue(chatroom in self.profile_4.chatroom_set.all())

    def test_chat_remove_user(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom.profiles.add(self.profile_3)
        chatroom_profile = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_1)
        chatroom_profile.is_admin = True
        chatroom_profile.save()
        chat_dict = {
            'removed_usernames': ['test_user1', 'test_user2'],
        }
        resp = self.client.put('/chatroom/%s/' % chatroom.id, chat_dict)
        data = resp.json()
        data_usernames = [profile['username'] for profile in data['profiles']]
        self.assertEqual(len(data_usernames), 1)
        self.assertTrue('test_user3' in data_usernames)
        self.assertTrue(chatroom not in self.profile_1.chatroom_set.all())
        self.assertTrue(chatroom not in self.profile_2.chatroom_set.all())
        self.assertTrue(chatroom in self.profile_3.chatroom_set.all())

    def test_chat_remove_then_add_user(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom.profiles.add(self.profile_3)
        chatroom_profile = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_1)
        chatroom_profile.is_admin = True
        chatroom_profile.save()
        chat_dict = {
            'removed_usernames': ['test_user2'],
        }
        resp = self.client.put('/chatroom/%s/' % chatroom.id, chat_dict)
        chat_dict = {
            'added_usernames': ['test_user2'],
        }
        resp = self.client.put('/chatroom/%s/' % chatroom.id, chat_dict)
        data = resp.json()
        data_usernames = [profile['username'] for profile in data['profiles']]
        self.assertEqual(len(data_usernames), 3)
        self.assertTrue('test_user1' in data_usernames)
        self.assertTrue('test_user2' in data_usernames)
        self.assertTrue('test_user3' in data_usernames)
        self.assertTrue(chatroom in self.profile_1.chatroom_set.all())
        self.assertTrue(chatroom in self.profile_2.chatroom_set.all())
        self.assertTrue(chatroom in self.profile_3.chatroom_set.all())

    def test_chat_promote_admin(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom_profile1 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_1)
        chatroom_profile1.is_admin = True
        chatroom_profile1.save()
        # promote admin user 2
        chat_dict = {
            'username': 'test_user2'
        }
        resp = self.client.put(
            '/chatroom/%s/promote-demote-admin/' % chatroom.id, chat_dict)
        chatroom_profile2 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_2)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(chatroom_profile2.is_admin, True)

        # promote user not in chat
        chat_dict = {
            'username': 'test_user3'
        }
        resp = self.client.put(
            '/chatroom/%s/promote-demote-admin/' % chatroom.id, chat_dict)
        self.assertEqual(resp.status_code, 400)

    def test_chat_demote_admin(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom_profile1 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_1)
        chatroom_profile1.is_admin = True
        chatroom_profile1.save()
        chatroom_profile2 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_2)
        chatroom_profile2.is_admin = True
        chatroom_profile2.save()
        # demote admin user 2
        chat_dict = {
            'username': 'test_user2'
        }
        resp = self.client.put(
            '/chatroom/%s/promote-demote-admin/' % chatroom.id, chat_dict)
        self.assertEqual(resp.status_code, 200)
        chatroom_profile2 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_2)
        self.assertEqual(chatroom_profile2.is_admin, False)

        # demote user not in chat
        chat_dict = {
            'username': 'test_user3'
        }
        resp = self.client.put(
            '/chatroom/%s/promote-demote-admin/' % chatroom.id, chat_dict)
        self.assertEqual(resp.status_code, 400)

    def test_chat_get_chatrooms(self):
        # add chat rooms
        chatroom1 = ChatRoom.objects.create()
        chatroom1.profiles.add(self.profile_1)
        chatroom1.profiles.add(self.profile_2)
        chatroom2 = ChatRoom.objects.create()
        chatroom2.profiles.add(self.profile_1)
        chatroom2.profiles.add(self.profile_3)
        # add chat
        chat_1 = Chat.objects.create(
            profile=self.profile_1, chatroom=chatroom1, body='chat 1')
        chat_2 = Chat.objects.create(
            profile=self.profile_2, chatroom=chatroom1, body='chat 2')
        chat_3 = Chat.objects.create(
            profile=self.profile_3, chatroom=chatroom2, body='chat 3')
        chat_4 = Chat.objects.create(
            profile=self.profile_1, chatroom=chatroom2, body='chat 4')
        # make user 3 online
        self.profile_3.online = 1
        self.profile_3.save()
        # update user 2 last active
        self.profile_2.last_active = timezone.now()
        self.profile_2.save()
        # change name room 1
        chatroom_detail1 = ChatRoomProfile.objects.get(
            chatroom=chatroom1, profile=self.profile_1)
        chatroom_detail1.name = 'Chat room 1'
        # mute room 2
        chatroom_detail2 = ChatRoomProfile.objects.get(
            chatroom=chatroom2, profile=self.profile_1)
        chatroom_detail2.is_mute = True
        # add chat read
        chatroom_detail1.last_seen = chat_2
        chatroom_detail2.last_seen = chat_3
        chatroom_detail1.save()
        chatroom_detail2.save()

        resp = self.client.get('/chatroom/')
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['chatroom_name'], None)
        self.assertEqual(data[0]['is_mute'], True)
        self.assertEqual(data[0]['is_online'], True)
        self.assertEqual(data[0]['last_active'], self.profile_3.last_active)
        self.assertEqual(data[0]['last_message'], chat_4.body)
        self.assertEqual(data[0]['is_have_new_chat'], True)
        self.assertEqual(set(['test_user1', 'test_user3']), set(
            [profile['username'] for profile in data[0]['profiles']]))

        self.assertEqual(data[1]['chatroom_name'], 'Chat room 1')
        self.assertEqual(data[1]['is_mute'], False)
        self.assertEqual(data[1]['is_online'], False)
        self.assertEqual(parse_datetime(
            data[1]['last_active']), self.profile_2.last_active)
        self.assertEqual(data[1]['last_message'], chat_2.body)
        self.assertEqual(data[1]['is_have_new_chat'], False)
        self.assertEqual(set(['test_user1', 'test_user2']), set(
            [profile['username'] for profile in data[1]['profiles']]))

    def test_chat_get_chat_list(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom.profiles.add(self.profile_3)
        chat_1 = Chat.objects.create(
            profile=self.profile_1, chatroom=chatroom, body='chat 1')
        time.sleep(0.05)
        chat_2 = Chat.objects.create(
            profile=self.profile_2, chatroom=chatroom, body='chat 2', reply_to=chat_1)
        time.sleep(0.05)
        chat_3 = Chat.objects.create(
            profile=self.profile_2, chatroom=chatroom, body='chat 3')
        ChatReaction.objects.create(
            profile=self.profile_2, reply_to=chat_1, type='like')
        ChatReaction.objects.create(
            profile=self.profile_3, reply_to=chat_1, type='laugh')
        chatroom_detail1 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_1)
        chatroom_detail2 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_2)
        chatroom_detail3 = ChatRoomProfile.objects.get(
            chatroom=chatroom, profile=self.profile_3)
        chatroom_detail2.last_seen = chat_1
        chatroom_detail2.save()
        chatroom_detail3.last_seen = chat_1
        chatroom_detail3.save()
        chatroom_detail1.last_seen = chat_3
        chatroom_detail1.save()

        resp = self.client.get('/chatroom/%s/chat/' % chatroom.id)
        data = resp.json()['results']
        # user 1 seen chat 2
        self.assertEqual(data[0]['profile']['username'], 'test_user2')
        self.assertEqual(data[0]['body'], chat_3.body)
        self.assertEqual(data[0]['reaction_count'], 0)
        self.assertEqual(data[0]['reaction_types'], None)
        self.assertEqual(len(data[0]['seen_profiles']), 1)
        self.assertEqual(data[0]['seen_profiles'][0]['username'], 'test_user1')

        self.assertEqual(data[1]['profile']['username'], 'test_user2')
        self.assertEqual(data[1]['body'], chat_2.body)
        self.assertEqual(data[1]['reply_to'], chat_1.id)
        self.assertEqual(data[1]['reaction_count'], 0)
        self.assertEqual(data[1]['reaction_types'], None)
        self.assertEqual(data[1]['seen_profiles'], None)

        # user 2 and 3 seen chat 1, user 2 and 3 react to chat 1
        self.assertEqual(data[2]['profile']['username'], 'test_user1')
        self.assertEqual(data[2]['body'], chat_1.body)
        self.assertEqual(data[2]['reaction_count'], 2)
        self.assertEqual(set(data[2]['reaction_types']),
                         set(['like', 'laugh']))
        self.assertEqual(len(data[2]['seen_profiles']), 2)
        self.assertEqual(set([data[2]['seen_profiles'][0]['username'], data[2]
                         ['seen_profiles'][1]['username']]), set(['test_user2', 'test_user3']))

    def test_chat_get_reaction_list(self):
        chatroom = ChatRoom.objects.create()
        chatroom.profiles.add(self.profile_1)
        chatroom.profiles.add(self.profile_2)
        chatroom.profiles.add(self.profile_3)
        chat_1 = Chat.objects.create(
            profile=self.profile_1, chatroom=chatroom, body='chat 1')
        time.sleep(0.05)
        chat_2 = Chat.objects.create(
            profile=self.profile_2, chatroom=chatroom, body='chat 2', reply_to=chat_1)
        time.sleep(0.05)
        chat_3 = Chat.objects.create(
            profile=self.profile_2, chatroom=chatroom, body='chat 3')
        ChatReaction.objects.create(
            profile=self.profile_2, reply_to=chat_1, type='like')
        ChatReaction.objects.create(
            profile=self.profile_3, reply_to=chat_1, type='laugh')

        resp = self.client.get('/chat/%s/reaction/' % chat_1.id)
        data = resp.json()['results']
        # user 2 and 3 react to chat 1
        self.assertEqual(len(data), 2)
        self.assertEqual(set([data[0]['username'], data[1]['username']]), set(
            ['test_user2', 'test_user3']))
        self.assertEqual(len(data[0]), 3)
        self.assertTrue(
            'name' in data[0] and 'avatar' in data[0] and 'username' in data[0])
        self.assertEqual(len(data[1]), 3)
        self.assertTrue(
            'name' in data[1] and 'avatar' in data[1] and 'username' in data[1])

        resp = self.client.get('/chat/%s/reaction/' % chat_2.id)
        data = resp.json()['results']
        self.assertEqual(len(data), 0)