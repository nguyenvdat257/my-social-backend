from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Profile, Post, Follow
from django.contrib.auth.models import User
from ..serializers import ProfileSerializer
from django.db.models import Q


@api_view(['PUT'])
def updateProfile(request):
    current_user = request.user
    data = request.data
    profile = Profile.objects.get(user__username=current_user.username)
    serializer = ProfileSerializer(instance=profile, data=data, context={
                                   'username': current_user.username, 'new_username': data['username']})

    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Profile was updated!', 'data': serializer.data})
    else:
        return Response('Error on update profile')


@api_view(['GET'])
def getProfile(request, username):  # get profile of username
    user = get_object_or_404(User, username=username)
    num_post = Post.objects.filter(profile__user__username=username).count()
    num_following = Follow.objects.filter(
        follower_profile__user__username=username).count()
    num_follower = Follow.objects.filter(
        followee_profile__user__username=username).count()
    response_data = {'num_post': num_post,
                     'num_following': num_following, 'num_follower': num_follower}
    profile = Profile.objects.get(user__username=username)
    fields = ('username', 'name', 'bio', 'avatar')
    serializer = ProfileSerializer(profile, fields=fields)
    response_data.update(serializer.data)
    return Response(response_data)


@api_view(['GET'])
def getSuggestProfile(request):  # get suggested profile for current user
    current_user = request.user
    followees = [
        follow.followee_profile for follow in current_user.profile.follow_followers.all()]
    suggested_profiles = []
    # get followee of followee
    for followee in followees:
        followee_of_followee = [follow.followee_profile for follow in followee.follow_followers.all(
        ) if follow.followee_profile != current_user.profile]
        fields = ('username', 'name', 'bio', 'avatar')
        profile_serializer = ProfileSerializer(
            followee_of_followee, many=True, fields=fields)
        suggested_profile = profile_serializer.data[:3]
        for profile in suggested_profile:
            profile.update({'followed_by': followee.user.username})
        suggested_profiles = suggested_profiles + suggested_profile
    return Response(suggested_profiles)


@api_view(['GET'])
def getSearchProfile(request, keyword):
    if request.user.is_authenticated:
        username = request.user.username
        profiles = Profile.objects.filter(~Q(user__username=username) & (Q(user__username__contains=keyword) | Q(name__contains=keyword)))[:20]
    else:
        profiles = Profile.objects.filter(Q(user__username__contains=keyword) | Q(name__contains=keyword))[:20]
    fields = ('username', 'name', 'bio', 'avatar')
    serializer = ProfileSerializer(profiles, fields=fields, many=True)
    return Response(serializer.data)
