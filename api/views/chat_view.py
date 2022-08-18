from functools import partial
from .my_imports import *
from django.db.models import Max, OuterRef, Subquery
from asgiref.sync import async_to_sync
import channels.layers


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_create_chat_room(request):
    if request.method == 'GET':
        # chatrooms = request.user.profile.chatroom_set.annotate(latest=Max('chat_set__created')).order_by('-latest')
        try: 
            chatrooms = ChatRoom.objects.filter(chatroom_profile__profile=request.user.profile).annotate(
                latest=Max('chat_set__created')).order_by('-latest')
            serializer = ChatRoomSerializer(chatrooms, many=True, context={
                                            'current_profile': request.user.profile})
            return Response(serializer.data)
        except Exception as e:
            return Response(str(e))

    if request.method == 'POST':
        current_profile = request.user.profile
        usernames = request.data['usernames']
        usernames.append(current_profile.user.username)
        profiles = Profile.objects.filter(user__username__in=usernames)
        serializer = ChatRoomSerializer(data={}, partial=True, context={
                                        'profiles': profiles, 'current_profile': current_profile})
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data)
        return Response('Cannot create chat room', status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def share_post_to_chat(request):
    if request.method == 'POST':
        current_profile = request.user.profile
        usernames = request.data['usernames']
        share_post_img = request.data['share_post_img']
        share_post_code = request.data['share_post_code']

        profiles = Profile.objects.filter(user__username__in=usernames)
        layer = channels.layers.get_channel_layer()
        for profile in profiles:
            serializer = ChatRoomSerializer(data={}, partial=True, context={
                                            'profiles': [current_profile, profile], 'current_profile': current_profile})
            if serializer.is_valid():
                serializer.save()
                chatroom = serializer.data
                chat = Chat.objects.create(
                    profile=current_profile, chatroom_id=chatroom['id'],
                    type='S', share_post_img=share_post_img, share_post_code=share_post_code)
                chat_data = ChatSerializer(chat).data
                send_obj = {'type': 'message', 'chat': chat_data}
                room_group_name = 'chatroom_%s' % chatroom['id']
                async_to_sync(layer.group_send)(
                    room_group_name, send_obj
                )
            else:
                return Response('Cannot share post', status=status.HTTP_400_BAD_REQUEST)
        return Response('Successfully share post')


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
        considered_profile = get_object_or_404(
            Profile, user__username=considered_username)
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
        result_page = paginator.paginate_queryset(
            chatroom.chat_set.all().order_by('-created'), request)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_suggest_profile(request):
    chatrooms = request.user.profile.chatroom_set.all()
    profiles = Profile.objects.filter(
        profile_chatroom__chatroom__in=chatrooms).exclude(pk=request.user.profile.id).distinct()
    serializer = ProfileChatSerializer(profiles[:10], many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_seen(request):
    current_profile = request.user.profile
    latest_chat = Subquery(Chat.objects.filter(
        chatroom_id=OuterRef("id")).order_by("-created").values('id')[:1])
    latest_chat_profile = Subquery(Chat.objects.filter(
        chatroom_id=OuterRef("id")).order_by("-created").values('profile')[:1])
    chatrooms = ChatRoom.objects.annotate(chat_count=Count('chat_set')).filter(Q(chatroom_profile__profile=current_profile) &
                                        Q(chat_count__gt = 0) &
                                        ~Q(chatroom_profile__last_seen=latest_chat) & 
                                        ~Q(chatroom_profile__profile=latest_chat_profile))
    if chatrooms.exists():
        return Response({'type': 'un_seen'})
    else:
        return Response({'type': 'seen'})
