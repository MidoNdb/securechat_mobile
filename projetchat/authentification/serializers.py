# authentification/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import hashlib

from .models import User, Device, Session

# ========================================
# USER SERIALIZERS
# ========================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour User"""
    
    name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'user_id',
            'phone_number',
            'display_name',
            'name',
            'email',
            'avatar',
            'bio',
            'dh_public_key',
            'sign_public_key',
            'encrypted_private_keys', 
            'safety_number',
            'is_online',
            'last_seen',
            'is_verified',
            'created_at',
        ]
        read_only_fields = [
            'id', 'user_id', 'phone_number',
            'dh_public_key', 'sign_public_key',
            'is_verified', 'created_at', 'last_seen',
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour le profil"""
    
    class Meta:
        model = User
        fields = ['display_name', 'email', 'avatar', 'bio']
    
    def validate_email(self, value):
        if value:
            user = self.context['request'].user
            if User.objects.exclude(pk=user.pk).filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value


# ========================================
# REGISTER SERIALIZER
# ========================================
# ========================================
# REGISTER SERIALIZER
# ========================================

class RegisterSerializer(serializers.Serializer):
    """Inscription avec clés DH + Ed25519"""
    
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, required=True)
    display_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    
    # Clés publiques
    dh_public_key = serializers.CharField(
        required=True,
        help_text="Clé publique X25519 (Base64)"
    )
    sign_public_key = serializers.CharField(
        required=True,
        help_text="Clé publique Ed25519 (Base64)"
    )
    
    # ✅ NOUVEAU: Backup chiffré des clés privées
    encrypted_private_keys = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Backup chiffré des clés privées (JSON chiffré avec PBKDF2)"
    )
    
    # Device info
    device_id = serializers.UUIDField(required=True)
    device_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=['ios', 'android', 'web'],
        default='android'
    )
    
    def validate_phone_number(self, value):
        normalized = ''.join(filter(str.isdigit, value))
        
        if len(normalized) < 8 or len(normalized) > 15:
            raise serializers.ValidationError(
                "Le numéro doit contenir entre 8 et 15 chiffres."
            )
        
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "Ce numéro est déjà enregistré."
            )
        
        return value
    
    def validate_email(self, value):
        if not value:
            return None
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate_password(self, value):
        if len(value) != 64 or not all(c in '0123456789abcdef' for c in value):
            raise serializers.ValidationError(
                "Format password invalide (SHA-256 attendu)"
            )
        return value
    
    def create(self, validated_data):
        device_id = validated_data.pop('device_id')
        device_name = validated_data.pop('device_name', None)
        device_type = validated_data.pop('device_type', 'android')
        encrypted_backup = validated_data.pop('encrypted_private_keys', None)  # ✅
        
        # Créer utilisateur
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            display_name=validated_data.get('display_name'),
            email=validated_data.get('email'),
            dh_public_key=validated_data['dh_public_key'],
            sign_public_key=validated_data['sign_public_key'],
            encrypted_private_keys=encrypted_backup,  # ✅ Sauvegarder le backup
        )
        
        # Générer safety_number
        user.safety_number = self._generate_safety_number(
            user.user_id,
            user.dh_public_key,
            user.sign_public_key
        )
        user.save()
        
        # Créer device unique
        Device.objects.create(
            user=user,
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
        )
        
        return user
    
    def _generate_safety_number(self, user_id, dh_key, sign_key):
        data = f"{user_id}{dh_key}{sign_key}".encode()
        hash_digest = hashlib.sha256(data).hexdigest()
        return '-'.join([hash_digest[i:i+4] for i in range(0, 12, 4)])


# ========================================
# LOGIN SERIALIZER (SIMPLIFIÉ)
# ========================================

class LoginSerializer(serializers.Serializer):
    """
    Login simplifié - Authentification uniquement
    La gestion des clés est faite côté client
    """
    
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    device_id = serializers.UUIDField(required=True)
    device_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=['ios', 'android', 'web'],
        default='android'
    )
    
    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        
        # Authentifier
        user = authenticate(
            request=self.context.get('request'),
            username=phone_number,
            password=password
        )
        
        if not user:
            raise serializers.ValidationError(
                "Numéro ou mot de passe incorrect.",
                code='authorization'
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                "Ce compte a été désactivé.",
                code='authorization'
            )
        
        attrs['user'] = user
        return attrs
# class RegisterSerializer(serializers.Serializer):
#     """Inscription avec clés DH + Ed25519"""
    
#     phone_number = serializers.CharField(max_length=20, required=True)
#     password = serializers.CharField(write_only=True, required=True)
#     display_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
#     email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    
#     # ✅ Nouvelles clés publiques
#     dh_public_key = serializers.CharField(
#         required=True,
#         help_text="Clé publique X25519 (Base64)"
#     )
#     sign_public_key = serializers.CharField(
#         required=True,
#         help_text="Clé publique Ed25519 (Base64)"
#     )
    
#     # Device info
#     device_id = serializers.UUIDField(required=True)
#     device_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
#     device_type = serializers.ChoiceField(
#         choices=['ios', 'android', 'web'],
#         default='android'
#     )
    
#     def validate_phone_number(self, value):
#         normalized = ''.join(filter(str.isdigit, value))
        
#         if len(normalized) < 8 or len(normalized) > 15:
#             raise serializers.ValidationError(
#                 "Le numéro doit contenir entre 8 et 15 chiffres."
#             )
        
#         if User.objects.filter(phone_number=value).exists():
#             raise serializers.ValidationError(
#                 "Ce numéro est déjà enregistré."
#             )
        
#         return value
    
#     def validate_email(self, value):
#         if not value:
#             return None
#         if User.objects.filter(email=value).exists():
#             raise serializers.ValidationError("Cet email est déjà utilisé.")
#         return value
    
#     def validate_password(self, value):
#         if len(value) != 64 or not all(c in '0123456789abcdef' for c in value):
#             raise serializers.ValidationError(
#                 "Format password invalide (SHA-256 attendu)"
#             )
#         return value
    
#     def create(self, validated_data):
#         device_id = validated_data.pop('device_id')
#         device_name = validated_data.pop('device_name', None)
#         device_type = validated_data.pop('device_type', 'android')
        
#         # Créer utilisateur
#         user = User.objects.create_user(
#             phone_number=validated_data['phone_number'],
#             password=validated_data['password'],
#             display_name=validated_data.get('display_name'),
#             email=validated_data.get('email'),
#             dh_public_key=validated_data['dh_public_key'],
#             sign_public_key=validated_data['sign_public_key'],
#         )
        
#         # Générer safety_number
#         user.safety_number = self._generate_safety_number(
#             user.user_id,
#             user.dh_public_key,
#             user.sign_public_key
#         )
#         user.save()
        
#         # Créer device unique
#         Device.objects.create(
#             user=user,
#             device_id=device_id,
#             device_name=device_name,
#             device_type=device_type,
#         )
        
#         return user
    
#     def _generate_safety_number(self, user_id, dh_key, sign_key):
#         data = f"{user_id}{dh_key}{sign_key}".encode()
#         hash_digest = hashlib.sha256(data).hexdigest()
#         return '-'.join([hash_digest[i:i+4] for i in range(0, 12, 4)])


# # ========================================
# # LOGIN SERIALIZER
# # ========================================

# class LoginSerializer(serializers.Serializer):
#     """
#     Login avec détection nouveau device
#     Si nouveau device → régénération clés requise
#     """
    
#     phone_number = serializers.CharField(required=True)
#     password = serializers.CharField(write_only=True, required=True)
#     device_id = serializers.UUIDField(required=True)
#     device_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
#     device_type = serializers.ChoiceField(
#         choices=['ios', 'android', 'web'],
#         default='android'
#     )
    
#     # ✅ NOUVEAUX champs pour régénération clés
#     new_dh_public_key = serializers.CharField(required=False, allow_null=True)
#     new_sign_public_key = serializers.CharField(required=False, allow_null=True)
#     confirmed_key_regeneration = serializers.BooleanField(default=False)
    
#     def validate(self, attrs):
#         phone_number = attrs.get('phone_number')
#         password = attrs.get('password')
        
#         # Authentifier
#         user = authenticate(
#             request=self.context.get('request'),
#             username=phone_number,
#             password=password
#         )
        
#         if not user:
#             raise serializers.ValidationError(
#                 "Numéro ou mot de passe incorrect.",
#                 code='authorization'
#             )
        
#         if not user.is_active:
#             raise serializers.ValidationError(
#                 "Ce compte a été désactivé.",
#                 code='authorization'
#             )
        
#         attrs['user'] = user
#         return attrs


# ========================================
# JWT TOKEN SERIALIZER
# ========================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    device_id = serializers.UUIDField(required=True)
    device_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=['ios', 'android', 'web'],
        default='android'
    )
    
    username_field = 'phone_number'
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.user_id)
        token['phone_number'] = user.phone_number
        token['display_name'] = user.display_name or ''
        token['is_verified'] = user.is_verified
        return token
    
    def validate(self, attrs):
        device_id = attrs.pop('device_id')
        device_name = attrs.get('device_name', '')
        device_type = attrs.get('device_type', 'android')
        
        data = super().validate(attrs)
        user = self.user
        
        # Créer/Mettre à jour device unique
        Device.objects.update_or_create(
            user=user,
            defaults={
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type,
            }
        )
        
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        access['device_id'] = str(device_id)
        refresh['device_id'] = str(device_id)
        
        # Session unique
        Session.objects.update_or_create(
            user=user,
            defaults={
                'device_id': Device.objects.get(user=user).id,
                'access_token_jti': str(access['jti']),
                'refresh_token_jti': str(refresh['jti']),
                'access_token_expires_at': timezone.now() + timedelta(minutes=15),
                'refresh_token_expires_at': timezone.now() + timedelta(days=30),
                'ip_address': self._get_client_ip(),
                'user_agent': self._get_user_agent(),
            }
        )
        
        user.last_seen = timezone.now()
        user.save(update_fields=['last_seen'])
        
        data['refresh'] = str(refresh)
        data['access'] = str(access)
        data['user'] = UserSerializer(user).data
        
        return data
    
    def _get_client_ip(self):
        request = self.context.get('request')
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        return None
    
    def _get_user_agent(self):
        request = self.context.get('request')
        return request.META.get('HTTP_USER_AGENT', '') if request else ''


# ========================================
# TOKEN REFRESH SERIALIZER
# ========================================

class CustomTokenRefreshSerializer(serializers.Serializer):
    """Rafraîchir le token"""
    
    refresh = serializers.CharField(required=True)
    
    def validate(self, attrs):
        refresh_token = attrs['refresh']
        
        try:
            refresh = RefreshToken(refresh_token)
            refresh_jti = str(refresh['jti'])
            
            session = Session.objects.get(refresh_token_jti=refresh_jti)
            
            if session.is_expired:
                raise serializers.ValidationError("Session expirée.", code='token_not_valid')
            
            access = refresh.access_token
            
            # Mettre à jour session
            session.access_token_jti = str(access['jti'])
            session.access_token_expires_at = timezone.now() + timedelta(minutes=15)
            session.last_used = timezone.now()
            session.save()
            
            new_refresh = refresh
            new_refresh.set_jti()
            new_refresh.set_exp()
            
            session.refresh_token_jti = str(new_refresh['jti'])
            session.refresh_token_expires_at = timezone.now() + timedelta(days=30)
            session.save()
            
            return {
                'access': str(access),
                'refresh': str(new_refresh),
            }
            
        except Exception as e:
            raise serializers.ValidationError(f"Token invalide: {str(e)}", code='token_not_valid')


# ========================================
# DEVICE SERIALIZER
# ========================================

class DeviceSerializer(serializers.ModelSerializer):
    """Serializer pour Device"""
    
    class Meta:
        model = Device
        fields = [
            'id', 'device_id', 'device_name',
            'device_type', 'last_seen', 'created_at',
        ]
        read_only_fields = ['id', 'last_seen', 'created_at']


# ========================================
# SESSION SERIALIZER
# ========================================

class SessionSerializer(serializers.ModelSerializer):
    """Serializer pour Session"""
    
    device = DeviceSerializer(read_only=True)
    
    class Meta:
        model = Session
        fields = [
            'id', 'device', 'ip_address', 'user_agent',
            'last_used', 'created_at',
            'access_token_expires_at', 'refresh_token_expires_at',
        ]
        read_only_fields = [
            'id', 'last_used', 'created_at',
            'access_token_expires_at', 'refresh_token_expires_at',
        ]


# ========================================
# CHANGE PASSWORD SERIALIZER
# ========================================

class ChangePasswordSerializer(serializers.Serializer):
    """Changer le mot de passe"""
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe incorrect.")
        return value
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user




# # authentification/serializers.py

# from rest_framework import serializers
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework_simplejwt.tokens import RefreshToken
# from django.contrib.auth import authenticate
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# from datetime import timedelta
# import uuid
# import hashlib

# from .models import User, Device, Session
# from .crypto_service import CryptoService

# # ========================================
# # USER SERIALIZERS
# # ========================================

# class UserSerializer(serializers.ModelSerializer):
#     """Serializer pour User"""
    
#     name = serializers.CharField(source='get_full_name', read_only=True)
    
#     class Meta:
#         model = User
#         fields = [
#             'id',
#             'user_id',
#             'phone_number',
#             'display_name',
#             'name',
#             'email',
#             'avatar',
#             'bio',
#             'public_key',
#             'safety_number',
#             'is_online',
#             'last_seen',
#             'is_verified',
#             'created_at',
#         ]
#         read_only_fields = [
#             'id',
#             'user_id',
#             'phone_number',
#             'public_key',
#             'is_verified',
#             'created_at',
#             'last_seen',
#         ]


# class UserUpdateSerializer(serializers.ModelSerializer):
#     """Serializer pour mettre à jour le profil utilisateur"""
    
#     class Meta:
#         model = User
#         fields = [
#             'display_name',
#             'email',
#             'avatar',
#             'bio',
#         ]
    
#     def validate_email(self, value):
#         if value:
#             user = self.context['request'].user
#             if User.objects.exclude(pk=user.pk).filter(email=value).exists():
#                 raise serializers.ValidationError("Cet email est déjà utilisé.")
#         return value


# # ========================================
# # REGISTER SERIALIZER
# # ========================================

# class RegisterSerializer(serializers.Serializer):
#     """Serializer pour l'inscription d'un nouvel utilisateur"""
    
#     phone_number = serializers.CharField(
#         max_length=20,
#         required=True,
#         help_text="Numéro de téléphone (ex: +22244010447)"
#     )
#     password = serializers.CharField(
#         write_only=True,
#         required=True,
#         style={'input_type': 'password'},
#         help_text="Mot de passe hashé côté client (SHA-256)"
#     )
#     display_name = serializers.CharField(
#         max_length=50,
#         required=False,
#         allow_blank=True,
#         help_text="Nom d'affichage (optionnel)"
#     )
#     email = serializers.EmailField(
#         required=False,
#         allow_blank=True,
#         allow_null=True,
#         help_text="Email (optionnel)"
#     )
#     public_key = serializers.CharField(
#         required=True,
#         help_text="Clé publique RSA (format PEM)"
#     )
#     encrypted_private_key = serializers.CharField(
#         required=True,
#         write_only=True,
#         help_text="Clé privée chiffrée côté client"
#     )
#     client_encryption_salt = serializers.CharField(
#         required=True,
#         write_only=True,
#         help_text="Salt utilisé côté client"
#     )
#     device_id = serializers.UUIDField(
#         required=True,
#         help_text="UUID unique de l'appareil"
#     )
#     device_name = serializers.CharField(
#         max_length=100,
#         required=False,
#         allow_blank=True,
#         help_text="Nom de l'appareil"
#     )
#     device_type = serializers.ChoiceField(
#         choices=['ios', 'android', 'web'],
#         default='android',
#         help_text="Type d'appareil"
#     )
    
#     def validate_phone_number(self, value):
#         normalized = ''.join(filter(str.isdigit, value))
        
#         if len(normalized) < 8 or len(normalized) > 15:
#             raise serializers.ValidationError(
#                 "Le numéro de téléphone doit contenir entre 8 et 15 chiffres."
#             )
        
#         if User.objects.filter(phone_number=value).exists():
#             raise serializers.ValidationError(
#                 "Ce numéro de téléphone est déjà enregistré."
#             )
        
#         return value
    
#     def validate_email(self, value):
#         if not value:
#             return None
            
#         if User.objects.filter(email=value).exists():
#             raise serializers.ValidationError(
#                 "Cet email est déjà utilisé."
#             )
#         return value
    
#     def validate_password(self, value):
#         if len(value) != 64 or not all(c in '0123456789abcdef' for c in value):
#             raise serializers.ValidationError(
#                 "Format de password invalide (doit être SHA-256)"
#             )
#         return value
    
#     def validate_public_key(self, value):
#         if not value.startswith('-----BEGIN PUBLIC KEY-----'):
#             raise serializers.ValidationError(
#                 "Format de clé publique invalide. Doit être au format PEM."
#             )
#         return value
    
#     def create(self, validated_data):
#         device_id = validated_data.pop('device_id')
#         device_name = validated_data.pop('device_name', None)
#         device_type = validated_data.pop('device_type', 'android')
#         encrypted_private_key = validated_data.pop('encrypted_private_key')
#         client_salt = validated_data.pop('client_encryption_salt')
        
#         user = User.objects.create_user(
#             phone_number=validated_data['phone_number'],
#             password=validated_data['password'],
#             display_name=validated_data.get('display_name'),
#             email=validated_data.get('email'),
#             public_key=validated_data['public_key'],
#         )
        
#         user.safety_number = self._generate_safety_number(
#             user.user_id,
#             user.public_key
#         )
        
#         user.encrypted_private_key_backup = encrypted_private_key
#         user.encryption_salt = client_salt
#         user.backup_created_at = timezone.now()
        
#         user.save()
        
#         Device.objects.create(
#             user=user,
#             device_id=device_id,
#             device_name=device_name,
#             device_type=device_type,
#         )
        
#         return user
    
#     def _generate_safety_number(self, user_id, public_key):
#         data = f"{user_id}{public_key}".encode()
#         hash_digest = hashlib.sha256(data).hexdigest()
#         return '-'.join([hash_digest[i:i+4] for i in range(0, 12, 4)])


# # ========================================
# # LOGIN SERIALIZER
# # ========================================

# class LoginSerializer(serializers.Serializer):
#     """Serializer pour la connexion utilisateur"""
    
#     phone_number = serializers.CharField(
#         required=True,
#         help_text="Numéro de téléphone"
#     )
#     password = serializers.CharField(
#         write_only=True,
#         required=True,
#         style={'input_type': 'password'},
#         help_text="Mot de passe"
#     )
#     device_id = serializers.UUIDField(
#         required=True,
#         help_text="UUID de l'appareil"
#     )
#     device_name = serializers.CharField(
#         max_length=100,
#         required=False,
#         allow_blank=True
#     )
#     device_type = serializers.ChoiceField(
#         choices=['ios', 'android', 'web'],
#         default='android'
#     )
    
#     def validate(self, attrs):
#         phone_number = attrs.get('phone_number')
#         password = attrs.get('password')
        
#         if phone_number and password:
#             user = authenticate(
#                 request=self.context.get('request'),
#                 username=phone_number,
#                 password=password
#             )
            
#             if not user:
#                 raise serializers.ValidationError(
#                     "Numéro de téléphone ou mot de passe incorrect.",
#                     code='authorization'
#                 )
            
#             if not user.is_active:
#                 raise serializers.ValidationError(
#                     "Ce compte a été désactivé.",
#                     code='authorization'
#                 )
            
#             attrs['user'] = user
#         else:
#             raise serializers.ValidationError(
#                 "Numéro de téléphone et mot de passe requis.",
#                 code='authorization'
#             )
        
#         return attrs


# # ========================================
# # CUSTOM JWT TOKEN SERIALIZER
# # ========================================

# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
#     device_id = serializers.UUIDField(required=True)
#     device_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
#     device_type = serializers.ChoiceField(
#         choices=['ios', 'android', 'web'],
#         default='android'
#     )
    
#     username_field = 'phone_number'
    
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
        
#         # ✅ Ajouter user_id (UUID) dans les claims
#         token['user_id'] = str(user.user_id)  # UUID converti en string
#         token['phone_number'] = user.phone_number
#         token['display_name'] = user.display_name or ''
#         token['is_verified'] = user.is_verified
        
#         return token
    
#     def validate(self, attrs):
#         device_id = attrs.pop('device_id')
#         device_name = attrs.get('device_name', '')
#         device_type = attrs.get('device_type', 'android')
        
#         data = super().validate(attrs)
        
#         user = self.user
        
#         device, created = Device.objects.get_or_create(
#             user=user,
#             device_id=device_id,
#             defaults={
#                 'device_name': device_name,
#                 'device_type': device_type,
#             }
#         )
        
#         if not created:
#             device.device_name = device_name or device.device_name
#             device.device_type = device_type
#             device.is_active = True
#             device.save()
        
#         refresh = RefreshToken.for_user(user)
#         access = refresh.access_token
        
#         access['device_id'] = str(device_id)
#         refresh['device_id'] = str(device_id)
        
#         access_expires_at = timezone.now() + timedelta(minutes=15)
#         refresh_expires_at = timezone.now() + timedelta(days=30)
        
#         Session.objects.create(
#             user=user,
#             device=device,
#             access_token_jti=str(access['jti']),
#             refresh_token_jti=str(refresh['jti']),
#             access_token_expires_at=access_expires_at,
#             refresh_token_expires_at=refresh_expires_at,
#             ip_address=self._get_client_ip(),
#             user_agent=self._get_user_agent(),
#         )
        
#         user.last_seen = timezone.now()
#         user.save(update_fields=['last_seen'])
        
#         data['refresh'] = str(refresh)
#         data['access'] = str(access)
#         data['user'] = UserSerializer(user).data
        
#         return data
    
#     def _get_client_ip(self):
#         request = self.context.get('request')
#         if request:
#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             return ip
#         return None
    
#     def _get_user_agent(self):
#         request = self.context.get('request')
#         if request:
#             return request.META.get('HTTP_USER_AGENT', '')
#         return ''


# # ========================================
# # TOKEN REFRESH SERIALIZER
# # ========================================

# class CustomTokenRefreshSerializer(serializers.Serializer):
#     """Serializer pour rafraîchir le token"""
    
#     refresh = serializers.CharField(required=True)
    
#     def validate(self, attrs):
#         refresh_token = attrs['refresh']
        
#         try:
#             refresh = RefreshToken(refresh_token)
#             refresh_jti = str(refresh['jti'])
            
#             try:
#                 session = Session.objects.get(
#                     refresh_token_jti=refresh_jti,
#                     is_active=True
#                 )
#             except Session.DoesNotExist:
#                 raise serializers.ValidationError(
#                     "Session invalide ou expirée.",
#                     code='token_not_valid'
#                 )
            
#             if session.is_expired:
#                 session.is_active = False
#                 session.save()
#                 raise serializers.ValidationError(
#                     "Session expirée.",
#                     code='token_not_valid'
#                 )
            
#             access = refresh.access_token
            
#             session.access_token_jti = str(access['jti'])
#             session.access_token_expires_at = timezone.now() + timedelta(minutes=15)
#             session.last_used = timezone.now()
#             session.save()
            
#             new_refresh = refresh
#             new_refresh.set_jti()
#             new_refresh.set_exp()
            
#             session.refresh_token_jti = str(new_refresh['jti'])
#             session.refresh_token_expires_at = timezone.now() + timedelta(days=30)
#             session.save()
            
#             return {
#                 'access': str(access),
#                 'refresh': str(new_refresh),
#             }
            
#         except Exception as e:
#             raise serializers.ValidationError(
#                 f"Token invalide: {str(e)}",
#                 code='token_not_valid'
#             )


# # ========================================
# # DEVICE & SESSION SERIALIZERS
# # ========================================

# class DeviceSerializer(serializers.ModelSerializer):
#     """Serializer pour Device"""
    
#     class Meta:
#         model = Device
#         fields = [
#             'id',
#             'device_id',
#             'device_name',
#             'device_type',
#             'is_active',
#             'last_seen',
#             'created_at',
#         ]
#         read_only_fields = ['id', 'last_seen', 'created_at']


# class SessionSerializer(serializers.ModelSerializer):
#     """Serializer pour Session"""
    
#     device = DeviceSerializer(read_only=True)
    
#     class Meta:
#         model = Session
#         fields = [
#             'id',
#             'device',
#             'is_active',
#             'ip_address',
#             'user_agent',
#             'last_used',
#             'created_at',
#             'access_token_expires_at',
#             'refresh_token_expires_at',
#         ]
#         read_only_fields = [
#             'id',
#             'last_used',
#             'created_at',
#             'access_token_expires_at',
#             'refresh_token_expires_at',
#         ]


# # ========================================
# # CHANGE PASSWORD SERIALIZER
# # ========================================

# class ChangePasswordSerializer(serializers.Serializer):
#     """Serializer pour changer le mot de passe"""
    
#     old_password = serializers.CharField(
#         required=True,
#         write_only=True,
#         style={'input_type': 'password'}
#     )
#     new_password = serializers.CharField(
#         required=True,
#         write_only=True,
#         style={'input_type': 'password'}
#     )
    
#     def validate_old_password(self, value):
#         user = self.context['request'].user
#         if not user.check_password(value):
#             raise serializers.ValidationError("Mot de passe incorrect.")
#         return value
    
#     def validate_new_password(self, value):
#         try:
#             validate_password(value)
#         except ValidationError as e:
#             raise serializers.ValidationError(list(e.messages))
#         return value
    
#     def save(self):
#         user = self.context['request'].user
#         user.set_password(self.validated_data['new_password'])
#         user.save()
        
#         current_session_jti = self.context.get('current_session_jti')
#         Session.objects.filter(user=user, is_active=True).exclude(
#             access_token_jti=current_session_jti
#         ).update(is_active=False)
        
#         return user
    
# # authentification/serializers.py

# # Ajouter ce serializer

# class UpdateKeysSerializer(serializers.Serializer):
#     """Serializer pour mettre à jour les clés RSA"""
    
#     public_key = serializers.CharField(
#         required=True,
#         help_text="Nouvelle clé publique RSA (format PEM)"
#     )
#     encrypted_private_key = serializers.CharField(
#         required=True,
#         write_only=True,
#         help_text="Nouvelle clé privée chiffrée"
#     )
#     client_encryption_salt = serializers.CharField(
#         required=True,
#         write_only=True,
#         help_text="Nouveau salt"
#     )
    
#     def validate_public_key(self, value):
#         if not value.startswith('-----BEGIN PUBLIC KEY-----'):
#             raise serializers.ValidationError(
#                 "Format de clé publique invalide. Doit être au format PEM."
#             )
#         return value
    
#     def update(self, instance, validated_data):
#         """Mettre à jour les clés de l'utilisateur"""
        
#         instance.public_key = validated_data['public_key']
#         instance.encrypted_private_key_backup = validated_data['encrypted_private_key']
#         instance.encryption_salt = validated_data['client_encryption_salt']
#         instance.backup_created_at = timezone.now()
        
#         # Régénérer le safety_number avec la nouvelle clé publique
#         data = f"{instance.user_id}{instance.public_key}".encode()
#         hash_digest = hashlib.sha256(data).hexdigest()
#         instance.safety_number = '-'.join([hash_digest[i:i+4] for i in range(0, 12, 4)])
        
#         instance.save()
        
#         return instance