# messagerie/views/message_status_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from messagerie.models.message_status import MessageStatus
from messagerie.models.message import Message
from messagerie.models.conversation import ConversationParticipant
from messagerie.serializers.message_status_serializers import (
    MessageStatusSerializer,
    MessageStatusDetailSerializer,
    MessageStatusUpdateSerializer,
    
)


class MessageStatusViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return MessageStatus.objects.filter(
            message__conversation__participants__user=self.request.user
        ).select_related('message', 'user')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return MessageStatusUpdateSerializer
        elif self.action == 'retrieve':
            return MessageStatusDetailSerializer
        elif self.action == 'bulk_update':
            return BulkMessageStatusUpdateSerializer
        return MessageStatusSerializer

    def list(self, request):
        message_id = request.query_params.get('message_id')
        if not message_id:
            return Response(
                {'success': False, 'error': 'message_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = Message.objects.filter(id=message_id).first()
        if not message:
            return Response(
                {'success': False, 'error': 'Message introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not ConversationParticipant.objects.filter(
            conversation=message.conversation,
            user=request.user
        ).exists():
            return Response(
                {'success': False, 'error': 'Accès refusé'},
                status=status.HTTP_403_FORBIDDEN
            )

        statuses = MessageStatus.objects.filter(message=message)

        return Response({
            'success': True,
            'data': {
                'message_id': message_id,
                'total_recipients': statuses.count(),
                'delivered_count': statuses.filter(
                    status__in=['DELIVERED', 'READ']
                ).count(),
                'read_count': statuses.filter(status='READ').count(),
                'statuses': MessageStatusSerializer(statuses, many=True).data
            }
        })

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        message_ids = request.data.get('message_ids', [])
        now = timezone.now()

        statuses = MessageStatus.objects.filter(
            message_id__in=message_ids,
            user=request.user
        ).exclude(status=MessageStatus.Status.READ)

        for s in statuses:
            s.status = MessageStatus.Status.READ
            s.read_at = now
            if not s.delivered_at:
                s.delivered_at = now

        MessageStatus.objects.bulk_update(
            statuses, ['status', 'read_at', 'delivered_at']
        )

        return Response({
            'success': True,
            'updated_count': len(statuses)
        })
