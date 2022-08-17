from .my_imports import *


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification(request):
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.NOTIFICATION_SIZE
    new_notis = Notification.objects.filter(
        receiver_profile=request.user.profile).filter(created__gt=timezone.now() - timezone.timedelta(days=60)).order_by('-created')

    result_page = paginator.paginate_queryset(new_notis, request)
    serializer = NotificationSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def seen_notification(request):
    if request.method == 'PUT':
        Notification.objects.filter(
        receiver_profile=request.user.profile).filter(user_seen=False).update(user_seen=True)
        return Response('Successfully seen notification')

    if request.method == 'GET':
        if Notification.objects.filter(receiver_profile=request.user.profile).filter(user_seen=False).exists():
            return Response(data={'type': 'un_seen'})
        return Response(data={'type': 'seen'})
