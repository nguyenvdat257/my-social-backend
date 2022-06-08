from .my_imports import *


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification(request):
    new_noti = Notification.objects.filter(
        receiver_profile=request.user.profile).filter(created__gt=timezone.now() - timezone.timedelta(days=60)).order_by('-created')

    serializer = NotificationSerializer(new_noti, many=True)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def seen_notification(request):
    Notification.objects.filter(
    receiver_profile=request.user.profile).filter(user_seen=False).update(user_seen=True)
    return Response('Successfully seen notification')
