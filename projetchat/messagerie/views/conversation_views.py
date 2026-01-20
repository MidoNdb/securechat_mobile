# messagerie/views/conversation_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch

from messagerie.models.conversation import Conversation, ConversationParticipant

# ✅ IMPORT CORRIGÉ : Depuis le package, pas directement depuis le fichier
from messagerie.serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    ConversationUpdateSerializer,
    ConversationParticipantSerializer
)


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les conversations"""
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """Récupérer les conversations de l'utilisateur"""
        user = self.request.user
        return (
            Conversation.objects
            .filter(participants__user=user)
            .select_related('created_by')
            .prefetch_related(
                Prefetch(
                    'participants',
                    queryset=ConversationParticipant.objects.select_related('user')
                )
            )
            .distinct()
            .order_by('-last_message_at', '-created_at')
        )

    def get_serializer_class(self):
        """Choisir le bon serializer selon l'action"""
        if self.action == 'list':
            return ConversationListSerializer
        elif self.action == 'create':
            return ConversationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConversationUpdateSerializer
        return ConversationDetailSerializer

    def list(self, request, *args, **kwargs):
        """
        Récupérer toutes les conversations de l'utilisateur
        GET /api/conversations/
        """
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            print(f"📊 Conversations trouvées: {queryset.count()}")
            print(f"📦 Conversations IDs: {[str(c.id) for c in queryset[:5]]}")
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Erreur list conversations: {e}")
            import traceback
            traceback.print_exc()
            
            return Response({
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """
        Récupérer une conversation spécifique
        GET /api/conversations/{id}/
        """
        try:
            conversation = self.get_object()
            serializer = self.get_serializer(conversation)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Conversation introuvable'
                }
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """
        Créer une nouvelle conversation
        POST /api/conversations/
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            conversation = serializer.save()

            # Retourner avec le serializer détaillé
            response_serializer = ConversationDetailSerializer(
                conversation, 
                context={'request': request}
            )

            return Response({
                'success': True,
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Erreur create conversation: {e}")
            import traceback
            traceback.print_exc()
            
            return Response({
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def participants(self, request, id=None):
        """
        Récupérer les participants d'une conversation
        GET /api/conversations/{id}/participants/
        """
        try:
            conversation = self.get_object()
            participants = conversation.participants.select_related('user')
            serializer = ConversationParticipantSerializer(participants, many=True)

            return Response({
                'success': True, 
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Erreur participants: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)