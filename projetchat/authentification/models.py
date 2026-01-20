# authentification/models.py

import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# ========================================
# USER MANAGER
# ========================================

class UserManager(BaseUserManager):
    """Manager personnalisé pour User"""
    
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Le numéro de téléphone est requis')
        
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        
        return self.create_user(phone_number, password, **extra_fields)


# ========================================
# USER MODEL
# ========================================

class User(AbstractBaseUser, PermissionsMixin):
    """Modèle utilisateur avec clés DH + Ed25519"""
    
    # Identifiants
    user_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    phone_number = models.CharField(
        max_length=20,
        unique=True
    )
    
    # Informations profil
    display_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True, null=True)
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # ✅ NOUVEAU: Clés publiques DH + Ed25519
    dh_public_key = models.TextField(
        help_text="Clé publique X25519 (Base64)"
    )
    sign_public_key = models.TextField(
        help_text="Clé publique Ed25519 (Base64)"
    )
    encrypted_private_keys = models.TextField(
        null=True,
        blank=True,
        help_text="Backup chiffré des clés privées {dh_private, sign_private} en JSON"
    )
    
    # Sécurité
    safety_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Numéro de sécurité pour vérification E2E"
    )
    
    # Statuts
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    # Django required
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return self.phone_number
    
    def get_full_name(self):
        return self.display_name or self.phone_number
    
    def get_short_name(self):
        return self.display_name or self.phone_number


# ========================================
# DEVICE MODEL (UN SEUL ACTIF)
# ========================================

class Device(models.Model):
    """
    UN SEUL appareil actif par utilisateur
    OneToOneField = maximum 1 device actif
    """
    
    id = models.BigAutoField(primary_key=True)
    
    # ✅ OneToOne = 1 seul device actif
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='active_device'
    )
    
    device_id = models.UUIDField(
        db_index=True,
        help_text="UUID généré par Flutter"
    )
    device_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('ios', 'iOS'),
            ('android', 'Android'),
            ('web', 'Web'),
        ],
        default='android'
    )
    
    # Métadonnées
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'devices'
        verbose_name = 'Device Actif'
        verbose_name_plural = 'Devices Actifs'
    
    def __str__(self):
        return f"{self.device_name or self.device_type} - {self.user.phone_number}"


# ========================================
# SESSION MODEL (SIMPLIFIÉ)
# ========================================

class Session(models.Model):
    """
    Session JWT simplifiée
    Une seule session active = un seul device
    """
    
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='active_session'
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='session'
    )
    
    # JWT identifiers
    access_token_jti = models.CharField(max_length=255, unique=True, db_index=True)
    refresh_token_jti = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Expiration
    access_token_expires_at = models.DateTimeField()
    refresh_token_expires_at = models.DateTimeField()
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sessions'
        verbose_name = 'Session Active'
        verbose_name_plural = 'Sessions Actives'
    
    def __str__(self):
        return f"Session {self.user.phone_number} - {self.device.device_type}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.refresh_token_expires_at




# # authentification/models.py

# import uuid
# import hashlib
# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# from django.utils import timezone
# from django.core.validators import RegexValidator

# # authentification/models.py

# # from django.db import models
# # from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
# # from django.utils import timezone
# # import uuid

# class UserManager(BaseUserManager):
#     """Manager personnalisé pour User"""
    
#     def create_user(self, phone_number, password=None, **extra_fields):
#         if not phone_number:
#             raise ValueError('Le numéro de téléphone est requis')
        
#         user = self.model(phone_number=phone_number, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
    
#     def create_superuser(self, phone_number, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('is_verified', True)
        
#         return self.create_user(phone_number, password, **extra_fields)


# class User(AbstractBaseUser, PermissionsMixin):
#     """Modèle utilisateur personnalisé"""
    
#     # Identifiants
#     user_id = models.UUIDField(
#         default=uuid.uuid4,
#         unique=True,
#         editable=False,
#         help_text="UUID unique de l'utilisateur"
#     )
#     phone_number = models.CharField(
#         max_length=20,
#         unique=True,
#         help_text="Numéro de téléphone au format E.164 (ex: +22244010447)"
#     )
#     phone_number_hash = models.CharField(
#         max_length=64,
#         blank=True,
#         null=True,
#         help_text="Hash du numéro pour recherche sécurisée"
#     )
    
#     # Informations profil
#     display_name = models.CharField(max_length=50, blank=True)
#     email = models.EmailField(blank=True, null=True)
#     avatar = models.URLField(blank=True, null=True)
#     bio = models.TextField(max_length=500, blank=True)
    
#     # Sécurité
#     public_key = models.TextField(
#         help_text="Clé publique RSA au format PEM"
#     )
#     safety_number = models.CharField(
#         max_length=20,
#         blank=True,
#         help_text="Numéro de sécurité pour vérification E2E"
#     )
    
#     # ← NOUVEAU : Backup chiffré
#     encrypted_private_key_backup = models.TextField(
#         blank=True,
#         null=True,
#         help_text="Clé privée chiffrée avec password utilisateur (AES-256-GCM)"
#     )
#     encryption_salt = models.CharField(
#         max_length=64,
#         blank=True,
#         null=True,
#         help_text="Salt pour dérivation de la clé de chiffrement (base64)"
#     )
#     backup_created_at = models.DateTimeField(
#         blank=True,
#         null=True,
#         help_text="Date de création du backup"
#     )
    
#     # Statuts
#     is_online = models.BooleanField(default=False)
#     last_seen = models.DateTimeField(auto_now=True)
#     is_verified = models.BooleanField(default=False)
    
#     # Django required
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
    
#     # Dates
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     objects = UserManager()
    
#     USERNAME_FIELD = 'phone_number'
#     REQUIRED_FIELDS = []
    
#     class Meta:
#         db_table = 'users'
#         verbose_name = 'Utilisateur'
#         verbose_name_plural = 'Utilisateurs'
    
#     def __str__(self):
#         return self.phone_number
    
#     def get_full_name(self):
#         return self.display_name or self.phone_number
    
#     def get_short_name(self):
#         return self.display_name or self.phone_number

# # ========================================
# # MODÈLE DEVICE (Multi-device)
# # ========================================
# class Device(models.Model):
#     """Gestion des appareils connectés (multi-device)"""
    
#     id = models.BigAutoField(primary_key=True)
#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name='devices'
#     )
#     device_id = models.UUIDField(
#         db_index=True,
#         help_text="UUID généré par Flutter"
#     )
#     device_name = models.CharField(
#         max_length=100,
#         blank=True,
#         null=True
#     )
#     device_type = models.CharField(
#         max_length=20,
#         choices=[
#             ('ios', 'iOS'),
#             ('android', 'Android'),
#             ('web', 'Web'),
#         ],
#         default='android'
#     )
#     fcm_token = models.TextField(
#         blank=True,
#         null=True,
#         help_text="Firebase token pour notifications"
#     )
#     is_active = models.BooleanField(default=True)
#     last_seen = models.DateTimeField(auto_now=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'devices'
#         verbose_name = 'Device'
#         verbose_name_plural = 'Devices'
#         unique_together = ['user', 'device_id']
#         ordering = ['-last_seen']
#         indexes = [
#             models.Index(fields=['device_id']),
#             models.Index(fields=['user', 'is_active']),
#         ]
    
#     def __str__(self):
#         return f"{self.device_name or self.device_type} - {self.user.phone_number}"


# # ========================================
# # MODÈLE SESSION (JWT Tracking)
# # ========================================
# class Session(models.Model):
#     """
#     Gestion des sessions JWT
#     Permet révocation immédiate des tokens
#     """
    
#     id = models.BigAutoField(primary_key=True)
#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name='sessions'
#     )
#     device = models.ForeignKey(
#         Device,
#         on_delete=models.CASCADE,
#         related_name='sessions',
#         null=True,
#         blank=True
#     )
    
#     # JWT identifiers (JTI uniquement, pas les tokens!)
#     access_token_jti = models.CharField(
#         max_length=255,
#         unique=True,
#         db_index=True
#     )
#     refresh_token_jti = models.CharField(
#         max_length=255,
#         unique=True,
#         db_index=True
#     )
    
#     # Expiration
#     access_token_expires_at = models.DateTimeField()
#     refresh_token_expires_at = models.DateTimeField()
    
#     # État
#     is_active = models.BooleanField(
#         default=True,
#         db_index=True
#     )
    
#     # Métadonnées sécurité
#     ip_address = models.GenericIPAddressField(
#         null=True,
#         blank=True
#     )
#     user_agent = models.TextField(
#         blank=True,
#         null=True
#     )
    
#     # Timestamps
#     last_used = models.DateTimeField(auto_now=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'sessions'
#         verbose_name = 'Session'
#         verbose_name_plural = 'Sessions'
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['access_token_jti']),
#             models.Index(fields=['refresh_token_jti']),
#             models.Index(fields=['user', 'is_active']),
#         ]
    
#     def __str__(self):
#         device_info = self.device.device_type if self.device else 'Unknown'
#         return f"Session {self.user.phone_number} - {device_info}"
    
#     @property
#     def is_expired(self):
#         """Vérifie si la session est expirée"""
#         return timezone.now() > self.refresh_token_expires_at

