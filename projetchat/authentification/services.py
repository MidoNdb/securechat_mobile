# authentification/services.py

from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
import hashlib

from .models import User, Device, Session

# ========================================
# AUTHENTICATION SERVICE
# ========================================

class AuthService:
    """Service pour gérer l'authentification"""
    
    @staticmethod
    def generate_safety_number(user_id, dh_key, sign_key):
        """Générer numéro de sécurité unique"""
        data = f"{user_id}{dh_key}{sign_key}".encode()
        hash_digest = hashlib.sha256(data).hexdigest()
        return '-'.join([hash_digest[i:i+4] for i in range(0, 12, 4)])
    
    @staticmethod
    @transaction.atomic
    def register_user(phone_number, password, dh_public_key, sign_public_key,
                     device_id, display_name=None, email=None, 
                     device_name=None, device_type='android'):
        """Inscription nouvel utilisateur"""
        
        if User.objects.filter(phone_number=phone_number).exists():
            raise Exception(f"Le numéro {phone_number} est déjà enregistré.")
        
        # Créer utilisateur
        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            display_name=display_name,
            email=email,
            dh_public_key=dh_public_key,
            sign_public_key=sign_public_key,
        )
        
        # Générer safety_number
        user.safety_number = AuthService.generate_safety_number(
            user.user_id,
            dh_public_key,
            sign_public_key
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


# ========================================
# TOKEN SERVICE
# ========================================

class TokenService:
    """Service pour gérer les tokens JWT"""
    
    @staticmethod
    @transaction.atomic
    def create_tokens_for_user(user, device_id, ip_address=None,
                               user_agent=None, device_name=None,
                               device_type='android'):
        """Créer tokens JWT"""
        
        # Créer/Mettre à jour device unique
        device, _ = Device.objects.update_or_create(
            user=user,
            defaults={
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type,
            }
        )
        
        # Générer tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        # Claims personnalisés
        access['user_id'] = str(user.user_id)
        access['phone_number'] = user.phone_number
        access['device_id'] = str(device_id)
        
        refresh['user_id'] = str(user.user_id)
        refresh['phone_number'] = user.phone_number
        refresh['device_id'] = str(device_id)
        
        # Créer/Mettre à jour session unique
        Session.objects.update_or_create(
            user=user,
            defaults={
                'device': device,
                'access_token_jti': str(access['jti']),
                'refresh_token_jti': str(refresh['jti']),
                'access_token_expires_at': timezone.now() + timedelta(minutes=15),
                'refresh_token_expires_at': timezone.now() + timedelta(days=30),
                'ip_address': ip_address,
                'user_agent': user_agent,
            }
        )
        
        user.last_seen = timezone.now()
        user.save(update_fields=['last_seen'])
        
        return {
            'access': str(access),
            'refresh': str(refresh),
            'user': user,
        }


# ========================================
# USER SERVICE
# ========================================

class UserService:
    """Service pour gérer les utilisateurs"""
    
    @staticmethod
    def update_user_profile(user, **kwargs):
        """Mettre à jour le profil"""
        allowed_fields = ['display_name', 'email', 'bio', 'avatar']
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)
        
        user.save()
        return user
    
    @staticmethod
    def delete_account(user):
        """Supprimer le compte"""
        user.delete()





# # authentification/services.py

# from django.contrib.auth import authenticate
# from django.utils import timezone
# from django.db import transaction
# from rest_framework_simplejwt.tokens import RefreshToken
# from datetime import timedelta
# import hashlib
# import uuid

# from .models import User, Device, Session
# from .exceptions import (
#     InvalidCredentialsException,
#     UserAlreadyExistsException,
#     SessionExpiredException,
#     DeviceNotFoundException
# )

# # ========================================
# # AUTHENTICATION SERVICE
# # ========================================

# class AuthService:
#     """Service pour gérer l'authentification"""
    
#     @staticmethod
#     def generate_safety_number(user_id, public_key):
#         """
#         Générer un numéro de sécurité unique
#         Format: XXXX-XXXX-XXXX
#         """
#         data = f"{user_id}{public_key}".encode()
#         hash_digest = hashlib.sha256(data).hexdigest()
#         return '-'.join([hash_digest[i:i+4] for i in range(0, 12, 4)])
    
#     @staticmethod
#     @transaction.atomic
#     def register_user(phone_number, password, public_key, device_id, 
#                      display_name=None, email=None, device_name=None, 
#                      device_type='android'):
#         """
#         Inscription d'un nouvel utilisateur avec son appareil
        
#         Args:
#             phone_number: Numéro de téléphone unique
#             password: Mot de passe (sera hashé)
#             public_key: Clé publique RSA (PEM)
#             device_id: UUID de l'appareil
#             display_name: Nom d'affichage (optionnel)
#             email: Email (optionnel)
#             device_name: Nom de l'appareil (optionnel)
#             device_type: Type d'appareil (ios/android/web)
        
#         Returns:
#             User: L'utilisateur créé
        
#         Raises:
#             UserAlreadyExistsException: Si le numéro existe déjà
#         """
#         # Vérifier si l'utilisateur existe
#         if User.objects.filter(phone_number=phone_number).exists():
#             raise UserAlreadyExistsException(
#                 f"Le numéro {phone_number} est déjà enregistré."
#             )
        
#         # Créer l'utilisateur
#         user = User.objects.create_user(
#             phone_number=phone_number,
#             password=password,
#             display_name=display_name,
#             email=email,
#             public_key=public_key,
#         )
        
#         # Générer le safety_number
#         user.safety_number = AuthService.generate_safety_number(
#             user.user_id, 
#             public_key
#         )
#         user.save()
        
#         # Créer l'appareil
#         Device.objects.create(
#             user=user,
#             device_id=device_id,
#             device_name=device_name,
#             device_type=device_type,
#         )
        
#         return user
    
#     @staticmethod
#     def authenticate_user(phone_number, password):
#         """
#         Authentifier un utilisateur
        
#         Args:
#             phone_number: Numéro de téléphone
#             password: Mot de passe
        
#         Returns:
#             User: L'utilisateur authentifié
        
#         Raises:
#             InvalidCredentialsException: Si les identifiants sont invalides
#         """
#         user = authenticate(username=phone_number, password=password)
        
#         if user is None:
#             raise InvalidCredentialsException(
#                 "Numéro de téléphone ou mot de passe incorrect."
#             )
        
#         if not user.is_active:
#             raise InvalidCredentialsException(
#                 "Ce compte a été désactivé."
#             )
        
#         return user


# # ========================================
# # TOKEN SERVICE
# # ========================================

# class TokenService:
#     """Service pour gérer les tokens JWT"""
    
#     @staticmethod
#     @transaction.atomic
#     def create_tokens_for_user(user, device_id, ip_address=None, 
#                                user_agent=None, device_name=None, 
#                                device_type='android'):
#         """
#         Créer des tokens JWT pour un utilisateur et enregistrer la session
        
#         Args:
#             user: Instance User
#             device_id: UUID de l'appareil
#             ip_address: Adresse IP (optionnel)
#             user_agent: User agent (optionnel)
#             device_name: Nom de l'appareil (optionnel)
#             device_type: Type d'appareil
        
#         Returns:
#             dict: {
#                 'access': token d'accès,
#                 'refresh': token de rafraîchissement,
#                 'user': données utilisateur
#             }
#         """
#         # Créer ou mettre à jour le device
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
#             device.last_seen = timezone.now()
#             device.save()
        
#         # Générer les tokens
#         refresh = RefreshToken.for_user(user)
#         access = refresh.access_token
        
#         # Ajouter des claims personnalisés
#         access['user_id'] = str(user.user_id)
#         access['phone_number'] = user.phone_number
#         access['device_id'] = str(device_id)
        
#         refresh['user_id'] = str(user.user_id)
#         refresh['phone_number'] = user.phone_number
#         refresh['device_id'] = str(device_id)
        
#         # Calculer les dates d'expiration
#         access_expires_at = timezone.now() + timedelta(minutes=15)
#         refresh_expires_at = timezone.now() + timedelta(days=30)
        
#         # Créer la session
#         Session.objects.create(
#             user=user,
#             device=device,
#             access_token_jti=str(access['jti']),
#             refresh_token_jti=str(refresh['jti']),
#             access_token_expires_at=access_expires_at,
#             refresh_token_expires_at=refresh_expires_at,
#             ip_address=ip_address,
#             user_agent=user_agent,
#         )
        
#         # Mettre à jour last_seen
#         user.last_seen = timezone.now()
#         user.save(update_fields=['last_seen'])
        
#         return {
#             'access': str(access),
#             'refresh': str(refresh),
#             'user': user,
#         }
    
#     @staticmethod
#     @transaction.atomic
#     def refresh_access_token(refresh_token_string):
#         """
#         Rafraîchir le token d'accès avec rotation du refresh token
        
#         Args:
#             refresh_token_string: Token de rafraîchissement
        
#         Returns:
#             dict: {
#                 'access': nouveau token d'accès,
#                 'refresh': nouveau token de rafraîchissement
#             }
        
#         Raises:
#             SessionExpiredException: Si la session est invalide
#         """
#         try:
#             refresh = RefreshToken(refresh_token_string)
#             refresh_jti = str(refresh['jti'])
            
#             # Vérifier la session
#             try:
#                 session = Session.objects.get(
#                     refresh_token_jti=refresh_jti,
#                     is_active=True
#                 )
#             except Session.DoesNotExist:
#                 raise SessionExpiredException("Session invalide ou expirée.")
            
#             # Vérifier l'expiration
#             if session.is_expired:
#                 session.is_active = False
#                 session.save()
#                 raise SessionExpiredException("Session expirée.")
            
#             # Générer nouveau access token
#             access = refresh.access_token
            
#             # Copier les claims personnalisés
#             access['user_id'] = refresh.get('user_id')
#             access['phone_number'] = refresh.get('phone_number')
#             access['device_id'] = refresh.get('device_id')
            
#             # Rotation du refresh token
#             new_refresh = refresh
#             new_refresh.set_jti()
#             new_refresh.set_exp()
            
#             # Mettre à jour la session
#             session.access_token_jti = str(access['jti'])
#             session.refresh_token_jti = str(new_refresh['jti'])
#             session.access_token_expires_at = timezone.now() + timedelta(minutes=15)
#             session.refresh_token_expires_at = timezone.now() + timedelta(days=30)
#             session.last_used = timezone.now()
#             session.save()
            
#             return {
#                 'access': str(access),
#                 'refresh': str(new_refresh),
#             }
            
#         except Exception as e:
#             raise SessionExpiredException(f"Token invalide: {str(e)}")
    
#     @staticmethod
#     def invalidate_session(access_token_jti):
#         """
#         Invalider une session (logout)
        
#         Args:
#             access_token_jti: JTI du token d'accès
#         """
#         Session.objects.filter(
#             access_token_jti=access_token_jti
#         ).update(is_active=False)
    
#     @staticmethod
#     def invalidate_all_user_sessions(user):
#         """
#         Invalider toutes les sessions d'un utilisateur
        
#         Args:
#             user: Instance User
#         """
#         Session.objects.filter(
#             user=user,
#             is_active=True
#         ).update(is_active=False)
    
#     @staticmethod
#     def get_active_sessions(user):
#         """
#         Récupérer toutes les sessions actives d'un utilisateur
        
#         Args:
#             user: Instance User
        
#         Returns:
#             QuerySet: Sessions actives
#         """
#         return Session.objects.filter(
#             user=user,
#             is_active=True
#         ).select_related('device').order_by('-last_used')


# # ========================================
# # DEVICE SERVICE
# # ========================================

# class DeviceService:
#     """Service pour gérer les appareils"""
    
#     @staticmethod
#     def get_user_devices(user):
#         """
#         Récupérer tous les appareils d'un utilisateur
        
#         Args:
#             user: Instance User
        
#         Returns:
#             QuerySet: Devices de l'utilisateur
#         """
#         return Device.objects.filter(user=user).order_by('-last_seen')
    
#     @staticmethod
#     def deactivate_device(user, device_id):
#         """
#         Désactiver un appareil et ses sessions
        
#         Args:
#             user: Instance User
#             device_id: UUID de l'appareil
        
#         Raises:
#             DeviceNotFoundException: Si l'appareil n'existe pas
#         """
#         try:
#             device = Device.objects.get(user=user, device_id=device_id)
#             device.is_active = False
#             device.save()
            
#             # Invalider toutes les sessions de cet appareil
#             Session.objects.filter(
#                 device=device,
#                 is_active=True
#             ).update(is_active=False)
            
#         except Device.DoesNotExist:
#             raise DeviceNotFoundException(
#                 f"Appareil {device_id} non trouvé."
#             )
    
#     @staticmethod
#     def update_fcm_token(user, device_id, fcm_token):
#         """
#         Mettre à jour le token FCM d'un appareil
        
#         Args:
#             user: Instance User
#             device_id: UUID de l'appareil
#             fcm_token: Token Firebase Cloud Messaging
        
#         Raises:
#             DeviceNotFoundException: Si l'appareil n'existe pas
#         """
#         try:
#             device = Device.objects.get(user=user, device_id=device_id)
#             device.fcm_token = fcm_token
#             device.save()
#         except Device.DoesNotExist:
#             raise DeviceNotFoundException(
#                 f"Appareil {device_id} non trouvé."
#             )


# # ========================================
# # USER SERVICE
# # ========================================

# class UserService:
#     """Service pour gérer les utilisateurs"""
    
#     @staticmethod
#     def update_user_profile(user, **kwargs):
#         """
#         Mettre à jour le profil utilisateur
        
#         Args:
#             user: Instance User
#             **kwargs: Champs à mettre à jour
        
#         Returns:
#             User: Utilisateur mis à jour
#         """
#         allowed_fields = ['display_name', 'email', 'bio', 'avatar']
        
#         for field, value in kwargs.items():
#             if field in allowed_fields and value is not None:
#                 setattr(user, field, value)
        
#         user.save()
#         return user
    
#     @staticmethod
#     def change_password(user, old_password, new_password, keep_current_session=True, current_jti=None):
#         """
#         Changer le mot de passe et invalider les sessions
        
#         Args:
#             user: Instance User
#             old_password: Ancien mot de passe
#             new_password: Nouveau mot de passe
#             keep_current_session: Garder la session courante active
#             current_jti: JTI de la session courante
        
#         Raises:
#             InvalidCredentialsException: Si l'ancien mot de passe est incorrect
#         """
#         if not user.check_password(old_password):
#             raise InvalidCredentialsException("Mot de passe incorrect.")
        
#         # Changer le mot de passe
#         user.set_password(new_password)
#         user.save()
        
#         # Invalider les sessions
#         if keep_current_session and current_jti:
#             Session.objects.filter(
#                 user=user,
#                 is_active=True
#             ).exclude(
#                 access_token_jti=current_jti
#             ).update(is_active=False)
#         else:
#             TokenService.invalidate_all_user_sessions(user)
    
#     @staticmethod
#     def delete_account(user):
#         """
#         Supprimer le compte utilisateur
        
#         Args:
#             user: Instance User
#         """
#         # Les cascades supprimeront automatiquement:
#         # - Devices
#         # - Sessions
#         # - Messages (si configuré)
#         user.delete()
    
#     @staticmethod
#     def search_users_by_phone(phone_number_query):
#         """
#         Rechercher des utilisateurs par numéro de téléphone
        
#         Args:
#             phone_number_query: Début du numéro à rechercher
        
#         Returns:
#             QuerySet: Utilisateurs trouvés
#         """
#         return User.objects.filter(
#             phone_number__icontains=phone_number_query,
#             is_active=True
#         )
    
#     @staticmethod
#     def get_user_by_phone(phone_number):
#         """
#         Récupérer un utilisateur par son numéro
        
#         Args:
#             phone_number: Numéro de téléphone
        
#         Returns:
#             User ou None
#         """
#         try:
#             return User.objects.get(phone_number=phone_number, is_active=True)
#         except User.DoesNotExist:
#             return None
    
#     @staticmethod
#     def update_online_status(user, is_online):
#         """
#         Mettre à jour le statut en ligne
        
#         Args:
#             user: Instance User
#             is_online: Boolean
#         """
#         user.is_online = is_online
#         if not is_online:
#             user.last_seen = timezone.now()
#         user.save(update_fields=['is_online', 'last_seen'])