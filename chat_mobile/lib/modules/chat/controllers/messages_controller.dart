// lib/modules/chat/controllers/messages_controller.dart

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/conversation.dart';
import '../../../data/models/message.dart';
import '../../../data/services/message_service.dart';
import '../../../data/services/websocket_service.dart';
import '../../../data/services/secure_storage_service.dart';
import '../views/chat_view.dart';

class MessagesController extends GetxController {
  final MessageService _messageService = Get.find<MessageService>();
  final WebSocketService _webSocketService = Get.find<WebSocketService>();
  final SecureStorageService _storage = Get.find<SecureStorageService>();

  final conversations = <Conversation>[].obs;
  final filteredConversations = <Conversation>[].obs;
  final isLoading = false.obs;
  final searchQuery = ''.obs;
  final selectedTabIndex = 0.obs;
  final totalUnreadCount = 0.obs;

  int? _currentUserId;
  int? get currentUserId => _currentUserId;

  @override
  void onInit() {
    super.onInit();
    initializeMessages();
  }

  // ✅ Tout en async dans le bon ordre
  Future<void> initializeMessages() async {
    // 1. Charger currentUserId D'ABORD
    await _initCurrentUser();
    
    // 2. Charger conversations
    await loadConversations();
    
    // 3. WebSocket
    _webSocketService.connect();
    listenToNewMessages();
  }

  Future<void> _initCurrentUser() async {
    try {
      final userId = await _storage.getUserId();
      
      if (userId != null) {
        _currentUserId = int.tryParse(userId);
        print('👤 Current user ID: $_currentUserId');
      } else {
        print('⚠️ No user ID in storage');
        // ✅ Fallback: charger depuis API
        await _loadUserIdFromAPI();
      }
    } catch (e) {
      print('❌ _initCurrentUser: $e');
      await _loadUserIdFromAPI();
    }
  }

// lib/modules/chat/controllers/messages_controller.dart

Future<void> _loadUserIdFromAPI() async {
  try {
    final data = await _messageService.getCurrentUser();  // ✅ Appel simplifié
    
    if (data != null) {
      final userIdValue = data['user_id'] ?? data['id'];
      
      if (userIdValue != null) {
        _currentUserId = int.tryParse(userIdValue.toString());
        print('👤 Current user ID from API: $_currentUserId');
        
        // Sauvegarde pour la prochaine fois
        await _storage.saveUserId(_currentUserId.toString());
      }
    }
  } catch (e) {
    print('❌ _loadUserIdFromAPI: $e');
  }
}

  Future<void> loadConversations() async {
    try {
      isLoading.value = true;
      
      final result = await _messageService.getConversations();
      
      if (result != null && result.isNotEmpty) {
        // Trie par date
        result.sort((a, b) {
          final aDate = a.lastMessageAt ?? a.createdAt;
          final bDate = b.lastMessageAt ?? b.createdAt;
          return bDate.compareTo(aDate);
        });
        
        conversations.assignAll(result);
        
        print('✅ Loaded ${conversations.length} conversations');
        print('📋 Conversations: ${conversations.map((c) => c.name ?? c.id).toList()}');
        
        _applyCurrentFilter();
        calculateUnreadCount();
      } else {
        print('⚠️ No conversations loaded');
        conversations.clear();
        filteredConversations.clear();
      }
    } catch (e) {
      print('❌ loadConversations: $e');
    } finally {
      isLoading.value = false;
    }
  }

  void openConversation(Conversation conversation) {
    print('📂 Opening conversation: ${conversation.id}');
    
    Get.to(
      () => ChatView(),
      arguments: {
        'conversation': conversation,
        'contactName': conversation.name ?? 'Conversation',
      },
      preventDuplicates: true,
    )?.then((_) {
      print('🔄 Returned from ChatView - Reloading conversations');
      loadConversations();
    });
  }

  Future<void> openOrCreateConversation({
    required String contactUserId,
    required String contactName,
  }) async {
    try {
      print('🔍 Looking for conversation with: $contactUserId');
      
      // 1. Cherche conversation existante
      var existing = conversations.firstWhereOrNull((conv) {
        if (conv.isGroup) return false;
        return conv.participants.any((p) =>
          p.userId.toString() == contactUserId.toString()
        );
      });

      if (existing == null) {
        await loadConversations();
        existing = conversations.firstWhereOrNull((conv) {
          if (conv.isGroup) return false;
          return conv.participants.any((p) =>
            p.userId.toString() == contactUserId.toString()
          );
        });
      }

      if (existing != null) {
        print('✅ Found existing conversation: ${existing.id}');
        Get.back();
        await Future.delayed(const Duration(milliseconds: 100));
        openConversation(existing);
        return;
      }

      // 2. Crée nouvelle conversation
      print('📝 Creating new conversation...');
      
      final newConversation = await _messageService.createDirectConversation(
        contactUserId,
      );

      if (newConversation != null) {
        print('✅ Conversation created: ${newConversation.id}');
        
        await loadConversations();
        
        Get.back();
        await Future.delayed(const Duration(milliseconds: 100));
        
        openConversation(newConversation);
      } else {
        throw Exception('Failed to create conversation');
      }
      
    } catch (e) {
      print('❌ openOrCreateConversation: $e');
      
      Get.snackbar(
        '❌ Erreur',
        'Impossible de créer la conversation',
        backgroundColor: Colors.red.withOpacity(0.1),
        colorText: Colors.red,
      );
    }
  }

  void listenToNewMessages() {
    _webSocketService.messageStream.listen((message) {
      updateConversationWithNewMessage(message);
      calculateUnreadCount();
    });
  }

  Future<void> updateConversationWithNewMessage(Message message) async {
    final index = conversations.indexWhere(
      (conv) => conv.id == message.conversationId,
    );

    if (index != -1) {
      final conv = conversations[index];
      
      final updatedConv = conv.copyWith(
        lastMessage: message,
        lastMessageAt: message.timestamp,
        unreadCount: conv.unreadCount + 1,
      );

      conversations.removeAt(index);
      conversations.insert(0, updatedConv);
      
      _applyCurrentFilter();
    } else {
      await loadConversations();
    }
  }

  void searchConversations(String query) {
    searchQuery.value = query;
    _applyCurrentFilter();
  }

  void changeTab(int index) {
    selectedTabIndex.value = index;
    _applyCurrentFilter();
  }

  void _applyCurrentFilter() {
    print('🔍 Applying filter - currentUserId: $_currentUserId');
    print('📊 Total conversations: ${conversations.length}');
    
    // ✅ Si pas de currentUserId, affiche quand même avec nom par défaut
    if (searchQuery.isNotEmpty) {
      filteredConversations.assignAll(
        conversations.where((c) {
          final name = (c.name ?? 'Conversation').toLowerCase();
          final lastMsg = c.lastMessage?.content?.toLowerCase() ?? '';
          final query = searchQuery.value.toLowerCase();
          return name.contains(query) || lastMsg.contains(query);
        }).toList(),
      );
      print('🔍 Filtered by search: ${filteredConversations.length} results');
      return;
    }

    switch (selectedTabIndex.value) {
      case 0: // Discussions
        filteredConversations.assignAll(
          conversations.where((c) => !c.isGroup).toList()
        );
        break;
      case 1: // Groupes
        filteredConversations.assignAll(
          conversations.where((c) => c.isGroup).toList()
        );
        break;
      default:
        filteredConversations.assignAll(conversations);
    }
    
    print('✅ Filtered conversations: ${filteredConversations.length}');
  }

  void calculateUnreadCount() {
    totalUnreadCount.value = conversations.fold(
      0,
      (sum, conv) => sum + conv.unreadCount,
    );
  }

  Future<void> refresh() async {
    await loadConversations();
  }
}


// // lib/modules/chat/controllers/messages_controller.dart

// import 'package:flutter/material.dart';
// import 'package:get/get.dart';
// import '../../../data/models/conversation.dart';
// import '../../../data/models/message.dart';
// import '../../../data/services/message_service.dart';
// import '../../../data/services/websocket_service.dart';
// import '../../../data/services/secure_storage_service.dart';
// import '../views/chat_view.dart';

// class MessagesController extends GetxController {
//   final MessageService _messageService = Get.find<MessageService>();
//   final WebSocketService _webSocketService = Get.find<WebSocketService>();
//   final SecureStorageService _storage = Get.find<SecureStorageService>();

//   final conversations = <Conversation>[].obs;
//   final filteredConversations = <Conversation>[].obs;
//   final isLoading = false.obs;
//   final searchQuery = ''.obs;
//   final selectedTabIndex = 0.obs;
//   final totalUnreadCount = 0.obs;

//   int? _currentUserId;
//   int? get currentUserId => _currentUserId;

//   @override
//   void onInit() {
//     super.onInit();
//     _initCurrentUser();
//     initializeMessages();
//   }

//   Future<void> _initCurrentUser() async {
//     final userId = await _storage.getUserId();
//     _currentUserId = userId != null ? int.tryParse(userId) : null;
//     print('👤 Current user ID: $_currentUserId');
//   }

//   Future<void> initializeMessages() async {
//     await loadConversations();
//     _webSocketService.connect();
//     listenToNewMessages();
//   }

//   Future<void> loadConversations() async {
//     try {
//       isLoading.value = true;
      
//       final result = await _messageService.getConversations();
      
//       if (result != null) {
//         // ✅ Trie par date (plus récent en premier)
//         result.sort((a, b) {
//           final aDate = a.lastMessageAt ?? a.createdAt;
//           final bDate = b.lastMessageAt ?? b.createdAt;
//           return bDate.compareTo(aDate);
//         });
        
//         conversations.assignAll(result);
//         _applyCurrentFilter();
//         calculateUnreadCount();
        
//         print('✅ Loaded ${conversations.length} conversations');
//       }
//     } catch (e) {
//       print('❌ loadConversations: $e');
//     } finally {
//       isLoading.value = false;
//     }
//   }

//   // ✅ OUVRIR CONVERSATION EXISTANTE
//   void openConversation(Conversation conversation) {
//     print('📂 Opening conversation: ${conversation.id}');
    
//     Get.to(
//       () => ChatView(),
//       arguments: {
//         'conversation': conversation,
//         'contactName': conversation.displayName(_currentUserId ?? 0),
//       },
//       preventDuplicates: true,
//     )?.then((_) {
//       // ✅ Recharge la liste au retour
//       print('🔄 Returned from ChatView - Reloading conversations');
//       loadConversations();
//     });
//   }

//   // ✅ OUVRIR OU CRÉER CONVERSATION (depuis contact)
//   Future<void> openOrCreateConversation({
//     required String contactUserId,
//     required String contactName,
//   }) async {
//     try {
//       print('🔍 Looking for conversation with: $contactUserId');
      
//       // 1. Cherche conversation existante
//       var existing = conversations.firstWhereOrNull((conv) {
//         if (conv.isGroup) return false;
//         return conv.participants.any((p) =>
//           p.userId.toString() == contactUserId.toString()
//         );
//       });

//       // 2. Si pas trouvé, recharge la liste (peut-être créée ailleurs)
//       if (existing == null) {
//         await loadConversations();
//         existing = conversations.firstWhereOrNull((conv) {
//           if (conv.isGroup) return false;
//           return conv.participants.any((p) =>
//             p.userId.toString() == contactUserId.toString()
//           );
//         });
//       }

//       // 3. Si trouvé, ouvre directement
//       if (existing != null) {
//         print('✅ Found existing conversation: ${existing.id}');
        
//         // ✅ Retourne d'abord à MessagesView
//         Get.back();  // Ferme ContactsView
        
//         // Attend un peu pour que l'animation se termine
//         await Future.delayed(const Duration(milliseconds: 100));
        
//         // Ouvre ChatView
//         openConversation(existing);
//         return;
//       }

//       // 4. Crée nouvelle conversation
//       print('📝 Creating new conversation...');
      
//       final newConversation = await _messageService.createDirectConversation(
//         contactUserId,
//       );

//       if (newConversation != null) {
//         print('✅ Conversation created: ${newConversation.id}');
        
//         // ✅ Recharge la liste complète
//         await loadConversations();
        
//         // Retourne à MessagesView
//         Get.back();
        
//         await Future.delayed(const Duration(milliseconds: 100));
        
//         // Ouvre ChatView avec la nouvelle conversation
//         openConversation(newConversation);
//       } else {
//         throw Exception('Failed to create conversation');
//       }
      
//     } catch (e) {
//       print('❌ openOrCreateConversation: $e');
      
//       Get.snackbar(
//         '❌ Erreur',
//         'Impossible de créer la conversation',
//         backgroundColor: Colors.red.withOpacity(0.1),
//         colorText: Colors.red,
//       );
//     }
//   }

//   void listenToNewMessages() {
//     _webSocketService.messageStream.listen((message) {
//       updateConversationWithNewMessage(message);
//       calculateUnreadCount();
//     });
//   }

//   Future<void> updateConversationWithNewMessage(Message message) async {
//     final index = conversations.indexWhere(
//       (conv) => conv.id == message.conversationId,
//     );

//     if (index != -1) {
//       final conv = conversations[index];
      
//       final updatedConv = conv.copyWith(
//         lastMessage: message,
//         lastMessageAt: message.timestamp,
//         unreadCount: conv.unreadCount + 1,
//       );

//       // ✅ Déplace en haut de la liste
//       conversations.removeAt(index);
//       conversations.insert(0, updatedConv);
      
//       _applyCurrentFilter();
//     } else {
//       // Conversation inconnue, recharge la liste
//       await loadConversations();
//     }
//   }

//   void searchConversations(String query) {
//     searchQuery.value = query;
//     _applyCurrentFilter();
//   }

//   void changeTab(int index) {
//     selectedTabIndex.value = index;
//     _applyCurrentFilter();
//   }

//   void _applyCurrentFilter() {
//     if (_currentUserId == null) return;

//     if (searchQuery.isNotEmpty) {
//       filteredConversations.assignAll(
//         conversations.where((c) {
//           final name = c.displayName(_currentUserId!).toLowerCase();
//           final lastMsg = c.lastMessage?.content?.toLowerCase() ?? '';
//           final query = searchQuery.value.toLowerCase();
//           return name.contains(query) || lastMsg.contains(query);
//         }).toList(),
//       );
//       return;
//     }

//     switch (selectedTabIndex.value) {
//       case 0: // Discussions
//         filteredConversations.assignAll(
//           conversations.where((c) => !c.isGroup).toList()
//         );
//         break;
//       case 1: // Groupes
//         filteredConversations.assignAll(
//           conversations.where((c) => c.isGroup).toList()
//         );
//         break;
//       default:
//         filteredConversations.assignAll(conversations);
//     }
//   }

//   void calculateUnreadCount() {
//     totalUnreadCount.value = conversations.fold(
//       0,
//       (sum, conv) => sum + conv.unreadCount,
//     );
//   }

//   Future<void> refresh() async {
//     await loadConversations();
//   }
// }

