from .my_imports import *
from django.db.models import Count
from django.db.models import F


def get_post_by_code(request, code):
    if request.user.is_authenticated:
        profile = request.user.profile
        posts = Post.objects.filter(code=code).filter(Q(profile__following__follower=profile) | Q(
            profile__account_type='PU') | Q(profile=profile)).distinct()
    else:
        posts = Post.objects.filter(code=code).filter(
            profile__account_type='PU').distinct()
    return posts


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def process_post(request, code):
    profile = get_object_or_404(
        Profile, user__username=request.user.username)
    if request.method == 'GET':
        posts = get_post_by_code(request, code)
        if len(posts) == 1:
            serializer = PostSerializer(
                posts[0], context={'current_profile': profile})
            return Response(serializer.data)
        else:
            return Response('Error on get post', status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'PUT':
        post = get_object_or_404(Post, code=code)
        if profile == post.profile:
            serializer = PostSerializer(
                instance=post, data=request.data, partial=True, context={'current_profile': profile})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        return Response('Error on update post', status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        post = get_object_or_404(Post, code=code)
        if post.profile == request.user.profile:
            post.delete()
            return Response('Post was deleted!')
        else:
            return Response('Cannot delete post', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_posts_by_code_and_recent(request, code):
    posts_by_code = get_post_by_code(request, code)
    if len(posts_by_code) == 1:
        post_by_code = posts_by_code[0]
        posts_recent = Post.objects.none()
        if request.user.is_authenticated:
            profile = request.user.profile
            posts_recent = Post.objects.exclude(code=code).filter(profile=post_by_code.profile).filter(Q(profile__following__follower=profile) | Q(
                profile__account_type='PU') | Q(profile=profile)).order_by('-created')[:6]
        else:
            posts_recent = Post.objects.exclude(code=code).filter(profile=post_by_code.profile).filter(
                profile__account_type='PU').order_by('-created')[:6]
        postSerializer = PostSerializer(
            posts_by_code, many=True, context={'current_profile': profile})
        postLightSerializer = PostLightSerializer(posts_recent, many=True)
        return Response(postSerializer.data + postLightSerializer.data)
    else:
        return Response('Error on get post', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_posts(request, username):  # 'posts/username/<str:username>/'
    request_profile = get_object_or_404(
        Profile, user__username=username)
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.POST_USER_PAGE_SIZE
    if request_profile.account_type == 'PU':
        posts = Post.objects.filter(
            profile__user__username=username).order_by('-created')
        result_page = paginator.paginate_queryset(posts, request)
        serializer = PostLightSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    else:
        if request.user.is_authenticated:
            current_profile = get_object_or_404(
                Profile, user__username=request.user.username)
            is_follow_request_user = Follow.objects.filter(
                Q(follower=current_profile) & Q(following=request_profile)).exists()
            is_same_user = username == request.user.username
            if is_follow_request_user or is_same_user:
                result_page = paginator.paginate_queryset(
                    request_profile.post_set.order_by('-created'), request)
                serializer = PostLightSerializer(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response({'results': [], 'next': None})
    return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_posts_current_user(request):  # 'posts/current-user/'
    profile = request.user.profile
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.POST_USER_PAGE_SIZE
    posts = Post.objects.filter(Q(profile__following__follower=profile) | Q(
        profile=profile))
    result_page = paginator.paginate_queryset(posts, request)
    serializer = PostSerializer(result_page, many=True, context={
                                'current_profile': profile})
    if not paginator.get_previous_link():
        profile.last_view_page_time = timezone.now()
        profile.save()
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_new_posts_current_user(request):  # 'posts/current-user/'
    profile = request.user.profile
    posts = Post.objects.filter(Q(profile__following__follower=profile) | Q(
        profile=profile)).filter(created__gt=profile.last_view_page_time)
    profile.last_view_page_time = timezone.now()
    profile.save()
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):  # 'posts/'
    profile = request.user.profile
    if isinstance(request.data, QueryDict):  # optional
        request.data._mutable = True
    request.data.update({'profile': profile.id})
    serializer = PostSerializer(data=request.data, partial=True, context={
                                'images': request.data.getlist('images'), 'current_profile': profile})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response('Error on create post', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_posts_by_tag_popular(request, tag):  # 'posts/tag-popular/<str:tag>'
    if request.user.is_authenticated:
        # get posts from public account or if current account follows that account
        profile = request.user.profile
        posts = Post.objects.filter(hash_tags__body=tag).filter(Q(profile__following__follower=profile) | Q(
            profile__account_type='PU')).order_by('-likes_count')[:10]
    else:
        posts = Post.objects.filter(hash_tags__body=tag).filter(
            profile__account_type='PU').order_by('-likes_count')[:10]
    serializer = PostLightSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_posts_by_tag_recent(request, tag):  # 'posts/tag-recent/<str:tag>/'
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.POST_TAG_PAGE_SIZE
    if request.user.is_authenticated:
        profile = request.user.profile
        # get posts from public account or if current account follows that account
        posts = Post.objects.filter(hash_tags__body=tag).filter(Q(profile__following__follower=profile) | Q(
            profile__account_type='PU'))
    else:
        posts = Post.objects.filter(hash_tags__body=tag).filter(
            profile__account_type='PU')
    result_page = paginator.paginate_queryset(posts, request)
    serializer = PostLightSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def get_suggest_posts(request):
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.POST_SUGGEST_PAGE_SIZE
    paginator.ordering = '-likes_count'
    if request.user.is_authenticated:
        profile = request.user.profile
        # get posts from public account or if current account follows that account
        posts = Post.objects.exclude(profile=profile).filter(
            Q(profile__account_type='PU') | Q(profile__following__follower=profile)).annotate(likes_count=Count('postlike'))
    else:
        posts = Post.objects.filter(profile__account_type='PU').annotate(
            likes_count=Count('postlike'))
    result_page = paginator.paginate_queryset(posts, request)
    serializer = PostLightSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def like_unlike_post(request):
    post_code = request.data['post_code']
    post = get_object_or_404(Post, code=post_code)
    post_like = PostLike.objects.filter(
        profile=request.user.profile, post=post)
    if post_like:
        post_like.delete()
        likes_count = post.postlike_set.count()
        return Response(data={'type': 'unlike', 'likes_count': likes_count})
    else:
        PostLike.objects.create(profile=request.user.profile, post=post)
        likes_count = post.postlike_set.count()
        return Response(data={'type': 'like', 'likes_count': likes_count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
# 'posts/like-profile/<str:post_code>'
def get_post_like_profile(request, post_code):
    profile = request.user.profile
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.POST_LIKE_PROFILE_PAGE_SIZE
    paginator.ordering = 'name'
    like_profiles = Profile.objects.filter(postlike__post__code=post_code)
    result_page = paginator.paginate_queryset(like_profiles, request)
    serializer = ProfileLightSerializer(
        result_page,  many=True, context={'profile': profile})
    return paginator.get_paginated_response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def save_unsave_post(request):  # 'posts/save-unsave/'
    post_code = request.data['post_code']
    post = get_object_or_404(Post, code=post_code)
    post_save = SavedPost.objects.filter(
        profile=request.user.profile, post=post)
    if post_save:
        post_save.delete()
        return Response(data={'type': 'unsave'})
    else:
        SavedPost.objects.create(profile=request.user.profile, post=post)
        return Response(data={'type': 'save'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_saved_post(request):  # 'posts/saved/'
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.POST_SAVED_PAGE_SIZE
    paginator.ordering = '-saved_date'
    saved_posts = Post.objects.filter(
        savedpost__profile=request.user.profile).annotate(
            saved_date=F('savedpost__created'))
    result_page = paginator.paginate_queryset(saved_posts, request)
    serializer = PostLightSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)
