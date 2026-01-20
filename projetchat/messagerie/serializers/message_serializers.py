# messagerie/serializers/message_serializers.py
# ✅ REMPLACE TON FICHIER message_serializers.py AVEC CE CODE COMPLET

from rest_framework import serializers
from messagerie.models.message import Message
from messagerie.models.conversation import Conversation, ConversationParticipant
from messagerie.models.message_status import MessageStatus
from authentification.models import User
from django.db import transaction
from django.utils import timezone


# ========================================
# MessageListSerializer (Liste messages)
# ========================================
class MessageListSerializer(serializers.ModelSerializer):
    """
    Serializer pour liste de messages
    Utilisé par GET /api/messages/conversation/{id}/
    """
    
    sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
    sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
    
    # ✅ CORRECTION CRITIQUE : Mapper au ForeignKey recipient_user
    recipient_user_id = serializers.SerializerMethodField()
    
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_id',
            'sender_name',
            'recipient_user_id',  # ✅ IMPORTANT
            'type',
            # ✅ Champs E2EE COMPLETS
            'encrypted_content',
            'nonce',
            'auth_tag',
            'signature',
            # Autres
            'metadata',
            'is_mine',
            'is_deleted',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_recipient_user_id(self, obj):
        """Retourner l'UUID du destinataire"""
        if obj.recipient_user:
            return str(obj.recipient_user.user_id)
        return None

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.from_user == request.user
        return False

# ========================================
# MessageDetailSerializer
# ========================================

class MessageDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour détail d'un message
    """
    
    sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
    sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
    
    # ✅ CORRECTION CRITIQUE
    recipient_user_id = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_id',
            'sender_name',
            'recipient_user_id',  # ✅ AJOUT
            'type',
            # Champs E2EE
            'encrypted_content',
            'nonce',
            'auth_tag',
            'signature',
            # Autres
            'metadata',
            'reply_to',
            'is_deleted',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_recipient_user_id(self, obj):
        """Retourner l'UUID du destinataire"""
        if obj.recipient_user:
            return str(obj.recipient_user.user_id)
        return None


# ========================================
# MessageCreateSerializer (pas de changement)
# ========================================

class MessageCreateSerializer(serializers.Serializer):
    """Serializer pour créer un message"""
    
    conversation_id = serializers.UUIDField(required=True)
    recipient_user_id = serializers.UUIDField(required=True)
    type = serializers.ChoiceField(choices=Message.Type.choices, default=Message.Type.TEXT)
    
    # Champs E2EE
    encrypted_content = serializers.CharField(required=True)
    nonce = serializers.CharField(required=True, max_length=255)
    auth_tag = serializers.CharField(required=True, max_length=255)
    signature = serializers.CharField(required=True)
    
    metadata = serializers.JSONField(required=False, allow_null=True)
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_conversation_id(self, value):
        request = self.context.get('request')
        if not Conversation.objects.filter(id=value, participants__user=request.user).exists():
            raise serializers.ValidationError("Conversation non trouvée")
        return value
    
    def validate_recipient_user_id(self, value):
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Destinataire introuvable")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        recipient_user = User.objects.get(user_id=validated_data['recipient_user_id'])
        
        message = Message.objects.create(
            conversation_id=validated_data['conversation_id'],
            from_user=request.user,
            recipient_user=recipient_user,  # ✅ IMPORTANT
            type=validated_data['type'],
            encrypted_content=validated_data['encrypted_content'],
            nonce=validated_data['nonce'],
            auth_tag=validated_data['auth_tag'],
            signature=validated_data['signature'],
            metadata=validated_data.get('metadata'),
            reply_to_id=validated_data.get('reply_to_id'),
        )
        
        print(f'✅ Message créé: {message.id}')
        print(f'   Pour: {recipient_user.phone_number}')
        
        return message


# ========================================
# MessageDetailSerializer (Détail message)
# ========================================

class MessageDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour détail d'un message
    Retourne TOUS les champs nécessaires pour déchiffrement
    """
    
    sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
    sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
    sender_phone = serializers.CharField(source='from_user.phone_number', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_id',
            'sender_name',
            'sender_phone',
            'recipient_user_id',
            'type',
            # ✅ CHAMPS E2EE COMPLETS
            'encrypted_content',
            'nonce',
            'auth_tag',
            'signature',
            # Autres
            'metadata',
            'reply_to',
            'is_deleted',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# # ========================================
# # MessageCreateSerializer (Envoi message)
# # ========================================

# class MessageCreateSerializer(serializers.Serializer):
#     """
#     Serializer pour créer un nouveau message chiffré
    
#     Utilisé par POST /api/messages/
    
#     Body attendu:
#     {
#         "conversation_id": "uuid",
#         "recipient_user_id": "uuid",  ← AJOUTÉ
#         "type": "TEXT",
#         "encrypted_content": "base64...",
#         "nonce": "base64...",
#         "auth_tag": "base64...",
#         "signature": "base64...",
#         "metadata": {...}  // optionnel
#     }
#     """
    
#     conversation_id = serializers.UUIDField(required=True)
#     recipient_user_id = serializers.UUIDField(required=True)  # ✅ AJOUT
#     type = serializers.ChoiceField(choices=Message.Type.choices, default=Message.Type.TEXT)
    
#     # ✅ CHAMPS E2EE OBLIGATOIRES
#     encrypted_content = serializers.CharField(
#         required=True,
#         help_text="Ciphertext AES-256-GCM en Base64"
#     )
#     nonce = serializers.CharField(
#         required=True,
#         max_length=255,
#         help_text="Nonce AES-GCM en Base64"
#     )
#     auth_tag = serializers.CharField(
#         required=True,
#         max_length=255,
#         help_text="Auth tag AES-GCM en Base64"
#     )
#     signature = serializers.CharField(
#         required=True,
#         help_text="Signature Ed25519 en Base64"
#     )
    
#     # Optionnels
#     metadata = serializers.JSONField(required=False, allow_null=True)
#     reply_to_id = serializers.UUIDField(required=False, allow_null=True)

#     def validate_conversation_id(self, value):
#         """Vérifie que la conversation existe et que user y a accès"""
#         request = self.context.get('request')
        
#         if not Conversation.objects.filter(
#             id=value,
#             participants__user=request.user
#         ).exists():
#             raise serializers.ValidationError(
#                 "Conversation non trouvée ou accès refusé"
#             )
        
#         return value
    
#     def validate_recipient_user_id(self, value):
#         """Vérifie que le destinataire existe"""
#         if not User.objects.filter(user_id=value).exists():
#             raise serializers.ValidationError("Destinataire introuvable")
#         return value

#     def validate_reply_to_id(self, value):
#         """Vérifie que le message de réponse existe"""
#         if value and not Message.objects.filter(id=value).exists():
#             raise serializers.ValidationError("Message de réponse introuvable")
#         return value

#     @transaction.atomic
#     def create(self, validated_data):
#         """
#         Crée le message + statuts pour tous les participants
#         """
#         request = self.context.get('request')
        
#         # ✅ AJOUT : Récupérer recipient_user
#         recipient_user = User.objects.get(user_id=validated_data['recipient_user_id'])
        
#         # Créer le message
#         message = Message.objects.create(
#             conversation_id=validated_data['conversation_id'],
#             from_user=request.user,
#             recipient_user=recipient_user,  # ✅ AJOUT
#             type=validated_data['type'],
#             # ✅ CHAMPS E2EE
#             encrypted_content=validated_data['encrypted_content'],
#             nonce=validated_data['nonce'],
#             auth_tag=validated_data['auth_tag'],
#             signature=validated_data['signature'],
#             # Optionnels
#             metadata=validated_data.get('metadata'),
#             reply_to_id=validated_data.get('reply_to_id'),
#         )
        
#         # Créer MessageStatus pour tous les participants (sauf expéditeur)
#         participants = ConversationParticipant.objects.filter(
#             conversation=message.conversation
#         ).exclude(user=request.user)

#         MessageStatus.objects.bulk_create([
#             MessageStatus(
#                 message=message,
#                 user=participant.user,
#                 status=MessageStatus.Status.SENT,
#                 created_at=timezone.now()
#             )
#             for participant in participants
#         ])
        
#         print(f'✅ Message créé: {message.id} dans conversation {message.conversation.id}')
#         print(f'   Chiffré pour: {recipient_user.phone_number}')
        
#         return message


# ========================================
# MessageDeleteSerializer
# ========================================

class MessageDeleteSerializer(serializers.Serializer):
    """Serializer pour suppression de message"""
    
    id = serializers.UUIDField()

    def validate_id(self, value):
        """Vérifie que le message existe"""
        try:
            
            Message.objects.get(id=value)
        except Message.DoesNotExist:
            raise serializers.ValidationError("Message introuvable")
        return value



# from rest_framework import serializers
# from messagerie.models.message import Message, MessageKey
# from messagerie.models.conversation import Conversation, ConversationParticipant
# from authentification.models import User
# from django.db import transaction
# from django.utils import timezone

# class MessageKeySerializer(serializers.ModelSerializer):
#     user_id = serializers.UUIDField(source='user.user_id')

#     class Meta:
#         model = MessageKey
#         fields = ['id', 'user_id', 'encrypted_key']
#         read_only_fields = ['id']

# # --------------------------
# # MessageListSerializer
# # --------------------------
# class MessageListSerializer(serializers.ModelSerializer):
#     sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
#     is_mine = serializers.SerializerMethodField()

#     class Meta:
#         model = Message
#         fields = ['id', 'conversation', 'type', 'encrypted_content', 'metadata', 'is_mine', 'created_at']

#     def get_is_mine(self, obj):
#         request = self.context.get('request')
#         return obj.from_user == request.user if request and request.user else False

# # --------------------------
# # MessageDetailSerializer
# # --------------------------
# class MessageDetailSerializer(serializers.ModelSerializer):
#     keys = MessageKeySerializer(many=True, read_only=True)  # 🔹 ton champ

#     class Meta:
#         model = Message
#         # Assure-toi que 'keys' est inclus ici !
#         fields = [
#             'id',
#             'conversation',
#             'from_user',
#             'encrypted_content',
#             'created_at',
#             'keys',  # 🔹 obligatoire
#         ]
# # --------------------------
# # MessageCreateSerializer
# # --------------------------
# class MessageCreateSerializer(serializers.Serializer):
#     conversation_id = serializers.UUIDField()
#     type = serializers.ChoiceField(choices=Message.Type.choices)
#     encrypted_content = serializers.CharField()
#     keys = serializers.ListField(child=serializers.DictField())
#     metadata = serializers.JSONField(required=False, allow_null=True)

#     def validate(self, data):
#         # Validation simplifiée
#         return data

#     @transaction.atomic
#     def create(self, validated_data):
#         request = self.context.get('request')
#         message = Message.objects.create(
#             conversation_id=validated_data['conversation_id'],
#             from_user=request.user,
#             type=validated_data['type'],
#             encrypted_content=validated_data['encrypted_content'],
#             metadata=validated_data.get('metadata')
#         )
#         return message

# # --------------------------
# # MessageDeleteSerializer
# # --------------------------
# class MessageDeleteSerializer(serializers.Serializer):
#     id = serializers.UUIDField()
#     def validate_id(self, value):
#         try:
#             Message.objects.get(id=value)
#         except Message.DoesNotExist:
#             raise serializers.ValidationError("Message introuvable")
#         return value
