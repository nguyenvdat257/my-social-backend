from insta_server.celery import app
import channels.layers
from asgiref.sync import sync_to_async, async_to_sync
from celery import shared_task
from .models import Notification
import json

@shared_task
def send_noti(noti_id):
    # layer = channels.layers.get_channel_layer()
    # noti = Notification.objects.get(pk=noti_id)
    # receiver_username = noti.receiver_profile.user.username
    # async_to_sync(layer.group_send)('user_%s' % receiver_username, 
    #     {'type': 'noti_alarm'}
    # )
    return True