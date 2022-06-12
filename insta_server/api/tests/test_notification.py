from .my_imports import *


class NotificationApiTestCase(MyTestCase):
    def test_notification_create_comment(self):
        # test comment mention
        Notification.objects.all().delete()
        Comment.objects.create(profile=self.profile_1, post=self.post_2, body='@test_user3 @test_user4 mention')
        notifications = Notification.objects.order_by('receiver_profile__user__username').all()
        self.assertTrue(len(notifications), 3)
        self.assertEqual(notifications[0].sender_profile, self.profile_1)
        self.assertEqual(notifications[1].sender_profile, self.profile_1)
        self.assertEqual(notifications[2].sender_profile, self.profile_1)
        self.assertEqual(notifications[0].receiver_profile, self.profile_2)
        self.assertEqual(notifications[1].receiver_profile, self.profile_3)
        self.assertEqual(notifications[2].receiver_profile, self.profile_4)
        self.assertEqual(notifications[0].type, 'comment_post')
        self.assertEqual(notifications[1].type, 'mention_comment')
        self.assertEqual(notifications[2].type, 'mention_comment')

        # test comment no mention
        Notification.objects.all().delete()
        Comment.objects.create(profile=self.profile_1, post=self.post_2, body='comment post 2')
        notifications = Notification.objects.all()
        self.assertTrue(len(notifications), 1)
        self.assertEqual(notifications[0].sender_profile, self.profile_1)
        self.assertEqual(notifications[0].receiver_profile, self.profile_2)
        self.assertEqual(notifications[0].type, 'comment_post')

    def test_notification_post_like(self):
        Notification.objects.all().delete()
        PostLike.objects.create(profile=self.profile_1, post=self.post_2)
        notifications = Notification.objects.all()
        self.assertTrue(len(notifications), 1)
        self.assertEqual(notifications[0].sender_profile, self.profile_1)
        self.assertEqual(notifications[0].receiver_profile, self.profile_2)
        self.assertEqual(notifications[0].type, 'like_post')

    def test_notification_comment_like(self):
        comment = Comment.objects.create(profile=self.profile_2, post=self.post_3)
        Notification.objects.all().delete()
        CommentLike.objects.create(profile=self.profile_1, comment=comment)
        notifications = Notification.objects.all()
        self.assertTrue(len(notifications), 1)
        self.assertEqual(notifications[0].sender_profile, self.profile_1)
        self.assertEqual(notifications[0].receiver_profile, self.profile_2)
        self.assertEqual(notifications[0].type, 'like_comment')

    def test_notification_following(self):
        Notification.objects.all().delete()
        Follow.objects.create(follower=self.profile_1, following=self.profile_3)
        notifications = Notification.objects.all()
        self.assertTrue(len(notifications), 1)
        self.assertEqual(notifications[0].sender_profile, self.profile_1)
        self.assertEqual(notifications[0].receiver_profile, self.profile_3)
        self.assertEqual(notifications[0].type, 'following')

    def test_notification_get(self):
        Notification.objects.all().delete()
        Notification.objects.create(sender_profile=self.profile_2, receiver_profile=self.profile_1)
        Notification.objects.create(sender_profile=self.profile_3, receiver_profile=self.profile_1)
        resp = self.client.get('/notification/')
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertTrue(data[0]['sender_profile'] in [self.profile_3.id, self.profile_2.id])
        self.assertEqual(data[0]['receiver_profile'], self.profile_1.id)
        self.assertTrue(data[1]['sender_profile'] in [self.profile_3.id, self.profile_2.id])
        self.assertEqual(data[1]['receiver_profile'], self.profile_1.id)
        self.assertNotEqual(data[1]['sender_profile'], data[0]['sender_profile'])

    def test_notification_seen(self):
        Notification.objects.all().delete()
        Notification.objects.create(sender_profile=self.profile_2, receiver_profile=self.profile_1)
        Notification.objects.create(sender_profile=self.profile_3, receiver_profile=self.profile_1)
        resp = self.client.put('/notification/seen/')
        notification = Notification.objects.all()
        self.assertEqual(notification[0].user_seen, True)
        self.assertEqual(notification[1].user_seen, True)


