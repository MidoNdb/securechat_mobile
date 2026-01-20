# messagerie/routing.py
from django.urls import path
from messagerie.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/", ChatConsumer.as_asgi()),
]
