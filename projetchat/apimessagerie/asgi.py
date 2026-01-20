"""
═══════════════════════════════════════════════════════════
ASGI Configuration avec support WebSocket Sécurisé (WSS)
═══════════════════════════════════════════════════════════
"""
import os
import django

# ⚠️ IMPORTANT: Configurer Django AVANT tous les imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apimessagerie.settings")
django.setup()

# Maintenant importer les modules Django/Channels
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from messagerie.routing import websocket_urlpatterns
from messagerie.middleware import JwtAuthMiddleware

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # HTTP/HTTPS
    "http": django_asgi_app,
    
    # WebSocket/WebSocket Secure
    "websocket": AllowedHostsOriginValidator(  # ✅ Validation CORS
        JwtAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})

print("✅ ASGI Application configurée avec support WSS")