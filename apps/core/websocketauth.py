"""JWT authentication middleware for Django Channels WebSocket connections."""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user(user_id):
    """Return an active user for a SimpleJWT user claim, or an anonymous user."""
    user_model = get_user_model()
    try:
        return user_model.objects.get(pk=user_id, is_active=True)
    except user_model.DoesNotExist:
        return AnonymousUser()


class JwtWebSocketAuthMiddleware(BaseMiddleware):
    """Attach the JWT user from ``?token=`` to ``scope['user']``."""

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope["user"] = AnonymousUser()

        query = parse_qs(scope.get("query_string", b"").decode("utf-8"))
        raw_token = query.get("token", [None])[0]

        if raw_token:
            try:
                token = AccessToken(raw_token)
                user_id = token[api_settings.USER_ID_CLAIM]
                scope["user"] = await get_user(user_id)
            except (KeyError, TokenError):
                # Invalid or expired tokens connect as anonymous users.
                pass

        return await super().__call__(scope, receive, send)
