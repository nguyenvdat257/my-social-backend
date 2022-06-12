from .my_imports import *


class StoryApiTestCase(MyTestCase):
    def test_story_create(self):
        story_dict = {
            'body': 'new post #seagame #hanoi bright',
            'video': SimpleUploadedFile(name='test_video1.mp4', content=open(self.video_path1, 'rb').read(), content_type='video'),
            'music': SimpleUploadedFile(name='test_music1.mp3', content=open(self.music_path1, 'rb').read(), content_type='music'),
            'images': [SimpleUploadedFile(name='test_img1.jpg', content=open(self.image_path1, 'rb').read(), content_type='image'),
                       SimpleUploadedFile(name='test_img2.jpg', content=open(self.image_path2, 'rb').read(), content_type='image')]
        }
        resp = self.client.post("/stories/", story_dict)
        story_id = resp.json()["id"]
        story = Story.objects.get(pk=story_id)
        self.assertEqual(story.body, story_dict["body"])
        self.assertTrue('video1' in story.video.url)
        self.assertTrue('music1' in story.music.url)
        self.assertEqual(len(story.storyimage_set.all()), 2)

    def test_story_get(self):
        Story.objects.create(profile=self.profile_1, body='story 1')
        Story.objects.create(profile=self.profile_1, body='story 2')
        Story.objects.create(profile=self.profile_2, body='story 3')
        Story.objects.create(profile=self.profile_3, body='story 4')
        resp = self.client.get("/stories/")
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0][0]['profile_info']['username'], 'test_user1')
        self.assertEqual(data[0][0]['body'], 'story 1')
        self.assertEqual(data[0][1]['profile_info']['username'], 'test_user1')
        self.assertEqual(data[0][1]['body'], 'story 2')
        self.assertEqual(data[1][0]['profile_info']['username'], 'test_user2')
        self.assertEqual(data[1][0]['body'], 'story 3')

    def test_story_delete(self):
        story = Story.objects.create(profile=self.profile_1, body='story 1')
        resp = self.client.delete("/stories/%s/" % story.id)
        self.assertEqual(Story.objects.count(), 0)

        story = Story.objects.create(profile=self.profile_2, body='story 2')
        resp = self.client.delete("/stories/%s/" % story.id)
        self.assertEqual(resp.status_code, 400)

    def test_story_like_unlike(self):
        # like my story => not count
        story = Story.objects.create(profile=self.profile_1, body='story 1')
        story_dict = {
            'id': story.id,
        }
        resp = self.client.put("/stories/like-unlike/", story_dict)
        data = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(StoryLike.objects.count(), 0)

        # like other story
        story = Story.objects.create(profile=self.profile_2, body='story 2')
        story_dict = {
            'id': story.id,
        }
        resp = self.client.put("/stories/like-unlike/", story_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'like')
        self.assertEqual(data['likes_count'], 1)
        story = Story.objects.get(pk=story.id)
        self.assertEqual(story.storylike_set.count(), 1)

        # unlike other story
        resp = self.client.put("/stories/like-unlike/", story_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'unlike')
        self.assertEqual(data['likes_count'], 0)
        story = Story.objects.get(pk=story.id)
        self.assertEqual(story.storylike_set.count(), 0)

    def test_story_view(self):
        # view my story => not count
        story = Story.objects.create(profile=self.profile_1, body='story 1')
        story_dict = {
            'id': story.id,
        }
        resp = self.client.put('/stories/view/', story_dict)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(StoryView.objects.count(), 0)

        # view others story twice
        story = Story.objects.create(profile=self.profile_2, body='story 2')
        story_dict = {
            'id': story.id,
        }
        self.client.put('/stories/view/', story_dict)
        self.assertEqual(StoryView.objects.count(), 1)
        self.client.put('/stories/view/', story_dict)
        self.assertEqual(StoryView.objects.count(), 1)

    def test_story_activity(self):
        story = Story.objects.create(profile=self.profile_1, body='story 1')
        StoryView.objects.create(profile=self.profile_2, story=story)
        StoryView.objects.create(profile=self.profile_3, story=story)
        StoryView.objects.create(profile=self.profile_4, story=story)
        StoryLike.objects.create(profile=self.profile_3, story=story)
        StoryLike.objects.create(profile=self.profile_4, story=story)
        resp = self.client.get('/stories/%s/activity/' % story.id)
        data = resp.json()['results']
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['profile_info']['username'], 'test_user2')
        self.assertEqual(data[1]['profile_info']['username'], 'test_user3')
        self.assertEqual(data[2]['profile_info']['username'], 'test_user4')
        self.assertEqual(data[0]['like'], False)
        self.assertEqual(data[1]['like'], True)
        self.assertEqual(data[2]['like'], True)
