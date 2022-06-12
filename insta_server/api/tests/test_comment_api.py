from .my_imports import *


class CommentApiTestCase(MyTestCase):
    def test_comment_create(self):
        comment_dict = {
            'post_code': 'code2',
            'body': 'comment for post 2',
        }
        resp = self.client.post("/comments/", comment_dict)
        comment_id = resp.json()["id"]
        comment = Comment.objects.get(pk=comment_id)
        self.assertEqual(comment.body, comment_dict["body"])
        self.assertEqual(comment.profile.user.username, 'test_user1')

        old_comment_id = comment_id
        comment_dict = {
            'post_code': 'code2',
            'body': 'comment for post 2',
            'reply_to_comment': old_comment_id
        }
        resp = self.client.post("/comments/", comment_dict)
        comment_id = resp.json()["id"]
        comment = Comment.objects.get(pk=comment_id)
        self.assertEqual(comment.body, comment_dict["body"])
        self.assertEqual(comment.profile.user.username, 'test_user1')
        self.assertEqual(comment.reply_to_comment.id, old_comment_id)

    def test_comment_delete(self):
        comment = Comment.objects.create(
            profile=self.profile_1, post=self.post_2, body='comment post 2')
        self.client.delete("/comments/%s/" % comment.id)
        self.assertEqual(Comment.objects.count(), 0)

        comment = Comment.objects.create(
            profile=self.profile_2, post=self.post_3, body='comment post 3')
        resp = self.client.delete("/comments/%s/" % comment.id)
        self.assertEqual(resp.status_code, 400)

    def test_comment_get_by_post_code(self):
        Comment.objects.create(
            profile=self.profile_1, post=self.post_2, body='comment 1 post 2')
        Comment.objects.create(
            profile=self.profile_2, post=self.post_2, body='comment 2 post 2')
        resp = self.client.get("/comments/post-code/code2/")
        data = resp.json()['results']
        self.assertEqual(data[0]['username'], 'test_user2')
        self.assertTrue('test_img2' in data[0]['avatar'])
        self.assertEqual(data[1]['username'], 'test_user1')
        self.assertTrue('test_img1' in data[1]['avatar'])

    
    def test_comment_like_unlike(self):
        comment = Comment.objects.create(
            profile=self.profile_1, post=self.post_2, body='comment 1 post 2')
        comment_dict = {
            'id': comment.id,
        }
        resp = self.client.put("/comments/like-unlike/", comment_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'like')
        self.assertEqual(data['likes_count'], 1)
        comment = Comment.objects.get(pk=comment.id)
        self.assertEqual(comment.commentlike_set.count(), 1)

        resp = self.client.put("/comments/like-unlike/", comment_dict)
        data = resp.json()
        self.assertEqual(data['type'], 'unlike')
        self.assertEqual(data['likes_count'], 0)
        comment = Comment.objects.get(pk=comment.id)
        self.assertEqual(comment.commentlike_set.count(), 0)

    def test_comment_get_like_profile(self):
        comment = Comment.objects.create(
            profile=self.profile_1, post=self.post_2, body='comment 1 post 2')
        CommentLike.objects.create(profile=self.profile_2, comment=comment)
        CommentLike.objects.create(profile=self.profile_3, comment=comment)
        resp = self.client.get("/comments/like-profile/%s/"%comment.id)
        data = resp.json()
        data = data['results']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['username'], 'test_user2')
        self.assertEqual(data[1]['username'], 'test_user3')