from .my_imports import *


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    current_user = request.user
    data = request.data
    profile = Profile.objects.get(user__username=current_user.username)
    serializer = ProfileSerializer(instance=profile, data=data, context={
                                   'username': current_user.username, 'new_username': data['username']})

    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Profile was updated!', 'data': serializer.data})
    else:
        return Response('Error on update profile', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_profile(request, username):  # get profile of username
    profile = get_object_or_404(Profile, user__username=username)
    fields = ('username', 'name', 'bio', 'avatar',
            'num_posts', 'num_followings', 'num_followers', 'is_follow')
    serializer = ProfileSerializer(profile, fields=fields)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suggest_profile(request):  # get suggested profile for current user
    followings = Profile.objects.filter(
        following__follower=request.user.profile)
    suggested_profiles = []
    for following in followings:
        following_of_following = Profile.objects.filter(following__follower=following).exclude(
            following__follower=request.user.profile).exclude(id=request.user.profile.id)
        profile_serializer = ProfileLightSerializer(
            following_of_following, many=True)
        suggested_profile = profile_serializer.data[:3]
        for profile in suggested_profile:
            profile.update({'followed_by': following.user.username})
        suggested_profiles = suggested_profiles + suggested_profile
    return Response(suggested_profiles[:20])


@api_view(['GET'])
def get_search_profile(request, keyword):
    if request.user.is_authenticated:
        username = request.user.username
        profiles = Profile.objects.filter(~Q(user__username=username) & (
            Q(user__username__contains=keyword) | Q(name__contains=keyword)))[:20]
    else:
        profiles = Profile.objects.filter(
            Q(user__username__contains=keyword) | Q(name__contains=keyword))[:20]
    serializer = ProfileLightSerializer(profiles, many=True)
    return Response(serializer.data)
