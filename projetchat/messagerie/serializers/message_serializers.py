# messagerie/serializers/message_serializers.py
# ✅ VERSION COMPLÈTE AVEC VALIDATION DE TAILLE + TOUS LES SERIALIZERS

from rest_framework import serializers
from messagerie.models.message import Message
from messagerie.models.conversation import Conversation
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
    recipient_user_id = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_id',
            'sender_name',
            'recipient_user_id',
            'type',
            # Champs E2EE COMPLETS
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
# MessageDetailSerializer (Détail message)
# ========================================
class MessageDetailSerializer(serializers.ModelSerializer):
    sender_id = serializers.CharField(source='from_user.user_id', read_only=True)
    sender_name = serializers.SerializerMethodField()
    
    # ✅ AJOUT CRITIQUE
    recipient_user_id = serializers.CharField(source='recipient_user.user_id', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id',
            'conversation_id',
            'sender_id',
            'recipient_user_id',  # ✅ AJOUTÉ
            'sender_name',
            'encrypted_content',
            'nonce',
            'auth_tag',
            'signature',
            'type',
            'created_at',
            'is_deleted',
            'metadata',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_sender_name(self, obj):
        return obj.from_user.display_name or obj.from_user.phone_number


# class MessageDetailSerializer(serializers.ModelSerializer):
#     """
#     Serializer pour détail d'un message
#     Retourne TOUS les champs nécessaires pour déchiffrement
#     """
    
#     sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
#     sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
#     sender_phone = serializers.CharField(source='from_user.phone_number', read_only=True)
#     recipient_user_id = serializers.SerializerMethodField()

#     class Meta:
#         model = Message
#         fields = [
#             'id',
#             'conversation',
#             'sender_id',
#             'sender_name',
#             'sender_phone',
#             'recipient_user_id',
#             'type',
#             # Champs E2EE COMPLETS
#             'encrypted_content',
#             'nonce',
#             'auth_tag',
#             'signature',
#             # Autres
#             'metadata',
#             'reply_to',
#             'is_deleted',
#             'created_at',
#         ]
#         read_only_fields = ['id', 'created_at']

#     def get_recipient_user_id(self, obj):
#         """Retourner l'UUID du destinataire"""
#         if obj.recipient_user:
#             return str(obj.recipient_user.user_id)
#         return None


# ========================================
# MessageCreateSerializer (Création message)
# ========================================
class MessageCreateSerializer(serializers.Serializer):
    """Serializer pour créer un message"""
    
    conversation_id = serializers.UUIDField(required=True)
    recipient_user_id = serializers.UUIDField(required=True)
    type = serializers.ChoiceField(
        choices=Message.Type.choices, 
        default=Message.Type.TEXT
    )
    
    # Champs E2EE
    encrypted_content = serializers.CharField(required=True)
    nonce = serializers.CharField(required=True, max_length=255)
    auth_tag = serializers.CharField(required=True, max_length=255)
    signature = serializers.CharField(required=True)
    
    metadata = serializers.JSONField(required=False, allow_null=True)
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)

    # ========================================
    # ✅ VALIDATION DE TAILLE PAR TYPE
    # ========================================
    def validate(self, attrs):
        """Valide la taille du contenu selon le type"""
        msg_type = attrs.get('type')
        encrypted_content = attrs.get('encrypted_content', '')
        
        # Calcul taille en bytes
        content_size = len(encrypted_content.encode('utf-8'))
        
        # Limites par type (après Base64, donc ~33% plus grand)
        MAX_SIZES = {
            'TEXT': 10 * 1024,              # 10 KB
            'IMAGE': 8 * 1024 * 1024,       # 8 MB (permet 6MB image originale)
            'VOICE': 3 * 1024 * 1024,       # 3 MB
            'VIDEO': 15 * 1024 * 1024,      # 15 MB
            'FILE': 15 * 1024 * 1024,       # 15 MB
        }
        
        max_size = MAX_SIZES.get(msg_type, 10 * 1024 * 1024)
        
        if content_size > max_size:
            max_mb = max_size / (1024 * 1024)
            current_mb = content_size / (1024 * 1024)
            raise serializers.ValidationError(
                f"Le contenu est trop volumineux pour le type {msg_type}. "
                f"Taille actuelle: {current_mb:.2f} MB, "
                f"Maximum autorisé: {max_mb:.1f} MB"
            )
        
        print(f"✅ Validation taille OK: {content_size / 1024:.1f} KB pour type {msg_type}")
        
        return attrs

    def validate_conversation_id(self, value):
        request = self.context.get('request')
        if not Conversation.objects.filter(
            id=value, 
            participants__user=request.user
        ).exists():
            raise serializers.ValidationError("Conversation non trouvée")
        return value
    
    def validate_recipient_user_id(self, value):
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Destinataire introuvable")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        recipient_user = User.objects.get(
            user_id=validated_data['recipient_user_id']
        )
        
        message = Message.objects.create(
            conversation_id=validated_data['conversation_id'],
            from_user=request.user,
            recipient_user=recipient_user,
            type=validated_data['type'],
            encrypted_content=validated_data['encrypted_content'],
            nonce=validated_data['nonce'],
            auth_tag=validated_data['auth_tag'],
            signature=validated_data['signature'],
            metadata=validated_data.get('metadata'),
            reply_to_id=validated_data.get('reply_to_id'),
        )
        
        print(f'✅ Message {validated_data["type"]} créé: {message.id}')
        print(f'   Pour: {recipient_user.phone_number}')
        
        return message


# ========================================
# MessageUpdateSerializer (Mise à jour message)
# ========================================
class MessageUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mettre à jour un message
    Permet seulement de modifier certains champs
    """
    
    class Meta:
        model = Message
        fields = ['is_deleted', 'metadata']
    
    def update(self, instance, validated_data):
        """Mise à jour partielle du message"""
        instance.is_deleted = validated_data.get('is_deleted', instance.is_deleted)
        instance.metadata = validated_data.get('metadata', instance.metadata)
        instance.save()
        
        print(f'✅ Message mis à jour: {instance.id}')
        
        return instance


# ========================================
# MessageDeleteSerializer (Suppression message)
# ========================================
class MessageDeleteSerializer(serializers.Serializer):
    """
    Serializer pour supprimer un message
    Marque le message comme supprimé (soft delete)
    """
    
    delete_for_everyone = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Valide que l'utilisateur peut supprimer le message"""
        message = self.instance
        request = self.context.get('request')
        
        # Vérifier que l'utilisateur est l'expéditeur
        if message.from_user != request.user:
            raise serializers.ValidationError(
                "Vous ne pouvez supprimer que vos propres messages"
            )
        
        # Si suppression pour tout le monde, vérifier le délai
        if attrs.get('delete_for_everyone', False):
            time_limit = timezone.now() - timezone.timedelta(hours=1)
            if message.created_at < time_limit:
                raise serializers.ValidationError(
                    "Vous ne pouvez supprimer pour tout le monde que dans l'heure suivant l'envoi"
                )
        
        return attrs
    
    def save(self):
        """Marque le message comme supprimé"""
        message = self.instance
        message.is_deleted = True
        message.save()
        
        print(f'✅ Message supprimé: {message.id}')
        
        return message


# ========================================
# MessageStatusSerializer (Statut message)
# ========================================
class MessageStatusSerializer(serializers.ModelSerializer):
    """
    Serializer pour les statuts de message (lu, livré, etc.)
    """
    
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    
    class Meta:
        model = MessageStatus
        fields = [
            'id',
            'message',
            'user_id',
            'user_name',
            'status',
            'read_at',
            'delivered_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ========================================
# MessageStatusUpdateSerializer (MAJ statut)
# ========================================
class MessageStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer pour mettre à jour le statut d'un message
    """
    
    status = serializers.ChoiceField(
        choices=['delivered', 'read'],
        required=True
    )
    
    def validate(self, attrs):
        """Valide que l'utilisateur peut mettre à jour le statut"""
        message = self.context.get('message')
        request = self.context.get('request')
        
        # Vérifier que l'utilisateur est le destinataire
        if message.recipient_user != request.user:
            raise serializers.ValidationError(
                "Vous ne pouvez mettre à jour que le statut de vos propres messages reçus"
            )
        
        return attrs
    
    def update(self, instance, validated_data):
        """Met à jour le statut du message"""
        status = validated_data.get('status')
        
        if status == 'delivered' and not instance.delivered_at:
            instance.status = 'delivered'
            instance.delivered_at = timezone.now()
        elif status == 'read' and not instance.read_at:
            instance.status = 'read'
            instance.read_at = timezone.now()
            # Si marqué comme lu, il est aussi livré
            if not instance.delivered_at:
                instance.delivered_at = timezone.now()
        
        instance.save()
        
        print(f'✅ Statut message mis à jour: {instance.message_id} → {status}')
        
        return instance


# ========================================
# MessageReactionSerializer (Réactions)
# ========================================
class MessageReactionSerializer(serializers.Serializer):
    """
    Serializer pour les réactions aux messages (👍, ❤️, etc.)
    Optionnel pour version future
    """
    
    message_id = serializers.UUIDField(required=True)
    reaction = serializers.CharField(max_length=10, required=True)
    
    def validate_reaction(self, value):
        """Valide que la réaction est autorisée"""
        allowed_reactions = ['👍', '❤️', '😂', '😮', '😢', '🙏']
        if value not in allowed_reactions:
            raise serializers.ValidationError(
                f"Réaction non autorisée. Utilisez: {', '.join(allowed_reactions)}"
            )
        return value
    
    def create(self, validated_data):
        """Ajoute une réaction à un message"""
        message_id = validated_data['message_id']
        reaction = validated_data['reaction']
        request = self.context.get('request')
        
        message = Message.objects.get(id=message_id)
        
        # Mettre à jour les métadonnées avec la réaction
        if not message.metadata:
            message.metadata = {}
        
        if 'reactions' not in message.metadata:
            message.metadata['reactions'] = {}
        
        user_id = str(request.user.user_id)
        message.metadata['reactions'][user_id] = reaction
        message.save()
        
        print(f'✅ Réaction ajoutée: {reaction} sur message {message_id}')
        
        return message



# # messagerie/serializers/message_serializers.py
# # ✅ REMPLACE TON FICHIER message_serializers.py AVEC CE CODE COMPLET

# from rest_framework import serializers
# from messagerie.models.message import Message
# from messagerie.models.conversation import Conversation, ConversationParticipant
# from messagerie.models.message_status import MessageStatus
# from authentification.models import User
# from django.db import transaction
# from django.utils import timezone


# # ========================================
# # MessageListSerializer (Liste messages)
# # ========================================
# class MessageListSerializer(serializers.ModelSerializer):
#     """
#     Serializer pour liste de messages
#     Utilisé par GET /api/messages/conversation/{id}/
#     """
    
#     sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
#     sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
    
#     # ✅ CORRECTION CRITIQUE : Mapper au ForeignKey recipient_user
#     recipient_user_id = serializers.SerializerMethodField()
    
#     is_mine = serializers.SerializerMethodField()

#     class Meta:
#         model = Message
#         fields = [
#             'id',
#             'conversation',
#             'sender_id',
#             'sender_name',
#             'recipient_user_id',  # ✅ IMPORTANT
#             'type',
#             # ✅ Champs E2EE COMPLETS
#             'encrypted_content',
#             'nonce',
#             'auth_tag',
#             'signature',
#             # Autres
#             'metadata',
#             'is_mine',
#             'is_deleted',
#             'created_at',
#         ]
#         read_only_fields = ['id', 'created_at']

#     def get_recipient_user_id(self, obj):
#         """Retourner l'UUID du destinataire"""
#         if obj.recipient_user:
#             return str(obj.recipient_user.user_id)
#         return None

#     def get_is_mine(self, obj):
#         request = self.context.get('request')
#         if request and request.user:
#             return obj.from_user == request.user
#         return False

# # ========================================
# # MessageDetailSerializer
# # ========================================

# class MessageDetailSerializer(serializers.ModelSerializer):
#     """
#     Serializer pour détail d'un message
#     """
    
#     sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
#     sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
    
#     # ✅ CORRECTION CRITIQUE
#     recipient_user_id = serializers.SerializerMethodField()

#     class Meta:
#         model = Message
#         fields = [
#             'id',
#             'conversation',
#             'sender_id',
#             'sender_name',
#             'recipient_user_id',  # ✅ AJOUT
#             'type',
#             # Champs E2EE
#             'encrypted_content',
#             'nonce',
#             'auth_tag',
#             'signature',
#             # Autres
#             'metadata',
#             'reply_to',
#             'is_deleted',
#             'created_at',
#         ]
#         read_only_fields = ['id', 'created_at']

#     def get_recipient_user_id(self, obj):
#         """Retourner l'UUID du destinataire"""
#         if obj.recipient_user:
#             return str(obj.recipient_user.user_id)
#         return None


# # ========================================
# # MessageCreateSerializer (pas de changement)
# # ========================================

# class MessageCreateSerializer(serializers.Serializer):
#     """Serializer pour créer un message"""
    
#     conversation_id = serializers.UUIDField(required=True)
#     recipient_user_id = serializers.UUIDField(required=True)
#     type = serializers.ChoiceField(choices=Message.Type.choices, default=Message.Type.TEXT)
    
#     # Champs E2EE
#     encrypted_content = serializers.CharField(required=True)
#     nonce = serializers.CharField(required=True, max_length=255)
#     auth_tag = serializers.CharField(required=True, max_length=255)
#     signature = serializers.CharField(required=True)
    
#     metadata = serializers.JSONField(required=False, allow_null=True)
#     reply_to_id = serializers.UUIDField(required=False, allow_null=True)

#     def validate_conversation_id(self, value):
#         request = self.context.get('request')
#         if not Conversation.objects.filter(id=value, participants__user=request.user).exists():
#             raise serializers.ValidationError("Conversation non trouvée")
#         return value
    
#     def validate_recipient_user_id(self, value):
#         if not User.objects.filter(user_id=value).exists():
#             raise serializers.ValidationError("Destinataire introuvable")
#         return value

#     @transaction.atomic
#     def create(self, validated_data):
#         request = self.context.get('request')
#         recipient_user = User.objects.get(user_id=validated_data['recipient_user_id'])
        
#         message = Message.objects.create(
#             conversation_id=validated_data['conversation_id'],
#             from_user=request.user,
#             recipient_user=recipient_user,  # ✅ IMPORTANT
#             type=validated_data['type'],
#             encrypted_content=validated_data['encrypted_content'],
#             nonce=validated_data['nonce'],
#             auth_tag=validated_data['auth_tag'],
#             signature=validated_data['signature'],
#             metadata=validated_data.get('metadata'),
#             reply_to_id=validated_data.get('reply_to_id'),
#         )
        
#         print(f'✅ Message créé: {message.id}')
#         print(f'   Pour: {recipient_user.phone_number}')
        
#         return message


# # ========================================
# # MessageDetailSerializer (Détail message)
# # ========================================

# class MessageDetailSerializer(serializers.ModelSerializer):
#     """
#     Serializer pour détail d'un message
#     Retourne TOUS les champs nécessaires pour déchiffrement
#     """
    
#     sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
#     sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
#     sender_phone = serializers.CharField(source='from_user.phone_number', read_only=True)

#     class Meta:
#         model = Message
#         fields = [
#             'id',
#             'conversation',
#             'sender_id',
#             'sender_name',
#             'sender_phone',
#             'recipient_user_id',
#             'type',
#             # ✅ CHAMPS E2EE COMPLETS
#             'encrypted_content',
#             'nonce',
#             'auth_tag',
#             'signature',
#             # Autres
#             'metadata',
#             'reply_to',
#             'is_deleted',
#             'created_at',
#         ]
#         read_only_fields = ['id', 'created_at']

