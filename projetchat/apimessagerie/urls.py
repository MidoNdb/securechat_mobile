# apimessagerie/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse

# Import de la vue public_keys
from authentification.views import public_keys_view

# ========================================
# SWAGGER/OPENAPI CONFIGURATION
# ========================================
schema_view = get_schema_view(
    openapi.Info(
        title="SecureChat API",
        default_version='v1',
        description="API REST pour SecureChat - Messagerie E2E Chiffrée",
        contact=openapi.Contact(email="contact@securechat.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# ========================================
# URL PATTERNS
# ========================================
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    
    # ✅ CORRECTION : Route publique des clés publiques (AVANT les includes)
    re_path(
        r'^api/users/(?P<user_id>[0-9a-f-]+)/public-keys/$',
        public_keys_view,
        name='public-keys'
    ),
    
    # API Apps
    path('api/auth/', include('authentification.urls')),
    path('api/', include('messagerie.urls')),
    
    # Health Check
    path('api/health/', lambda request: JsonResponse({'status': 'ok'}), name='health-check'),
]

# Media Files (Development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin Customization
admin.site.site_header = "SecureChat Administration"
admin.site.site_title = "SecureChat Admin"
admin.site.index_title = "Bienvenue sur SecureChat Admin"


# # apimessagerie/urls.py

# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from django.http import JsonResponse

# # ========================================
# # SWAGGER/OPENAPI CONFIGURATION
# # ========================================
# schema_view = get_schema_view(
#     openapi.Info(
#         title="SecureChat API",
#         default_version='v1',
#         description="""
#         API REST pour SecureChat - Messagerie E2E Chiffrée
        
#         ## Fonctionnalités
        
#         ### Authentification
#         - Inscription avec clé publique RSA
#         - Connexion avec JWT
#         - Multi-device support
#         - Gestion des sessions
        
#         ### Sécurité
#         - Tokens JWT avec rotation
#         - End-to-End Encryption
#         - Session tracking
#         - Device management
        
#         ## Authentication
        
#         La plupart des endpoints nécessitent un token JWT.
        
#         **Header:**
# ```
#         Authorization: Bearer {access_token}
# ```
        
#         **Obtenir un token:**
#         1. POST /api/auth/register/ ou /api/auth/login/
#         2. Utiliser le `access_token` retourné
        
#         **Rafraîchir un token:**
#         - POST /api/auth/refresh/ avec le `refresh_token`
#         """,
#         terms_of_service="https://www.securechat.com/terms/",
#         contact=openapi.Contact(email="contact@securechat.com"),
#         license=openapi.License(name="MIT License"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )

# # ========================================
# # URL PATTERNS
# # ========================================
# urlpatterns = [
#     # Admin
#     path('admin/', admin.site.urls),
    
#     # API Documentation (Swagger)
#     path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
#     path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
#     path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
#     path('api/swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
#     path('api/swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
    
#     # API Endpoints
#     path('api/auth/', include('authentification.urls')),
#     path('api/', include('messagerie.urls')),
    
#     # Health Check
#     path('api/health/', lambda request: JsonResponse({'status': 'ok'}), name='health-check'),
# ]

# # Media Files (Development only)
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# # Admin Customization
# admin.site.site_header = "SecureChat Administration"
# admin.site.site_title = "SecureChat Admin"
# admin.site.index_title = "Bienvenue sur SecureChat Admin"



