// lib/modules/chat/controllers/chat_controller.dart

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/conversation.dart';
import '../../../data/models/message.dart';
import '../../../data/services/message_service.dart';
import '../../../data/services/websocket_service.dart';
import '../../../data/services/secure_storage_service.dart';

class ChatController extends GetxController {
  final MessageService _messageService = Get.find<MessageService>();
  final WebSocketService _webSocketService = Get.find<WebSocketService>();
  final SecureStorageService _storage = Get.find<SecureStorageService>();

  late final TextEditingController messageController;
  final scrollController = ScrollController();

  final messages = <Message>[].obs;
  final isLoading = false.obs;
  final isSendingMessage = false.obs;
  final isLoadingMore = false.obs;

  late Conversation conversation;
  int? _currentUserId;
  int? get currentUserId => _currentUserId;
  int _currentPage = 1;
  bool _hasMoreMessages = true;

  @override
  void onInit() {
    super.onInit();
    messageController = TextEditingController();
    
    // ✅ Récupère conversation des arguments
    final args = Get.arguments as Map<String, dynamic>;
    conversation = args['conversation'] as Conversation;
    
    _initCurrentUser();
    _initChat();
  }

  Future<void> _initCurrentUser() async {
    final userId = await _storage.getUserId();
    _currentUserId = userId != null ? int.tryParse(userId) : null;
  }

  Future<void> _initChat() async {
    await loadMessages();
    _listenToNewMessages();
    _markAsRead();
  }

  Future<void> loadMessages({bool isRefresh = false}) async {
    if (isRefresh) {
      _currentPage = 1;
      _hasMoreMessages = true;
    }

    if (!_hasMoreMessages) return;

    try {
      if (isRefresh) {
        isLoading.value = true;
      } else {
        isLoadingMore.value = true;
      }

      // ✅ conversation.id est String
      final result = await _messageService.getMessages(
        conversation.id,  // String UUID
        page: _currentPage,
      );

      if (result != null) {
        if (isRefresh) {
          messages.assignAll(result.reversed);
        } else {
          messages.insertAll(0, result.reversed);
        }

        _hasMoreMessages = result.length >= 50;
        _currentPage++;

        Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
      }
    } catch (e) {
      print('❌ loadMessages: $e');
    } finally {
      isLoading.value = false;
      isLoadingMore.value = false;
    }
  }

  Future<void> sendMessage() async {
    final content = messageController.text.trim();
    if (content.isEmpty || isSendingMessage.value) return;

    final recipientUserId = _getRecipientUserId();
    if (recipientUserId == null) {
      Get.snackbar('Erreur', 'Destinataire introuvable');
      return;
    }

    try {
      isSendingMessage.value = true;

      // ✅ ID temporaire String unique
      final tempId = 'temp_${DateTime.now().millisecondsSinceEpoch}';

      final tempMessage = Message(
        id: tempId,  // ✅ String
        conversationId: conversation.id,  // ✅ String
        senderId: _currentUserId ?? 0,
        content: content,
        type: 'text',
        status: 'sending',
        timestamp: DateTime.now(),
      );

      messages.add(tempMessage);
      messageController.clear();
      _scrollToBottom();

      // ✅ conversation.id est String
      final sentMessage = await _messageService.sendMessage(
        conversationId: conversation.id,  // String UUID
        content: content,
        recipientUserId: recipientUserId.toString(),
      );

      if (sentMessage != null) {
        final index = messages.indexWhere((m) => m.id == tempId);
        if (index != -1) {
          messages[index] = sentMessage;
        }
      } else {
        final index = messages.indexWhere((m) => m.id == tempId);
        if (index != -1) {
          messages[index] = tempMessage.copyWith(status: 'failed');
        }
      }
    } catch (e) {
      print('❌ sendMessage: $e');
      Get.snackbar('Erreur', 'Impossible d\'envoyer le message');
    } finally {
      isSendingMessage.value = false;
    }
  }

  void _listenToNewMessages() {
    _webSocketService.messageStream.listen((message) {
      // ✅ Compare String IDs
      if (message.conversationId == conversation.id) {
        final exists = messages.any((m) => m.id == message.id);
        if (!exists) {
          messages.add(message);
          _scrollToBottom();
          _markAsRead();
        }
      }
    });

    _webSocketService.statusStream.listen((status) {
      if (status['type'] == 'delivered' || status['type'] == 'read') {
        _updateMessageStatus(status);
      }
    });
  }

  void _updateMessageStatus(Map<String, dynamic> status) {
    // ✅ Normalise en String
    final messageId = status['message_id']?.toString() ?? '';
    final newStatus = status['type']?.toString() ?? '';

    final index = messages.indexWhere((m) => m.id == messageId);
    if (index != -1) {
      messages[index] = messages[index].copyWith(
        status: newStatus,
        isDelivered: newStatus == 'delivered' || newStatus == 'read',
        isRead: newStatus == 'read',
      );
    }
  }

  Future<void> _markAsRead() async {
    try {
      // ✅ conversation.id est String
      await _messageService.markAsRead(conversation.id);  // String UUID
    } catch (e) {
      print('❌ _markAsRead: $e');
    }
  }

  int? _getRecipientUserId() {
    if (conversation.isGroup) {
      return conversation.participants.isNotEmpty 
          ? conversation.participants.first.userId 
          : null;
    }

    final other = conversation.participants.firstWhereOrNull(
      (p) => p.userId != _currentUserId,
    );

    return other?.userId;
  }

  void _scrollToBottom() {
    if (scrollController.hasClients) {
      scrollController.animateTo(
        scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void onLoadMore() {
    if (!isLoadingMore.value && _hasMoreMessages) {
      loadMessages();
    }
  }

  @override
  void onClose() {
    _markAsRead();
    messageController.dispose();
    scrollController.dispose();
    super.onClose();
  }
}