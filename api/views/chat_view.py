from functools import partial
from .my_imports import *


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_create_chat_room(request):
    if request.method == 'GET':
        chatrooms = request.user.profile.chatroom_set.order_by('-updated')
        serializer = ChatRoomSerializer(chatrooms, many=True, context={'current_profile': request.user.profile})
        return Response(serializer.data)

    if request.method == 'POST':
        usernames = request.data.getlist('usernames')
        profiles = Profile.objects.filter(user__username__in=usernames)
        serializer = ChatRoomSerializer(data={}, partial=True, context={
                                        'profiles': profiles, 'current_profile': request.user.profile})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response('Cannot create chat room', status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_chat_room(request, pk):
    chatroom = get_object_or_404(ChatRoom, pk=pk)
    try:
        chatroom_profile = ChatRoomProfile.objects.get(
            profile=request.user.profile, chatroom=chatroom)
    except:
        return Response('Cannot update chat room', status=status.HTTP_400_BAD_REQUEST)
    if chatroom_profile.is_admin:
        context = {'current_profile': request.user.profile}
        if 'added_usernames' in request.data:
            usernames = request.data.getlist('added_usernames')
            context['added_profiles'] = Profile.objects.filter(
                user__username__in=usernames)
        if 'removed_usernames' in request.data:
            usernames = request.data.getlist('removed_usernames')
            context['removed_profiles'] = Profile.objects.filter(
                user__username__in=usernames)
        if 'chatroom_name' in request.data:
            context['chatroom_name'] = request.data['chatroom_name']
        if 'is_mute' in request.data:
            context['is_mute'] = request.data['is_mute']
        serializer = ChatRoomSerializer(
            chatroom, data={}, partial=True, context=context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
    return Response('Cannot update chat room', status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def promote_demote_admin(request, pk):
    chatroom = get_object_or_404(ChatRoom, pk=pk)
    considered_username = request.data['username']
    try:
        considered_profile = get_object_or_404(Profile, user__username=considered_username)
        chatroom_profile = ChatRoomProfile.objects.get(
            profile=considered_profile, chatroom=chatroom)
        chatroom_profile.is_admin = not chatroom_profile.is_admin
        chatroom_profile.save()
        return Response('Successfully change admin right')
    except:
        return Response('Cannot change admin right', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_list(request, pk):
    chatroom = get_object_or_404(ChatRoom, pk=pk)
    if request.user.profile in chatroom.profiles.all():
        paginator = pagination.CursorPagination()
        paginator.page_size = settings.CHAT_LIST_SIZE
        result_page = paginator.paginate_queryset(chatroom.chat_set.all(), request)
        serializer = ChatSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    return Response('Cannot get chat list', status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reaction_list(request, pk):
    chat = get_object_or_404(Chat, pk=pk)
    if request.user.profile in chat.chatroom.profiles.all():
        reaction_profiles = Profile.objects.filter(chatreaction__reply_to=chat)
        paginator = pagination.CursorPagination()
        paginator.page_size = settings.CHAT_LIST_SIZE
        paginator.ordering = 'name'
        result_page = paginator.paginate_queryset(reaction_profiles, request)
        serializer = ProfileChatSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    return Response('Cannot get chat reaction list', status=status.HTTP_400_BAD_REQUEST)