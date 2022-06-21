from .my_imports import *

class ProfileApiTestCase(MyTestCase):
    def test_profile_get(self):
        resp = self.client.get("/profiles/username/test_user1/")
        data = resp.json()
        assert data['username'] == 'test_user1'
        assert 'thumbnail' in data['avatar']
        assert 'thumbnail_larger' in data['avatar']
        assert data['num_posts'] == 1
        assert data['num_followings'] == 1
        assert data['num_followers'] == 0
        assert data['name'] == None
        assert data['bio'] == None

    def test_profile_update(self):
        user_data = {
            'username': 'new_test_user_1',
            'bio': 'new bio',
            'email': 'new_email@gmail.com'
        }
        self.client.put('/profiles/', user_data)
        self.profile_1.refresh_from_db()
        assert self.profile_1.user.username == 'new_test_user_1'
        assert self.profile_1.bio == 'new bio'
        assert self.profile_1.email == 'new_email@gmail.com'

    def test_profile_get_suggested(self):
        Follow.objects.create(follower=self.profile_2, following=self.profile_3)
        Follow.objects.create(follower=self.profile_2, following=self.profile_4)
        Follow.objects.create(follower=self.profile_2, following=self.profile_1)
        resp = self.client.get("/profiles/suggest/")
        data = resp.json()
        assert len(data) == 2
        assert set([data[0]['username'], data[1]['username']]) == set(['test_user3', 'test_user4'])
        assert len(data[0]) == 4
        assert 'username' in data[0]
        assert 'name' in data[0]
        assert 'avatar' in data[0]
        assert 'followed_by' in data[0]

    def test_profile_get_search(self):
        resp = self.client.get("/profiles/search/3/")
        data = resp.json()
        assert len(data) == 1
        assert data[0]['username'] == 'test_user3'
        assert len(data[0]) == 3
        assert 'username' in data[0]
        assert 'name' in data[0]
        assert 'avatar' in data[0]

        resp = self.client.get("/profiles/search/test/")
        data = resp.json()
        assert len(data) == 3 # except test_user1

    def test_profile_signup(self):
        user_data = {
            'name': 'datnguyen',
            'username': 'datnv',
            'password': 'my password',
            'email': 'datnguyen@gmail.com'
        }
        resp = self.client.post('/signup/', user_data)
        data = resp.json()
        user = User.objects.get(username='datnv')
        assert user.profile.name == 'datnguyen'
        assert user.profile.email == 'datnguyen@gmail.com'


    def test_profile_validate_signup(self):
        # invalid data
        user_data = {
            'name': 'datnguyen',
            'username': 'test_user2',
            'password': 'my password',
            'email': 'datnguyengmail.com'
        }
        resp = self.client.post('/signup/validate/', user_data)
        data = resp.json()
        assert resp.status_code == 400
        assert set(data) == set(['username', 'email'])

        # valid data
        user_data = {
            'name': 'datnguyen',
            'username': 'datnv',
            'password': 'my password',
            'email': 'datnguyen@gmail.com'
        }
        resp = self.client.post('/signup/validate/', user_data)
        assert resp.status_code == 200