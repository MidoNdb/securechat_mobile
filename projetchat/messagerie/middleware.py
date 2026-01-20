# messagerie/middleware.py
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.authentication import JWTAuthentication


class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        # 🔑 récupérer token depuis l'URL ?token=xxx
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token")

        if token:
            token = token[0]
            user = await self.get_user(token)
            if user:
                scope["user"] = user

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
            return JWTAuthentication().get_user(validated_token)
        except Exception as e:
            print("❌ JWT invalide :", e)
            return None
