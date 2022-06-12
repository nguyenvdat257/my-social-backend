import os
from django import setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insta_server.settings")
setup()
from ..models import *
import glob
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from django.test import TestCase
from django.contrib.auth import get_user_model


class MyTestCase(TestCase):
    def setUp(self):
        self.video_path1 = os.path.join(os.path.join(
            settings.TEST_ROOT, 'sample'), 'video_1.mp4')
        self.music_path1 = os.path.join(os.path.join(
            settings.TEST_ROOT, 'sample'), 'music_1.mp3')
        self.image_path1 = os.path.join(os.path.join(
            settings.TEST_ROOT, 'sample'), 'img_1.JPG')
        self.image_path2 = os.path.join(os.path.join(
            settings.TEST_ROOT, 'sample'), 'img_2.PNG')
        self.image_1 = SimpleUploadedFile(name='test_img1.jpg', content=open(self.image_path1, 'rb').read(), content_type='image')
        self.image_2 = SimpleUploadedFile(name='test_img2.jpg', content=open(self.image_path2, 'rb').read(), content_type='image')
        self.video_1 = SimpleUploadedFile(name='test_video1.mp4', content=open(self.video_path1, 'rb').read(), content_type='video')
        self.u1 = get_user_model().objects.create_user(
            username="test_user1", password="password"
        )
        self.profile_1 = Profile.objects.create(user=self.u1, avatar=self.image_1)
        self.u2 = get_user_model().objects.create_user(
            username="test_user2", password="password2"
        )
        self.profile_2 = Profile.objects.create(user=self.u2, avatar=self.image_2)
        self.u3 = get_user_model().objects.create_user(
            username="test_user3", password="password3"
        )
        self.profile_3 = Profile.objects.create(user=self.u3)
        self.u4 = get_user_model().objects.create_user(
            username="test_user4", password="password4"
        )
        self.profile_4 = Profile.objects.create(user=self.u4, type='PR')
        self.post_1 = Post.objects.create(
                profile=self.profile_1,
                body="Post 1#hanoi #seagame body",
                video=self.video_1,
                code='code1',
                likes_count=1,
            )
        self.post_2 = Post.objects.create(
                profile=self.profile_2,
                body="Post 2#hanoi #beach body",
                video=self.video_1,
                code='code2',
                likes_count=5,
            )
        self.post_3 = Post.objects.create(
                profile=self.profile_3,
                body="Post 3#hanoi #mountain body",
                video=self.video_1,
                code='code3',
                likes_count=2,
            )
        self.post_4 = Post.objects.create(
                profile=self.profile_3,
                body="Post 3#hanoi #animal body",
                video=self.video_1,
                code='code4',
                likes_count=9,
            )
        self.post_5 = Post.objects.create(
                profile=self.profile_4,
                body="Post 4 #hanoi #animal body",
                video=self.video_1,
                code='code5',
                likes_count=20,
            )
        hanoi_tag = HashTag.objects.create(body='hanoi')
        seagame_tag = HashTag.objects.create(body='seagame')
        mountain_tag = HashTag.objects.create(body='mountain')
        animal_tag = HashTag.objects.create(body='animal')
        beach_tag = HashTag.objects.create(body='beach')
        self.post_1.hash_tags.add(hanoi_tag)
        self.post_1.hash_tags.add(seagame_tag)
        self.post_2.hash_tags.add(hanoi_tag)
        self.post_2.hash_tags.add(beach_tag)
        self.post_3.hash_tags.add(hanoi_tag)
        self.post_3.hash_tags.add(mountain_tag)
        self.post_4.hash_tags.add(hanoi_tag)
        self.post_4.hash_tags.add(animal_tag)
        self.post_5.hash_tags.add(hanoi_tag)
        self.post_5.hash_tags.add(animal_tag)
        Follow.objects.create(follower=self.profile_1,
                                following=self.profile_2)
        # override test client
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.u1)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        
    def tearDown(self):
        image_files = glob.glob(os.path.join(os.path.join(
            settings.MEDIA_ROOT, 'images'), 'test*'), recursive=True)
        video_files = glob.glob(os.path.join(os.path.join(
            settings.MEDIA_ROOT, 'videos'), 'test*'), recursive=True)
        for file_path in image_files + video_files:
            try:
                os.remove(file_path)
            except OSError:
                print("Error while deleting file")
