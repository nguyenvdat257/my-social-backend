"""
ASGI config for insta_server project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import api.routing
from .middlewares.channelsmiddleware import JwtAuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insta_server.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': JwtAuthMiddlewareStack(
        URLRouter(
            api.routing.websocket_urlpatterns
        )
    )
})
