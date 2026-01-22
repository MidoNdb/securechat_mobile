// lib/data/services/message_service.dart

import 'dart:async';
import 'dart:math';
import 'package:get/get.dart';
import '../api/api_endpoints.dart';
import '../api/dio_client.dart';
import '../models/message.dart';
import '../models/conversation.dart';
import 'crypto_service.dart';
import 'websocket_service.dart';
import 'auth_service.dart';
import 'secure_storage_service.dart';

class MessageService extends GetxService {
  final DioClient _dioClient = Get.find<DioClient>();
  final CryptoService _cryptoService = Get.find<CryptoService>();
  final WebSocketService _wsService = Get.find<WebSocketService>();
  final AuthService _authService = Get.find<AuthService>();
  final SecureStorageService _secureStorage = Get.find<SecureStorageService>();
  
  StreamSubscription? _wsSubscription;
  
  final _newMessagesController = StreamController<Message>.broadcast();
  Stream<Message> get newMessagesStream => _newMessagesController.stream;
  
  @override
  void onInit() {
    super.onInit();
    _listenWebSocket();
    print('✅ MessageService initialized');
  }
  
  @override
  void onClose() {
    _wsSubscription?.cancel();
    _newMessagesController.close();
    super.onClose();
  }
  
  void _listenWebSocket() {
    _wsSubscription = _wsService.messageStream.listen((data) {
      final type = data['type'] as String?;
      
      if (type == 'new_message') {
        _handleNewMessage(data);
      } else if (type == 'typing') {
        print('⌨️ ${data['user_name']} typing...');
      } else if (type == 'message_read_receipt') {
        print('✅ Message read: ${data['message_id']}');
      }
    });
  }
  
  void _handleNewMessage(Map<String, dynamic> data) {
    try {
      final messageData = data['message'] as Map<String, dynamic>;
      final message = Message.fromJson(messageData);
      
      print('📨 New message: ${message.id}');
      
      final currentUserId = _authService.currentUser.value?.userId;
      if (message.senderId != currentUserId) {
        _decryptAndEmit(message);
      } else {
        _newMessagesController.add(message);
      }
      
    } catch (e) {
      print('❌ Handle new message error: $e');
    }
  }
  
  Future<void> _decryptAndEmit(Message message) async {
    try {
      final decrypted = await decryptMessage(message);
      final decryptedMessage = message.copyWith(decryptedContent: decrypted);
      _newMessagesController.add(decryptedMessage);
    } catch (e) {
      print('❌ Decrypt and emit error: $e');
      _newMessagesController.add(message);
    }
  }
  
  Future<List<Conversation>?> getConversations() async {
    try {
      print('📥 Fetching conversations...');
      
      final response = await _dioClient.privateDio.get(ApiEndpoints.conversations);
      
      if (response.statusCode == 200) {
        final data = response.data['data'] as List;
        final conversations = data.map((json) => Conversation.fromJson(json)).toList();
        print('✅ ${conversations.length} conversations loaded');
        return conversations;
      }
      
      throw Exception('Error ${response.statusCode}');
    } catch (e) {
      print('❌ getConversations error: $e');
      return null;
    }
  }
  
  Future<Conversation?> createDirectConversation(String participantUserId) async {
    try {
      print('📝 Creating conversation with: $participantUserId');
      
      final response = await _dioClient.privateDio.post(
        ApiEndpoints.createConversation,
        data: {
          'type': 'DIRECT',
          'participant_ids': [participantUserId],
        },
      );
      
      if (response.statusCode == 201) {
        final conversation = Conversation.fromJson(response.data['data']);
        print('✅ Conversation created: ${conversation.id}');
        return conversation;
      }
      
      throw Exception('Error ${response.statusCode}');
    } catch (e) {
      print('❌ createDirectConversation error: $e');
      return null;
    }
  }
  
  Future<Map<String, dynamic>?> getCurrentUser() async {
    try {
      final response = await _dioClient.privateDio.get(ApiEndpoints.me);
      
      if (response.statusCode == 200) {
        return response.data['data'] as Map<String, dynamic>;
      }
      
      return null;
    } catch (e) {
      print('❌ getCurrentUser error: $e');
      return null;
    }
  }
  
  Future<Message> sendMessage({
    required String conversationId,
    required String recipientUserId,
    required String content,
    String type = 'TEXT',
    Map<String, dynamic>? metadata,
  }) async {
    try {
      print('📤 Sending message...');
      
      final encrypted = await encryptMessage(recipientUserId, content);
      
      final data = {
        'conversation_id': conversationId,
        'recipient_user_id': recipientUserId,
        'type': type,
        'encrypted_content': encrypted['ciphertext'],
        'nonce': encrypted['nonce'],
        'auth_tag': encrypted['auth_tag'],
        'signature': encrypted['signature'],
        if (metadata != null) 'metadata': metadata,
      };
      
      final response = await _dioClient.privateDio.post(
        ApiEndpoints.sendMessage,
        data: data,
      );
      
      if (response.statusCode == 201) {
        final messageData = response.data['data'] as Map<String, dynamic>;
        final message = Message.fromJson(messageData);
        
        print('✅ Message sent: ${message.id}');
        
        await _secureStorage.saveMessagePlaintext(message.id, content);
        
        return message.copyWith(decryptedContent: content);
      }
      
      throw Exception('Error ${response.statusCode}');
    } catch (e) {
      print('❌ sendMessage error: $e');
      rethrow;
    }
  }
  
  Future<List<Message>> getConversationMessages({
    required String conversationId,
    int page = 1,
    int pageSize = 50,
  }) async {
    try {
      print('📥 Fetching messages: $conversationId');
      
      final response = await _dioClient.privateDio.get(
        ApiEndpoints.getMessagesByConversation(conversationId),
        queryParameters: {
          'page': page,
          'page_size': pageSize,
        },
      );
      
      if (response.statusCode == 200) {
        final data = response.data['data'] as List;
        final messages = data.map((json) => Message.fromJson(json)).toList();
        
        print('✅ ${messages.length} messages fetched');
        
        final decryptedMessages = await _decryptMessages(messages);
        
        return decryptedMessages;
      }
      
      throw Exception('Error ${response.statusCode}');
    } catch (e) {
      print('❌ getConversationMessages error: $e');
      rethrow;
    }
  }

Future<List<Message>> _decryptMessages(List<Message> messages) async {
  final decrypted = <Message>[];
  final currentUserId = _authService.currentUser.value?.userId;
  
  for (final message in messages) {
    try {
      // ✅ AJOUT : Vérifier champs E2EE obligatoires
      if (message.nonce == null || message.nonce!.isEmpty ||
          message.authTag == null || message.authTag!.isEmpty ||
          message.signature == null || message.signature!.isEmpty) {
        print('⚠️ Message ${message.id} sans champs E2EE complets');
        decrypted.add(message.copyWith(
          decryptedContent: '[Message non chiffré]'
        ));
        continue;
      }
      
      // ✅ Vérifier cache en premier
      final cached = await _secureStorage.getMessagePlaintext(message.id);
      
      if (cached != null) {
        decrypted.add(message.copyWith(decryptedContent: cached));
        print('✅ From cache: ${message.id}');
        continue;
      }
      
      // ✅ Déchiffrer
      final content = await decryptMessage(message);
      
      // ✅ Sauvegarder en cache pour la prochaine fois
      await _secureStorage.saveMessagePlaintext(message.id, content);
      
      decrypted.add(message.copyWith(decryptedContent: content));
      
      final preview = content.length > 20 ? '${content.substring(0, 20)}...' : content;
      print('✅ Decrypted: ${message.id} - "$preview"');
      
    } catch (e) {
      print('❌ Decrypt error ${message.id}: $e');
      
      // ✅ AMÉLIORATION : Message d'erreur informatif
      String fallbackText;
      
      if (e.toString().contains('Signature invalide')) {
        fallbackText = '[Message chiffré avec anciennes clés]';
      } else if (e.toString().contains('recipientUserId missing')) {
        fallbackText = '[Erreur: destinataire inconnu]';
      } else if (e.toString().contains('E2EE fields missing')) {
        fallbackText = '[Message corrompu]';
      } else {
        fallbackText = '[Message illisible]';
      }
      
      decrypted.add(message.copyWith(decryptedContent: fallbackText));
    }
  }
  
  return decrypted;
}

Future<String> decryptMessage(Message message) async {
  try {
    print('🔓 Decrypting message ${message.id}');
    print('   From: ${message.senderId}');
    
    // ✅ VÉRIFICATION STRICTE des champs E2EE
    if (message.nonce == null || message.nonce!.isEmpty) {
      throw Exception('E2EE fields missing: nonce');
    }
    if (message.authTag == null || message.authTag!.isEmpty) {
      throw Exception('E2EE fields missing: authTag');
    }
    if (message.signature == null || message.signature!.isEmpty) {
      throw Exception('E2EE fields missing: signature');
    }
    
    final myDhPrivate = await _secureStorage.getDHPrivateKey();
    
    if (myDhPrivate == null) {
      throw Exception('Private key missing');
    }
    
    final currentUserId = _authService.currentUser.value?.userId;
    
    // ✅ LOGIQUE CORRECTE : Déterminer qui est "l'autre"
    String otherUserId;
    
    if (message.senderId == currentUserId) {
      // ✅ CAS 1 : C'est NOTRE message → Utiliser le DESTINATAIRE
      if (message.recipientUserId == null || message.recipientUserId!.isEmpty) {
        // ⚠️ FALLBACK : Si recipient manque, chercher dans participants
        print('   ⚠️ recipientUserId manquant, tentative fallback...');
        
        // Option A : Utiliser le premier participant qui n'est pas nous
        // (nécessite d'avoir accès à la conversation, sinon lever exception)
        throw Exception('recipientUserId missing for own message');
      }
      
      otherUserId = message.recipientUserId!;
      print('   → Message de NOUS → Clés du DESTINATAIRE: $otherUserId');
      
    } else {
      // ✅ CAS 2 : Message REÇU → Utiliser l'EXPÉDITEUR
      otherUserId = message.senderId;
      print('   → Message REÇU → Clés de l\'EXPÉDITEUR: $otherUserId');
    }
    
    // ✅ Récupérer clés publiques de "l'autre"
    final otherUserKeys = await _getRecipientPublicKeys(otherUserId);
    
    // ✅ Déchiffrer
    final plaintext = await _cryptoService.decryptMessage(
      ciphertextB64: message.encryptedContent,
      nonceB64: message.nonce!,
      authTagB64: message.authTag!,
      signatureB64: message.signature!,
      myDhPrivateKeyB64: myDhPrivate,
      theirDhPublicKeyB64: otherUserKeys['dh_public_key']!,
      theirSignPublicKeyB64: otherUserKeys['sign_public_key']!,
    );
    
    print('✅ Déchiffrement réussi');
    
    return plaintext;
    
  } catch (e) {
    print('❌ decryptMessage error: $e');
    rethrow;
  }
}
  
  Future<void> markConversationAsRead(String conversationId) async {
    try {
      await _dioClient.privateDio.post(
        ApiEndpoints.markAsRead,
        data: {'conversation_id': conversationId},
      );
      print('✅ Marked as read');
    } catch (e) {
      print('❌ markConversationAsRead error: $e');
    }
  }
  
  Future<Map<String, String>> encryptMessage(
    String recipientUserId,
    String plaintext,
  ) async {
    try {
      print('🔐 Encrypting for: $recipientUserId');
      
      final myDhPrivate = await _secureStorage.getDHPrivateKey();
      final mySignPrivate = await _secureStorage.getSignPrivateKey();
      
      if (myDhPrivate == null || mySignPrivate == null) {
        throw Exception('Private keys missing');
      }
      
      final recipientKeys = await _getRecipientPublicKeys(recipientUserId);
      
      final encrypted = await _cryptoService.encryptMessage(
        plaintext: plaintext,
        myDhPrivateKeyB64: myDhPrivate,
        theirDhPublicKeyB64: recipientKeys['dh_public_key']!,
        mySignPrivateKeyB64: mySignPrivate,
      );
      
      print('✅ Encrypted');
      
      return encrypted;
    } catch (e) {
      print('❌ encryptMessage error: $e');
      rethrow;
    }
  }
  
  // Future<String> decryptMessage(Message message) async {
  //   try {
  //     print('🔓 Decrypting from: ${message.senderId}');
      
  //     if (message.nonce == null || message.authTag == null || message.signature == null) {
  //       throw Exception('E2EE fields missing');
  //     }
      
  //     final myDhPrivate = await _secureStorage.getDHPrivateKey();
      
  //     if (myDhPrivate == null) {
  //       throw Exception('Private key missing');
  //     }
      
  //     final currentUserId = _authService.currentUser.value?.userId;
      
  //     String otherUserId;
  //     if (message.senderId == currentUserId) {
  //       if (message.recipientUserId == null) {
  //         throw Exception('recipientUserId missing for own message');
  //       }
  //       otherUserId = message.recipientUserId!;
  //       print('  → Using recipient keys: $otherUserId');
  //     } else {
  //       otherUserId = message.senderId;
  //       print('  → Using sender keys: $otherUserId');
  //     }
      
  //     final otherUserKeys = await _getRecipientPublicKeys(otherUserId);
      
  //     final plaintext = await _cryptoService.decryptMessage(
  //       ciphertextB64: message.encryptedContent,
  //       nonceB64: message.nonce!,
  //       authTagB64: message.authTag!,
  //       signatureB64: message.signature!,
  //       myDhPrivateKeyB64: myDhPrivate,
  //       theirDhPublicKeyB64: otherUserKeys['dh_public_key']!,
  //       theirSignPublicKeyB64: otherUserKeys['sign_public_key']!,
  //     );
      
  //     print('✅ Decrypted');
      
  //     return plaintext;
  //   } catch (e) {
  //     print('❌ decryptMessage error: $e');
  //     rethrow;
  //   }
  // }
  
  Future<Map<String, String>> _getRecipientPublicKeys(String userId) async {
    try {
      final response = await _dioClient.privateDio.get(
        ApiEndpoints.getPublicKeys(userId),
      );
      
      if (response.statusCode == 200) {
        final data = response.data['data'] as Map<String, dynamic>;
        return {
          'dh_public_key': data['dh_public_key'] as String,
          'sign_public_key': data['sign_public_key'] as String,
        };
      }
      
      throw Exception('Error ${response.statusCode}');
    } catch (e) {
      print('❌ getPublicKeys error: $e');
      rethrow;
    }
  }
  
  void joinConversation(String conversationId) {
    _wsService.joinConversation(conversationId);
  }
  
  void sendTypingIndicator(String conversationId, bool isTyping) {
    _wsService.sendTyping(conversationId, isTyping);
  }
}



// // lib/data/services/message_service.dart

// import 'dart:async';
// import 'dart:math';
// import 'package:get/get.dart';
// import '../api/api_endpoints.dart';
// import '../api/dio_client.dart';
// import '../models/message.dart';
// import '../models/conversation.dart';
// import 'crypto_service.dart';
// import 'websocket_service.dart';
// import 'auth_service.dart';
// import 'secure_storage_service.dart';

// /// Service de gestion des messages
// /// 
// /// Architecture B (HTTP + WebSocket HYBRIDE):
// /// - ENVOI: HTTP POST (fiable, retry automatique)
// /// - RÉCEPTION: WebSocket push (temps réel < 100ms)
// class MessageService extends GetxService {
//   // ═══════════════════════════════════════════════════════════════
//   // DÉPENDANCES
//   // ═══════════════════════════════════════════════════════════════
  
//   final DioClient _dioClient = Get.find<DioClient>();
//   final CryptoService _cryptoService = Get.find<CryptoService>();
//   final WebSocketService _wsService = Get.find<WebSocketService>();
//   final AuthService _authService = Get.find<AuthService>();
//   final SecureStorageService _secureStorage = Get.find<SecureStorageService>();
  
//   StreamSubscription? _wsSubscription;
  
//   // Stream controller pour les nouveaux messages
//   final _newMessagesController = StreamController<Message>.broadcast();
//   Stream<Message> get newMessagesStream => _newMessagesController.stream;
  
//   // ═══════════════════════════════════════════════════════════════
//   // INITIALISATION
//   // ═══════════════════════════════════════════════════════════════
  
//   @override
//   void onInit() {
//     super.onInit();
//     _listenWebSocket();
//     print('✅ MessageService initialized');
//   }
  
//   @override
//   void onClose() {
//     _wsSubscription?.cancel();
//     _newMessagesController.close();
//     super.onClose();
//   }
  
//   // ═══════════════════════════════════════════════════════════════
//   // ÉCOUTE WEBSOCKET (RÉCEPTION TEMPS RÉEL)
//   // ═══════════════════════════════════════════════════════════════
  
//   /// Écouter les messages WebSocket
//   void _listenWebSocket() {
//     _wsSubscription = _wsService.messageStream.listen((data) {
//       final type = data['type'] as String?;
      
//       if (type == 'new_message') {
//         _handleNewMessage(data);
//       } else if (type == 'typing') {
//         _handleTypingIndicator(data);
//       } else if (type == 'message_read_receipt') {
//         _handleReadReceipt(data);
//       }
//     });
//   }
  
//   /// Gérer nouveau message reçu via WebSocket
//   void _handleNewMessage(Map<String, dynamic> data) {
//     try {
//       final messageData = data['message'] as Map<String, dynamic>;
      
//       // Convertir en Message
//       final message = Message.fromJson(messageData);
      
//       print('📨 Nouveau message reçu: ${message.id}');
      
//       // Déchiffrer si ce n'est pas notre message
//       final currentUserId = _authService.currentUser.value?.userId;
//       if (message.senderId != currentUserId) {
//         _decryptAndEmit(message);
//       } else {
//         // Notre propre message (déjà déchiffré)
//         _newMessagesController.add(message);
//       }
      
//     } catch (e) {
//       print('❌ Erreur traitement nouveau message: $e');
//     }
//   }
  
//   /// Déchiffrer un message et l'émettre
//   /// /// Déchiffrer une liste de messages
// Future<List<Message>> _decryptMessages(List<Message> messages) async {
//   final decrypted = <Message>[];
//   final currentUserId = _authService.currentUser.value?.userId;
  
//   for (final message in messages) {
//     try {
//       // ✅ CORRECTION : Déchiffrer TOUS les messages, même les nôtres
//       // Car ils sont stockés chiffrés sur le serveur
      
//       final content = await decryptMessage(message);
      
//       decrypted.add(message.copyWith(decryptedContent: content));
      
//       print('✅ Message ${message.id} déchiffré: ${content.substring(0, min(20, content.length))}...');
      
//     } catch (e) {
//       print('❌ Erreur déchiffrement message ${message.id}: $e');
//       // Ajouter quand même le message (chiffré)
//       decrypted.add(message);
//     }
//   }
  
//   return decrypted;
// }

// Future<void> _decryptAndEmit(Message message) async {
//   try {
//     // Déchiffrer le message
//       final decrypted = await decryptMessage(message);
      
//       // Créer nouveau message avec contenu déchiffré
//       final decryptedMessage = message.copyWith(
//         decryptedContent: decrypted,
//       );
      
//       // Émettre dans le stream
//       _newMessagesController.add(decryptedMessage);
      
//     } catch (e) {
//       print('❌ Erreur déchiffrement message: $e');
//       // Émettre quand même le message (chiffré)
//       _newMessagesController.add(message);
//     }
//   }
  
//   void _handleTypingIndicator(Map<String, dynamic> data) {
//     // TODO: Implémenter si nécessaire
//     print('⌨️ ${data['user_name']} est en train d\'écrire...');
//   }
  
//   void _handleReadReceipt(Map<String, dynamic> data) {
//     // TODO: Implémenter si nécessaire
//     print('✅ Message lu: ${data['message_id']}');
//   }
  
//   // ═══════════════════════════════════════════════════════════════
//   // CONVERSATIONS (pour MessagesController)
//   // ═══════════════════════════════════════════════════════════════
  
//   /// Récupérer toutes les conversations
//   Future<List<Conversation>?> getConversations() async {
//     try {
//       print('📥 Récupération conversations...');
      
//       final response = await _dioClient.privateDio.get(
//         ApiEndpoints.conversations,
//       );
      
//       if (response.statusCode == 200) {
//         final data = response.data['data'] as List;
//         final conversations = data
//             .map((json) => Conversation.fromJson(json))
//             .toList();
        
//         print('✅ ${conversations.length} conversations récupérées');
        
//         return conversations;
//       } else {
//         throw Exception('Erreur récupération conversations: ${response.statusCode}');
//       }
      
//     } catch (e) {
//       print('❌ Erreur getConversations: $e');
//       return null;
//     }
//   }
  
//   /// Créer une conversation directe avec un contact
//   Future<Conversation?> createDirectConversation(String participantUserId) async {
//     try {
//       print('📝 Création conversation avec: $participantUserId');
      
//       final response = await _dioClient.privateDio.post(
//         ApiEndpoints.createConversation,
//         data: {
//           'type': 'DIRECT',
//           'participant_ids': [participantUserId],
//         },
//       );
      
//       if (response.statusCode == 201) {
//         final conversation = Conversation.fromJson(response.data['data']);
//         print('✅ Conversation créée: ${conversation.id}');
//         return conversation;
//       } else {
//         throw Exception('Erreur création conversation: ${response.statusCode}');
//       }
      
//     } catch (e) {
//       print('❌ Erreur createDirectConversation: $e');
//       return null;
//     }
//   }
  
//   /// Récupérer les infos du user actuel
//   Future<Map<String, dynamic>?> getCurrentUser() async {
//     try {
//       final response = await _dioClient.privateDio.get(
//         ApiEndpoints.me,
//       );
      
//       if (response.statusCode == 200) {
//         return response.data['data'] as Map<String, dynamic>;
//       }
      
//       return null;
//     } catch (e) {
//       print('❌ Erreur getCurrentUser: $e');
//       return null;
//     }
//   }
  
//   // ═══════════════════════════════════════════════════════════════
//   // ENVOI DE MESSAGES (HTTP)
//   // ═══════════════════════════════════════════════════════════════
  
//   /// Envoyer un message chiffré
//   /// 
//   /// Architecture B: Utilise HTTP POST (fiable)
//   Future<Message> sendMessage({
//     required String conversationId,
//     required String recipientUserId,
//     required String content,
//     String type = 'TEXT',
//     Map<String, dynamic>? metadata,
//   }) async {
//     try {
//       print('📤 Envoi message via HTTP...');
      
//       // 1. Chiffrer le message
//       final encrypted = await encryptMessage(recipientUserId, content);
      
//       // 2. Préparer les données
//       final data = {
//         'conversation_id': conversationId,
//         'type': type,
//         'encrypted_content': encrypted['ciphertext'],
//         'nonce': encrypted['nonce'],
//         'auth_tag': encrypted['auth_tag'],
//         'signature': encrypted['signature'],
//         if (metadata != null) 'metadata': metadata,
//       };
      
//       // 3. Envoyer via HTTP POST (utilise privateDio avec AuthInterceptor)
//       final response = await _dioClient.privateDio.post(
//         ApiEndpoints.sendMessage,
//         data: data,
//       );
      
//       if (response.statusCode == 201) {
//         final messageData = response.data['data'] as Map<String, dynamic>;
//         final message = Message.fromJson(messageData);
        
//         print('✅ Message envoyé via HTTP: ${message.id}');
        
//         // Le backend broadcast via WebSocket aux autres participants
//         // On recevra notre propre message via WebSocket aussi
        
//         return message.copyWith(decryptedContent: content);
//       } else {
//         throw Exception('Erreur envoi message: ${response.statusCode}');
//       }
      
//     } catch (e) {
//       print('❌ Erreur sendMessage: $e');
//       rethrow;
//     }
//   }
  
//   // ═══════════════════════════════════════════════════════════════
//   // RÉCUPÉRATION DES MESSAGES (HTTP)
//   // ═══════════════════════════════════════════════════════════════
  
//   /// Récupérer les messages d'une conversation
//   /// 
//   /// Utilisé pour:
//   /// - Chargement initial
//   /// - Pagination (messages plus anciens)
//   Future<List<Message>> getConversationMessages({
//     required String conversationId,
//     int page = 1,
//     int pageSize = 50,
//   }) async {
//     try {
//       print('📥 Récupération messages conversation: $conversationId');
      
//       final response = await _dioClient.privateDio.get(
//         ApiEndpoints.getMessagesByConversation(conversationId),
//         queryParameters: {
//           'page': page,
//           'page_size': pageSize,
//         },
//       );
      
//       if (response.statusCode == 200) {
//         final data = response.data['data'] as List;
//         final messages = data.map((json) => Message.fromJson(json)).toList();
        
//         print('✅ ${messages.length} messages récupérés');
        
//         // Déchiffrer tous les messages
//         final decryptedMessages = await _decryptMessages(messages);
        
//         return decryptedMessages;
//       } else {
//         throw Exception('Erreur récupération messages: ${response.statusCode}');
//       }
      
//     } catch (e) {
//       print('❌ Erreur getConversationMessages: $e');
//       rethrow;
//     }
//   }
  
//   /// Déchiffrer une liste de messages
//   // Future<List<Message>> _decryptMessages(List<Message> messages) async {
//   //   final decrypted = <Message>[];
//   //   final currentUserId = _authService.currentUser.value?.userId;
    
//   //   for (final message in messages) {
//   //     try {
//   //       // Si c'est notre message, pas besoin de déchiffrer
//   //       if (message.senderId == currentUserId) {
//   //         decrypted.add(message);
//   //         continue;
//   //       }
        
//   //       // Déchiffrer le message
//   //       final content = await decryptMessage(message);
        
//   //       decrypted.add(message.copyWith(decryptedContent: content));
        
//   //     } catch (e) {
//   //       print('❌ Erreur déchiffrement message ${message.id}: $e');
//   //       // Ajouter quand même le message (chiffré)
//   //       decrypted.add(message);
//   //     }
//   //   }
    
//   //   return decrypted;
//   // }
  
//   // ═══════════════════════════════════════════════════════════════
//   // MARQUER COMME LU
//   // ═══════════════════════════════════════════════════════════════
  
//   /// Marquer les messages d'une conversation comme lus
//   Future<void> markConversationAsRead(String conversationId) async {
//     try {
//       // Envoyer via HTTP
//       await _dioClient.privateDio.post(
//         ApiEndpoints.markAsRead,
//         data: {'conversation_id': conversationId},
//       );
      
//       print('✅ Conversation marquée comme lue');
      
//     } catch (e) {
//       print('❌ Erreur markConversationAsRead: $e');
//     }
//   }
  
//   // ═══════════════════════════════════════════════════════════════
//   // CHIFFREMENT / DÉCHIFFREMENT
//   // ═══════════════════════════════════════════════════════════════
  
//   /// Chiffrer un message pour un destinataire
//   Future<Map<String, String>> encryptMessage(
//     String recipientUserId,
//     String plaintext,
//   ) async {
//     try {
//       print('🔐 Chiffrement message pour user: $recipientUserId');
      
//       // 1. Récupérer mes clés privées depuis SecureStorage
//       final myDhPrivate = await _secureStorage.getDHPrivateKey();
//       final mySignPrivate = await _secureStorage.getSignPrivateKey();
      
//       if (myDhPrivate == null || mySignPrivate == null) {
//         throw Exception('Clés privées manquantes');
//       }
      
//       // 2. Récupérer les clés publiques du destinataire
//       final recipientKeys = await _getRecipientPublicKeys(recipientUserId);
      
//       // 3. Chiffrer avec TON CryptoService
//       final encrypted = await _cryptoService.encryptMessage(
//         plaintext: plaintext,
//         myDhPrivateKeyB64: myDhPrivate,
//         theirDhPublicKeyB64: recipientKeys['dh_public_key']!,
//         mySignPrivateKeyB64: mySignPrivate,
//       );
      
//       print('✅ Message chiffré');
      
//       return encrypted;
      
//     } catch (e) {
//       print('❌ Erreur encryptMessage: $e');
//       rethrow;
//     }
//   }
  
//   /// Déchiffrer un message reçu
//   Future<String> decryptMessage(Message message) async {
//     try {
//       print('🔓 Déchiffrement message de user: ${message.senderId}');
      
//       // Vérifier que les champs E2EE existent
//       if (message.nonce == null || 
//           message.authTag == null || 
//           message.signature == null) {
//         throw Exception('Champs E2EE manquants');
//       }
      
//       // 1. Récupérer mes clés privées
//       final myDhPrivate = await _secureStorage.getDHPrivateKey();
//       final mySignPrivate = await _secureStorage.getSignPrivateKey();
      
//       if (myDhPrivate == null || mySignPrivate == null) {
//         throw Exception('Clés privées manquantes');
//       }
      
//       // 2. Récupérer les clés publiques de l'expéditeur
//       final senderKeys = await _getRecipientPublicKeys(message.senderId);
      
//       // 3. Déchiffrer avec TON CryptoService
//       final plaintext = await _cryptoService.decryptMessage(
//         ciphertextB64: message.encryptedContent,
//         nonceB64: message.nonce!,
//         authTagB64: message.authTag!,
//         signatureB64: message.signature!,
//         myDhPrivateKeyB64: myDhPrivate,
//         theirDhPublicKeyB64: senderKeys['dh_public_key']!,
//         theirSignPublicKeyB64: senderKeys['sign_public_key']!,
//       );
      
//       print('✅ Message déchiffré');
      
//       return plaintext;
      
//     } catch (e) {
//       print('❌ Erreur decryptMessage: $e');
//       rethrow;
//     }
//   }
  
//   /// Récupérer les clés publiques d'un utilisateur
//   Future<Map<String, String>> _getRecipientPublicKeys(String userId) async {
//     try {
//       final response = await _dioClient.privateDio.get(
//         ApiEndpoints.getPublicKeys(userId),
//       );
      
//       if (response.statusCode == 200) {
//         final data = response.data['data'] as Map<String, dynamic>;
//         return {
//           'dh_public_key': data['dh_public_key'] as String,
//           'sign_public_key': data['sign_public_key'] as String,
//         };
//       } else {
//         throw Exception('Erreur récupération clés: ${response.statusCode}');
//       }
      
//     } catch (e) {
//       print('❌ Erreur _getRecipientPublicKeys: $e');
//       rethrow;
//     }
//   }
  
//   // ═══════════════════════════════════════════════════════════════
//   // WEBSOCKET ACTIONS
//   // ═══════════════════════════════════════════════════════════════
  
//   /// Rejoindre une conversation (WebSocket)
//   void joinConversation(String conversationId) {
//     _wsService.joinConversation(conversationId);
//   }
  
//   /// Envoyer indicateur de saisie
//   void sendTypingIndicator(String conversationId, bool isTyping) {
//     _wsService.sendTyping(conversationId, isTyping);
//   }
// }

