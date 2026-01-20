# messagerie/views/contact_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from messagerie.models.contact import Contact
from authentification.models import User
from messagerie.serializers.contact_serializers import (
    ContactListSerializer,
    ContactDetailSerializer,
    ContactCreateSerializer,
    ContactUpdateSerializer,
    UserSuggestionSerializer
)


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les contacts
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Retourne uniquement les contacts de l'utilisateur connecté
        """
        user = self.request.user
        
        queryset = Contact.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('contact_user')
        
        # Filtres optionnels
        favorites_only = self.request.query_params.get('favorites')
        blocked_only = self.request.query_params.get('blocked')
        
        if favorites_only == 'true':
            queryset = queryset.filter(is_favorite=True)
        
        if blocked_only == 'true':
            queryset = queryset.filter(is_blocked=True)
        
        return queryset.order_by('-is_favorite', '-added_at')
    
    def get_serializer_class(self):
        """Choisir le bon serializer"""
        if self.action == 'create':
            return ContactCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ContactUpdateSerializer
        elif self.action == 'retrieve':
            return ContactDetailSerializer
        return ContactListSerializer
    
    def list(self, request, *args, **kwargs):
        """Liste des contacts"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Recherche par nom/numéro
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nickname__icontains=search) |
                Q(contact_user__display_name__icontains=search) |
                Q(contact_user__phone_number__icontains=search)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Ajouter un nouveau contact"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        
        # Retourner avec ContactListSerializer
        detail_serializer = ContactListSerializer(contact)
        
        return Response(
            {
                'success': True,
                'message': 'Contact ajouté',
                'data': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Détails d'un contact"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Modifier un contact"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Contact mis à jour',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Supprimer un contact (soft delete)"""
        instance = self.get_object()
        instance.soft_delete()
        
        return Response({
            'success': True,
            'message': 'Contact supprimé'
        }, status=status.HTTP_204_NO_CONTENT)
    
    # ========================================
    # ACTIONS CUSTOM
    # ========================================
    
    @action(detail=True, methods=['post'])
    def block(self, request, id=None):
        """Bloquer un contact"""
        contact = self.get_object()
        contact.block()
        
        serializer = ContactListSerializer(contact)
        
        return Response({
            'success': True,
            'message': 'Contact bloqué',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, id=None):
        """Débloquer un contact"""
        contact = self.get_object()
        contact.unblock()
        
        serializer = ContactListSerializer(contact)
        
        return Response({
            'success': True,
            'message': 'Contact débloqué',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def favorite(self, request, id=None):
        """Toggle favoris"""
        contact = self.get_object()
        contact.toggle_favorite()
        
        message = 'Ajouté aux favoris' if contact.is_favorite else 'Retiré des favoris'
        
        return Response({
            'success': True,
            'message': message,
            'data': {
                'is_favorite': contact.is_favorite
            }
        })
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Liste des contacts favoris"""
        contacts = self.get_queryset().filter(is_favorite=True)
        serializer = ContactListSerializer(contacts, many=True)
        
        return Response({
            'success': True,
            'count': contacts.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def blocked(self, request):
        """Liste des contacts bloqués"""
        contacts = self.get_queryset().filter(is_blocked=True)
        serializer = ContactListSerializer(contacts, many=True)
        
        return Response({
            'success': True,
            'count': contacts.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        ✅ Rechercher des utilisateurs à ajouter
        
        GET /api/contacts/search/?q=+222
        GET /api/contacts/search/?q=alice
        """
        query = request.query_params.get('q', '').strip()
        
        print(f'🔍 Search endpoint called with query: "{query}"')
        
        if not query or len(query) < 3:
            return Response(
                {
                    'success': False,
                    'error': 'La recherche nécessite au moins 3 caractères'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rechercher utilisateurs (excluant soi-même)
        users = User.objects.filter(
            Q(phone_number__icontains=query) |
            Q(display_name__icontains=query)
        ).exclude(
            user_id=request.user.user_id
        ).filter(
            is_active=True
        )[:20]
        
        print(f'✅ Found {users.count()} users')
        
        serializer = UserSuggestionSerializer(
            users,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'count': users.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Suggestions de contacts"""
        # Exclure l'utilisateur actuel et ses contacts existants
        existing_contact_ids = Contact.objects.filter(
            user=request.user,
            is_deleted=False
        ).values_list('contact_user_id', flat=True)
        
        # Suggestions: utilisateurs actifs récents
        suggestions = User.objects.filter(
            is_active=True,
            is_verified=True
        ).exclude(
            user_id=request.user.user_id
        ).exclude(
            user_id__in=existing_contact_ids
        ).order_by('-created_at')[:10]
        
        serializer = UserSuggestionSerializer(
            suggestions,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'count': suggestions.count(),
            'data': serializer.data
        })
    

# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.db.models import Q
# from messagerie.models.contact import Contact
# from authentification.models import User
# from messagerie.serializers.contact_serializers import (
#     ContactListSerializer,
#     ContactDetailSerializer,
#     ContactCreateSerializer,
#     ContactUpdateSerializer,
#     ContactSearchSerializer,
#     UserSuggestionSerializer
# )


# class ContactViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet pour gérer les contacts
    
#     Endpoints:
#     - GET    /api/contacts/                  → Liste des contacts
#     - POST   /api/contacts/                  → Ajouter un contact
#     - GET    /api/contacts/{id}/             → Détail d'un contact
#     - PATCH  /api/contacts/{id}/             → Modifier nickname/notes
#     - DELETE /api/contacts/{id}/             → Supprimer (soft delete)
#     - POST   /api/contacts/{id}/block/       → Bloquer
#     - POST   /api/contacts/{id}/unblock/     → Débloquer
#     - POST   /api/contacts/{id}/favorite/    → Toggle favoris
#     - GET    /api/contacts/favorites/        → Liste des favoris
#     - GET    /api/contacts/blocked/          → Liste des bloqués
#     - GET    /api/contacts/search/           → Rechercher utilisateurs
#     - GET    /api/contacts/suggestions/      → Suggestions de contacts
#     """
#     permission_classes = [IsAuthenticated]
#     lookup_field = 'id'
    
#     def get_queryset(self):
#         """
#         Retourne uniquement les contacts de l'utilisateur connecté
#         (excluant les soft-deleted par défaut)
#         """
#         user = self.request.user
        
#         queryset = Contact.objects.filter(
#             user=user,
#             is_deleted=False
#         ).select_related('contact_user')
        
#         # Filtres optionnels
#         favorites_only = self.request.query_params.get('favorites')
#         blocked_only = self.request.query_params.get('blocked')
        
#         if favorites_only == 'true':
#             queryset = queryset.filter(is_favorite=True)
        
#         if blocked_only == 'true':
#             queryset = queryset.filter(is_blocked=True)
        
#         return queryset.order_by('-is_favorite', '-added_at')
    
#     def get_serializer_class(self):
#         """Choisir le bon serializer"""
#         if self.action == 'create':
#             return ContactCreateSerializer
#         elif self.action in ['update', 'partial_update']:
#             return ContactUpdateSerializer
#         elif self.action == 'retrieve':
#             return ContactDetailSerializer
#         return ContactListSerializer
    
#     def list(self, request, *args, **kwargs):
#         """Liste des contacts"""
#         queryset = self.filter_queryset(self.get_queryset())
        
#         # Recherche par nom/numéro
#         search = request.query_params.get('search')
#         if search:
#             queryset = queryset.filter(
#                 Q(nickname__icontains=search) |
#                 Q(contact_user__display_name__icontains=search) |
#                 Q(contact_user__phone_number__icontains=search)
#             )
        
#         serializer = self.get_serializer(queryset, many=True)
        
#         return Response({
#             'success': True,
#             'count': queryset.count(),
#             'data': serializer.data
#         })
    
#     def create(self, request, *args, **kwargs):
#         """Ajouter un nouveau contact"""
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         contact = serializer.save()
        
#         # Retourner le détail complet
#         detail_serializer = ContactDetailSerializer(contact)
        
#         return Response(
#             {
#                 'success': True,
#                 'message': 'Contact ajouté',
#                 'data': detail_serializer.data
#             },
#             status=status.HTTP_201_CREATED
#         )
    
#     def retrieve(self, request, *args, **kwargs):
#         """Détails d'un contact"""
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
        
#         return Response({
#             'success': True,
#             'data': serializer.data
#         })
    
#     def update(self, request, *args, **kwargs):
#         """Modifier un contact (nickname, notes)"""
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
        
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
        
#         return Response({
#             'success': True,
#             'message': 'Contact mis à jour',
#             'data': serializer.data
#         })
    
#     def destroy(self, request, *args, **kwargs):
#         """Supprimer un contact (soft delete)"""
#         instance = self.get_object()
#         instance.soft_delete()
        
#         return Response({
#             'success': True,
#             'message': 'Contact supprimé'
#         }, status=status.HTTP_200_OK)
    
#     @action(detail=True, methods=['post'])
#     def block(self, request, id=None):
#         """Bloquer un contact"""
#         contact = self.get_object()
#         contact.block()
        
#         return Response({
#             'success': True,
#             'message': 'Contact bloqué',
#             'data': ContactDetailSerializer(contact).data
#         })
    
#     @action(detail=True, methods=['post'])
#     def unblock(self, request, id=None):
#         """Débloquer un contact"""
#         contact = self.get_object()
#         contact.unblock()
        
#         return Response({
#             'success': True,
#             'message': 'Contact débloqué',
#             'data': ContactDetailSerializer(contact).data
#         })
    
#     @action(detail=True, methods=['post'])
#     def favorite(self, request, id=None):
#         """Toggle favoris"""
#         contact = self.get_object()
#         contact.toggle_favorite()
        
#         message = 'Ajouté aux favoris' if contact.is_favorite else 'Retiré des favoris'
        
#         return Response({
#             'success': True,
#             'message': message,
#             'data': {
#                 'is_favorite': contact.is_favorite
#             }
#         })
    
#     @action(detail=False, methods=['get'])
#     def favorites(self, request):
#         """Liste des contacts favoris"""
#         contacts = self.get_queryset().filter(is_favorite=True)
#         serializer = ContactListSerializer(contacts, many=True)
        
#         return Response({
#             'success': True,
#             'count': contacts.count(),
#             'data': serializer.data
#         })
    
#     @action(detail=False, methods=['get'])
#     def blocked(self, request):
#         """Liste des contacts bloqués"""
#         contacts = self.get_queryset().filter(is_blocked=True)
#         serializer = ContactListSerializer(contacts, many=True)
        
#         return Response({
#             'success': True,
#             'count': contacts.count(),
#             'data': serializer.data
#         })
    
#     @action(detail=False, methods=['get'])
#     def search(self, request):
#         """
#         Rechercher des utilisateurs à ajouter
        
#         GET /api/contacts/search/?q=+222
#         GET /api/contacts/search/?q=alice
#         """
#         query = request.query_params.get('q', '').strip()
        
#         if not query or len(query) < 3:
#             return Response(
#                 {
#                     'success': False,
#                     'error': 'La recherche nécessite au moins 3 caractères'
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Rechercher utilisateurs (excluant soi-même)
#         users = User.objects.filter(
#             Q(phone_number__icontains=query) |
#             Q(display_name__icontains=query)
#         ).exclude(
#             user_id=request.user.user_id
#         ).filter(
#             is_active=True
#         )[:20]  # Limiter à 20 résultats
        
#         serializer = UserSuggestionSerializer(
#             users,
#             many=True,
#             context={'request': request}
#         )
        
#         return Response({
#             'success': True,
#             'count': users.count(),
#             'data': serializer.data
#         })
    
#     @action(detail=False, methods=['get'])
#     def suggestions(self, request):
#         """
#         Suggestions de contacts basées sur:
#         - Utilisateurs récemment inscrits
#         - Utilisateurs populaires
#         - Etc.
#         """
#         # Exclure l'utilisateur actuel et ses contacts existants
#         existing_contact_ids = Contact.objects.filter(
#             user=request.user,
#             is_deleted=False
#         ).values_list('contact_user_id', flat=True)
        
#         # Suggestions: utilisateurs actifs récents
#         suggestions = User.objects.filter(
#             is_active=True,
#             is_verified=True
#         ).exclude(
#             user_id=request.user.user_id
#         ).exclude(
#             user_id__in=existing_contact_ids
#         ).order_by('-created_at')[:10]
        
#         serializer = UserSuggestionSerializer(
#             suggestions,
#             many=True,
#             context={'request': request}
#         )
        
#         return Response({
#             'success': True,
#             'count': suggestions.count(),
#             'data': serializer.data
#         })
    
#     @action(detail=False, methods=['get'])
#     def stats(self, request):
#         """Statistiques des contacts"""
#         total = Contact.objects.filter(
#             user=request.user,
#             is_deleted=False
#         ).count()
        
#         favorites = Contact.objects.filter(
#             user=request.user,
#             is_deleted=False,
#             is_favorite=True
#         ).count()
        
#         blocked = Contact.objects.filter(
#             user=request.user,
#             is_deleted=False,
#             is_blocked=True
#         ).count()
        
#         online = Contact.objects.filter(
#             user=request.user,
#             is_deleted=False,
#             contact_user__is_online=True
#         ).count()
        
#         return Response({
#             'success': True,
#             'data': {
#                 'total': total,
#                 'favorites': favorites,
#                 'blocked': blocked,
#                 'online': online
#             }
#         })