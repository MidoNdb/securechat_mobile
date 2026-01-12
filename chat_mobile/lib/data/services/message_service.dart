// lib/data/services/message_service.dart

import 'package:get/get.dart' hide FormData, MultipartFile;
import 'package:dio/dio.dart';
import '../models/conversation.dart';
import '../models/message.dart';
import '../api/dio_client.dart';
import '../api/api_endpoints.dart';
import 'secure_storage_service.dart';
import 'crypto_service.dart';

class MessageService extends GetxService {
  late final DioClient _dioClient;
  late final SecureStorageService _storage;
  late final CryptoService _crypto;
  
  @override
  void onInit() {
    super.onInit();
    _dioClient = Get.find<DioClient>();
    _storage = Get.find<SecureStorageService>();
    _crypto = CryptoService();
  }

 Future<Map<String, dynamic>?> getCurrentUser() async {
    try {
      final response = await _dioClient.get('/api/auth/me/');
      
      if (response.statusCode == 200) {
        return response.data;
      }
      return null;
    } catch (e) {
      print('❌ getCurrentUser: $e');
      return null;
    }
  }
  // ==================== CONVERSATIONS ====================

  Future<List<Conversation>?> getConversations({int page = 1}) async {
    try {
      final response = await _dioClient.get(
        ApiEndpoints.conversations,
        queryParameters: {'page': page},
      );

      if (response.statusCode != 200) return null;

      final List<dynamic> data = _extractList(response.data);
      final conversations = <Conversation>[];

      for (var json in data) {
        final conv = Conversation.fromJson(json);
        
        if (conv.lastMessage?.encryptedContent != null) {
          try {
            final decrypted = await _decryptMessage(conv.lastMessage!);
            conversations.add(conv.copyWith(
              lastMessage: conv.lastMessage!.copyWith(content: decrypted),
            ));
          } catch (e) {
            conversations.add(conv.copyWith(
              lastMessage: conv.lastMessage!.copyWith(content: '🔒 Chiffré'),
            ));
          }
        } else {
          conversations.add(conv);
        }
      }

      return conversations;
    } catch (e) {
      print('❌ getConversations: $e');
      return null;
    }
  }

  // ✅ CRÉER CONVERSATION DIRECTE
  Future<Conversation?> createDirectConversation(String contactUserId) async {
    try {
      print('📤 Creating conversation with user: $contactUserId');
      
      final response = await _dioClient.post(
        ApiEndpoints.conversations,
        data: {
          'type': 'DIRECT',
          'participant_ids': [contactUserId],
        },
      );

      if (response.statusCode == 201 || response.statusCode == 200) {
        final data = response.data;
        
        if (data['success'] == true && data['data'] != null) {
          print('✅ Conversation created: ${data['data']['id']}');
          return Conversation.fromJson(data['data']);
        }
      }
      
      return null;
    } catch (e) {
      print('❌ createDirectConversation: $e');
      rethrow;
    }
  }

  // ==================== MESSAGES ====================
// lib/data/services/message_service.dart

Future<List<Message>?> getMessages(
  String conversationId,
  {int page = 1, int pageSize = 50}
) async {
  try {
    print('🔄 Loading messages for conversation: $conversationId');
    
    final response = await _dioClient.get(
      ApiEndpoints.getMessagesByConversation(conversationId),  // ✅ Correct
      queryParameters: {'page': page, 'page_size': pageSize},
    );

    if (response.statusCode != 200) return null;

    // ✅ Extraction depuis success response
    final data = response.data;
    final List<dynamic> messagesList = data['data'] ?? data['results'] ?? [];
    
    final messages = <Message>[];

    print('📥 Received ${messagesList.length} messages');

    for (var json in messagesList) {
      final message = Message.fromJson(json);
      
      if (message.encryptedContent != null) {
        try {
          final decrypted = await _decryptMessage(message);
          messages.add(message.copyWith(content: decrypted));
        } catch (e) {
          print('⚠️ Decrypt error for message ${message.id}: $e');
          messages.add(message.copyWith(content: '🔒 Erreur déchiffrement'));
        }
      } else {
        messages.add(message);
      }
    }

    print('✅ Loaded ${messages.length} messages');
    return messages;
  } catch (e) {
    print('❌ getMessages: $e');
    return null;
  }
}
  // ✅ Signature corrigée: String conversationId
  Future<Message?> sendMessage({
    required String conversationId,  // ✅ String UUID
    required String content,
    required String recipientUserId,
  }) async {
    try {
      print('📤 Sending message to conversation: $conversationId');
      
      final recipientKeys = await _getPublicKeys(recipientUserId);
      if (recipientKeys == null) {
        throw Exception('Clés destinataire introuvables');
      }

      final myDhPrivate = await _storage.getDHPrivateKey();
      final mySignPrivate = await _storage.getSignPrivateKey();

      if (myDhPrivate == null || mySignPrivate == null) {
        throw Exception('Clés privées manquantes');
      }

      print('🔐 Encrypting message...');
      final encrypted = await _crypto.encryptMessage(
        plaintext: content,
        myDhPrivateKeyB64: myDhPrivate,
        theirDhPublicKeyB64: recipientKeys['dh_public_key']!,
        mySignPrivateKeyB64: mySignPrivate,
      );

      final response = await _dioClient.post(
        ApiEndpoints.sendMessage,
        data: {
          'conversation_id': conversationId,  // ✅ String UUID
          'type': 'text',
          'ciphertext': encrypted['ciphertext'],
          'nonce': encrypted['nonce'],
          'auth_tag': encrypted['auth_tag'],
          'signature': encrypted['signature'],
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        print('✅ Message sent successfully');
        return Message.fromJson(response.data).copyWith(content: content);
      }
      
      return null;
    } catch (e) {
      print('❌ sendMessage: $e');
      return null;
    }
  }

  // ✅ Signature corrigée: String conversationId
  Future<bool> markAsRead(String conversationId) async {  // ✅ String UUID
    try {
      print('📖 Marking conversation as read: $conversationId');
      
      final response = await _dioClient.post(
        ApiEndpoints.markAsRead,
        data: {'conversation_id': conversationId},  // ✅ String UUID
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('❌ markAsRead: $e');
      return false;
    }
  }

  // ==================== HELPERS ====================

  Future<String> _decryptMessage(Message message) async {
    final senderKeys = await _getPublicKeys(message.senderId.toString());
    final myDhPrivate = await _storage.getDHPrivateKey();

    if (senderKeys == null || myDhPrivate == null) {
      throw Exception('Clés manquantes pour déchiffrement');
    }

    return await _crypto.decryptMessage(
      ciphertextB64: message.encryptedContent!['ciphertext'],
      nonceB64: message.encryptedContent!['nonce'],
      authTagB64: message.encryptedContent!['auth_tag'],
      signatureB64: message.encryptedContent!['signature'],
      myDhPrivateKeyB64: myDhPrivate,
      theirDhPublicKeyB64: senderKeys['dh_public_key']!,
      theirSignPublicKeyB64: senderKeys['sign_public_key']!,
    );
  }

  Future<Map<String, String>?> _getPublicKeys(String userId) async {
    try {
      final response = await _dioClient.get('/api/users/$userId/public-keys/');
      
      if (response.statusCode == 200) {
        final data = response.data;
        return {
          'dh_public_key': data['dh_public_key'],
          'sign_public_key': data['sign_public_key'],
        };
      }
      return null;
    } catch (e) {
      print('❌ _getPublicKeys: $e');
      return null;
    }
  }

  List<dynamic> _extractList(dynamic data) {
    if (data is Map) {
      return data['results'] ?? data['data'] ?? [];
    }
    if (data is List) {
      return data;
    }
    return [];
  }
}

// // lib/data/services/message_service.dart

// import 'package:get/get.dart' hide FormData, MultipartFile;
// import 'package:dio/dio.dart';
// import '../models/conversation.dart';
// import '../models/message.dart';
// import '../api/dio_client.dart';
// import '../api/api_endpoints.dart';
// import 'secure_storage_service.dart';
// import 'crypto_service.dart';

// class MessageService extends GetxService {
//   late final DioClient _dioClient;
//   late final SecureStorageService _storage;
//   late final CryptoService _crypto;
  
//   @override
//   void onInit() {
//     super.onInit();
//     _dioClient = Get.find<DioClient>();
//     _storage = Get.find<SecureStorageService>();
//     _crypto = CryptoService();
//   }

//   // ==================== CONVERSATIONS ====================

//   Future<List<Conversation>?> getConversations({int page = 1}) async {
//     try {
//       final response = await _dioClient.get(
//         ApiEndpoints.conversations,
//         queryParameters: {'page': page},
//       );

//       if (response.statusCode != 200) return null;

//       final List<dynamic> data = _extractList(response.data);
//       final conversations = <Conversation>[];

//       for (var json in data) {
//         final conv = Conversation.fromJson(json);
        
//         if (conv.lastMessage?.encryptedContent != null) {
//           try {
//             final decrypted = await _decryptMessage(conv.lastMessage!);
//             conversations.add(conv.copyWith(
//               lastMessage: conv.lastMessage!.copyWith(content: decrypted),
//             ));
//           } catch (e) {
//             conversations.add(conv.copyWith(
//               lastMessage: conv.lastMessage!.copyWith(content: '🔒 Chiffré'),
//             ));
//           }
//         } else {
//           conversations.add(conv);
//         }
//       }

//       return conversations;
//     } catch (e) {
//       print('❌ getConversations: $e');
//       return null;
//     }
//   }

//   // lib/data/services/message_service.dart

// // Ajouter cette méthode
// Future<Conversation?> createDirectConversation(String contactUserId) async {
//   try {
//     print('📤 Creating conversation with user: $contactUserId');
    
//     final response = await _dioClient.post(
//       ApiEndpoints.conversations,
//       data: {
//         'type': 'DIRECT',
//         'participant_ids': [contactUserId],  // ✅ UUID en liste
//       },
//     );

//     if (response.statusCode == 201 || response.statusCode == 200) {
//       final data = response.data;
      
//       if (data['success'] == true && data['data'] != null) {
//         print('✅ Conversation created: ${data['data']['id']}');
//         return Conversation.fromJson(data['data']);
//       }
//     }
    
//     return null;
//   } catch (e) {
//     print('❌ createDirectConversation: $e');
//     rethrow;
//   }
// }
//   // ==================== MESSAGES ====================

//   Future<List<Message>?> getMessages(
//     String conversationId, {
//     int page = 1,
//     int pageSize = 50,
//   }) async {
//     try {
//       final response = await _dioClient.get(
//         ApiEndpoints.getMessagesByConversation(conversationId),
//         queryParameters: {'page': page, 'page_size': pageSize},
//       );

//       if (response.statusCode != 200) return null;

//       final List<dynamic> data = _extractList(response.data);
//       final messages = <Message>[];

//       for (var json in data) {
//         final message = Message.fromJson(json);
        
//         if (message.encryptedContent != null) {
//           try {
//             final decrypted = await _decryptMessage(message);
//             messages.add(message.copyWith(content: decrypted));
//           } catch (e) {
//             messages.add(message.copyWith(content: '🔒 Erreur déchiffrement'));
//           }
//         } else {
//           messages.add(message);
//         }
//       }

//       return messages;
//     } catch (e) {
//       print('❌ getMessages: $e');
//       return null;
//     }
//   }

//   Future<Message?> sendMessage({
//     required int conversationId,
//     required String content,
//     required String recipientUserId,
//   }) async {
//     try {
//       final recipientKeys = await _getPublicKeys(recipientUserId);
//       if (recipientKeys == null) {
//         throw Exception('Clés destinataire introuvables');
//       }

//       final myDhPrivate = await _storage.getDHPrivateKey();
//       final mySignPrivate = await _storage.getSignPrivateKey();

//       if (myDhPrivate == null || mySignPrivate == null) {
//         throw Exception('Clés privées manquantes');
//       }

//       final encrypted = await _crypto.encryptMessage(
//         plaintext: content,
//         myDhPrivateKeyB64: myDhPrivate,
//         theirDhPublicKeyB64: recipientKeys['dh_public_key']!,
//         mySignPrivateKeyB64: mySignPrivate,
//       );

//       final response = await _dioClient.post(
//         ApiEndpoints.sendMessage,
//         data: {
//           'conversation_id': conversationId,
//           'type': 'text',
//           'ciphertext': encrypted['ciphertext'],
//           'nonce': encrypted['nonce'],
//           'auth_tag': encrypted['auth_tag'],
//           'signature': encrypted['signature'],
//         },
//       );

//       if (response.statusCode == 200 || response.statusCode == 201) {
//         return Message.fromJson(response.data).copyWith(content: content);
//       }
//       return null;
//     } catch (e) {
//       print('❌ sendMessage: $e');
//       return null;
//     }
//   }

//   Future<bool> markAsRead(int conversationId) async {
//     try {
//       final response = await _dioClient.post(
//         ApiEndpoints.markAsRead,
//         data: {'conversation_id': conversationId},
//       );
//       return response.statusCode == 200;
//     } catch (e) {
//       return false;
//     }
//   }

//   // ==================== HELPERS ====================

//   Future<String> _decryptMessage(Message message) async {
//     final senderKeys = await _getPublicKeys(message.senderId.toString());
//     final myDhPrivate = await _storage.getDHPrivateKey();

//     if (senderKeys == null || myDhPrivate == null) {
//       throw Exception('Clés manquantes pour déchiffrement');
//     }

//     return await _crypto.decryptMessage(
//       ciphertextB64: message.encryptedContent!['ciphertext'],
//       nonceB64: message.encryptedContent!['nonce'],
//       authTagB64: message.encryptedContent!['auth_tag'],
//       signatureB64: message.encryptedContent!['signature'],
//       myDhPrivateKeyB64: myDhPrivate,
//       theirDhPublicKeyB64: senderKeys['dh_public_key']!,
//       theirSignPublicKeyB64: senderKeys['sign_public_key']!,
//     );
//   }

//   Future<Map<String, String>?> _getPublicKeys(String userId) async {
//     try {
//       final response = await _dioClient.get('/api/users/$userId/public-keys/');
      
//       if (response.statusCode == 200) {
//         final data = response.data;
//         return {
//           'dh_public_key': data['dh_public_key'],
//           'sign_public_key': data['sign_public_key'],
//         };
//       }
//       return null;
//     } catch (e) {
//       print('❌ _getPublicKeys: $e');
//       return null;
//     }
//   }

//   List<dynamic> _extractList(dynamic data) {
//     if (data is Map) {
//       return data['results'] ?? data['data'] ?? [];
//     }
//     if (data is List) {
//       return data;
//     }
//     return [];
//   }
// }















// // // lib/data/services/message_service.dart
// // import 'dart:convert';
// // import 'package:flutter/material.dart';
// // import 'package:get/get.dart' hide FormData, MultipartFile;
// // import 'package:dio/dio.dart';
// // import 'package:cryptography/cryptography.dart';
// // import '../models/conversation.dart';
// // import '../models/message.dart';
// // import '../api/dio_client.dart';
// // import '../api/api_endpoints.dart';
// // import 'secure_storage_service.dart';
// // import '../../core/shared/environment.dart';

// // class MessageService extends GetxService {
// //   late final DioClient _dioClient;
// //   late final SecureStorageService _storage;

// //   final _x25519 = X25519();
// //   final _ed25519 = Ed25519();
// //   final _aesGcm = AesGcm.with256bits();
// //   final _sha256 = Sha256();

// //   @override
// //   void onInit() {
// //     super.onInit();
// //     _dioClient = Get.find<DioClient>();
// //     _storage = Get.find<SecureStorageService>();
// //   }

// //   // ========================================
// //   // CONVERSATIONS
// //   // ========================================

// //   Future<List<Conversation>?> getConversations({int page = 1}) async {
// //     try {
// //       final response = await _dioClient.get(
// //         ApiEndpoints.conversations,
// //         queryParameters: {'page': page},
// //       );
// //       if (response.statusCode == 200) {
// //         final dynamic rawData = response.data;
// //         List<dynamic> listData;
// //         if (rawData is Map) {
// //           listData = rawData['results'] ?? rawData['data'] ?? [];
// //         } else if (rawData is List) {
// //           listData = rawData;
// //         } else {
// //           listData = [];
// //         }
// //         return listData.map((json) => Conversation.fromJson(json)).toList();
// //       }
// //       return null;
// //     } catch (e) {
// //       if (AppEnvironment.enableLogs) print('❌ getConversations: $e');
// //       return null;
// //     }
// //   }

// //   /// ✅ Crée une conversation DIRECTE
// //   Future<Conversation?> createDirectConversation(int contactUserId) async {
// //     try {
// //       final response = await _dioClient.post(
// //         ApiEndpoints.createConversation,
// //         data: {
// //           'contact_user_id': contactUserId,
// //           'is_group': false,
// //         },
// //       );
// //       if (response.statusCode == 201 || response.statusCode == 200) {
// //         return Conversation.fromJson(response.data);
// //       }
// //       return null;
// //     } on DioException catch (e) {
// //       if (e.response?.statusCode == 400 || e.response?.statusCode == 404) {
// //         Get.snackbar(
// //           "❌ Indisponible",
// //           "Cet utilisateur n'a pas encore activé son compte de messagerie sécurisée.",
// //           snackPosition: SnackPosition.BOTTOM,
// //           backgroundColor: Colors.orange,
// //           colorText: Colors.white,
// //         );
// //       }
// //       return null;
// //     } catch (e) {
// //       return null;
// //     }
// //   }

// //   // ========================================
// //   // MESSAGES + CHIFFREMENT E2E
// //   // ========================================

// //   /// ✅ ENVOIE UN MESSAGE CHIFFRÉ
// //   Future<Message?> sendMessage({
// //     required int conversationId,
// //     required String content,
// //     required String recipientUserId,
// //   }) async {
// //     try {
// //       final recipientKeys = await _getPublicKeys(recipientUserId);
// //       if (recipientKeys == null) {
// //         Get.snackbar(
// //           "❌ Erreur",
// //           "Clés publiques du destinataire introuvables",
// //           snackPosition: SnackPosition.BOTTOM,
// //         );
// //         return null;
// //       }
      
// //       final encrypted = await _encryptMessage(
// //         content, 
// //         recipientKeys['dh_public_key']!
// //       );
      
// //       // ✅ CORRECTION: Indentation correcte
// //       final response = await _dioClient.post(
// //         ApiEndpoints.sendMessage,
// //         data: {
// //           'conversation_id': conversationId,
// //           'type': 'text',
// //           'ciphertext': encrypted['ciphertext'],
// //           'nonce': encrypted['nonce'],
// //           'auth_tag': encrypted['auth_tag'],
// //           'signature': encrypted['signature'],
// //         },
// //       );

// //       if (response.statusCode == 201 || response.statusCode == 200) {
// //         return Message.fromJson(response.data).copyWith(content: content);
// //       }
// //       return null;
// //     } catch (e) {
// //       if (AppEnvironment.enableLogs) print('❌ sendMessage: $e');
// //       Get.snackbar(
// //         "❌ Échec",
// //         "Impossible d'envoyer le message",
// //         snackPosition: SnackPosition.BOTTOM,
// //       );
// //       return null;
// //     }
// //   }

// //   Future<List<Message>?> getMessages(
// //     int conversationId, {
// //     int page = 1,
// //     int pageSize = 50,
// //   }) async {
// //     try {
// //       final response = await _dioClient.get(
// //         ApiEndpoints.getMessagesByConversation(conversationId),
// //         queryParameters: {'page': page, 'page_size': pageSize},
// //       );
      
// //       if (response.statusCode == 200) {
// //         // ✅ CORRECTION: Meilleure gestion de la réponse
// //         final dynamic rawData = response.data;
// //         final List<dynamic> data = rawData is Map 
// //             ? (rawData['results'] ?? rawData['data'] ?? [])
// //             : (rawData is List ? rawData : []);
        
// //         final decryptedMessages = <Message>[];
// //         for (var json in data) {
// //           try {
// //             final message = Message.fromJson(json);
// //             if (message.encryptedContent != null) {
// //               final decryptedContent = await _decryptMessage(message);
// //               decryptedMessages.add(message.copyWith(content: decryptedContent));
// //             } else {
// //               decryptedMessages.add(message);
// //             }
// //           } catch (e) {
// //             decryptedMessages.add(
// //               Message.fromJson(json).copyWith(
// //                 content: '🔒 Impossible de déchiffrer'
// //               ),
// //             );
// //           }
// //         }
// //         return decryptedMessages;
// //       }
// //       return null;
// //     } catch (e) {
// //       if (AppEnvironment.enableLogs) print('❌ getMessages: $e');
// //       return null;
// //     }
// //   }

// //   // ========================================
// //   // CRYPTOGRAPHIE (INTERNE)
// //   // ========================================

// //   Future<Map<String, String>> _encryptMessage(
// //     String plaintext, 
// //     String recipientDhPubKeyB64
// //   ) async {
// //     final myDhPrivKeyB64 = await _storage.getDHPrivateKey();
// //     final mySignPrivKeyB64 = await _storage.getSignPrivateKey();
    
// //     if (myDhPrivKeyB64 == null || mySignPrivKeyB64 == null) {
// //       throw Exception('Clés privées manquantes dans le stockage sécurisé');
// //     }

// //     final sharedSecret = await _x25519.sharedSecretKey(
// //       keyPair: SimpleKeyPairData(
// //         base64Decode(myDhPrivKeyB64),
// //         publicKey: SimplePublicKey([], type: KeyPairType.x25519),
// //         type: KeyPairType.x25519,
// //       ),
// //       remotePublicKey: SimplePublicKey(
// //         base64Decode(recipientDhPubKeyB64),
// //         type: KeyPairType.x25519,
// //       ),
// //     );

// //     final hkdf = Hkdf(hmac: Hmac(_sha256), outputLength: 32);
// //     final aesKey = await hkdf.deriveKey(
// //       secretKey: sharedSecret,
// //       nonce: utf8.encode('SecureChat-v1'),
// //       info: utf8.encode('message-encryption'),
// //     );

// //     final secretBox = await _aesGcm.encrypt(
// //       utf8.encode(plaintext), 
// //       secretKey: aesKey
// //     );
    
// //     final ciphertextHash = await _sha256.hash(secretBox.cipherText);

// //     final signature = await _ed25519.sign(
// //       ciphertextHash.bytes,
// //       keyPair: SimpleKeyPairData(
// //         base64Decode(mySignPrivKeyB64),
// //         publicKey: SimplePublicKey([], type: KeyPairType.ed25519),
// //         type: KeyPairType.ed25519,
// //       ),
// //     );

// //     return {
// //       'ciphertext': base64Encode(secretBox.cipherText),
// //       'nonce': base64Encode(secretBox.nonce),
// //       'auth_tag': base64Encode(secretBox.mac.bytes),
// //       'signature': base64Encode(signature.bytes),
// //     };
// //   }

// //   Future<String> _decryptMessage(Message message) async {
// //     final senderKeys = await _getPublicKeys(message.senderId.toString());
// //     final myDhPrivKeyB64 = await _storage.getDHPrivateKey();
    
// //     if (senderKeys == null || myDhPrivKeyB64 == null) {
// //       throw Exception('Impossible de déchiffrer: clés manquantes');
// //     }

// //     final sharedSecret = await _x25519.sharedSecretKey(
// //       keyPair: SimpleKeyPairData(
// //         base64Decode(myDhPrivKeyB64),
// //         publicKey: SimplePublicKey([], type: KeyPairType.x25519),
// //         type: KeyPairType.x25519,
// //       ),
// //       remotePublicKey: SimplePublicKey(
// //         base64Decode(senderKeys['dh_public_key']!),
// //         type: KeyPairType.x25519,
// //       ),
// //     );

// //     final hkdf = Hkdf(hmac: Hmac(_sha256), outputLength: 32);
// //     final aesKey = await hkdf.deriveKey(
// //       secretKey: sharedSecret,
// //       nonce: utf8.encode('SecureChat-v1'),
// //       info: utf8.encode('message-encryption'),
// //     );

// //     final secretBox = SecretBox(
// //       base64Decode(message.encryptedContent!['ciphertext']),
// //       nonce: base64Decode(message.encryptedContent!['nonce']),
// //       mac: Mac(base64Decode(message.encryptedContent!['auth_tag'])),
// //     );

// //     final decrypted = await _aesGcm.decrypt(secretBox, secretKey: aesKey);
// //     return utf8.decode(decrypted);
// //   }

// //   Future<Map<String, String>?> _getPublicKeys(String userId) async {
// //     try {
// //       final response = await _dioClient.get('/api/users/$userId/public-keys/');
// //       if (response.statusCode == 200) {
// //         return {
// //           'dh_public_key': response.data['dh_public_key'],
// //           'sign_public_key': response.data['sign_public_key'],
// //         };
// //       }
// //       return null;
// //     } catch (e) {
// //       if (AppEnvironment.enableLogs) print('❌ _getPublicKeys: $e');
// //       return null;
// //     }
// //   }

// //   // ========================================
// //   // ACTIONS COMPLÉMENTAIRES
// //   // ========================================

// //   Future<bool> markAsRead(int conversationId) async {
// //     try {
// //       final response = await _dioClient.post(
// //         ApiEndpoints.markAsRead,
// //         data: {'conversation_id': conversationId},
// //       );
// //       return response.statusCode == 200;
// //     } catch (e) {
// //       return false;
// //     }
// //   }
// // }