from .my_imports import *


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def create_get_story(request):
    if request.method == 'POST':
        profile = request.user.profile
        data = {'profile': profile.id,
                'body': request.data['body'], 'video': request.data.get('video')}
        serializer = StorySerializer(data=data, partial=True, context={
                                     'images': request.data.getlist('images')})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response('Error on create post', status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        profile = request.user.profile
        following_stories = Story.objects.filter(profile__following__follower=profile).filter(
            created__gt=timezone.now() - timezone.timedelta(days=10)).order_by('-created')
        self_stories = StorySerializer(profile.story_set.all(), many=True).data
        following_stories = StorySerializer(following_stories, many=True).data
        response_data = {}
        for story in self_stories + following_stories:
            if not story['profile'] in response_data:
                response_data[story['profile']] = [story]
            else:
                response_data[story['profile']].append(story)
        return Response(list(response_data.values()))


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_story(request, pk):
    story = get_object_or_404(Story, pk=pk)
    if story.profile == request.user.profile:
        story.delete()
        return Response('Story was deleted!')
    else:
        return Response('Cannot delete story', status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def like_unlike_story(request):
    story = get_object_or_404(Story, pk=request.data['id'])
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
def view_story(request):
    story = get_object_or_404(Story, pk=request.data['id'])
    story_view = StoryView.objects.filter(
        profile=request.user.profile, story=story)
    if not story_view:
        StoryView.objects.create(profile=request.user.profile, story=story)
        return Response('Successfully view story')
    else:
        return Response('Successfully view story')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_story_activity(request, pk): # 'stories/<int:pk>/activity'
    story = get_object_or_404(Story, pk=pk)
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.STORY_ACTIVITY_PAGE_SIZE
    paginator.ordering = 'name'
    if story.profile == request.user.profile:
        view_profiles = story.view_profiles.all()
        like_profiles = set(story.like_profiles.all())
        response_data = []
        result_set = paginator.paginate_queryset(view_profiles, request)
        serializer = ProfileLightSerializer(result_set, many=True)
        for profile, profile_data in zip(view_profiles, serializer.data):
            is_like = profile in like_profiles
            response_data.append(
                {'profile_data': profile_data, 'like': is_like})
        return paginator.get_paginated_response(response_data)
    else:
        return Response('Cannot get story activity', status=status.HTTP_400_BAD_REQUEST)
