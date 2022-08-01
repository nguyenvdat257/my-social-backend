from .my_imports import *


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_story(request):
    profile = request.user.profile
    data = {'profile': profile.id,
            'body': request.data['body'], 'video': request.data.get('video'), 'music': request.data.get('music')}
    serializer = StorySerializer(data=data, partial=True, context={
                                 'images': request.data.getlist('images'), 'current_profile': profile})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response('Error on create post', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_stories_current_user(request):
    profile = request.user.profile
    following_stories = Story.objects.filter(profile__following__follower=profile).filter(
        created__gt=timezone.now() - timezone.timedelta(days=settings.STORY_VALID_DAY)).order_by('-created')
    self_stories = profile.story_set.filter(created__gt=timezone.now(
    ) - timezone.timedelta(days=settings.STORY_VALID_DAY))
    self_stories = StorySerializer(self_stories, many=True, context={
                                   'current_profile': profile}).data
    following_stories = StorySerializer(following_stories, many=True, remove_fields=['view_count'], context={
                                        'current_profile': profile}).data
    response_following = {}
    for story in following_stories:
        if not story['profile_info']['username'] in response_following:
            response_following[story['profile_info']['username']] = [story]
        else:
            response_following[story['profile_info']['username']].append(story)
    return Response({'self_stories': [[profile.user.username, self_stories]], 'following_stories': response_following.items()})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_story(request, pk):
    story = get_object_or_404(Story, pk=pk)
    if request.method == 'DELETE':
        if story.profile == request.user.profile:
            story.delete()
            return Response('Story was deleted!')
        else:
            return Response('Cannot delete story', status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        serializer = StorySerializer(story)
        return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def like_unlike_story(request):
    story = get_object_or_404(Story, pk=request.data['id'])
    if story.profile == request.user.profile:
        return Response('Cannot like story', status=status.HTTP_400_BAD_REQUEST)
    story_like = StoryLike.objects.filter(
        profile=request.user.profile, story=story)
    if story_like:
        story_like.delete()
        likes_count = story.storylike_set.count()
        story.likes_count = likes_count
        story.save()
        return Response(data={'type': 'unlike', 'likes_count': likes_count})
    else:
        StoryLike.objects.create(profile=request.user.profile, story=story)
        likes_count = story.storylike_set.count()
        story.likes_count = likes_count
        story.save()
        return Response(data={'type': 'like', 'likes_count': likes_count})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def view_story(request):  # a user views a story
    story = get_object_or_404(Story, pk=request.data['id'])
    story_view = StoryView.objects.filter(
        profile=request.user.profile, story=story)
    if not story_view:  # a different user who has not viewed
        StoryView.objects.create(profile=request.user.profile, story=story)
        return Response('Successfully view story')
    return Response('Cannot view story', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_story_activity(request, pk):  # 'stories/<int:pk>/activity/'
    story = get_object_or_404(Story, pk=pk)
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.STORY_ACTIVITY_PAGE_SIZE
    paginator.ordering = 'name'
    if story.profile == request.user.profile:
        view_profiles = story.view_profiles.exclude(pk=request.user.profile.pk)
        like_profile_ids = story.like_profiles.values_list('id', flat=True)
        response_data = []
        result_set = paginator.paginate_queryset(view_profiles, request)
        serializer = ProfileLightSerializer(result_set, context={'profile': request.user.profile}, many=True)
        for profile_info in  serializer.data:
            if profile_info['id'] in like_profile_ids:
                profile_info['is_like_story'] = True
            else:
                profile_info['is_like_story'] = False
            
        return paginator.get_paginated_response(serializer.data)
    else:
        return Response('Cannot get story activity', status=status.HTTP_400_BAD_REQUEST)
