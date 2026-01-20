# authentification/urls.py

from django.urls import path, re_path
from .views import (
    RegisterView,
    LoginView,
    update_public_keys_view,
    upload_encrypted_keys_view,
    download_encrypted_keys_view,
    logout_view,
    current_user_view,
    update_profile_view,
    change_password_view,
    refresh_token_view,
    active_session_view,
    delete_account_view,
    public_keys_view,
)

app_name = 'authentification'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', refresh_token_view, name='token-refresh'),
    
    # User Profile
    path('me/', current_user_view, name='me'),
    path('profile/', update_profile_view, name='update-profile'),
    path('change-password/', change_password_view, name='change-password'),
    path('delete-account/', delete_account_view, name='delete-account'),
    
    # Session
    path('session/', active_session_view, name='active-session'),
    
    # ✅ BACKUP KEYS - Deux routes séparées pour GET et POST
    path('backup-keys/upload/', upload_encrypted_keys_view, name='upload-backup-keys'),
    path('backup-keys/download/', download_encrypted_keys_view, name='download-backup-keys'),
    
    # Public Keys
    path('users/public-keys/', update_public_keys_view, name='update-public-keys'),
    re_path(r'^users/(?P<user_id>[0-9a-f-]+)/public-keys/$', public_keys_view, name='public-keys'),
    
]


# # authentification/urls.py

# from django.urls import path
# from django.urls import path, re_path
# from .views import (
#     RegisterView,
#     LoginView,
#     download_encrypted_keys_view,
#     logout_view,
#     current_user_view,
#     update_profile_view,
#     change_password_view,
#     refresh_token_view,
#     active_session_view,
#     delete_account_view,
#     public_keys_view,
#     upload_encrypted_keys_view,  # ← AJOUTÉ
# )


# app_name = 'authentification'

# urlpatterns = [
#     # Authentication
#     re_path(r'^users/(?P<user_id>[0-9a-f-]+)/public-keys/$', public_keys_view, name='public-keys'),
#     path('register/', RegisterView.as_view(), name='register'),
#     path('login/', LoginView.as_view(), name='login'),
#     path('logout/', logout_view, name='logout'),
#     path('refresh/', refresh_token_view, name='token-refresh'),
    
#     # User Profile
#     path('me/', current_user_view, name='me'),
#     path('profile/', update_profile_view, name='update-profile'),
#     path('change-password/', change_password_view, name='change-password'),
#     path('delete-account/', delete_account_view, name='delete-account'),
    
#     # Session
#     path('session/', active_session_view, name='active-session'),

#     path('backup-keys/', upload_encrypted_keys_view, name='upload-backup-keys'),
#     path('backup-keys/', download_encrypted_keys_view, name='download-backup-keys'),
# ]

    

