# authentification/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Device, Session

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin pour User"""
    
    list_display = [
        'id', 'phone_number', 'display_name', 'email',
        'is_verified', 'is_online', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'is_verified', 'is_online', 'is_staff', 'created_at']
    search_fields = ['phone_number', 'display_name', 'email', 'user_id']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Authentification', {
            'fields': ('phone_number', 'password', 'email')
        }),
        ('Profil', {
            'fields': ('display_name', 'avatar', 'bio')
        }),
        ('Cryptographie', {
            'fields': ('dh_public_key', 'sign_public_key', 'safety_number'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_online', 'last_seen', 'is_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['user_id', 'created_at', 'updated_at']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'display_name'),
        }),
    )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin pour Device"""
    
    list_display = ['id', 'user', 'device_type', 'device_name', 'last_seen', 'created_at']
    list_filter = ['device_type', 'created_at']
    search_fields = ['user__phone_number', 'device_id', 'device_name']
    ordering = ['-last_seen']
    readonly_fields = ['created_at', 'last_seen']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin pour Session"""
    
    list_display = ['id', 'user', 'device', 'created_at', 'expires_status']
    list_filter = ['created_at']
    search_fields = ['user__phone_number', 'access_token_jti', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'last_used']
    
    def expires_status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expiré</span>')
        return format_html('<span style="color: green;">Valide</span>')
    expires_status.short_description = 'Statut'



# # authentification/admin.py

# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.html import format_html
# from .models import User, Device, Session

# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     """Admin pour User"""
    
#     list_display = [
#         'id', 'phone_number', 'display_name', 'email',
#         'is_verified', 'is_online', 'is_active', 'created_at'
#     ]
#     list_filter = ['is_active', 'is_verified', 'is_online', 'is_staff', 'created_at']
#     search_fields = ['phone_number', 'display_name', 'email', 'user_id']
#     ordering = ['-created_at']
    
#     fieldsets = (
#         ('Authentification', {
#             'fields': ('phone_number', 'password', 'email')
#         }),
#         ('Profil', {
#             'fields': ('display_name', 'avatar', 'bio')
#         }),
#         ('Cryptographie', {
#             'fields': ('public_key', 'safety_number'),
#             'classes': ('collapse',)
#         }),
#         ('Statut', {
#             'fields': ('is_online', 'last_seen', 'is_verified')
#         }),
#         ('Permissions', {
#             'fields': ('is_active', 'is_staff', 'is_superuser'),
#         }),
#         ('Dates', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
    
#     readonly_fields = ['user_id', 'phone_number_hash', 'created_at', 'updated_at']
    
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('phone_number', 'password1', 'password2', 'display_name'),
#         }),
#     )


# @admin.register(Device)
# class DeviceAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'device_type', 'device_name', 'is_active', 'last_seen']
#     list_filter = ['device_type', 'is_active', 'created_at']
#     search_fields = ['user__phone_number', 'device_id', 'device_name']
#     ordering = ['-last_seen']


# @admin.register(Session)
# class SessionAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'device', 'is_active', 'created_at', 'expires_status']
#     list_filter = ['is_active', 'created_at']
#     search_fields = ['user__phone_number', 'access_token_jti', 'ip_address']
#     ordering = ['-created_at']
#     readonly_fields = ['created_at', 'last_used']
    
#     def expires_status(self, obj):
#         if obj.is_expired:
#             return format_html('<span style="color: red;">Expiré</span>')
#         return format_html('<span style="color: green;">Valide</span>')
#     expires_status.short_description = 'Statut'