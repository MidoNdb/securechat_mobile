# authentification/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from .models import User, Device, Session
from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    RegisterSerializer,
    LoginSerializer,
    CustomTokenRefreshSerializer,
    DeviceSerializer,
    SessionSerializer,
    ChangePasswordSerializer,
)
from .services import TokenService

# ========================================
# HELPER FUNCTIONS
# ========================================

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')

def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)

def error_response(message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({
        'success': False,
        'error': {
            'message': message,
            'details': details,
            'code': status_code
        }
    }, status=status_code)


# ========================================
# REGISTER VIEW
# ========================================

class RegisterView(generics.CreateAPIView):
    """Inscription avec clés DH + Ed25519 + backup chiffré"""
    
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Créer tokens
                tokens = TokenService.create_tokens_for_user(
                    user=user,
                    device_id=serializer.validated_data['device_id'],
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    device_name=serializer.validated_data.get('device_name'),
                    device_type=serializer.validated_data.get('device_type', 'android'),
                )
                
                print(f'✅ Inscription réussie: {user.phone_number}')
                if user.encrypted_private_keys:
                    print('✅ Backup des clés sauvegardé')
                
                return success_response(
                    data={
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'access': tokens['access'],
                            'refresh': tokens['refresh'],
                        }
                    },
                    message="Compte créé avec succès",
                    status_code=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                print(f'❌ Erreur register: {e}')
                return error_response(
                    message="Erreur lors de la création du compte",
                    details=str(e),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return error_response(
            message="Données invalides",
            details=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ========================================
# LOGIN VIEW (SIMPLIFIÉ - PAS DE RÉGÉNÉRATION)
# ========================================

class LoginView(generics.GenericAPIView):
    """
    Login simplifié - Authentification uniquement
    La récupération/régénération des clés est gérée côté client
    """
    
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.validated_data['user']
                device_id = request.data.get('device_id')
                device_name = request.data.get('device_name')
                device_type = request.data.get('device_type', 'android')
                
                # Mise à jour/création du Device
                Device.objects.update_or_create(
                    user=user,
                    defaults={
                        'device_id': device_id,
                        'device_name': device_name or 'Unknown Device',
                        'device_type': device_type,
                    }
                )
                
                # Créer tokens
                tokens = TokenService.create_tokens_for_user(
                    user=user,
                    device_id=device_id,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    device_name=device_name,
                    device_type=device_type,
                )
                
                # Vérifier si un backup existe
                has_backup = bool(user.encrypted_private_keys)
                
                print(f'✅ Login réussi: {user.phone_number}')
                print(f'📦 Backup disponible: {has_backup}')
                
                return success_response(
                    data={
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'access': tokens['access'],
                            'refresh': tokens['refresh'],
                        },
                        'has_backup': has_backup,  # ✅ Info pour le client
                    },
                    message="Connexion réussie"
                )
                
            except Exception as e:
                print(f'❌ Erreur login: {e}')
                return error_response(
                    message="Erreur lors de la connexion",
                    details=str(e),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return error_response(
            message="Données invalides",
            details=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ========================================
# LOGOUT VIEW
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Déconnexion"""
    
    try:
        Session.objects.filter(user=request.user).delete()
        return success_response(message="Déconnexion réussie")
    except Exception as e:
        return error_response(
            message="Erreur lors de la déconnexion",
            details=str(e)
        )


# ========================================
# CURRENT USER VIEW
# ========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Récupérer infos utilisateur connecté"""
    
    serializer = UserSerializer(request.user)
    return success_response(data=serializer.data)


# ========================================
# UPDATE PROFILE VIEW
# ========================================

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """Mettre à jour le profil"""
    
    serializer = UserUpdateSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return success_response(
            data=UserSerializer(request.user).data,
            message="Profil mis à jour"
        )
    
    return error_response(
        message="Données invalides",
        details=serializer.errors
    )


# ========================================
# CHANGE PASSWORD VIEW
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Changer le mot de passe"""
    
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        try:
            serializer.save()
            return success_response(message="Mot de passe changé avec succès")
        except Exception as e:
            return error_response(
                message="Erreur lors du changement de mot de passe",
                details=str(e)
            )
    
    return error_response(
        message="Données invalides",
        details=serializer.errors
    )


# ========================================
# REFRESH TOKEN VIEW
# ========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Rafraîchir le token d'accès"""
    
    serializer = CustomTokenRefreshSerializer(data=request.data)
    
    if serializer.is_valid():
        return success_response(
            data=serializer.validated_data,
            message="Token rafraîchi"
        )
    
    return error_response(
        message="Token invalide",
        details=serializer.errors,
        status_code=status.HTTP_401_UNAUTHORIZED
    )


# ========================================
# ACTIVE SESSION VIEW
# ========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_session_view(request):
    """Récupérer la session active"""
    
    try:
        session = Session.objects.get(user=request.user)
        serializer = SessionSerializer(session)
        return success_response(data=serializer.data)
    except Session.DoesNotExist:
        return error_response(
            message="Aucune session active",
            status_code=status.HTTP_404_NOT_FOUND
        )


# ========================================
# DELETE ACCOUNT VIEW
# ========================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """Supprimer le compte utilisateur"""
    
    try:
        # Supprimer sessions, devices et utilisateur
        Session.objects.filter(user=request.user).delete()
        Device.objects.filter(user=request.user).delete()
        request.user.delete()
        return success_response(message="Compte supprimé avec succès")
    except Exception as e:
        return error_response(
            message="Erreur lors de la suppression",
            details=str(e)
        )


# ========================================
# PUBLIC KEYS VIEW (POUR CHIFFREMENT E2E)
# ========================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def public_keys_view(request, user_id):
    """
    GET /api/users/{user_id}/public-keys/
    
    Récupère les clés publiques DH + Ed25519 d'un utilisateur.
    Nécessaire pour chiffrer des messages destinés à cet utilisateur.
    """
    try:
        user = get_object_or_404(User, user_id=user_id)
        
        if not user.dh_public_key or not user.sign_public_key:
            return error_response(
                message='Clés publiques non disponibles pour cet utilisateur',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        print(f'✅ Clés publiques récupérées pour {user.phone_number}')
        
        return success_response(
            data={
                'user_id': str(user.user_id),
                'phone_number': user.phone_number,
                'display_name': user.display_name or user.phone_number,
                'dh_public_key': user.dh_public_key,
                'sign_public_key': user.sign_public_key,
            }
        )
    
    except Exception as e:
        print(f'❌ public_keys_view error: {e}')
        return error_response(
            message='Erreur lors de la récupération des clés',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================================
# POST: Upload clés publiques
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_public_keys_view(request):
    """
    POST /api/users/public-keys/
    
    Upload/mise à jour des clés publiques de l'utilisateur connecté.
    Appelé UNE SEULE FOIS lors de:
    - L'inscription (après création compte)
    - Premier login (si clés pas encore générées)
    
    Body:
        {
            "dh_public_key": "base64_encoded_x25519_public_key",
            "sign_public_key": "base64_encoded_ed25519_public_key"
        }
    
    Returns:
        {
            "success": true,
            "message": "Clés publiques enregistrées avec succès"
        }
    
    Example:
        POST /api/users/public-keys/
        Headers: 
            Authorization: Bearer <token>
            Content-Type: application/json
        Body:
            {
                "dh_public_key": "MCowBQYDK2VuAy...",
                "sign_public_key": "MCowBQYDK2VwAy..."
            }
    """
    try:
        dh_public_key = request.data.get('dh_public_key')
        sign_public_key = request.data.get('sign_public_key')
        
        # Validation
        if not dh_public_key or not sign_public_key:
            return Response(
                {
                    'success': False,
                    'error': 'dh_public_key et sign_public_key sont requis'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation longueur (approximative)
        if len(dh_public_key) < 20 or len(sign_public_key) < 20:
            return Response(
                {
                    'success': False,
                    'error': 'Les clés semblent invalides (trop courtes)'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mise à jour du user
        user = request.user
        user.dh_public_key = dh_public_key
        user.sign_public_key = sign_public_key
        user.save(update_fields=['dh_public_key', 'sign_public_key', 'updated_at'])
        
        print(f'✅ Clés publiques uploadées pour {user.phone_number}')
        print(f'   DH key: {dh_public_key[:30]}...')
        print(f'   Sign key: {sign_public_key[:30]}...')
        
        return Response({
            'success': True,
            'message': 'Clés publiques enregistrées avec succès',
            'data': {
                'user_id': str(user.user_id),
                'dh_public_key': dh_public_key,
                'sign_public_key': sign_public_key,
            }
        })
    
    except Exception as e:
        print(f'❌ upload_public_keys_view error: {e}')
        import traceback
        traceback.print_exc()
        return Response(
            {
                'success': False,
                'error': 'Erreur lors de l\'upload des clés'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
# ========================================
# BACKUP CLÉS PRIVÉES CHIFFRÉES
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_encrypted_keys_view(request):
    """
    POST /api/auth/backup-keys/
    Sauvegarder le backup chiffré des clés privées
    """
    try:
        encrypted_backup = request.data.get('encrypted_private_keys')
        
        if not encrypted_backup:
            return error_response(
                message="encrypted_private_keys requis",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Sauvegarder
        user = request.user
        user.encrypted_private_keys = encrypted_backup
        user.save(update_fields=['encrypted_private_keys'])
        
        print(f'✅ Backup clés sauvegardé pour {user.phone_number}')
        
        return success_response(
            message="Backup des clés sauvegardé avec succès"
        )
        
    except Exception as e:
        print(f'❌ Erreur upload_encrypted_keys: {e}')
        return error_response(
            message="Erreur lors de la sauvegarde",
            details=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_encrypted_keys_view(request):
    """
    GET /api/auth/backup-keys/
    Récupérer le backup chiffré des clés privées
    """
    try:
        user = request.user
        
        if not user.encrypted_private_keys:
            return error_response(
                message="Aucun backup disponible",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        print(f'✅ Backup clés récupéré pour {user.phone_number}')
        
        return success_response(
            data={
                'encrypted_private_keys': user.encrypted_private_keys
            }
        )
        
    except Exception as e:
        print(f'❌ Erreur download_encrypted_keys: {e}')
        return error_response(
            message="Erreur lors de la récupération",
            details=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ========================================
# UPDATE PUBLIC KEYS (après régénération)
# ========================================

@api_view(['POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_public_keys_view(request):
    """
    POST/PUT/PATCH /api/users/public-keys/
    
    Mettre à jour les clés publiques de l'utilisateur connecté
    (Utilisé après régénération des clés)
    """
    try:
        dh_public_key = request.data.get('dh_public_key')
        sign_public_key = request.data.get('sign_public_key')
        
        # Validation
        if not dh_public_key or not sign_public_key:
            return error_response(
                message='dh_public_key et sign_public_key sont requis',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation longueur (approximative)
        if len(dh_public_key) < 20 or len(sign_public_key) < 20:
            return error_response(
                message='Les clés semblent invalides (trop courtes)',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Mise à jour du user
        user = request.user
        user.dh_public_key = dh_public_key
        user.sign_public_key = sign_public_key
        
        # Régénérer safety_number
        import hashlib
        data = f"{user.user_id}{dh_public_key}{sign_public_key}".encode()
        hash_digest = hashlib.sha256(data).hexdigest()
        user.safety_number = '-'.join([hash_digest[i:i+4] for i in range(0, 12, 4)])
        
        user.save(update_fields=['dh_public_key', 'sign_public_key', 'safety_number', 'updated_at'])
        
        print(f'✅ Clés publiques mises à jour pour {user.phone_number}')
        print(f'   DH key: {dh_public_key[:30]}...')
        print(f'   Sign key: {sign_public_key[:30]}...')
        print(f'   Safety number: {user.safety_number}')
        
        return success_response(
            message='Clés publiques mises à jour avec succès',
            data={
                'user_id': str(user.user_id),
                'dh_public_key': dh_public_key,
                'sign_public_key': sign_public_key,
                'safety_number': user.safety_number,
            }
        )
    
    except Exception as e:
        print(f'❌ update_public_keys_view error: {e}')
        import traceback
        traceback.print_exc()
        return error_response(
            message='Erreur lors de la mise à jour des clés',
            details=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )