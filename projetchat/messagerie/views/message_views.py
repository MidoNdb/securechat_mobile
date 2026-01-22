# messagerie/views/message_views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from messagerie.serializers import (
    MessageListSerializer,
    MessageDetailSerializer,
    MessageCreateSerializer,
)

from ..models import Message, Conversation, MessageStatus
from authentification.models import User


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les messages E2EE
    
    Routes standard (via router):
    - GET    /api/messages/              → list()
    - POST   /api/messages/              → create()
    - GET    /api/messages/{id}/         → retrieve()
    - PUT    /api/messages/{id}/         → update()
    - DELETE /api/messages/{id}/         → destroy()
    
    Routes custom (manuelles):
    - GET    /api/messages/conversation/{id}/  → by_conversation()
    - POST   /api/messages/mark-read/          → mark_read()
    """
    
    serializer_class = MessageListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtrer messages accessibles par l'utilisateur"""
        return Message.objects.filter(
            conversation__participants__user=self.request.user
        ).select_related(
            'from_user', 
            'recipient_user'
        ).prefetch_related(
            'statuses'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Choisir le bon serializer selon l'action"""
        if self.action == 'create':
            return MessageCreateSerializer
        elif self.action == 'retrieve':
            return MessageDetailSerializer
        return MessageListSerializer

    # ========================================
    # CREATE MESSAGE (POST /api/messages/)
    # ========================================
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Créer un nouveau message chiffré E2EE
        
        POST /api/messages/
        Body: {
            "conversation_id": "uuid",
            "recipient_user_id": "uuid",
            "encrypted_content": "base64",
            "nonce": "base64",
            "auth_tag": "base64",
            "signature": "base64",
            "type": "TEXT"
        }
        """
        try:
            print('📨 Création message E2EE...')
            
            # 1. Validation des données
            conversation_id = request.data.get('conversation_id')
            recipient_user_id = request.data.get('recipient_user_id')
            encrypted_content = request.data.get('encrypted_content')
            nonce = request.data.get('nonce')
            auth_tag = request.data.get('auth_tag')
            signature = request.data.get('signature')
            message_type = request.data.get('type', 'TEXT')

            if not all([conversation_id, recipient_user_id, encrypted_content, nonce, auth_tag, signature]):
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'MISSING_FIELDS',
                            'message': 'Tous les champs E2EE sont requis'
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Vérifier la conversation
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                participants__user=request.user
            )
            
            # 3. Vérifier le destinataire
            recipient_user = get_object_or_404(User, user_id=recipient_user_id)

            # 4. Créer le message
            message = Message.objects.create(
                conversation=conversation,
                from_user=request.user,
                recipient_user=recipient_user,
                encrypted_content=encrypted_content,
                nonce=nonce,
                auth_tag=auth_tag,
                signature=signature,
                type=message_type
            )
            
            print(f'✅ Message créé: {message.id}')
            print(f'   De: {request.user.phone_number}')
            print(f'   Pour: {recipient_user.phone_number}')
            print(f'   Conversation: {conversation.id}')

            # 5. Créer MessageStatus pour tous les participants
            statuses_to_create = []
            participant_users = conversation.participants.values_list('user_id', flat=True)
            
            for user_id in set(participant_users):  # set() pour éviter doublons
                is_sender = (user_id == request.user.id)
                
                statuses_to_create.append(
                    MessageStatus(
                        message=message,
                        user_id=user_id,
                        status=MessageStatus.Status.READ if is_sender else MessageStatus.Status.SENT,
                        read_at=timezone.now() if is_sender else None
                    )
                )
            
            MessageStatus.objects.bulk_create(statuses_to_create)
            print(f'✅ {len(statuses_to_create)} MessageStatus créés')

            # 6. Mettre à jour la conversation
            conversation.last_message = message
            conversation.last_message_at = message.created_at
            conversation.save(update_fields=['last_message', 'last_message_at'])

            # 7. Broadcast via WebSocket
            self._broadcast_message(conversation, message)

            # 8. Réponse
            response_serializer = MessageDetailSerializer(
                message,
                context={'request': request}
            )
            
            return Response(
                {
                    'success': True,
                    'data': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'CONVERSATION_NOT_FOUND',
                        'message': 'Conversation introuvable ou accès refusé'
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'RECIPIENT_NOT_FOUND',
                        'message': 'Destinataire introuvable'
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f'❌ Erreur création message: {e}')
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'SERVER_ERROR',
                        'message': 'Erreur lors de la création du message',
                        'details': str(e)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ========================================
    # GET MESSAGES BY CONVERSATION (Custom)
    # ========================================
    
    def by_conversation(self, request, conversation_id=None):
        """
        Récupérer les messages d'une conversation avec pagination
        
        GET /api/messages/conversation/{conversation_id}/?page=1&page_size=50
        
        Query params:
        - page: numéro de page (default: 1)
        - page_size: nombre de messages par page (default: 50, max: 100)
        """
        try:
            print(f'📥 Récupération messages conversation: {conversation_id}')
            
            # 1. Vérifier accès à la conversation
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                participants__user=request.user
            )

            # 2. Pagination
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 50)), 100)

            # 3. Récupérer messages
            messages = Message.objects.filter(
                conversation=conversation
            ).select_related(
                'from_user',
                'recipient_user'
            ).prefetch_related(
                'statuses'
            ).order_by('-created_at')

            total_count = messages.count()

            # 4. Appliquer pagination
            start = (page - 1) * page_size
            end = start + page_size
            paginated_messages = messages[start:end]

            # 5. Serializer
            serializer = MessageListSerializer(
                paginated_messages,
                many=True,
                context={'request': request}
            )

            print(f'✅ {len(serializer.data)} messages récupérés (page {page}/{(total_count + page_size - 1) // page_size})')

            return Response(
                {
                    'success': True,
                    'data': serializer.data,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total_count,
                        'total_pages': (total_count + page_size - 1) // page_size
                    }
                },
                status=status.HTTP_200_OK
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'CONVERSATION_NOT_FOUND',
                        'message': 'Conversation introuvable ou accès refusé'
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_PARAMETERS',
                        'message': 'Paramètres de pagination invalides'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f'❌ Erreur by_conversation: {e}')
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'SERVER_ERROR',
                        'message': 'Erreur lors de la récupération des messages',
                        'details': str(e)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ========================================
    # MARK AS READ (Custom)
    # ========================================
    
    def mark_read(self, request):
        """
        Marquer les messages d'une conversation comme lus
        
        POST /api/messages/mark-read/
        Body: {
            "conversation_id": "uuid"
        }
        """
        try:
            print('👁️ Marquage messages comme lus...')
            
            conversation_id = request.data.get('conversation_id')

            if not conversation_id:
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'MISSING_CONVERSATION_ID',
                            'message': 'conversation_id est requis'
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérifier accès
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                participants__user=request.user
            )

            # Mettre à jour les statuts non lus
            updated_count = MessageStatus.objects.filter(
                message__conversation=conversation,
                user=request.user,
                status=MessageStatus.Status.SENT
            ).update(
                status=MessageStatus.Status.READ,
                read_at=timezone.now()
            )

            print(f'✅ {updated_count} messages marqués comme lus')

            return Response(
                {
                    'success': True,
                    'message': f'{updated_count} messages marqués comme lus',
                    'data': {
                        'updated_count': updated_count
                    }
                },
                status=status.HTTP_200_OK
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'CONVERSATION_NOT_FOUND',
                        'message': 'Conversation introuvable ou accès refusé'
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f'❌ Erreur mark_read: {e}')
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'SERVER_ERROR',
                        'message': 'Erreur lors du marquage des messages',
                        'details': str(e)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ========================================
    # HELPER : Broadcast WebSocket
    # ========================================
    
    def _broadcast_message(self, conversation, message):
        """
        Envoyer le message via WebSocket à tous les participants
        """
        try:
            channel_layer = get_channel_layer()
            
            # Serializer pour broadcast
            serializer = MessageDetailSerializer(
                message,
                context={'request': None}
            )
            
            # Envoyer au groupe WebSocket
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation.id}",
                {
                    "type": "new_message",
                    "message": serializer.data
                }
            )
            
            print(f'✅ Message broadcast à chat_{conversation.id}')
            
        except Exception as e:
            print(f'❌ Erreur broadcast WebSocket: {e}')
            # Ne pas bloquer si WebSocket échoue








# # messagerie/views/message_views.py

# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer

# # ✅ CORRECTION : Import des CLASSES au lieu du module
# from messagerie.serializers import (
#     MessageListSerializer,
#     MessageDetailSerializer,
#     MessageCreateSerializer,
# )

# from ..models import Message, Conversation, MessageStatus
# from authentification.models import User


# class MessageViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet pour gérer les messages E2EE
#     """
#     # ✅ CORRECTION : Classe au lieu de module
#     serializer_class = MessageListSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Message.objects.filter(
#             conversation__participants__user=self.request.user
#         ).select_related('from_user').prefetch_related('statuses').order_by('-created_at')
    
# def get_serializer_class(self):
#     """Sélectionne le bon serializer selon l'action"""
#     if self.action == 'create':
#         return MessageCreateSerializer
#     elif self.action == 'retrieve':
#         return MessageDetailSerializer
#     return MessageListSerializer

# @transaction.atomic
# def create(self, request, *args, **kwargs):
#     """
#     Créer un nouveau message chiffré E2EE
    
#     POST /api/messages/
#     Body: {
#         "conversation_id": "uuid",
#         "recipient_user_id": "uuid",
#         "encrypted_content": "base64",
#         "nonce": "base64",
#         "auth_tag": "base64",
#         "signature": "base64",
#         "type": "TEXT"
#     }
#     """
#     try:
#         # 1. Récupérer les données
#         conversation_id = request.data.get('conversation_id')
#         recipient_user_id = request.data.get('recipient_user_id')  # ✅ AJOUT
#         encrypted_content = request.data.get('encrypted_content')
#         nonce = request.data.get('nonce')
#         auth_tag = request.data.get('auth_tag')
#         signature = request.data.get('signature')
#         message_type = request.data.get('type', 'TEXT')

#         # ✅ MODIFICATION : Validation avec recipient_user_id
#         if not all([conversation_id, recipient_user_id, encrypted_content, nonce, auth_tag, signature]):
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'MISSING_FIELDS',
#                         'message': 'Champs E2EE manquants'
#                     }
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # 2. Vérifier la conversation
#         conversation = get_object_or_404(
#             Conversation,
#             id=conversation_id,
#             participants__user=request.user
#         )
        
#         # ✅ AJOUT : Vérifier destinataire
#         recipient_user = get_object_or_404(User, user_id=recipient_user_id)

#         # 3. Créer le message
#         message = Message.objects.create(
#             conversation=conversation,
#             from_user=request.user,
#             recipient_user=recipient_user,  # ✅ AJOUT
#             encrypted_content=encrypted_content,
#             nonce=nonce,
#             auth_tag=auth_tag,
#             signature=signature,
#             type=message_type
#         )

#         print(f"✅ Message créé: {message.id} dans conversation {conversation.id}")
#         print(f"   Chiffré pour: {recipient_user.phone_number}")

#         # 4. Créer MessageStatus SANS DOUBLONS
#         statuses_to_create = []
        
#         # Récupérer TOUS les users de la conversation (via Participant)
#         participant_users = conversation.participants.values_list('user_id', flat=True)
        
#         # Créer un statut pour CHAQUE user UNIQUE
#         for user_id in set(participant_users):  # set() pour éviter doublons
#             is_sender = (user_id == request.user.id)
            
#             statuses_to_create.append(
#                 MessageStatus(
#                     message=message,
#                     user_id=user_id,
#                     status=MessageStatus.Status.READ if is_sender else MessageStatus.Status.SENT,
#                     read_at=timezone.now() if is_sender else None
#                 )
#             )
        
#         # Créer tous les statuts en une fois
#         MessageStatus.objects.bulk_create(statuses_to_create)
        
#         print(f"✅ {len(statuses_to_create)} MessageStatus créés")

#         # 5. Mettre à jour la conversation
#         conversation.last_message = message
#         conversation.last_message_at = message.created_at
#         conversation.save(update_fields=['last_message', 'last_message_at'])

#         # 6. Broadcast via WebSocket
#         self._broadcast_message(conversation, message)

#         # 7. Réponse avec MessageDetailSerializer
#         response_serializer = MessageDetailSerializer(
#             message,
#             context={'request': request}
#         )
        
#         return Response(
#             {
#                 'success': True,
#                 'data': response_serializer.data
#             },
#             status=status.HTTP_201_CREATED
#         )

#     except Conversation.DoesNotExist:
#         return Response(
#             {
#                 'success': False,
#                 'error': {
#                     'code': 'CONVERSATION_NOT_FOUND',
#                     'message': 'Conversation introuvable'
#                 }
#             },
#             status=status.HTTP_404_NOT_FOUND
#         )
#     except User.DoesNotExist:
#         return Response(
#             {
#                 'success': False,
#                 'error': {
#                     'code': 'RECIPIENT_NOT_FOUND',
#                     'message': 'Destinataire introuvable'
#                 }
#             },
#             status=status.HTTP_404_NOT_FOUND
#         )
#     except Exception as e:
#         print(f"❌ Erreur création message: {e}")
#         import traceback
#         traceback.print_exc()
        
#         return Response(
#             {
#                 'success': False,
#                 'error': {
#                     'code': 'SERVER_ERROR',
#                     'message': str(e)
#                 }
#             },
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     def _broadcast_message(self, conversation, message):
#         """
#         Broadcast le message via WebSocket à tous les participants
#         """
#         try:
#             channel_layer = get_channel_layer()
            
#             # Utiliser MessageDetailSerializer pour le broadcast
#             serializer = MessageDetailSerializer(
#                 message,
#                 context={'request': None}
#             )
            
#             # Broadcast à tous les participants
#             async_to_sync(channel_layer.group_send)(
#                 f"chat_{conversation.id}",
#                 {
#                     "type": "new_message",
#                     "message": serializer.data
#                 }
#             )
            
#             print(f"✅ Message broadcast à chat_{conversation.id}")
            
#         except Exception as e:
#             print(f"❌ Erreur broadcast: {e}")

#     @action(detail=False, methods=['get'], url_path='conversation/(?P<conversation_id>[^/.]+)')
#     def by_conversation(self, request, conversation_id=None):
#         """
#         Récupérer les messages d'une conversation
#         """
#         try:
#             # Vérifier accès
#             conversation = get_object_or_404(
#                 Conversation,
#                 id=conversation_id,
#                 participants__user=request.user
#             )

#             # Pagination
#             page = int(request.query_params.get('page', 1))
#             page_size = int(request.query_params.get('page_size', 50))

#             # Messages
#             messages = Message.objects.filter(
#                 conversation=conversation
#             ).select_related('from_user').prefetch_related('statuses').order_by('-created_at')

#             # Paginer
#             start = (page - 1) * page_size
#             end = start + page_size
#             paginated_messages = messages[start:end]

#             # ✅ CORRECTION : Utiliser MessageListSerializer (CLASSE)
#             serializer = MessageListSerializer(
#                 paginated_messages,
#                 many=True,
#                 context={'request': request}
#             )

#             print(f"✅ Messages chargés: {len(serializer.data)} pour conversation {conversation_id}")

#             return Response(
#                 {
#                     'success': True,
#                     'data': serializer.data,
#                     'pagination': {
#                         'page': page,
#                         'page_size': page_size,
#                         'total': messages.count()
#                     }
#                 },
#                 status=status.HTTP_200_OK
#             )

#         except Conversation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'CONVERSATION_NOT_FOUND',
#                         'message': 'Conversation introuvable'
#                     }
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             print(f"❌ Erreur by_conversation: {e}")
#             import traceback
#             traceback.print_exc()
            
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'SERVER_ERROR',
#                         'message': str(e)
#                     }
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     @action(detail=False, methods=['post'], url_path='mark-read')
#     def mark_read(self, request):
#         """
#         Marquer les messages d'une conversation comme lus
#         """
#         try:
#             conversation_id = request.data.get('conversation_id')

#             if not conversation_id:
#                 return Response(
#                     {
#                         'success': False,
#                         'error': {
#                             'code': 'MISSING_CONVERSATION_ID',
#                             'message': 'conversation_id requis'
#                         }
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # Mettre à jour les statuts
#             updated = MessageStatus.objects.filter(
#                 message__conversation_id=conversation_id,
#                 user=request.user,
#                 status=MessageStatus.Status.SENT
#             ).update(
#                 status=MessageStatus.Status.READ,
#                 read_at=timezone.now()
#             )

#             print(f"✅ {updated} messages marqués comme lus dans conversation {conversation_id}")

#             return Response(
#                 {
#                     'success': True,
#                     'message': f'{updated} messages marqués comme lus'
#                 },
#                 status=status.HTTP_200_OK
#             )

#         except Exception as e:
#             print(f"❌ Erreur mark_read: {e}")
#             import traceback
#             traceback.print_exc()
            
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'SERVER_ERROR',
#                         'message': str(e)
#                     }
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

















# # messagerie/views/message_views.py

# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from django.utils import timezone  # ✅ CORRIGÉ: django.utils au lieu de pytz
# from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer

# from messagerie.serializers import message_serializers


# from ..models import Message, Conversation, MessageStatus
# from authentification.models import User


# class MessageViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet pour gérer les messages E2EE
#     """
#     serializer_class = message_serializers  # ✅ CORRIGÉ: Classe au lieu de module
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Message.objects.filter(
#             conversation__participants__user=self.request.user
#         ).select_related('from_user').prefetch_related('statuses').order_by('-created_at')  # ✅ CORRIGÉ: from_user

#     @transaction.atomic
#     def create(self, request, *args, **kwargs):
#         """
#         Créer un nouveau message chiffré E2EE
#         """
#         try:
#             # 1. Récupérer les données
#             conversation_id = request.data.get('conversation_id')
#             encrypted_content = request.data.get('encrypted_content')
#             nonce = request.data.get('nonce')
#             auth_tag = request.data.get('auth_tag')
#             signature = request.data.get('signature')
#             message_type = request.data.get('type', 'TEXT')

#             # Validation
#             if not all([conversation_id, encrypted_content, nonce, auth_tag, signature]):
#                 return Response(
#                     {
#                         'success': False,
#                         'error': {
#                             'code': 'MISSING_FIELDS',
#                             'message': 'Champs E2EE manquants'
#                         }
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # 2. Vérifier la conversation
#             conversation = get_object_or_404(
#                 Conversation,
#                 id=conversation_id,
#                 participants__user=request.user
#             )

#             # 3. Créer le message
#             message = Message.objects.create(
#                 conversation=conversation,
#                 from_user=request.user,  # ✅ CORRIGÉ: from_user au lieu de sender
#                 encrypted_content=encrypted_content,
#                 nonce=nonce,
#                 auth_tag=auth_tag,
#                 signature=signature,
#                 type=message_type
#             )

#             print(f"✅ Message créé: {message.id} dans conversation {conversation.id}")

#             # 4. Créer MessageStatus SANS DOUBLONS
#             statuses_to_create = []
            
#             # Récupérer TOUS les users de la conversation (via Participant)
#             participant_users = conversation.participants.values_list('user_id', flat=True)
            
#             # Créer un statut pour CHAQUE user UNIQUE
#             for user_id in set(participant_users):  # ✅ set() pour éviter doublons
#                 is_sender = (user_id == request.user.id)  # ✅ CORRIGÉ: user.id au lieu de user.user_id
                
#                 statuses_to_create.append(
#                     MessageStatus(
#                         message=message,
#                         user_id=user_id,
#                         status=MessageStatus.Status.READ if is_sender else MessageStatus.Status.SENT,  # ✅
#                         read_at=timezone.now() if is_sender else None  # ✅ CORRIGÉ: timezone.now()
#                     )
#                 )
            
#             # Créer tous les statuts en une fois
#             MessageStatus.objects.bulk_create(statuses_to_create)
            
#             print(f"✅ {len(statuses_to_create)} MessageStatus créés")

#             # 5. Mettre à jour la conversation
#             conversation.last_message = message
#             conversation.last_message_at = message.created_at
#             conversation.save(update_fields=['last_message', 'last_message_at'])

#             # 6. Broadcast via WebSocket
#             self._broadcast_message(conversation, message)

#             # 7. Réponse
#             serializer = self.get_serializer(message)
#             return Response(
#                 {
#                     'success': True,
#                     'data': serializer.data
#                 },
#                 status=status.HTTP_201_CREATED
#             )

#         except Conversation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'CONVERSATION_NOT_FOUND',
#                         'message': 'Conversation introuvable'
#                     }
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             print(f"❌ Erreur création message: {e}")
#             import traceback
#             traceback.print_exc()
            
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'SERVER_ERROR',
#                         'message': str(e)
#                     }
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     def _broadcast_message(self, conversation, message):
#         """
#         Broadcast le message via WebSocket à tous les participants
#         """
#         try:
#             channel_layer = get_channel_layer()
#             serializer = self.get_serializer(message)
            
#             # Broadcast à tous les participants
#             async_to_sync(channel_layer.group_send)(
#                 f"chat_{conversation.id}",  # ✅ CORRIGÉ: chat_ au lieu de conversation_
#                 {
#                     "type": "new_message",
#                     "message": serializer.data
#                 }
#             )
            
#             print(f"✅ Message broadcast à chat_{conversation.id}")
            
#         except Exception as e:
#             print(f"❌ Erreur broadcast: {e}")

#     @action(detail=False, methods=['get'], url_path='conversation/(?P<conversation_id>[^/.]+)')
#     def by_conversation(self, request, conversation_id=None):
#         """
#         Récupérer les messages d'une conversation
#         """
#         try:
#             # Vérifier accès
#             conversation = get_object_or_404(
#                 Conversation,
#                 id=conversation_id,
#                 participants__user=request.user
#             )

#             # Pagination
#             page = int(request.query_params.get('page', 1))
#             page_size = int(request.query_params.get('page_size', 50))

#             # Messages
#             messages = Message.objects.filter(
#                 conversation=conversation
#             ).select_related('from_user').prefetch_related('statuses').order_by('-created_at')  # ✅ CORRIGÉ: from_user

#             # Paginer
#             start = (page - 1) * page_size
#             end = start + page_size
#             paginated_messages = messages[start:end]

#             # Sérialiser
#             serializer = self.get_serializer(paginated_messages, many=True)

#             return Response(
#                 {
#                     'success': True,
#                     'data': serializer.data,
#                     'pagination': {
#                         'page': page,
#                         'page_size': page_size,
#                         'total': messages.count()
#                     }
#                 },
#                 status=status.HTTP_200_OK
#             )

#         except Conversation.DoesNotExist:
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'CONVERSATION_NOT_FOUND',
#                         'message': 'Conversation introuvable'
#                     }
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             print(f"❌ Erreur by_conversation: {e}")
#             import traceback
#             traceback.print_exc()
            
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'SERVER_ERROR',
#                         'message': str(e)
#                     }
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     @action(detail=False, methods=['post'], url_path='mark-read')
#     def mark_read(self, request):
#         """
#         Marquer les messages d'une conversation comme lus
#         """
#         try:
#             conversation_id = request.data.get('conversation_id')

#             if not conversation_id:
#                 return Response(
#                     {
#                         'success': False,
#                         'error': {
#                             'code': 'MISSING_CONVERSATION_ID',
#                             'message': 'conversation_id requis'
#                         }
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # Mettre à jour les statuts
#             MessageStatus.objects.filter(
#                 message__conversation_id=conversation_id,
#                 user=request.user,
#                 status=MessageStatus.Status.SENT  # ✅ CORRIGÉ: Utilise l'enum
#             ).update(
#                 status=MessageStatus.Status.READ,  # ✅ CORRIGÉ: Utilise l'enum
#                 read_at=timezone.now()  # ✅ CORRIGÉ: timezone.now()
#             )

#             return Response(
#                 {
#                     'success': True,
#                     'message': 'Messages marqués comme lus'
#                 },
#                 status=status.HTTP_200_OK
#             )

#         except Exception as e:
#             print(f"❌ Erreur mark_read: {e}")
#             import traceback
#             traceback.print_exc()
            
#             return Response(
#                 {
#                     'success': False,
#                     'error': {
#                         'code': 'SERVER_ERROR',
#                         'message': str(e)
#                     }
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

