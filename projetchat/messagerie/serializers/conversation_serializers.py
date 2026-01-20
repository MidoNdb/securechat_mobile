# messagerie/serializers/conversation_serializers.py

from rest_framework import serializers
from messagerie.models.conversation import Conversation, ConversationParticipant
from messagerie.models.contact import Contact
from messagerie.models.message import Message
from authentification.models import User
from django.db import transaction


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer pour les participants - NE PAS EXPOSER display_name"""
    user_id = serializers.UUIDField(source='user.user_id', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    is_online = serializers.BooleanField(source='user.is_online', read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'id', 'user_id', 'phone_number',
            'role', 'joined_at', 'is_muted', 'is_archived', 'is_online'
        ]
        read_only_fields = ['id', 'joined_at']


# ========================================
# ✅ SERIALIZER POUR DERNIER MESSAGE (CORRIGÉ)
# ========================================

class LastMessageSerializer(serializers.ModelSerializer):
    """
    Serializer pour le dernier message dans la liste des conversations
    ✅ DOIT inclure TOUS les champs E2EE pour permettre le déchiffrement
    """
    sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
    sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
    
    # ✅ AJOUT CRITIQUE : recipient_user_id pour le déchiffrement
    recipient_user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'sender_id',
            'sender_name',
            'recipient_user_id',  # ✅ AJOUTÉ
            'type',
            # ✅ CHAMPS E2EE COMPLETS (CRITIQUES)
            'encrypted_content',
            'nonce',              # ✅ AJOUTÉ
            'auth_tag',           # ✅ AJOUTÉ
            'signature',          # ✅ AJOUTÉ
            # Dates
            'created_at',
        ]
    
    def get_recipient_user_id(self, obj):
        """Retourner l'UUID du destinataire"""
        if obj.recipient_user:
            return str(obj.recipient_user.user_id)
        return None


# ========================================
# ✅ CONVERSATION LIST (SANS CHANGEMENT)
# ========================================

class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste - Display name basé sur CONTACT uniquement"""
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    # ✅ Inclure le dernier message avec TOUS les champs E2EE
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'type', 'name', 'display_name', 'participants',
            'participant_count', 'unread_count', 
            'last_message',
            'last_message_at', 'created_at'
        ]
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_unread_count(self, obj):
        # TODO: Implémenter le vrai compteur
        return 0
    
    def get_last_message(self, obj):
        """
        ✅ Retourne le dernier message avec TOUS les champs E2EE
        """
        # Chercher le dernier message
        last_msg = obj.messages.select_related('from_user', 'recipient_user').order_by('-created_at').first()
        
        if last_msg:
            return LastMessageSerializer(
                last_msg,
                context=self.context
            ).data
        
        return None
    
    def get_display_name(self, obj):
        """
        ✅ SÉCURISÉ: Nickname OU Numéro (JAMAIS nom système)
        """
        request = self.context.get('request')
        
        if obj.type == Conversation.Type.GROUP:
            return obj.name or 'Groupe'
        
        # DIRECT: trouve l'autre participant
        if not request:
            return None
        
        other_participant = obj.participants.exclude(
            user=request.user
        ).select_related('user').first()
        
        if not other_participant:
            return None
        
        other_user = other_participant.user
        
        # ✅ Cherche le contact pour nickname
        try:
            contact = Contact.objects.get(
                user=request.user,
                contact_user=other_user,
                is_deleted=False
            )
            
            if contact.nickname and contact.nickname.strip():
                return contact.nickname.strip()
        except Contact.DoesNotExist:
            pass
        
        # Pas de nickname → Numéro
        return other_user.phone_number


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé - Participants sans noms"""
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = LastMessageSerializer(read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'type', 'name', 'participants',
            'last_message',
            'created_at', 'last_message_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_message_at']


class ConversationCreateSerializer(serializers.Serializer):
    """Serializer pour créer"""
    type = serializers.ChoiceField(choices=Conversation.Type.choices)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    
    def validate(self, data):
        conv_type = data.get('type')
        participant_ids = data.get('participant_ids', [])
        
        if conv_type == Conversation.Type.DIRECT and len(participant_ids) != 1:
            raise serializers.ValidationError('DIRECT nécessite 1 participant')
        
        if conv_type == Conversation.Type.GROUP and not data.get('name'):
            raise serializers.ValidationError('Nom requis pour GROUP')
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        conv_type = validated_data['type']
        participant_ids = validated_data['participant_ids']
        name = validated_data.get('name', '').strip() or None
        
        # Vérifier si conversation DIRECTE existe déjà
        if conv_type == Conversation.Type.DIRECT:
            other_user_id = participant_ids[0]
            
            existing = Conversation.objects.filter(
                type=Conversation.Type.DIRECT,
                participants__user=request.user
            ).filter(
                participants__user__user_id=other_user_id
            ).distinct().first()
            
            if existing:
                print(f'✅ Conversation existante trouvée: {existing.id}')
                return existing
        
        # Créer nouvelle conversation
        conversation = Conversation.objects.create(
            type=conv_type,
            name=name,
            created_by=request.user
        )
        
        # Ajouter user actuel
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user,
            role=ConversationParticipant.Role.ADMIN
        )
        
        # Ajouter autres participants
        for user_id in participant_ids:
            user = User.objects.get(user_id=user_id)
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=user,
                role=ConversationParticipant.Role.MEMBER
            )
        
        print(f'✅ Nouvelle conversation créée: {conversation.id}')
        return conversation


class ConversationUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour modifier"""
    class Meta:
        model = Conversation
        fields = ['name']




# # messagerie/serializers/conversation_serializers.py

# from rest_framework import serializers
# from messagerie.models.conversation import Conversation, ConversationParticipant
# from messagerie.models.contact import Contact
# from messagerie.models.message import Message
# from authentification.models import User
# from django.db import transaction


# class ConversationParticipantSerializer(serializers.ModelSerializer):
#     """Serializer pour les participants - NE PAS EXPOSER display_name"""
#     user_id = serializers.UUIDField(source='user.user_id', read_only=True)
#     phone_number = serializers.CharField(source='user.phone_number', read_only=True)
#     is_online = serializers.BooleanField(source='user.is_online', read_only=True)
    
#     class Meta:
#         model = ConversationParticipant
#         fields = [
#             'id', 'user_id', 'phone_number',
#             'role', 'joined_at', 'is_muted', 'is_archived', 'is_online'
#         ]
#         read_only_fields = ['id', 'joined_at']


# # ========================================
# # ✅ SERIALIZER POUR DERNIER MESSAGE
# # ========================================

# class LastMessageSerializer(serializers.ModelSerializer):
#     """
#     Serializer simplifié pour le dernier message
#     Utilisé dans ConversationListSerializer
#     """
#     sender_id = serializers.UUIDField(source='from_user.user_id', read_only=True)
#     sender_name = serializers.CharField(source='from_user.display_name', read_only=True)
    
#     # ✅ IMPORTANT : Retourner le contenu déchiffré si disponible
#     decrypted_content = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Message
#         fields = [
#             'id',
#             'sender_id',
#             'sender_name',
#             'type',
#             'encrypted_content',
#             'decrypted_content',  # ✅ Ajouté
#             'created_at',
#         ]
    
#     def get_decrypted_content(self, obj):
#         """
#         Retourne le texte en clair SI le message est de l'utilisateur actuel
#         Sinon retourne None (sera affiché comme "Message chiffré")
        
#         Note: On ne peut déchiffrer que nos propres messages côté serveur
#         car on a sauvegardé le plaintext lors de l'envoi
#         """
#         request = self.context.get('request')
        
#         # Si c'est notre message, on pourrait avoir le plaintext en cache
#         # Pour l'instant, retourne None car on ne stocke pas le plaintext côté serveur
#         # Le client devra déchiffrer lui-même
        
#         # TODO: Si on veut afficher le plaintext dans la liste,
#         # il faudrait soit :
#         # 1. Stocker le plaintext côté serveur (moins sécurisé)
#         # 2. Déchiffrer côté client après réception (ce qu'on fait)
        
#         return None  # Le client déchiffrera


# # ========================================
# # ✅ CONVERSATION LIST (CORRIGÉ)
# # ========================================

# class ConversationListSerializer(serializers.ModelSerializer):
#     """Serializer pour la liste - Display name basé sur CONTACT uniquement"""
#     participants = ConversationParticipantSerializer(many=True, read_only=True)
#     participant_count = serializers.SerializerMethodField()
#     unread_count = serializers.SerializerMethodField()
#     display_name = serializers.SerializerMethodField()
    
#     # ✅ AJOUT CRITIQUE : Inclure le dernier message
#     last_message = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Conversation
#         fields = [
#             'id', 'type', 'name', 'display_name', 'participants',
#             'participant_count', 'unread_count', 
#             'last_message',  # ✅ AJOUTÉ
#             'last_message_at', 'created_at'
#         ]
    
#     def get_participant_count(self, obj):
#         return obj.participants.count()
    
#     def get_unread_count(self, obj):
#         # TODO: Implémenter le vrai compteur
#         return 0
    
#     def get_last_message(self, obj):
#         """
#         ✅ Retourne le dernier message de la conversation
#         """
#         # Récupérer le dernier message (via relation)
#         if hasattr(obj, 'last_message') and obj.last_message:
#             # Utiliser le ForeignKey last_message du modèle
#             return LastMessageSerializer(
#                 obj.last_message,
#                 context=self.context
#             ).data
        
#         # Sinon, chercher manuellement
#         last_msg = obj.messages.order_by('-created_at').first()
#         if last_msg:
#             return LastMessageSerializer(
#                 last_msg,
#                 context=self.context
#             ).data
        
#         return None
    
#     def get_display_name(self, obj):
#         """
#         ✅ SÉCURISÉ: Nickname OU Numéro (JAMAIS nom système)
#         """
#         request = self.context.get('request')
        
#         if obj.type == Conversation.Type.GROUP:
#             return obj.name or 'Groupe'
        
#         # DIRECT: trouve l'autre participant
#         if not request:
#             return None
        
#         other_participant = obj.participants.exclude(
#             user=request.user
#         ).select_related('user').first()
        
#         if not other_participant:
#             return None
        
#         other_user = other_participant.user
        
#         # ✅ Cherche le contact pour nickname
#         try:
#             contact = Contact.objects.get(
#                 user=request.user,
#                 contact_user=other_user,
#                 is_deleted=False
#             )
            
#             if contact.nickname and contact.nickname.strip():
#                 return contact.nickname.strip()
#         except Contact.DoesNotExist:
#             pass
        
#         # Pas de nickname → Numéro
#         return other_user.phone_number


# class ConversationDetailSerializer(serializers.ModelSerializer):
#     """Serializer détaillé - Participants sans noms"""
#     participants = ConversationParticipantSerializer(many=True, read_only=True)
#     last_message = LastMessageSerializer(read_only=True)  # ✅ Ajouté
    
#     class Meta:
#         model = Conversation
#         fields = [
#             'id', 'type', 'name', 'participants',
#             'last_message',  # ✅ Ajouté
#             'created_at', 'last_message_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'last_message_at']


# class ConversationCreateSerializer(serializers.Serializer):
#     """Serializer pour créer"""
#     type = serializers.ChoiceField(choices=Conversation.Type.choices)
#     name = serializers.CharField(max_length=100, required=False, allow_blank=True)
#     participant_ids = serializers.ListField(
#         child=serializers.UUIDField(),
#         min_length=1
#     )
    
#     def validate(self, data):
#         conv_type = data.get('type')
#         participant_ids = data.get('participant_ids', [])
        
#         if conv_type == Conversation.Type.DIRECT and len(participant_ids) != 1:
#             raise serializers.ValidationError('DIRECT nécessite 1 participant')
        
#         if conv_type == Conversation.Type.GROUP and not data.get('name'):
#             raise serializers.ValidationError('Nom requis pour GROUP')
        
#         return data
    
#     @transaction.atomic
#     def create(self, validated_data):
#         request = self.context.get('request')
#         conv_type = validated_data['type']
#         participant_ids = validated_data['participant_ids']
#         name = validated_data.get('name', '').strip() or None
        
#         # Vérifier si conversation DIRECTE existe déjà
#         if conv_type == Conversation.Type.DIRECT:
#             other_user_id = participant_ids[0]
            
#             existing = Conversation.objects.filter(
#                 type=Conversation.Type.DIRECT,
#                 participants__user=request.user
#             ).filter(
#                 participants__user__user_id=other_user_id
#             ).distinct().first()
            
#             if existing:
#                 print(f'✅ Conversation existante trouvée: {existing.id}')
#                 return existing
        
#         # Créer nouvelle conversation
#         conversation = Conversation.objects.create(
#             type=conv_type,
#             name=name,
#             created_by=request.user
#         )
        
#         # Ajouter user actuel
#         ConversationParticipant.objects.create(
#             conversation=conversation,
#             user=request.user,
#             role=ConversationParticipant.Role.ADMIN
#         )
        
#         # Ajouter autres participants
#         for user_id in participant_ids:
#             user = User.objects.get(user_id=user_id)
#             ConversationParticipant.objects.create(
#                 conversation=conversation,
#                 user=user,
#                 role=ConversationParticipant.Role.MEMBER
#             )
        
#         print(f'✅ Nouvelle conversation créée: {conversation.id}')
#         return conversation


# class ConversationUpdateSerializer(serializers.ModelSerializer):
#     """Serializer pour modifier"""
#     class Meta:
#         model = Conversation
#         fields = ['name']
