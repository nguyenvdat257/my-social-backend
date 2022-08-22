from .my_imports import *


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def my_profile(request):
    if request.method == 'GET':
        current_user = request.user
        data = request.data
        profile = Profile.objects.get(user__username=current_user.username)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    if request.method == 'PUT':
        current_user = request.user
        data = request.data
        profile = Profile.objects.get(user__username=current_user.username)
        context = {'username': current_user.username}
        if 'username' in data:
            context['new_username'] = data['username']
        serializer = ProfileEditSerializer(
            instance=profile, data=data, context=context, partial=True)
        is_valid, errors = serializer.is_valid()
        if is_valid:
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_profile(request, username):  # get profile of username
    profile = get_object_or_404(Profile, user__username=username)
    fields = ('username', 'name', 'bio', 'avatar',
              'num_posts', 'num_followings', 'num_followers', 'is_follow', 'is_has_story', 'is_story_seen')
    serializer = ProfileSerializer(profile, fields=fields, context={'profile': request.user.profile})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suggest_profile(request):  # get suggested profile for current user
    current_profile = request.user.profile
    followings = Profile.objects.filter(
        following__follower=current_profile)
    following_ids = [x.id for x in followings]
    suggested_profiles = []
    for following in followings:
        following_of_following = Profile.objects.filter(Q(following__follower=following) & ~Q(
            id__in=following_ids) & ~Q(id=current_profile.id))
        profile_serializer = ProfileLightSerializer(
            following_of_following, many=True)
        suggested_profile = profile_serializer.data[:3]
        for profile in suggested_profile:
            profile.update({'followed_by': following.user.username})
        suggested_profiles = suggested_profiles + suggested_profile
    used_id = set()
    filtered_profiles = []
    for profile in suggested_profiles:
        if not profile['id'] in used_id:
            filtered_profiles.append(profile)
            used_id.add(profile['id'])
    return Response(filtered_profiles[:20])


@api_view(['GET'])
def get_search_profile(request, keyword):
    if request.user.is_authenticated:
        username = request.user.username
        profiles = Profile.objects.filter(~Q(user__username=username) & (
            Q(user__username__contains=keyword) | Q(name__contains=keyword)))[:20]
    else:
        profiles = Profile.objects.filter(
            Q(user__username__contains=keyword) | Q(name__contains=keyword))[:20]
    
    serializer = ProfileLightSerializer(profiles, remove_fields=['is_follow'], context={'profile': request.user.profile}, many=True)
    return Response(serializer.data)
