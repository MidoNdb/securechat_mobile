"""
═══════════════════════════════════════════════════════════════
Django Settings - Environnement DÉVELOPPEMENT
═══════════════════════════════════════════════════════════════
Configuration optimisée pour développement local
- SQLite (base de données simple)
- InMemory Channels (pas besoin de Redis)
- CORS permissif
- Debug activé
═══════════════════════════════════════════════════════════════
"""

from pathlib import Path
from datetime import timedelta
import os

# ═══════════════════════════════════════════════════════════════
# CHEMINS DE BASE
# ═══════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).resolve().parent.parent

# ═══════════════════════════════════════════════════════════════
# SÉCURITÉ (Développement)
# ═══════════════════════════════════════════════════════════════
SECRET_KEY = 'django-insecure-$nafznxbk0u7#n7h!hzovw^&op_=un)*&@9gzp&^+p4y*f0*j5'
DEBUG = True
ALLOWED_HOSTS = ['*']

# ═══════════════════════════════════════════════════════════════
# APPLICATIONS INSTALLÉES
# ═══════════════════════════════════════════════════════════════
INSTALLED_APPS = [
    # ─────────────────────────────────────────────────────────
    # WebSocket Support (DOIT ÊTRE EN PREMIER)
    # ─────────────────────────────────────────────────────────
    'daphne',
    
    # ─────────────────────────────────────────────────────────
    # Applications Django Core
    # ─────────────────────────────────────────────────────────
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # ─────────────────────────────────────────────────────────
    # Packages Tiers
    # ─────────────────────────────────────────────────────────
    'rest_framework',               # Django REST Framework
    'rest_framework_simplejwt',     # Authentification JWT
    'corsheaders',                  # Gestion CORS
    'drf_yasg',                     # Documentation API Swagger
    'channels',                     # WebSocket support
    
    # ─────────────────────────────────────────────────────────
    # Applications Locales
    # ─────────────────────────────────────────────────────────
    'authentification',             # Gestion utilisateurs
    'messagerie',                   # Messagerie E2EE
]

# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',              # CORS (en premier)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ═══════════════════════════════════════════════════════════════
# URLS & ROUTING
# ═══════════════════════════════════════════════════════════════
ROOT_URLCONF = 'apimessagerie.urls'

# ═══════════════════════════════════════════════════════════════
# TEMPLATES
# ═══════════════════════════════════════════════════════════════
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ═══════════════════════════════════════════════════════════════
# ASGI / WSGI
# ═══════════════════════════════════════════════════════════════
ASGI_APPLICATION = 'apimessagerie.asgi.application'
WSGI_APPLICATION = 'apimessagerie.wsgi.application'

# ═══════════════════════════════════════════════════════════════
# BASE DE DONNÉES (SQLite pour développement)
# ═══════════════════════════════════════════════════════════════
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ═══════════════════════════════════════════════════════════════
# CHANNELS (WebSocket - InMemory pour développement)
# ═══════════════════════════════════════════════════════════════
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# ═══════════════════════════════════════════════════════════════
# CACHE (Local Memory pour développement)
# ═══════════════════════════════════════════════════════════════
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ═══════════════════════════════════════════════════════════════
# MODÈLE UTILISATEUR PERSONNALISÉ
# ═══════════════════════════════════════════════════════════════
AUTH_USER_MODEL = 'authentification.User'

# ═══════════════════════════════════════════════════════════════
# VALIDATION DES MOTS DE PASSE
# ═══════════════════════════════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ═══════════════════════════════════════════════════════════════
# HASHERS DE MOTS DE PASSE
# ═══════════════════════════════════════════════════════════════
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# ═══════════════════════════════════════════════════════════════
# INTERNATIONALISATION
# ═══════════════════════════════════════════════════════════════
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ═══════════════════════════════════════════════════════════════
# FICHIERS STATIQUES
# ═══════════════════════════════════════════════════════════════
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ═══════════════════════════════════════════════════════════════
# FICHIERS MÉDIA
# ═══════════════════════════════════════════════════════════════
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ═══════════════════════════════════════════════════════════════
# CHAMP AUTO PAR DÉFAUT
# ═══════════════════════════════════════════════════════════════
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ═══════════════════════════════════════════════════════════════
# DJANGO REST FRAMEWORK
# ═══════════════════════════════════════════════════════════════
REST_FRAMEWORK = {
    # ─────────────────────────────────────────────────────────
    # Authentification
    # ─────────────────────────────────────────────────────────
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    
    # ─────────────────────────────────────────────────────────
    # Permissions
    # ─────────────────────────────────────────────────────────
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    
    # ─────────────────────────────────────────────────────────
    # Renderers
    # ─────────────────────────────────────────────────────────
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Interface debug
    ),
    
    # ─────────────────────────────────────────────────────────
    # Parsers
    # ─────────────────────────────────────────────────────────
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
    
    # ─────────────────────────────────────────────────────────
    # Pagination
    # ─────────────────────────────────────────────────────────
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    
    # ─────────────────────────────────────────────────────────
    # Throttling (Désactivé en développement)
    # ─────────────────────────────────────────────────────────
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/hour',    # Très élevé en dev
        'user': '100000/hour',   # Très élevé en dev
    },
    
    # ─────────────────────────────────────────────────────────
    # Format des dates
    # ─────────────────────────────────────────────────────────
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
    'DATETIME_INPUT_FORMATS': ['%Y-%m-%dT%H:%M:%S.%fZ', 'iso-8601'],
    
    # ─────────────────────────────────────────────────────────
    # Gestion des exceptions
    # ─────────────────────────────────────────────────────────
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# ═══════════════════════════════════════════════════════════════
# SIMPLE JWT (Authentification)
# ═══════════════════════════════════════════════════════════════
SIMPLE_JWT = {
    # ─────────────────────────────────────────────────────────
    # Durée de vie des tokens
    # ─────────────────────────────────────────────────────────
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),      # 1 heure en dev
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),        # 30 jours
    
    # ─────────────────────────────────────────────────────────
    # Rotation des tokens
    # ─────────────────────────────────────────────────────────
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    # ─────────────────────────────────────────────────────────
    # Algorithme de signature
    # ─────────────────────────────────────────────────────────
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    # ─────────────────────────────────────────────────────────
    # Claims JWT
    # ─────────────────────────────────────────────────────────
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',
    
    # ─────────────────────────────────────────────────────────
    # Headers HTTP
    # ─────────────────────────────────────────────────────────
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # ─────────────────────────────────────────────────────────
    # Classes de tokens
    # ─────────────────────────────────────────────────────────
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    # ─────────────────────────────────────────────────────────
    # JTI (JWT ID unique)
    # ─────────────────────────────────────────────────────────
    'JTI_CLAIM': 'jti',
}

# ═══════════════════════════════════════════════════════════════
# CORS (Permissif en développement)
# ═══════════════════════════════════════════════════════════════
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ═══════════════════════════════════════════════════════════════
# SÉCURITÉ (Désactivée en développement)
# ═══════════════════════════════════════════════════════════════
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ═══════════════════════════════════════════════════════════════
# SESSIONS
# ═══════════════════════════════════════════════════════════════
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 semaines
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ═══════════════════════════════════════════════════════════════
# EMAIL (Console backend pour développement)
# ═══════════════════════════════════════════════════════════════
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@securechat.local'

# ═══════════════════════════════════════════════════════════════
# LOGGING (Simplifié pour développement)
# ═══════════════════════════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    # ─────────────────────────────────────────────────────────
    # Formatters
    # ─────────────────────────────────────────────────────────
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    
    # ─────────────────────────────────────────────────────────
    # Handlers
    # ─────────────────────────────────────────────────────────
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    
    # ─────────────────────────────────────────────────────────
    # Root logger
    # ─────────────────────────────────────────────────────────
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    
    # ─────────────────────────────────────────────────────────
    # Loggers spécifiques
    # ─────────────────────────────────────────────────────────
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'authentification': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'messagerie': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ═══════════════════════════════════════════════════════════════
# SWAGGER / API DOCUMENTATION
# ═══════════════════════════════════════════════════════════════
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Token (format: Bearer <token>)'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
    'DOC_EXPANSION': 'list',
    'APIS_SORTER': 'alpha',
    'OPERATIONS_SORTER': 'alpha',
}

# ═══════════════════════════════════════════════════════════════
# UPLOAD DE FICHIERS
# ═══════════════════════════════════════════════════════════════
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024      # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024      # 10 MB

# Extensions autorisées
ALLOWED_FILE_EXTENSIONS = [
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    # Vidéos
    'mp4', 'mov', 'avi', 'mkv',
    # Audio
    'mp3', 'wav', 'ogg', 'm4a',
    # Documents
    'pdf', 'doc', 'docx', 'txt',
]

# Taille maximale par type (en bytes)
MAX_FILE_SIZE = {
    'image': 10 * 1024 * 1024,      # 10 MB
    'video': 100 * 1024 * 1024,     # 100 MB
    'audio': 20 * 1024 * 1024,      # 20 MB
    'document': 10 * 1024 * 1024,   # 10 MB
}

# ═══════════════════════════════════════════════════════════════
# PARAMÈTRES PERSONNALISÉS
# ═══════════════════════════════════════════════════════════════
# Nombre maximum de devices par utilisateur
MAX_DEVICES_PER_USER = 1

# Durée de validité du code OTP (en secondes)
OTP_EXPIRY = 300  # 5 minutes

# Nombre maximum de tentatives OTP
MAX_OTP_ATTEMPTS = 3

# Délai avant de pouvoir renvoyer un OTP (en secondes)
OTP_RESEND_DELAY = 60  # 1 minute

# Timeout WebSocket
WEBSOCKET_TIMEOUT = 300  # 5 minutes

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION WEBSOCKET SÉCURISÉ (WSS)
# ═══════════════════════════════════════════════════════════════

# Hosts autorisés pour WebSocket
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Configuration SSL pour développement local
# En production, ces valeurs doivent être True
WEBSOCKET_ACCEPT_ALL = True  # Accepter tous les origins en dev

# CSRF pour WebSocket sécurisé
CSRF_TRUSTED_ORIGINS = [
    'https://localhost:8443',
    'https://127.0.0.1:8443',
    'wss://localhost:8443',
    'wss://127.0.0.1:8443',
]

# Headers de sécurité WebSocket
SECURE_WEBSOCKET_ACCEPT_ALL = True  # Dev uniquement

# Timeouts WebSocket
WEBSOCKET_CONNECT_TIMEOUT = 30  # secondes
WEBSOCKET_CLOSE_TIMEOUT = 10    # secondes

# ═══════════════════════════════════════════════════════════════
# PARAMÈTRES SSL DÉVELOPPEMENT
# ═══════════════════════════════════════════════════════════════
import os
BASE_DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SSL_CERTIFICATE = os.path.join(BASE_DIR_PATH, 'ssl_certificates', 'cert.pem')
SSL_PRIVATE_KEY = os.path.join(BASE_DIR_PATH, 'ssl_certificates', 'key.pem')

# Vérifier que les certificats existent
if not os.path.exists(SSL_CERTIFICATE):
    print(f"⚠️  ATTENTION: Certificat SSL non trouvé: {SSL_CERTIFICATE}")
    print("   Exécutez: openssl req -x509 -newkey rsa:4096 -keyout ssl_certificates/key.pem -out ssl_certificates/cert.pem -days 365 -nodes")

if not os.path.exists(SSL_PRIVATE_KEY):
    print(f"⚠️  ATTENTION: Clé privée SSL non trouvée: {SSL_PRIVATE_KEY}")