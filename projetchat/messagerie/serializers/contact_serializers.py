# messagerie/serializers/contact_serializers.py

from rest_framework import serializers
from django.db import transaction
from messagerie.models.contact import Contact
from authentification.models import User


class UserSuggestionSerializer(serializers.ModelSerializer):
    """SÉCURISÉ: Search ne révèle QUE le numéro"""
    user_id = serializers.UUIDField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['user_id', 'phone_number']


class ContactListSerializer(serializers.ModelSerializer):
    """Affiche nickname OU numéro"""
    contact_user_id = serializers.UUIDField(source='contact_user.user_id', read_only=True)
    contact_phone = serializers.CharField(source='contact_user.phone_number', read_only=True)
    display_name = serializers.SerializerMethodField()
    is_online = serializers.BooleanField(source='contact_user.is_online', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'contact_user_id', 'contact_phone', 'display_name',
            'nickname', 'is_favorite', 'is_blocked', 'is_online', 'added_at'
        ]
    
    def get_display_name(self, obj):
        if obj.nickname and obj.nickname.strip():
            return obj.nickname.strip()
        return obj.contact_user.phone_number


class ContactDetailSerializer(serializers.ModelSerializer):
    """Détails d'un contact"""
    contact_user_id = serializers.UUIDField(source='contact_user.user_id', read_only=True)
    contact_phone = serializers.CharField(source='contact_user.phone_number', read_only=True)
    display_name = serializers.SerializerMethodField()
    is_online = serializers.BooleanField(source='contact_user.is_online', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'contact_user_id', 'contact_phone', 'display_name',
            'nickname', 'is_favorite', 'is_blocked', 'is_online',
            'added_at', 'updated_at', 'notes'
        ]
    
    def get_display_name(self, obj):
        if obj.nickname and obj.nickname.strip():
            return obj.nickname.strip()
        return obj.contact_user.phone_number


class ContactCreateSerializer(serializers.Serializer):
    """Créer contact"""
    phone_number = serializers.CharField(max_length=20)
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_phone_number(self, value):
        value = value.strip()
        
        if len(value) < 8:
            raise serializers.ValidationError('Numéro invalide')
        
        if not User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Ce numéro n\'utilise pas l\'application')
        
        return value
    
    def validate(self, data):
        request = self.context.get('request')
        phone = data.get('phone_number')
        
        if request.user.phone_number == phone:
            raise serializers.ValidationError('Vous ne pouvez pas vous ajouter')
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        phone = validated_data['phone_number']
        nickname = validated_data.get('nickname', '').strip() or None
        
        contact_user = User.objects.get(phone_number=phone)
        
        existing = Contact.objects.filter(
            user=request.user,
            contact_user=contact_user
        ).first()
        
        if existing:
            if existing.is_deleted:
                existing.is_deleted = False
                existing.nickname = nickname
                existing.save()
                return existing
            else:
                raise serializers.ValidationError('Contact déjà ajouté')
        
        contact = Contact.objects.create(
            user=request.user,
            contact_user=contact_user,
            nickname=nickname
        )
        
        return contact


class ContactUpdateSerializer(serializers.ModelSerializer):
    """Modifier contact"""
    class Meta:
        model = Contact
        fields = ['nickname', 'is_favorite', 'is_blocked', 'notes']

# # messagerie/serializers/contact_serializers.py

# from rest_framework import serializers
# from messagerie.models.contact import Contact
# from authentification.models import User
# from django.core.exceptions import ValidationError as DjangoValidationError


# class ContactListSerializer(serializers.ModelSerializer):
#     """
#     Serializer optimisé pour la liste des contacts
#     """
#     contact_user_id = serializers.UUIDField(source='contact_user.user_id', read_only=True)
#     contact_phone = serializers.CharField(source='contact_user.phone_number', read_only=True)
#     contact_avatar = serializers.URLField(source='contact_user.avatar', read_only=True, allow_null=True)
#     is_online = serializers.BooleanField(source='contact_user.is_online', read_only=True)
#     last_seen = serializers.DateTimeField(source='contact_user.last_seen', read_only=True, allow_null=True)
    
#     # ✅ AJOUT: display_name calculé
#     display_name = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Contact
#         fields = [
#             'id',
#             'contact_user_id',
#             'contact_phone',
#             'nickname',  # ✅ Nickname personnalisé
#             'display_name',  # ✅ Nom affiché (calculé)
#             'contact_avatar',
#             'is_favorite',
#             'is_blocked',
#             'is_online',
#             'last_seen',
#             'added_at'
#         ]
    
#     def get_display_name(self, obj):
#         """
#         Retourne le nom à afficher :
#         1. nickname si défini
#         2. sinon display_name de l'utilisateur
#         3. sinon phone_number
#         """
#         if obj.nickname and obj.nickname.strip():
#             return obj.nickname.strip()
        
#         if obj.contact_user.display_name:
#             return obj.contact_user.display_name
        
#         return obj.contact_user.phone_number


# class ContactDetailSerializer(serializers.ModelSerializer):
#     """
#     Serializer détaillé pour un contact
#     """
#     contact_user = serializers.SerializerMethodField()
#     display_name = serializers.SerializerMethodField()  # ✅ AJOUTÉ
    
#     class Meta:
#         model = Contact
#         fields = [
#             'id',
#             'contact_user',
#             'nickname',
#             'display_name',  # ✅ AJOUTÉ
#             'notes',
#             'is_favorite',
#             'is_blocked',
#             'is_deleted',
#             'added_at',
#             'updated_at',
#             'blocked_at'
#         ]
#         read_only_fields = ['id', 'added_at', 'updated_at', 'blocked_at']
    
#     def get_contact_user(self, obj):
#         """Infos complètes de l'utilisateur contact"""
#         return {
#             'user_id': str(obj.contact_user.user_id),
#             'phone_number': obj.contact_user.phone_number,
#             'display_name': obj.contact_user.display_name,
#             'email': obj.contact_user.email,
#             'avatar': obj.contact_user.avatar,
#             'bio': obj.contact_user.bio,
#             'is_online': obj.contact_user.is_online,
#             'last_seen': obj.contact_user.last_seen,
#             'is_verified': obj.contact_user.is_verified
#         }
    
#     def get_display_name(self, obj):
#         """Nom affiché calculé"""
#         if obj.nickname and obj.nickname.strip():
#             return obj.nickname.strip()
        
#         if obj.contact_user.display_name:
#             return obj.contact_user.display_name
        
#         return obj.contact_user.phone_number


# class ContactCreateSerializer(serializers.Serializer):
#     """
#     Serializer pour ajouter un nouveau contact
#     """
#     phone_number = serializers.CharField(
#         help_text="Numéro de téléphone au format E.164 (ex: +22244010447)"
#     )
#     nickname = serializers.CharField(
#         max_length=100,
#         required=False,
#         allow_blank=True,
#         help_text="Surnom personnalisé (optionnel)"
#     )
#     notes = serializers.CharField(
#         required=False,
#         allow_blank=True,
#         help_text="Notes privées (optionnel)"
#     )
    
#     def validate_phone_number(self, value):
#         """Vérifier que l'utilisateur existe"""
#         try:
#             user = User.objects.get(phone_number=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError(
#                 "Aucun utilisateur trouvé avec ce numéro"
#             )
        
#         if not user.is_active:
#             raise serializers.ValidationError(
#                 "Cet utilisateur n'est pas actif"
#             )
        
#         return value
    
#     def validate(self, data):
#         """Validation globale"""
#         request = self.context.get('request')
#         phone_number = data.get('phone_number')
        
#         contact_user = User.objects.get(phone_number=phone_number)
        
#         if contact_user == request.user:
#             raise serializers.ValidationError({
#                 'phone_number': 'Vous ne pouvez pas vous ajouter vous-même'
#             })
        
#         existing = Contact.objects.filter(
#             user=request.user,
#             contact_user=contact_user
#         ).first()
        
#         if existing and not existing.is_deleted:
#             raise serializers.ValidationError({
#                 'phone_number': 'Ce contact existe déjà'
#             })
        
#         data['_existing_contact'] = existing
#         data['_contact_user'] = contact_user
        
#         return data
    
#     def create(self, validated_data):
#         """Créer ou restaurer le contact"""
#         request = self.context.get('request')
#         existing = validated_data.pop('_existing_contact', None)
#         contact_user = validated_data.pop('_contact_user')
#         phone_number = validated_data.pop('phone_number')
        
#         # ✅ Récupérer nickname (peut être vide)
#         nickname = validated_data.get('nickname', '').strip()
#         notes = validated_data.get('notes', '').strip()
        
#         if existing:
#             # Restaurer le contact supprimé
#             existing.is_deleted = False
#             existing.nickname = nickname
#             existing.notes = notes
#             existing.save()
#             return existing
        
#         # ✅ Créer nouveau contact avec nickname
#         contact = Contact.objects.create(
#             user=request.user,
#             contact_user=contact_user,
#             nickname=nickname,
#             notes=notes
#         )
        
#         return contact


# class ContactUpdateSerializer(serializers.ModelSerializer):
#     """
#     Serializer pour modifier un contact (nickname, notes)
#     """
#     class Meta:
#         model = Contact
#         fields = ['nickname', 'notes']
    
#     def validate_nickname(self, value):
#         """Validation du nickname"""
#         if value:
#             return value.strip()
#         return ''


# class ContactSearchSerializer(serializers.Serializer):
#     """
#     Serializer pour rechercher des utilisateurs à ajouter
#     """
#     query = serializers.CharField(
#         min_length=3,
#         help_text="Numéro de téléphone ou nom (min 3 caractères)"
#     )


# class UserSuggestionSerializer(serializers.ModelSerializer):
#     """
#     Serializer pour suggestions d'utilisateurs
#     """
#     is_contact = serializers.SerializerMethodField()
    
#     class Meta:
#         model = User
#         fields = [
#             'user_id',
#             'phone_number',
#             'display_name',
#             'avatar',
#             'is_online',
#             'is_verified',
#             'is_contact'
#         ]
    
#     def get_is_contact(self, obj):
#         """Vérifier si déjà dans les contacts"""
#         request = self.context.get('request')
#         if not request:
#             return False
        
#         return Contact.objects.filter(
#             user=request.user,
#             contact_user=obj,
#             is_deleted=False
#         ).exists()

