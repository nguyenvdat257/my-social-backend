from .my_imports import *


class FollowApiTestCase(MyTestCase):
    def test_follow(self):
        # test follow
        follow_dict = {
            'username': 'test_user3'
        }
        resp = self.client.put('/follows/follow-unfollow/', follow_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'follow')
        followings = Profile.objects.filter(following__follower=self.profile_1).all()
        self.assertTrue(self.profile_3 in followings)

        # test unfollow
        resp = self.client.put('/follows/follow-unfollow/', follow_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'unfollow')
        followings = Profile.objects.filter(following__follower=self.profile_1).all()
        self.assertTrue(self.profile_3 not in followings)

    def test_follow_get_follower(self):
        Follow.objects.create(follower=self.profile_2, following=self.profile_3)
        Follow.objects.create(follower=self.profile_2, following=self.profile_4)
        Follow.objects.create(follower=self.profile_3, following=self.profile_4)
        # get follower of user 3
        resp = self.client.get('/follows/follower/user/test_user3/')
        data = resp.json()['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['username'], 'test_user2')

        # get follower of user 4
        resp = self.client.get('/follows/follower/user/test_user4/')
        data = resp.json()['results']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['username'], 'test_user2')
        self.assertEqual(data[1]['username'], 'test_user3')

    def test_follow_get_following(self):
        Follow.objects.create(follower=self.profile_2, following=self.profile_3)
        Follow.objects.create(follower=self.profile_2, following=self.profile_4)
        Follow.objects.create(follower=self.profile_3, following=self.profile_4)
        # get following of user 3
        resp = self.client.get('/follows/following/user/test_user3/')
        data = resp.json()['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['username'], 'test_user4')

        # get following of user 2
        resp = self.client.get('/follows/following/user/test_user2/')
        data = resp.json()['results']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['username'], 'test_user3')
        self.assertEqual(data[1]['username'], 'test_user4')