# authentification/exceptions.py

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour des réponses cohérentes
    """
    # Appeler le gestionnaire par défaut de DRF
    response = exception_handler(exc, context)
    
    if response is not None:
        # Formater la réponse d'erreur de manière cohérente
        custom_response_data = {
            'success': False,
            'error': {
                'message': None,
                'details': None,
                'code': None
            }
        }
        
        # Extraire le message d'erreur
        if isinstance(response.data, dict):
            # Si c'est un dict, essayer d'extraire le message
            if 'detail' in response.data:
                custom_response_data['error']['message'] = response.data['detail']
            else:
                custom_response_data['error']['message'] = 'Une erreur est survenue'
                custom_response_data['error']['details'] = response.data
        elif isinstance(response.data, list):
            custom_response_data['error']['message'] = response.data[0] if response.data else 'Erreur'
        else:
            custom_response_data['error']['message'] = str(response.data)
        
        # Ajouter le code d'erreur
        custom_response_data['error']['code'] = response.status_code
        
        response.data = custom_response_data
    
    return response


class AuthenticationException(Exception):
    """Exception de base pour les erreurs d'authentification"""
    pass


class InvalidCredentialsException(AuthenticationException):
    """Exception pour identifiants invalides"""
    pass


class UserAlreadyExistsException(AuthenticationException):
    """Exception pour utilisateur déjà existant"""
    pass


class SessionExpiredException(AuthenticationException):
    """Exception pour session expirée"""
    pass


class DeviceNotFoundException(AuthenticationException):
    """Exception pour appareil non trouvé"""
    pass