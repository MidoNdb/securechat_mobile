# messagerie/consumers.py

"""
WebSocket Consumer pour messagerie temps réel E2EE
Architecture Diffie-Hellman (SANS MessageKey)
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour chat E2EE temps réel
    
    Architecture DH:
    - Client chiffre avec secret partagé DH
    - Envoie: encrypted_content + nonce + auth_tag + signature
    - PAS de clés par message (calculées côté client)
    
    Actions supportées:
    - ping: Keepalive
    - join_conversation: Rejoindre une conversation
    - send_message: Envoyer un message chiffré
    - typing: Indicateur de saisie
    - mark_read: Marquer comme lu
    """
    
    async def connect(self):
        """Connexion WebSocket"""
        user = self.scope["user"]
        
        print(f"🔌 Tentative connexion WebSocket")
        print(f"   User: {user}")
        print(f"   Authenticated: {user.is_authenticated}")
        
        if not user.is_authenticated:
            print("❌ User non authentifié - Rejet")
            await self.close(code=4001)
            return
        
        # Stocker l'utilisateur
        self.user = user
        self.user_id = str(user.user_id)  # ✅ UUID
        
        # Rejoindre le canal personnel
        self.user_group_name = f'user_{self.user_id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        # Initialiser la liste des conversations jointes
        self.conversation_groups = []
        
        # Accepter la connexion
        await self.accept()
        print(f"✅ WebSocket accepté pour {user.phone_number}")
        
        # Envoyer confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté avec succès',
            'user_id': self.user_id,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket"""
        print(f"🔌 Déconnexion WebSocket - Code: {close_code}")
        
        # Quitter le groupe personnel
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        # Quitter toutes les conversations
        if hasattr(self, 'conversation_groups'):
            for group_name in self.conversation_groups:
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name
                )
    
    async def receive(self, text_data):
        """Recevoir un message du client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            print(f"📨 Action reçue: {action}")
            
            # ─────────────────────────────────────────────────────────
            # ACTION: Ping (keepalive)
            # ─────────────────────────────────────────────────────────
            if action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
                return
            
            # ─────────────────────────────────────────────────────────
            # ACTION: Rejoindre une conversation
            # ─────────────────────────────────────────────────────────
            elif action == 'join_conversation':
                conversation_id = data.get('conversation_id')
                await self.join_conversation(conversation_id)
                return
            
            # ─────────────────────────────────────────────────────────
            # ACTION: Envoyer un message
            # ─────────────────────────────────────────────────────────
            elif action == 'send_message':
                await self.handle_send_message(data)
                return
            
            # ─────────────────────────────────────────────────────────
            # ACTION: Indicateur de saisie
            # ─────────────────────────────────────────────────────────
            elif action == 'typing':
                conversation_id = data.get('conversation_id')
                is_typing = data.get('is_typing', True)
                await self.handle_typing(conversation_id, is_typing)
                return
            
            # ─────────────────────────────────────────────────────────
            # ACTION: Marquer comme lu
            # ─────────────────────────────────────────────────────────
            elif action == 'mark_read':
                message_ids = data.get('message_ids', [])
                await self.handle_mark_read(message_ids)
                return
            
            # ─────────────────────────────────────────────────────────
            # ACTION: Inconnue - Ignore silencieusement
            # ─────────────────────────────────────────────────────────
            else:
                print(f"⚠️ Action inconnue ignorée: {action}")
                # Ne pas envoyer d'erreur, juste ignorer
                return
        
        except Exception as e:
            print(f"❌ Erreur WebSocket receive: {e}")
            import traceback
            traceback.print_exc()
            
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': str(e)
            }))
    
    # ═══════════════════════════════════════════════════════════════
    # HANDLERS D'ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    async def join_conversation(self, conversation_id):
        """Rejoindre un groupe de conversation"""
        # Vérifier que l'utilisateur est membre
        is_member = await self.check_conversation_member(conversation_id)
        
        if not is_member:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Vous n\'êtes pas membre de cette conversation'
            }))
            return
        
        # Rejoindre le groupe
        group_name = f'chat_{conversation_id}'
        
        if group_name not in self.conversation_groups:
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )
            self.conversation_groups.append(group_name)
            print(f"✅ Utilisateur {self.user_id} a rejoint {group_name}")
        
        # Confirmer
        await self.send(text_data=json.dumps({
            'type': 'joined_conversation',
            'conversation_id': conversation_id,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_send_message(self, data):
        """
        Gérer l'envoi d'un message chiffré VIA WEBSOCKET
        
        ⚠️ NOTE: Cette méthode n'est plus utilisée car on envoie via HTTP
        mais gardée pour compatibilité future
        
        Architecture DH - Format attendu:
        {
            "action": "send_message",
            "conversation_id": "uuid",
            "encrypted_content": "base64...",
            "nonce": "base64...",
            "auth_tag": "base64...",
            "signature": "base64...",
            "type": "TEXT",
            "metadata": {...}  // optionnel
        }
        """
        conversation_id = data.get('conversation_id')
        encrypted_content = data.get('encrypted_content')
        nonce = data.get('nonce')
        auth_tag = data.get('auth_tag')
        signature = data.get('signature')
        msg_type = data.get('type', 'TEXT')
        reply_to_id = data.get('reply_to_id')
        metadata = data.get('metadata')
        
        # ✅ Validation champs E2EE
        if not all([conversation_id, encrypted_content, nonce, auth_tag, signature]):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Données manquantes (encrypted_content, nonce, auth_tag, signature)'
            }))
            return
        
        # Sauvegarder le message
        message = await self.save_message(
            conversation_id=conversation_id,
            encrypted_content=encrypted_content,
            nonce=nonce,
            auth_tag=auth_tag,
            signature=signature,
            msg_type=msg_type,
            reply_to_id=reply_to_id,
            metadata=metadata
        )
        
        if not message:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Erreur lors de la sauvegarde du message'
            }))
            return
        
        # Préparer les données à diffuser
        message_data = {
            'type': 'new_message',
            'message': {
                'id': str(message['id']),
                'conversation_id': conversation_id,
                'sender_id': str(message['sender_id']),
                'sender_name': message['sender_name'],
                # ✅ Champs E2EE complets
                'encrypted_content': encrypted_content,
                'nonce': nonce,
                'auth_tag': auth_tag,
                'signature': signature,
                # Autres
                'type': msg_type,
                'reply_to_id': str(reply_to_id) if reply_to_id else None,
                'metadata': metadata,
                'created_at': message['created_at'],
            }
        }
        
        # Diffuser à tous les membres de la conversation
        await self.channel_layer.group_send(
            f"chat_{conversation_id}",
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
        
        # Confirmer l'envoi à l'expéditeur
        await self.send(text_data=json.dumps({
            'type': 'message_sent',
            'message_id': str(message['id']),
            'status': 'success',
            'timestamp': message['created_at']
        }))
    
    async def handle_typing(self, conversation_id, is_typing):
        """Indicateur de saisie"""
        await self.channel_layer.group_send(
            f"chat_{conversation_id}",
            {
                'type': 'typing_indicator',
                'user_id': self.user_id,
                'user_name': self.user.display_name or self.user.phone_number,
                'is_typing': is_typing
            }
        )
    
    async def handle_mark_read(self, message_ids):
        """Marquer des messages comme lus"""
        updated_count = await self.mark_messages_read(message_ids)
        
        # Notifier les expéditeurs
        for message_id in message_ids:
            message_info = await self.get_message_info(message_id)
            
            if message_info:
                await self.channel_layer.group_send(
                    f"user_{message_info['sender_id']}",
                    {
                        'type': 'message_read_receipt',
                        'message_id': str(message_id),
                        'read_by': self.user_id,
                        'read_by_name': self.user.display_name or self.user.phone_number,
                        'read_at': timezone.now().isoformat()
                    }
                )
        
        # Confirmer
        await self.send(text_data=json.dumps({
            'type': 'messages_marked_read',
            'count': updated_count
        }))
    
    # ═══════════════════════════════════════════════════════════════
    # ✅ HANDLERS POUR MESSAGES DU CHANNEL LAYER (group_send)
    # ═══════════════════════════════════════════════════════════════
    
    async def new_message(self, event):
        """
        ✅ HANDLER CRITIQUE : Gérer les messages broadcastés depuis message_views.py
        
        Appelé quand message_views.py fait:
        channel_layer.group_send(f"chat_{conversation_id}", {
            "type": "new_message",
            "message": serializer.data
        })
        
        Django Channels convertit "new_message" → appelle new_message()
        """
        try:
            message_data = event.get("message")
            
            print(f"📤 Broadcast nouveau message: {message_data.get('id')}")
            
            # Envoyer au client WebSocket
            await self.send(text_data=json.dumps({
                'type': 'new_message',
                'message': message_data
            }))
            
        except Exception as e:
            print(f"❌ Erreur new_message handler: {e}")
            import traceback
            traceback.print_exc()
    
    async def chat_message(self, event):
        """
        Handler pour messages envoyés via WebSocket (handle_send_message)
        
        ⚠️ Différent de new_message qui vient de message_views.py
        """
        await self.send(text_data=json.dumps(event['message']))
    
    async def typing_indicator(self, event):
        """Recevoir indicateur de saisie"""
        # Ne pas renvoyer son propre indicateur
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))
    
    async def message_read_receipt(self, event):
        """Recevoir accusé de lecture"""
        await self.send(text_data=json.dumps(event))
    
    # ═══════════════════════════════════════════════════════════════
    # DATABASE OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    @database_sync_to_async
    def check_conversation_member(self, conversation_id):
        """Vérifier que l'utilisateur est membre de la conversation"""
        from messagerie.models.conversation import ConversationParticipant
        
        return ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=self.user
        ).exists()
    
    @database_sync_to_async
    def save_message(self, conversation_id, encrypted_content, nonce, auth_tag, 
                     signature, msg_type, reply_to_id, metadata):
        """
        Sauvegarder le message en DB
        Architecture DH - SANS MessageKey
        """
        from messagerie.models.conversation import Conversation, ConversationParticipant
        from messagerie.models.message import Message
        from messagerie.models.message_status import MessageStatus
        
        try:
            # Récupérer la conversation
            conversation = Conversation.objects.get(id=conversation_id)
            
            # ✅ Créer le message avec TOUS les champs E2EE
            message = Message.objects.create(
                conversation=conversation,
                from_user=self.user,
                type=msg_type,
                encrypted_content=encrypted_content,
                nonce=nonce,
                auth_tag=auth_tag,
                signature=signature,
                reply_to_id=reply_to_id,
                metadata=metadata
            )
            
            print(f"✅ Message créé: {message.id}")
            
            # Créer les statuts pour chaque participant SANS DOUBLONS
            participants = ConversationParticipant.objects.filter(
                conversation=conversation
            ).select_related('user')
            
            # ✅ Utiliser set() pour éviter doublons
            user_ids = set(p.user_id for p in participants)
            
            statuses_to_create = []
            for user_id in user_ids:
                # Statut READ pour l'expéditeur, SENT pour les autres
                is_sender = (user_id == self.user.id)
                
                statuses_to_create.append(
                    MessageStatus(
                        message=message,
                        user_id=user_id,
                        status=MessageStatus.Status.READ if is_sender else MessageStatus.Status.SENT,
                        read_at=timezone.now() if is_sender else None
                    )
                )
            
            MessageStatus.objects.bulk_create(statuses_to_create)
            print(f"✅ {len(statuses_to_create)} MessageStatus créés")
            
            # Mettre à jour last_message et last_message_at
            conversation.last_message = message
            conversation.last_message_at = message.created_at
            conversation.save(update_fields=['last_message', 'last_message_at'])
            
            # Retourner les infos du message
            return {
                'id': message.id,
                'sender_id': self.user.user_id,
                'sender_name': self.user.display_name or self.user.phone_number,
                'created_at': message.created_at.isoformat()
            }
        
        except Exception as e:
            print(f"❌ Erreur save_message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Marquer les messages comme lus"""
        from messagerie.models.message_status import MessageStatus
        
        statuses = MessageStatus.objects.filter(
            message_id__in=message_ids,
            user=self.user
        ).exclude(status=MessageStatus.Status.READ)
        
        now = timezone.now()
        for status in statuses:
            status.status = MessageStatus.Status.READ
            status.read_at = now
        
        MessageStatus.objects.bulk_update(statuses, ['status', 'read_at'])
        
        return len(statuses)
    
    @database_sync_to_async
    def get_message_info(self, message_id):
        """Récupérer les infos d'un message"""
        from messagerie.models.message import Message
        
        try:
            message = Message.objects.get(id=message_id)
            return {
                'sender_id': str(message.from_user.user_id),
                'conversation_id': str(message.conversation.id)
            }
        except Message.DoesNotExist:
            return None




# # messagerie/consumers.py

# """
# WebSocket Consumer pour messagerie temps réel E2EE
# Architecture Diffie-Hellman (SANS MessageKey)
# """
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.utils import timezone


# class ChatConsumer(AsyncWebsocketConsumer):
#     """
#     Consumer WebSocket pour chat E2EE temps réel
    
#     Architecture DH:
#     - Client chiffre avec secret partagé DH
#     - Envoie: encrypted_content + nonce + auth_tag + signature
#     - PAS de clés par message (calculées côté client)
    
#     Actions supportées:
#     - ping: Keepalive
#     - join_conversation: Rejoindre une conversation
#     - send_message: Envoyer un message chiffré
#     - typing: Indicateur de saisie
#     - mark_read: Marquer comme lu
#     """
    
#     async def connect(self):
#         """Connexion WebSocket"""
#         user = self.scope["user"]
        
#         print(f"🔌 Tentative connexion WebSocket")
#         print(f"   User: {user}")
#         print(f"   Authenticated: {user.is_authenticated}")
        
#         if not user.is_authenticated:
#             print("❌ User non authentifié - Rejet")
#             await self.close(code=4001)
#             return
        
#         # Stocker l'utilisateur
#         self.user = user
#         self.user_id = str(user.user_id)  # ✅ UUID
        
#         # Rejoindre le canal personnel
#         self.user_group_name = f'user_{self.user_id}'
#         await self.channel_layer.group_add(
#             self.user_group_name,
#             self.channel_name
#         )
        
#         # Initialiser la liste des conversations jointes
#         self.conversation_groups = []
        
#         # Accepter la connexion
#         await self.accept()
#         print(f"✅ WebSocket accepté pour {user.phone_number}")
        
#         # Envoyer confirmation
#         await self.send(text_data=json.dumps({
#             'type': 'connection_established',
#             'message': 'Connecté avec succès',
#             'user_id': self.user_id,
#             'timestamp': timezone.now().isoformat()
#         }))
    
#     async def disconnect(self, close_code):
#         """Déconnexion WebSocket"""
#         print(f"🔌 Déconnexion WebSocket - Code: {close_code}")
        
#         # Quitter le groupe personnel
#         if hasattr(self, 'user_group_name'):
#             await self.channel_layer.group_discard(
#                 self.user_group_name,
#                 self.channel_name
#             )
        
#         # Quitter toutes les conversations
#         if hasattr(self, 'conversation_groups'):
#             for group_name in self.conversation_groups:
#                 await self.channel_layer.group_discard(
#                     group_name,
#                     self.channel_name
#                 )
    
#     async def receive(self, text_data):
#         """Recevoir un message du client"""
#         try:
#             data = json.loads(text_data)
#             action = data.get('action')
            
#             print(f"📨 Action reçue: {action}")
            
#             # ─────────────────────────────────────────────────────────
#             # ACTION: Ping (keepalive)
#             # ─────────────────────────────────────────────────────────
#             if action == 'ping':
#                 await self.send(text_data=json.dumps({
#                     'type': 'pong',
#                     'timestamp': timezone.now().isoformat()
#                 }))
#                 return
            
#             # ─────────────────────────────────────────────────────────
#             # ACTION: Rejoindre une conversation
#             # ─────────────────────────────────────────────────────────
#             elif action == 'join_conversation':
#                 conversation_id = data.get('conversation_id')
#                 await self.join_conversation(conversation_id)
#                 return
            
#             # ─────────────────────────────────────────────────────────
#             # ACTION: Envoyer un message
#             # ─────────────────────────────────────────────────────────
#             elif action == 'send_message':
#                 await self.handle_send_message(data)
#                 return
            
#             # ─────────────────────────────────────────────────────────
#             # ACTION: Indicateur de saisie
#             # ─────────────────────────────────────────────────────────
#             elif action == 'typing':
#                 conversation_id = data.get('conversation_id')
#                 is_typing = data.get('is_typing', True)
#                 await self.handle_typing(conversation_id, is_typing)
#                 return
            
#             # ─────────────────────────────────────────────────────────
#             # ACTION: Marquer comme lu
#             # ─────────────────────────────────────────────────────────
#             elif action == 'mark_read':
#                 message_ids = data.get('message_ids', [])
#                 await self.handle_mark_read(message_ids)
#                 return
            
#             # ─────────────────────────────────────────────────────────
#             # ACTION: Inconnue - Ignore silencieusement
#             # ─────────────────────────────────────────────────────────
#             else:
#                 print(f"⚠️ Action inconnue ignorée: {action}")
#                 # Ne pas envoyer d'erreur, juste ignorer
#                 return
        
#         except Exception as e:
#             print(f"❌ Erreur WebSocket receive: {e}")
#             import traceback
#             traceback.print_exc()
            
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'error': str(e)
#             }))
    
#     # ═══════════════════════════════════════════════════════════════
#     # HANDLERS D'ACTIONS
#     # ═══════════════════════════════════════════════════════════════
    
#     async def join_conversation(self, conversation_id):
#         """Rejoindre un groupe de conversation"""
#         # Vérifier que l'utilisateur est membre
#         is_member = await self.check_conversation_member(conversation_id)
        
#         if not is_member:
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'error': 'Vous n\'êtes pas membre de cette conversation'
#             }))
#             return
        
#         # Rejoindre le groupe
#         group_name = f'chat_{conversation_id}'
        
#         if group_name not in self.conversation_groups:
#             await self.channel_layer.group_add(
#                 group_name,
#                 self.channel_name
#             )
#             self.conversation_groups.append(group_name)
#             print(f"✅ Utilisateur {self.user_id} a rejoint {group_name}")
        
#         # Confirmer
#         await self.send(text_data=json.dumps({
#             'type': 'joined_conversation',
#             'conversation_id': conversation_id,
#             'timestamp': timezone.now().isoformat()
#         }))
    
#     async def handle_send_message(self, data):
#         """
#         Gérer l'envoi d'un message chiffré
        
#         Architecture DH - Format attendu:
#         {
#             "action": "send_message",
#             "conversation_id": "uuid",
#             "encrypted_content": "base64...",
#             "nonce": "base64...",
#             "auth_tag": "base64...",
#             "signature": "base64...",
#             "type": "TEXT",
#             "metadata": {...}  // optionnel
#         }
#         """
#         conversation_id = data.get('conversation_id')
#         encrypted_content = data.get('encrypted_content')
#         nonce = data.get('nonce')
#         auth_tag = data.get('auth_tag')
#         signature = data.get('signature')
#         msg_type = data.get('type', 'TEXT')
#         reply_to_id = data.get('reply_to_id')
#         metadata = data.get('metadata')
        
#         # ✅ Validation champs E2EE
#         if not all([conversation_id, encrypted_content, nonce, auth_tag, signature]):
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'error': 'Données manquantes (encrypted_content, nonce, auth_tag, signature)'
#             }))
#             return
        
#         # Sauvegarder le message
#         message = await self.save_message(
#             conversation_id=conversation_id,
#             encrypted_content=encrypted_content,
#             nonce=nonce,
#             auth_tag=auth_tag,
#             signature=signature,
#             msg_type=msg_type,
#             reply_to_id=reply_to_id,
#             metadata=metadata
#         )
        
#         if not message:
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'error': 'Erreur lors de la sauvegarde du message'
#             }))
#             return
        
#         # Préparer les données à diffuser
#         message_data = {
#             'type': 'new_message',
#             'message': {
#                 'id': str(message['id']),
#                 'conversation_id': conversation_id,
#                 'sender_id': str(message['sender_id']),
#                 'sender_name': message['sender_name'],
#                 # ✅ Champs E2EE complets
#                 'encrypted_content': encrypted_content,
#                 'nonce': nonce,
#                 'auth_tag': auth_tag,
#                 'signature': signature,
#                 # Autres
#                 'type': msg_type,
#                 'reply_to_id': str(reply_to_id) if reply_to_id else None,
#                 'metadata': metadata,
#                 'created_at': message['created_at'],
#             }
#         }
        
#         # Diffuser à tous les membres de la conversation
#         await self.channel_layer.group_send(
#             f"chat_{conversation_id}",
#             {
#                 'type': 'chat_message',
#                 'message': message_data
#             }
#         )
        
#         # Confirmer l'envoi à l'expéditeur
#         await self.send(text_data=json.dumps({
#             'type': 'message_sent',
#             'message_id': str(message['id']),
#             'status': 'success',
#             'timestamp': message['created_at']
#         }))
    
#     async def handle_typing(self, conversation_id, is_typing):
#         """Indicateur de saisie"""
#         await self.channel_layer.group_send(
#             f"chat_{conversation_id}",
#             {
#                 'type': 'typing_indicator',
#                 'user_id': self.user_id,
#                 'user_name': self.user.display_name or self.user.phone_number,
#                 'is_typing': is_typing
#             }
#         )
    
#     async def handle_mark_read(self, message_ids):
#         """Marquer des messages comme lus"""
#         updated_count = await self.mark_messages_read(message_ids)
        
#         # Notifier les expéditeurs
#         for message_id in message_ids:
#             message_info = await self.get_message_info(message_id)
            
#             if message_info:
#                 await self.channel_layer.group_send(
#                     f"user_{message_info['sender_id']}",
#                     {
#                         'type': 'message_read_receipt',
#                         'message_id': str(message_id),
#                         'read_by': self.user_id,
#                         'read_by_name': self.user.display_name or self.user.phone_number,
#                         'read_at': timezone.now().isoformat()
#                     }
#                 )
        
#         # Confirmer
#         await self.send(text_data=json.dumps({
#             'type': 'messages_marked_read',
#             'count': updated_count
#         }))
    
#     # ═══════════════════════════════════════════════════════════════
#     # RECEIVERS (Messages du channel layer)
#     # ═══════════════════════════════════════════════════════════════
    
#     async def chat_message(self, event):
#         """Recevoir un nouveau message"""
#         await self.send(text_data=json.dumps(event['message']))
    
#     async def typing_indicator(self, event):
#         """Recevoir indicateur de saisie"""
#         # Ne pas renvoyer son propre indicateur
#         if event['user_id'] != self.user_id:
#             await self.send(text_data=json.dumps({
#                 'type': 'typing',
#                 'user_id': event['user_id'],
#                 'user_name': event['user_name'],
#                 'is_typing': event['is_typing']
#             }))
    
#     async def message_read_receipt(self, event):
#         """Recevoir accusé de lecture"""
#         await self.send(text_data=json.dumps(event))
    
#     # ═══════════════════════════════════════════════════════════════
#     # DATABASE OPERATIONS
#     # ═══════════════════════════════════════════════════════════════
    
#     @database_sync_to_async
#     def check_conversation_member(self, conversation_id):
#         """Vérifier que l'utilisateur est membre de la conversation"""
#         from messagerie.models.conversation import ConversationParticipant
        
#         return ConversationParticipant.objects.filter(
#             conversation_id=conversation_id,
#             user=self.user
#         ).exists()
    
#     @database_sync_to_async
#     def save_message(self, conversation_id, encrypted_content, nonce, auth_tag, 
#                      signature, msg_type, reply_to_id, metadata):
#         """
#         Sauvegarder le message en DB
#         Architecture DH - SANS MessageKey
#         """
#         from messagerie.models.conversation import Conversation, ConversationParticipant
#         from messagerie.models.message import Message
#         from messagerie.models.message_status import MessageStatus
        
#         try:
#             # Récupérer la conversation
#             conversation = Conversation.objects.get(id=conversation_id)
            
#             # ✅ Créer le message avec TOUS les champs E2EE
#             message = Message.objects.create(
#                 conversation=conversation,
#                 from_user=self.user,
#                 type=msg_type,
#                 encrypted_content=encrypted_content,
#                 nonce=nonce,
#                 auth_tag=auth_tag,
#                 signature=signature,
#                 reply_to_id=reply_to_id,
#                 metadata=metadata
#             )
            
#             print(f"✅ Message créé: {message.id}")
            
#             # Créer les statuts pour chaque participant SANS DOUBLONS
#             participants = ConversationParticipant.objects.filter(
#                 conversation=conversation
#             ).select_related('user')
            
#             # ✅ Utiliser set() pour éviter doublons
#             user_ids = set(p.user_id for p in participants)
            
#             statuses_to_create = []
#             for user_id in user_ids:
#                 # Statut READ pour l'expéditeur, SENT pour les autres
#                 is_sender = (user_id == self.user.id)
                
#                 statuses_to_create.append(
#                     MessageStatus(
#                         message=message,
#                         user_id=user_id,
#                         status=MessageStatus.Status.READ if is_sender else MessageStatus.Status.SENT,
#                         read_at=timezone.now() if is_sender else None
#                     )
#                 )
            
#             MessageStatus.objects.bulk_create(statuses_to_create)
#             print(f"✅ {len(statuses_to_create)} MessageStatus créés")
            
#             # Mettre à jour last_message_at
#             conversation.last_message_at = timezone.now()
#             conversation.save(update_fields=['last_message_at'])
            
#             # Retourner les infos du message
#             return {
#                 'id': message.id,
#                 'sender_id': self.user.user_id,
#                 'sender_name': self.user.display_name or self.user.phone_number,
#                 'created_at': message.created_at.isoformat()
#             }
        
#         except Exception as e:
#             print(f"❌ Erreur save_message: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
    
#     @database_sync_to_async
#     def mark_messages_read(self, message_ids):
#         """Marquer les messages comme lus"""
#         from messagerie.models.message_status import MessageStatus
        
#         statuses = MessageStatus.objects.filter(
#             message_id__in=message_ids,
#             user=self.user
#         ).exclude(status=MessageStatus.Status.READ)
        
#         now = timezone.now()
#         for status in statuses:
#             status.status = MessageStatus.Status.READ
#             status.read_at = now
#             if not status.delivered_at:
#                 status.delivered_at = now
        
#         MessageStatus.objects.bulk_update(statuses, ['status', 'read_at', 'delivered_at'])
        
#         return len(statuses)
    
#     @database_sync_to_async
#     def get_message_info(self, message_id):
#         """Récupérer les infos d'un message"""
#         from messagerie.models.message import Message
        
#         try:
#             message = Message.objects.get(id=message_id)
#             return {
#                 'sender_id': str(message.from_user.user_id),
#                 'conversation_id': str(message.conversation.id)
#             }
#         except Message.DoesNotExist:
#             return None