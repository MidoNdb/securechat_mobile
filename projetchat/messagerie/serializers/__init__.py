# messagerie/serializers/__init__.py

"""
Serializers pour l'application messagerie
Centralise tous les serializers pour faciliter les imports
"""

# ============================================
# CONTACT SERIALIZERS
# ============================================
from .contact_serializers import (
    UserSuggestionSerializer,
    ContactListSerializer,
    ContactDetailSerializer,
    ContactCreateSerializer,
    ContactUpdateSerializer,
)

# ============================================
# CONVERSATION SERIALIZERS
# ============================================
from .conversation_serializers import (
    ConversationParticipantSerializer,
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    ConversationUpdateSerializer,
)

# ============================================
# MESSAGE SERIALIZERS
# ============================================
from .message_serializers import (
    MessageListSerializer,
    MessageDetailSerializer,
    MessageCreateSerializer,
    MessageDeleteSerializer,
)

# ============================================
# MESSAGE STATUS SERIALIZERS
# ============================================
from .message_status_serializers import (
    MessageStatusSerializer,
    MessageStatusListSerializer,
    MessageStatusDetailSerializer,
    MessageStatusUpdateSerializer,
)

# ============================================
# MEDIA SERIALIZERS (si le fichier existe)
# ============================================
# Décommente quand tu auras créé media_serializers.py
# from .media_serializers import (
#     MediaSerializer,
#     MediaUploadSerializer,
# )


# ============================================
# EXPORTS
# ============================================
__all__ = [
    # Contact
    'UserSuggestionSerializer',
    'ContactListSerializer',
    'ContactDetailSerializer',
    'ContactCreateSerializer',
    'ContactUpdateSerializer',
    
    # Conversation
    'ConversationParticipantSerializer',
    'ConversationListSerializer',
    'ConversationDetailSerializer',
    'ConversationCreateSerializer',
    'ConversationUpdateSerializer',
    
    # Message
    'MessageListSerializer',
    'MessageDetailSerializer',
    'MessageCreateSerializer',
    'MessageDeleteSerializer',
    
    # Message Status
    'MessageStatusSerializer',
    'MessageStatusListSerializer',
    'MessageStatusDetailSerializer',
    'MessageStatusUpdateSerializer',
    
    # Media (quand disponible)
    # 'MediaSerializer',
    # 'MediaUploadSerializer',
]


# """
# Serializers pour l'application messagerie
# Import uniquement ce qui existe réellement
# """

# # Laisser vide pour l'instant ou importer seulement ce qui existe
# # Les ViewSets importeront directement depuis les fichiers individuels
# from .contact_serializers import *
# from .conversation_serializers import *
# from .message_serializers import *
# from .message_status_serializers import *
# from .media_serializers import *
# __all__ = [
#     'contact_serializers',
#     'conversation_serializer',    
#     'message_serializer',
#     'media_serializer',
#     'message_status_serializer',
# ]


