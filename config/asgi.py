"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter



os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


django_asgi_app = get_asgi_application()

# Initialize Django before imports that touch authentication models.
from django.conf import settings
from channels.security.websocket import OriginValidator
from apps.core.websocketauth import JwtWebSocketAuthMiddleware
from .routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": OriginValidator(
        JwtWebSocketAuthMiddleware(URLRouter(websocket_urlpatterns)),
        settings.AI_WEBSOCKET_ALLOWED_ORIGINS,
    ),
})
