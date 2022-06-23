from .my_imports import *

class PostApiTestCase(MyTestCase):
    def test_post_get_user(self):
        resp = self.client.get("/posts/user/test_user1/")
        data = resp.json()
        result = data['results']
        self.assertEqual(len(result), 1)

    def test_post_get_code(self):
        resp = self.client.get("/posts/code/code1/")
        post = resp.json()
        true_post = self.post_1
        self.assertEqual(post['body'], true_post.body)
        self.assertEqual(post['video'], true_post.video.url)

    def test_post_unauthenticated_create(self):
        # unset credentials so we are an anonymous user
        self.client.credentials()
        post_dict = {
            'body': 'new post #seagame #hanoi bright',
            'video': SimpleUploadedFile(name='test_video.jpg', content=open(self.video_path1, 'rb').read(), content_type='video'),
            'images': [self.image_1,
                       SimpleUploadedFile(name='test_img2.jpg', content=open(self.image_path2, 'rb').read(), content_type='image')]
        }
        resp = self.client.post("/posts/", post_dict)
        self.assertEqual(resp.status_code, 401)

    # def test_post_create(self):
    #     post_dict = {
    #         'body': 'new post #seagame #hanoi bright',
    #         # 'video': self.video_mages1,
    #         # 'images': [self.image_1, self.image_2]
    #         'video': SimpleUploadedFile(name='test_video1.mp4', content=open(self.video_path1, 'rb').read(), content_type='video'),
    #         'images': [SimpleUploadedFile(name='test_img1.jpg', content=open(self.image_path1, 'rb').read(), content_type='image'),
    #                    SimpleUploadedFile(name='test_img2.jpg', content=open(self.image_path2, 'rb').read(), content_type='image')]
    #     }
    #     resp = self.client.post("/posts/", post_dict)
    #     post_id = resp.json()["id"]
    #     post = Post.objects.get(pk=post_id)
    #     hash_tags = [hash_tag.body for hash_tag in post.hash_tags.all()]
    #     self.assertEqual(post.body, post_dict["body"])
    #     self.assertTrue('video1' in post.video.url)
    #     self.assertTrue('video_thumbnail' in post.video_thumbnail.url)
    #     self.assertEqual(len(post.postimage_set.all()), 2)
    #     self.assertTrue('seagame' in hash_tags)
    #     self.assertTrue('hanoi' in hash_tags)

    def test_post_update(self):
        post_dict = {
            'body': 'new post #asiangame #danang bright',
        }
        resp = self.client.put("/posts/code/code1/", post_dict)
        post_id = resp.json()["id"]
        post = Post.objects.get(pk=post_id)
        hash_tags = [hash_tag.body for hash_tag in post.hash_tags.all()]
        self.assertEqual(post.body, post_dict["body"])
        self.assertTrue('asiangame' in hash_tags)
        self.assertTrue('danang' in hash_tags)

    def test_post_get_current_user(self):
        resp = self.client.get('/posts/current-user/')
        data = resp.json()
        result = data['results']
        self.assertEqual(len(result), 2)
        self.assertTrue((self.profile_1.last_view_page_time - timezone.now()).total_seconds() < 0.5)

    def test_post_get_new_current_user(self):
        self.profile_1.last_view_page_time = timezone.now()
        self.profile_1.save()
        resp = self.client.get('/posts/current-user/new/')
        data = resp.json()
        self.assertEqual(len(data), 0)

        # reset created to make a new post
        self.post_2.created = timezone.now()
        self.post_2.save()
        # get post 2
        resp = self.client.get('/posts/current-user/new/')
        data = resp.json()
        self.assertEqual(len(data), 1)

    def test_post_get_by_tag_popular(self):
        resp = self.client.get('/posts/tag-popular/hanoi/')
        data = resp.json()
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['likes_count'], 9)
        self.assertEqual(data[1]['likes_count'], 5)
        self.assertEqual(data[2]['likes_count'], 2)
        self.assertEqual(data[3]['likes_count'], 1)

    def test_post_get_by_tag_recent(self):
        resp = self.client.get('/posts/tag-recent/hanoi/')
        data = resp.json()
        data = data['results']
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['code'], 'code4')
        self.assertEqual(data[1]['code'], 'code3')
        self.assertEqual(data[2]['code'], 'code2')
        self.assertEqual(data[3]['code'], 'code1')

    def test_post_get_suggest(self):
        resp = self.client.get('/posts/suggest/')
        data = resp.json()
        data = data['results']
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['likes_count'], 9)
        self.assertEqual(data[1]['likes_count'], 5)
        self.assertEqual(data[2]['likes_count'], 2)
    
    def test_post_like_unlike(self):
        post_dict = {
            'post_code': 'code2',
        }
        resp = self.client.put("/posts/like-unlike/", post_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'like')
        self.assertEqual(data['likes_count'], 1)
        post = Post.objects.get(code='code2')
        self.assertEqual(post.postlike_set.count(), 1)

        resp = self.client.put("/posts/like-unlike/", post_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'unlike')
        self.assertEqual(data['likes_count'], 0)
        post = Post.objects.get(code='code2')
        self.assertEqual(post.postlike_set.count(), 0)
        

    def test_post_get_like_profile(self):
        PostLike.objects.create(profile=self.profile_1, post=self.post_2)
        PostLike.objects.create(profile=self.profile_3, post=self.post_2)
        resp = self.client.get("/posts/like-profile/code/code2/")
        data = resp.json()
        data = data['results']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['username'], 'test_user1')
        self.assertEqual(data[1]['username'], 'test_user3')

    def test_post_save_unsave(self):
        post_dict = {
            'post_code': 'code2',
        }
        resp = self.client.post("/posts/save-unsave/", post_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'save')
        self.assertEqual(self.profile_1.savedpost_set.count(), 1)

        post_dict = {
            'post_code': 'code3',
        }
        resp = self.client.post("/posts/save-unsave/", post_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'save')
        self.assertEqual(self.profile_1.savedpost_set.count(), 2)

        post_dict = {
            'post_code': 'code2',
        }
        resp = self.client.post("/posts/save-unsave/", post_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'unsave')
        self.assertEqual(self.profile_1.savedpost_set.count(), 1)

    def test_post_get_saved(self):
        SavedPost.objects.create(profile=self.profile_1, post=self.post_2)
        SavedPost.objects.create(profile=self.profile_1, post=self.post_3)
        SavedPost.objects.create(profile=self.profile_1, post=self.post_4)
        resp = self.client.get("/posts/saved/")
        data = resp.json()['results']
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['code'], 'code4')
        self.assertEqual(data[1]['code'], 'code3')
        self.assertEqual(data[2]['code'], 'code2')

