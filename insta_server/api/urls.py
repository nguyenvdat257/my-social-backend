from django.urls import path
from . import views
from .views import MyTokenObtainPairView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path('profiles/', views.update_profile, name="update-profile"),
    path('profiles/<str:username>', views.get_profile, name="get-profile"),
    path('profiles/suggest/', views.get_suggest_profile, name="get-suggest-profile"),
    path('profiles/search/<str:keyword>', views.get_search_profile, name="get-search-profile"),
    path('posts/code/<str:code>/', views.process_post, name="process-post"),
    path('posts/user/<str:username>/', views.get_posts, name="get-posts"),
    path('posts/', views.create_post, name="create-post"),
    path('posts/current-user/', views.get_posts_current_user, name="get-posts-current-user"),
    path('posts/tag-popular/<str:tag>/', views.get_posts_by_tag_popular, name="get-posts-by-tag-popular"),
    path('posts/tag-recent/<str:tag>/', views.get_posts_by_tag_recent, name="get-posts-by-tag-recent"),
    path('posts/suggest/', views.get_suggest_posts, name="get-suggest_posts"),
    path('posts/like-unlike/', views.like_unlike_post, name="like-unlike-post"),
    path('posts/like-profile/code/<str:post_code>/', views.get_post_like_profile, name="post-like-profile"),
    path('posts/save-unsave/', views.save_unsave_post, name="save-unsave-post"),
    path('posts/saved/', views.get_saved_post, name="get-saved-post"),
    path('comments/', views.create_comment, name="create-comment"),
    path('comments/<int:pk>/', views.delete_comment, name="delete-comment"),
    path('comments/post-code/<str:post_code>/', views.get_comments, name="get-comments"),
    path('comments/like-unlike/', views.like_unlike_comment, name="like-unlike-comment"),
    path('comments/like-profile/<int:pk>/', views.get_comment_like_profile, name="comment-like-profile"),
    path('stories/', views.create_get_story, name="create-get-story"),
    path('stories/<int:pk>/', views.delete_story, name="delete-story"),
    path('stories/like-unlike/', views.like_unlike_story, name="like-unlike-story"),
    path('stories/view/', views.view_story, name="view-story"),
    path('stories/<int:pk>/activity/', views.get_story_activity, name="get-story-activity"),
    path('follows/follow-unfollow/', views.follow_unfollow, name="follow-unfollow"),
    path('follows/follower/user/<str:username>/', views.get_follower, name="get-follower"),
    path('follows/following/user/<str:username>/', views.get_following, name="get-following"),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', views.user_signup, name='signup'),
    path('notification/', views.get_notification, name='get-notification'),
    path('notification/seen/', views.seen_notification, name='seen-notification'),
]