from .my_imports import *


class TokenApiTestCase(MyTestCase):
    def test_token_get_pair(self):
        # test valid account
        post_data = {
            'username': 'test_user1',
            'password': 'password'
        }
        resp = self.client.post('/token/', post_data)
        data = resp.json()
        self.assertGreater(len(data['refresh']), 10)
        self.assertGreater(len(data['access']), 10)

        # test invalid account
        post_data = {
            'username': 'test_user',
            'password': 'password'
        }
        resp = self.client.post('/token/', post_data)
        self.assertEqual(resp.status_code, 401)

    def test_token_refresh(self):
        post_data = {
            'username': 'test_user1',
            'password': 'password'
        }
        resp = self.client.post('/token/', post_data)
        data = resp.json()

        post_data = {
            'refresh': data['refresh']
        }
        resp = self.client.post('/token/refresh/', post_data)
        data = resp.json()
        self.assertGreater(len(data['refresh']), 10)
        self.assertGreater(len(data['access']), 10)

    def test_token_user_signup(self):
        post_data = {
            'username': 'test_user6',
            'password': 'password6',
            'email': 'test_email6@gmail.com',
            'name': 'user6'
        }
        resp = self.client.post('/signup/', post_data)
        self.assertEqual(resp.status_code, 200)
        profile = Profile.objects.get(user__username='test_user6')
        self.assertTrue(profile.user.check_password(post_data['password']))
        self.assertEqual(profile.email, post_data['email'])
        self.assertEqual(profile.name, post_data['name'])
