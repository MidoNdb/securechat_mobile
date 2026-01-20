from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from messagerie.models.media import Media
from messagerie.models.message import Message
from messagerie.models.conversation import ConversationParticipant
from messagerie.serializers.media_serializers import (
    MediaListSerializer,
    MediaDetailSerializer,
    MediaCreateSerializer,
    MediaProgressSerializer,
    MediaBulkDownloadSerializer
)


class MediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les médias E2EE
    
    Endpoints:
    - GET    /api/media/                      → Liste des médias
    - POST   /api/media/                      → Créer média (après upload CDN)
    - GET    /api/media/{id}/                 → Détail d'un média
    - DELETE /api/media/{id}/                 → Supprimer média
    - PATCH  /api/media/{id}/progress/        → Mettre à jour progression
    - GET    /api/media/conversation-media/   → Médias d'une conversation
    - GET    /api/media/message-media/        → Médias d'un message
    - POST   /api/media/bulk-download/        → Télécharger plusieurs médias
    - GET    /api/media/stats/                → Statistiques médias
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Retourne uniquement les médias accessibles par l'utilisateur
        (médias des conversations dont il est membre)
        """
        user = self.request.user
        
        queryset = Media.objects.filter(
            message__conversation__participants__user=user
        ).select_related(
            'message',
            'message__from_user',
            'message__conversation'
        ).distinct()
        
        # Filtres optionnels
        media_type = self.request.query_params.get('type')
        message_id = self.request.query_params.get('message_id')
        conversation_id = self.request.query_params.get('conversation_id')
        
        if media_type:
            queryset = queryset.filter(type=media_type)
        
        if message_id:
            queryset = queryset.filter(message_id=message_id)
        
        if conversation_id:
            queryset = queryset.filter(message__conversation_id=conversation_id)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Choisir le bon serializer"""
        if self.action == 'create':
            return MediaCreateSerializer
        elif self.action == 'retrieve':
            return MediaDetailSerializer
        elif self.action == 'progress':
            return MediaProgressSerializer
        elif self.action == 'bulk_download':
            return MediaBulkDownloadSerializer
        return MediaListSerializer
    
    def list(self, request, *args, **kwargs):
        """Liste des médias"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """
        Créer un média
        
        Le client doit avoir déjà uploadé le fichier chiffré sur CDN
        et envoie ici l'URL + métadonnées
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        media = serializer.save()
        
        # Retourner le détail complet
        detail_serializer = MediaDetailSerializer(media)
        
        return Response(
            {
                'success': True,
                'message': 'Média créé',
                'data': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Récupérer un média"""
        instance = self.get_object()
        
        # Vérifier l'accès
        if not ConversationParticipant.objects.filter(
            conversation=instance.message.conversation,
            user=request.user
        ).exists():
            return Response(
                {
                    'success': False,
                    'error': 'Accès refusé'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """
        Supprimer un média
        
        Seul l'expéditeur du message peut supprimer
        """
        instance = self.get_object()
        
        # Vérifier que c'est bien l'expéditeur
        if instance.message.from_user != request.user:
            return Response(
                {
                    'success': False,
                    'error': 'Seul l\'expéditeur peut supprimer ce média'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # TODO: Supprimer le fichier du CDN aussi
        instance.delete()
        
        return Response({
            'success': True,
            'message': 'Média supprimé'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def progress(self, request, id=None):
        """
        Mettre à jour la progression d'upload
        
        PATCH /api/media/{id}/progress/
        {"progress": 45}
        """
        media = self.get_object()
        
        # Vérifier que c'est l'expéditeur
        if media.message.from_user != request.user:
            return Response(
                {
                    'success': False,
                    'error': 'Accès refusé'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        progress = serializer.validated_data['progress']
        media.update_progress(progress)
        
        return Response({
            'success': True,
            'data': {
                'progress': media.upload_progress,
                'is_uploaded': media.is_uploaded
            }
        })
    
    @action(detail=False, methods=['get'])
    def conversation_media(self, request):
        """
        Récupérer tous les médias d'une conversation
        
        GET /api/media/conversation-media/?conversation_id=xxx&type=IMAGE
        """
        conversation_id = request.query_params.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {
                    'success': False,
                    'error': 'conversation_id est requis'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier l'accès
        if not ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=request.user
        ).exists():
            return Response(
                {
                    'success': False,
                    'error': 'Accès refusé'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def message_media(self, request):
        """
        Récupérer les médias d'un message spécifique
        
        GET /api/media/message-media/?message_id=xxx
        """
        message_id = request.query_params.get('message_id')
        
        if not message_id:
            return Response(
                {
                    'success': False,
                    'error': 'message_id est requis'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_download(self, request):
        """
        Télécharger plusieurs médias en batch
        
        POST /api/media/bulk-download/
        {"media_ids": ["uuid1", "uuid2"]}
        """
        serializer = BulkDownloadSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        media_ids = serializer.validated_data['media_ids']
        
        # Récupérer tous les médias
        media = Media.objects.filter(id__in=media_ids)
        
        data = MediaDetailSerializer(media, many=True).data
        
        return Response({
            'success': True,
            'count': len(data),
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques sur les médias
        
        GET /api/media/stats/
        GET /api/media/stats/?conversation_id=xxx
        """
        conversation_id = request.query_params.get('conversation_id')
        
        queryset = self.get_queryset()
        
        if conversation_id:
            queryset = queryset.filter(message__conversation_id=conversation_id)
        
        # Compter par type
        stats = {
            'total': queryset.count(),
            'by_type': {}
        }
        
        for media_type in Media.Type:
            count = queryset.filter(type=media_type.value).count()
            if count > 0:
                stats['by_type'][media_type.value] = count
        
        # Taille totale
        total_size = sum(m.file_size for m in queryset)
        stats['total_size_bytes'] = total_size
        stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return Response({
            'success': True,
            'data': stats
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Médias récents (toutes conversations)
        
        GET /api/media/recent/?limit=20&type=IMAGE
        """
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 100)  # Max 100
        
        queryset = self.filter_queryset(self.get_queryset())[:limit]
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        })