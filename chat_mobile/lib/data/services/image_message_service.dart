// lib/data/services/image_message_service.dart
// ✅ VERSION FINALE - Logs minimaux uniquement pour erreurs critiques

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:get/get.dart';
import '../models/message.dart';
import 'crypto_service.dart';
import 'file_service.dart';
import 'secure_storage_service.dart';
import '../api/dio_client.dart';
import '../api/api_endpoints.dart';

class ImageMessageService extends GetxService {
  final CryptoService _crypto = Get.find<CryptoService>();
  final FileService _fileService = Get.find<FileService>();
  final SecureStorageService _storage = Get.find<SecureStorageService>();
  final DioClient _dio = Get.find<DioClient>();
  
  // ==================== ENVOI IMAGE ====================
  
  Future<Message> sendImage({
    required String conversationId,
    required String recipientUserId,
    required File imageFile,
  }) async {
    try {
      // 1. Compression
      final compressedBytes = await _fileService.compressImage(
        imageFile,
        maxSizeKB: 500,
        quality: 85,
      );
      
      // 2. Métadonnées
      final metadata = await _extractImageMetadata(imageFile, compressedBytes);
      
      // 3. Récupérer clés E2EE
      final myDhPrivateKey = await _storage.getDHPrivateKey();
      final mySignPrivateKey = await _storage.getSignPrivateKey();
      
      if (myDhPrivateKey == null || mySignPrivateKey == null) {
        throw Exception('Clés E2EE manquantes');
      }
      
      // 4. Récupérer clés publiques destinataire
      final recipientKeys = await _getRecipientPublicKeys(recipientUserId);
      
      // 5. Convertir en Base64
      final base64Image = base64Encode(compressedBytes);
      
      // 6. Chiffrement
      final encrypted = await _crypto.encryptMessage(
        plaintext: base64Image,
        myDhPrivateKeyB64: myDhPrivateKey,
        theirDhPublicKeyB64: recipientKeys['dh_public_key']!,
        mySignPrivateKeyB64: mySignPrivateKey,
      );
      
      // 7. Préparation requête
      final payload = {
        'conversation_id': conversationId,
        'recipient_user_id': recipientUserId,
        'type': 'IMAGE',
        'encrypted_content': encrypted['ciphertext']!,
        'nonce': encrypted['nonce']!,
        'auth_tag': encrypted['auth_tag']!,
        'signature': encrypted['signature']!,
        'metadata': metadata,
      };
      
      // 8. Envoi HTTP
      final response = await _dio.privateDio.post(
        ApiEndpoints.sendMessage,
        data: payload,
      );
      
      // 9. Extraction message
      final messageData = response.data['data'] as Map<String, dynamic>;
      final message = Message.fromJson(messageData);
      
      // 10. Sauvegarder en cache
      await _fileService.saveToCacheDir(
        compressedBytes,
        message.id,
        extension: 'jpg',
      );
      
      return message;
      
    } catch (e) {
      print('❌ Erreur sendImage: $e');
      rethrow;
    }
  }
  
  // ==================== RÉCEPTION IMAGE ====================
  
  Future<File> decryptImage(Message message) async {
    try {
      // 1. Vérifier cache
      final cachedFile = await _fileService.getFromCache(message.id);
      if (cachedFile != null) {
        return cachedFile;
      }
      
      // 2. Récupérer clés E2EE
      final myDhPrivateKey = await _storage.getDHPrivateKey();
      
      if (myDhPrivateKey == null) {
        throw Exception('Clé DH manquante');
      }
      
      // 3. Récupérer clés publiques expéditeur
      final senderKeys = await _getRecipientPublicKeys(message.senderId);
      
      // 4. Déchiffrement
      final decryptedBase64 = await _crypto.decryptMessage(
        ciphertextB64: message.encryptedContent,
        nonceB64: message.nonce!,
        authTagB64: message.authTag!,
        signatureB64: message.signature!,
        myDhPrivateKeyB64: myDhPrivateKey,
        theirDhPublicKeyB64: senderKeys['dh_public_key']!,
        theirSignPublicKeyB64: senderKeys['sign_public_key']!,
      );
      
      // 5. Décoder Base64
      final imageBytes = base64Decode(decryptedBase64);
      
      // 6. Sauvegarder en cache
      final file = await _fileService.saveToCacheDir(
        Uint8List.fromList(imageBytes),
        message.id,
        extension: 'jpg',
      );
      
      return file;
      
    } catch (e) {
      print('❌ Erreur decryptImage: $e');
      rethrow;
    }
  }
  
  // ==================== MÉTADONNÉES ====================
  
  Future<Map<String, dynamic>> _extractImageMetadata(
    File imageFile,
    Uint8List compressedBytes,
  ) async {
    try {
      final codec = await ui.instantiateImageCodec(compressedBytes);
      final frame = await codec.getNextFrame();
      final image = frame.image;
      
      return {
        'width': image.width,
        'height': image.height,
        'size': compressedBytes.length,
        'format': 'jpg',
        'original_name': imageFile.path.split('/').last,
      };
      
    } catch (e) {
      return {
        'size': compressedBytes.length,
        'format': 'jpg',
      };
    }
  }
  
  // ==================== RÉCUPÉRATION CLÉS ====================
  
  Future<Map<String, String>> _getRecipientPublicKeys(String userId) async {
    try {
      final response = await _dio.privateDio.get(
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
      print('❌ Erreur récupération clés: $e');
      rethrow;
    }
  }
  
  // ==================== UTILITAIRES ====================
  
  Future<bool> isImageCached(String messageId) async {
    return await _fileService.existsInCache(messageId);
  }
  
  Future<void> deleteImageFromCache(String messageId) async {
    await _fileService.deleteFromCache(messageId);
  }
}