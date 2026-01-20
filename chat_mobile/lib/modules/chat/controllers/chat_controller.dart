// lib/modules/chat/controllers/chat_controller.dart

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/conversation.dart';
import '../../../data/models/message.dart';
import '../../../data/services/message_service.dart';
import '../../../data/services/websocket_service.dart';
import '../../../data/services/secure_storage_service.dart';

class ChatController extends GetxController {
  final MessageService _messageService = Get.find<MessageService>();
  final WebSocketService _websocketService = Get.find<WebSocketService>();
  final SecureStorageService _storage = Get.find<SecureStorageService>();

  // Conversation
  late Conversation conversation;

  // UI Controllers
  final messageController = TextEditingController();
  final scrollController = ScrollController();

  // States
  final messages = <Message>[].obs;
  final isLoading = false.obs;
  final isLoadingMore = false.obs;  // ✅ AJOUTÉ
  final isSendingMessage = false.obs;

  // User ID
  String? _currentUserId;  // ✅ String UUID
  String? get currentUserId => _currentUserId;

  // Pagination
  int _currentPage = 1;
  final int _pageSize = 50;
  bool _hasMoreMessages = true;

  StreamSubscription? _newMessagesSubscription;

  @override
  void onInit() {
    super.onInit();
    _initChat();
  }

  Future<void> _initChat() async {
    try {
      // 1. Récupérer conversation depuis arguments
      final args = Get.arguments as Map<String, dynamic>;
      conversation = args['conversation'] as Conversation;

      print('💬 ChatController init pour conversation: ${conversation.id}');

      // 2. Charger currentUserId
      await _loadCurrentUserId();

      // 3. Connecter WebSocket si nécessaire
      if (!_websocketService.isConnected.value) {
        await _websocketService.connect();
      }

      // 4. Rejoindre la conversation
      _messageService.joinConversation(conversation.id);

      // 5. Charger messages initiaux
      await loadMessages();

      // 6. Écouter nouveaux messages
      _listenNewMessages();

      // 7. Marquer comme lu
      await _messageService.markConversationAsRead(conversation.id);

    } catch (e) {
      print('❌ Erreur init chat: $e');
      Get.snackbar(
        'Erreur',
        'Impossible de charger le chat',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.red,
      );
    }
  }

  Future<void> _loadCurrentUserId() async {
    try {
      final userId = await _storage.getUserId();
      _currentUserId = userId;  // ✅ String
      print('👤 Current user ID: $_currentUserId');
    } catch (e) {
      print('❌ Erreur chargement user ID: $e');
    }
  }

  /// ✅ Charge les messages initiaux
  Future<void> loadMessages({bool showLoading = true}) async {
    try {
      if (showLoading) isLoading.value = true;

      print('📥 Chargement messages...');

      final loadedMessages = await _messageService.getConversationMessages(
        conversationId: conversation.id,
        page: _currentPage,
        pageSize: _pageSize,
      );

      messages.value = loadedMessages.reversed.toList();

      print('✅ ${messages.length} messages chargés');

      // Scroll vers le bas
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _scrollToBottom();
      });

    } catch (e) {
      print('❌ Erreur loadMessages: $e');
      Get.snackbar(
        'Erreur',
        'Impossible de charger les messages',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.red,
      );
    } finally {
      isLoading.value = false;
    }
  }

  /// ✅ Charger plus de messages (pagination)
  Future<void> onLoadMore() async {
    if (isLoadingMore.value || !_hasMoreMessages) return;

    try {
      isLoadingMore.value = true;
      _currentPage++;

      print('📥 Chargement page $_currentPage...');

      final olderMessages = await _messageService.getConversationMessages(
        conversationId: conversation.id,
        page: _currentPage,
        pageSize: _pageSize,
      );

      if (olderMessages.isEmpty) {
        _hasMoreMessages = false;
        print('⚠️ Plus de messages à charger');
      } else {
        // Ajouter en début de liste (messages plus anciens)
        messages.insertAll(0, olderMessages.reversed);
        print('✅ ${olderMessages.length} messages supplémentaires chargés');
      }

    } catch (e) {
      print('❌ Erreur onLoadMore: $e');
    } finally {
      isLoadingMore.value = false;
    }
  }

  /// ✅ Écouter nouveaux messages WebSocket
  void _listenNewMessages() {
    _newMessagesSubscription = _messageService.newMessagesStream.listen(
      (message) {
        // Vérifier que le message est pour cette conversation
        if (message.conversationId == conversation.id) {
          _addNewMessage(message);
        }
      },
      onError: (error) {
        print('❌ Erreur stream nouveaux messages: $error');
      },
    );

    print('👂 Écoute des nouveaux messages activée');
  }

  /// ✅ Ajouter nouveau message
  void _addNewMessage(Message message) {
    // Vérifier que le message n'existe pas déjà
    final exists = messages.any((m) => m.id == message.id);
    if (exists) {
      print('⚠️ Message déjà dans la liste: ${message.id}');
      return;
    }

    print('📨 Nouveau message ajouté: ${message.id}');

    // Ajouter à la fin de la liste
    messages.add(message);

    // Scroll vers le bas
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
    });

    // Marquer comme lu si ce n'est pas notre message
    if (message.senderId != _currentUserId) {
      _messageService.markConversationAsRead(conversation.id);
    }
  }

  /// ✅ Envoyer un message
  Future<void> sendMessage() async {
    final text = messageController.text.trim();

    if (text.isEmpty) return;
    if (isSendingMessage.value) return;

    try {
      isSendingMessage.value = true;

      print('📤 Envoi message...');

      // Récupérer l'autre participant
      final recipientId = _getRecipientId();

      // Envoyer via HTTP
      final sentMessage = await _messageService.sendMessage(
        conversationId: conversation.id,
        recipientUserId: recipientId,
        content: text,
        type: 'TEXT',
      );

      print('✅ Message envoyé: ${sentMessage.id}');

      // Effacer le champ
      messageController.clear();

      // Le message sera reçu via WebSocket et ajouté automatiquement
      // Mais on peut l'ajouter optimistiquement:
      _addNewMessage(sentMessage);

    } catch (e) {
      print('❌ Erreur sendMessage: $e');
      Get.snackbar(
        'Erreur',
        'Impossible d\'envoyer le message',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.red,
      );
    } finally {
      isSendingMessage.value = false;
    }
  }

  /// ✅ Récupérer l'ID du destinataire
  String _getRecipientId() {
    return conversation.participants
        .firstWhere((p) => p.userId != _currentUserId)
        .userId;
  }

  /// ✅ Scroll vers le bas
  void _scrollToBottom() {
    if (scrollController.hasClients) {
      scrollController.animateTo(
        scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  void onClose() {
    messageController.dispose();
    scrollController.dispose();
    _newMessagesSubscription?.cancel();
    super.onClose();
  }
}



// // lib/modules/chat/controllers/chat_controller.dart

// import 'package:flutter/material.dart';
// import 'package:get/get.dart';
// import '../../../data/models/conversation.dart';
// import '../../../data/models/message.dart';
// import '../../../data/services/message_service.dart';
// import '../../../data/services/websocket_service.dart';
// import '../../../data/services/secure_storage_service.dart';

// class ChatController extends GetxController {
//   final MessageService _messageService = Get.find<MessageService>();
//   final WebSocketService _webSocketService = Get.find<WebSocketService>();
//   final SecureStorageService _storage = Get.find<SecureStorageService>();

//   late final TextEditingController messageController;
//   final scrollController = ScrollController();

//   final messages = <Message>[].obs;
//   final isLoading = false.obs;
//   final isSendingMessage = false.obs;
//   final isLoadingMore = false.obs;

//   late Conversation conversation;
//   int? _currentUserId;
//   int? get currentUserId => _currentUserId;
//   int _currentPage = 1;
//   bool _hasMoreMessages = true;

//   @override
//   void onInit() {
//     super.onInit();
//     messageController = TextEditingController();
    
//     // ✅ Récupère conversation des arguments
//     final args = Get.arguments as Map<String, dynamic>;
//     conversation = args['conversation'] as Conversation;
    
//     print('💬 ChatController initialized for: ${conversation.name}');
    
//     _initCurrentUser();
//     _initChat();
//   }

//   /// ✅ Charge l'ID du user actuel
//   Future<void> _initCurrentUser() async {
//     try {
//       final userId = await _storage.getUserId();
//       _currentUserId = userId != null ? int.tryParse(userId) : null;
//       print('👤 Current user ID in chat: $_currentUserId');
//     } catch (e) {
//       print('❌ _initCurrentUser: $e');
//     }
//   }

//   /// ✅ Initialise le chat
//   Future<void> _initChat() async {
//     await loadMessages();
//     _listenToNewMessages();
//     _markAsRead();
//   }

//   /// ✅ Charge les messages d'une conversation
//   Future<void> loadMessages({bool isRefresh = false}) async {
//     if (isRefresh) {
//       _currentPage = 1;
//       _hasMoreMessages = true;
//     }

//     if (!_hasMoreMessages) return;

//     try {
//       if (isRefresh) {
//         isLoading.value = true;
//       } else {
//         isLoadingMore.value = true;
//       }

//       // ✅ conversation.id est String UUID
//       final result = await _messageService.getMessages(
//         conversation.id,
//         page: _currentPage,
//       );

//       if (result != null) {
//         if (isRefresh) {
//           messages.assignAll(result.reversed);
//         } else {
//           messages.insertAll(0, result.reversed);
//         }

//         _hasMoreMessages = result.length >= 50;
//         _currentPage++;

//         print('✅ Loaded ${result.length} messages (page $_currentPage)');

//         Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
//       }
//     } catch (e) {
//       print('❌ loadMessages: $e');
//     } finally {
//       isLoading.value = false;
//       isLoadingMore.value = false;
//     }
//   }

//   /// ✅ Envoie un message
//   Future<void> sendMessage() async {
//     final content = messageController.text.trim();
//     if (content.isEmpty || isSendingMessage.value) return;

//     final recipientUserId = _getRecipientUserId();
//     if (recipientUserId == null) {
//       Get.snackbar('Erreur', 'Destinataire introuvable');
//       return;
//     }

//     try {
//       isSendingMessage.value = true;

//       // ✅ ID temporaire String unique
//       final tempId = 'temp_${DateTime.now().millisecondsSinceEpoch}';

//       final tempMessage = Message(
//         id: tempId,
//         conversationId: conversation.id,
//         senderId: _currentUserId ?? 0,
//         content: content,
//         type: 'text',
//         status: 'sending',
//         timestamp: DateTime.now(),
//       );

//       messages.add(tempMessage);
//       messageController.clear();
//       _scrollToBottom();

//       print('📤 Sending message to conversation: ${conversation.id}');

//       // ✅ conversation.id est String UUID
//       final sentMessage = await _messageService.sendMessage(
//         conversationId: conversation.id,
//         content: content,
//         recipientUserId: recipientUserId.toString(),
//       );

//       if (sentMessage != null) {
//         print('✅ Message sent successfully');
//         final index = messages.indexWhere((m) => m.id == tempId);
//         if (index != -1) {
//           messages[index] = sentMessage;
//         }
//       } else {
//         print('❌ Message send failed');
//         final index = messages.indexWhere((m) => m.id == tempId);
//         if (index != -1) {
//           messages[index] = tempMessage.copyWith(status: 'failed');
//         }
//       }
//     } catch (e) {
//       print('❌ sendMessage: $e');
//       Get.snackbar('Erreur', 'Impossible d\'envoyer le message');
//     } finally {
//       isSendingMessage.value = false;
//     }
//   }

//   /// ✅ Écoute les nouveaux messages WebSocket
//   void _listenToNewMessages() {
//     _webSocketService.messageStream.listen((message) {
//       // ✅ Compare String IDs
//       if (message.conversationId == conversation.id) {
//         final exists = messages.any((m) => m.id == message.id);
//         if (!exists) {
//           print('📨 New message received via WebSocket');
//           messages.add(message);
//           _scrollToBottom();
//           _markAsRead();
//         }
//       }
//     });

//     _webSocketService.statusStream.listen((status) {
//       if (status['type'] == 'delivered' || status['type'] == 'read') {
//         _updateMessageStatus(status);
//       }
//     });
//   }

//   /// ✅ Met à jour le statut d'un message
//   void _updateMessageStatus(Map<String, dynamic> status) {
//     // ✅ Normalise en String
//     final messageId = status['message_id']?.toString() ?? '';
//     final newStatus = status['type']?.toString() ?? '';

//     final index = messages.indexWhere((m) => m.id == messageId);
//     if (index != -1) {
//       messages[index] = messages[index].copyWith(
//         status: newStatus,
//         isDelivered: newStatus == 'delivered' || newStatus == 'read',
//         isRead: newStatus == 'read',
//       );
//     }
//   }

//   /// ✅ Marque les messages comme lus
//   Future<void> _markAsRead() async {
//     try {
//       // ✅ conversation.id est String UUID
//       await _messageService.markAsRead(conversation.id);
//       print('✅ Messages marked as read');
//     } catch (e) {
//       print('❌ _markAsRead: $e');
//     }
//   }

//   /// ✅ Obtient l'ID du destinataire
//   int? _getRecipientUserId() {
//     if (conversation.isGroup) {
//       // Pour les groupes, retourne le premier participant (à améliorer)
//       return conversation.participants.isNotEmpty 
//           ? conversation.participants.first.userId 
//           : null;
//     }

//     // Pour les conversations directes, trouve l'autre participant
//     final other = conversation.participants.firstWhereOrNull(
//       (p) => p.userId != _currentUserId,
//     );

//     return other?.userId;
//   }

//   /// ✅ Scroll vers le bas
//   void _scrollToBottom() {
//     if (scrollController.hasClients) {
//       scrollController.animateTo(
//         scrollController.position.maxScrollExtent,
//         duration: const Duration(milliseconds: 300),
//         curve: Curves.easeOut,
//       );
//     }
//   }

//   /// ✅ Charge plus de messages (pagination)
//   void onLoadMore() {
//     if (!isLoadingMore.value && _hasMoreMessages) {
//       print('📄 Loading more messages...');
//       loadMessages();
//     }
//   }

//   @override
//   void onClose() {
//     _markAsRead();
//     messageController.dispose();
//     scrollController.dispose();
//     super.onClose();
//   }
// }

