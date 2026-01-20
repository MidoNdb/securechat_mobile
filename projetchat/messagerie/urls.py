# messagerie/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from messagerie.views.contact_views import ContactViewSet
from messagerie.views.conversation_views import ConversationViewSet
from messagerie.views.message_views import MessageViewSet

# ========================================
# ROUTER DRF (routes CRUD standard)
# ========================================
router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

# ========================================
# URL PATTERNS
# ========================================
urlpatterns = [
    # ✅ IMPORTANT : Routes custom AVANT le router
    # Sinon le router intercepte avec son pattern générique
    
    # Route : GET /api/messages/conversation/{uuid}/
    path(
        'messages/conversation/<uuid:conversation_id>/',
        MessageViewSet.as_view({'get': 'by_conversation'}),
        name='messages-by-conversation'
    ),
    
    # Route : POST /api/messages/mark-read/
    path(
        'messages/mark-read/',
        MessageViewSet.as_view({'post': 'mark_read'}),
        name='messages-mark-read'
    ),
    
    # Routes du router (en dernier)
    # GET    /api/messages/
    # POST   /api/messages/
    # GET    /api/messages/{id}/
    # etc.
    path('', include(router.urls)),
]



# # messagerie/urls.py

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from messagerie.views.contact_views import ContactViewSet
# from messagerie.views.conversation_views import ConversationViewSet
# from messagerie.views.message_views import MessageViewSet
# from authentification.views import public_keys_view

# # Router DRF
# router = DefaultRouter()

# # ✅ Enregistrer ContactViewSet
# router.register(r'contacts', ContactViewSet, basename='contact')
# router.register(r'conversations', ConversationViewSet, basename='conversation')
# router.register(r'messages', MessageViewSet, basename='message')

# # URLs
# urlpatterns = [
#     path('api/', include(router.urls)),
#     path('api/users/<uuid:user_id>/public-keys/', public_keys_view, name='public-keys'),
# ]












# messagerie/urls.py

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views.conversation_views import ConversationViewSet
# from .views.message_views import MessageViewSet
# from .views.contact_views import ContactViewSet

# router = DefaultRouter()
# router.register(r'conversations', ConversationViewSet, basename='conversation')
# router.register(r'messages', MessageViewSet, basename='message')
# router.register(r'contacts', ContactViewSet, basename='contact')

# urlpatterns = [
#     path('', include(router.urls)),
# ]


# """
# URLs pour l'application messagerie
# """
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter

# # ✅ Import DIRECT depuis les fichiers (pas depuis __init__.py)
# from messagerie.views.conversation_views import ConversationViewSet
# from messagerie.views.message_views import MessageViewSet
# from messagerie.views.message_status_views import MessageStatusViewSet
# from messagerie.views.contact_views import ContactViewSet
# from messagerie.views.media_views import MediaViewSet
# from authentification.views import public_keys_view # Import de la fonction

# # Router DRF
# router = DefaultRouter()

# # Enregistrer les ViewSets
# router.register(r'conversations', ConversationViewSet, basename='conversation')
# router.register(r'messages', MessageViewSet, basename='message')
# router.register(r'message-statuses', MessageStatusViewSet, basename='message-status')
# router.register(r'contacts', ContactViewSet, basename='contact')
# router.register(r'media', MediaViewSet, basename='media')

# # URLs
# urlpatterns = [
#     path('api/', include(router.urls)),
#     path('api/users/<uuid:user_id>/public-keys/', public_keys_view, name='public-keys'),
# ]