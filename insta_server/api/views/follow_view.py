from .my_imports import *


class FollowUserPagination(pagination.CursorPagination):
    page_size = settings.FOLLOW_FOLLOWER_SIZE
    ordering = 'name'


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def follow_unfollow(request):
    following = get_object_or_404(
        Profile, user__username=request.data['username'])
    follow = Follow.objects.filter(
        follower=request.user.profile, following=following)
    if follow:
        follow.delete()
        return Response(data={'type': 'unfollow'})
    else:
        Follow.objects.create(
            follower=request.user.profile, following=following)
        return Response(data={'type': 'follow'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_follower(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    paginator = FollowUserPagination()
    followers = Profile.objects.filter(follower__following=profile)
    result_page = paginator.paginate_queryset(followers, request)
    serializer = ProfileLightSerializer(
        result_page, many=True, context={'profile': profile})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    paginator = FollowUserPagination()
    followings = Profile.objects.filter(following__follower=profile)
    result_page = paginator.paginate_queryset(followings, request)
    serializer = ProfileLightSerializer(
        result_page, many=True, context={'profile': profile})
    return paginator.get_paginated_response(serializer.data)
