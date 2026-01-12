// lib/data/services/auth_service.dart

import 'package:uuid/uuid.dart';
import 'package:get/get.dart';
import 'secure_storage_service.dart';
import 'crypto_service.dart';
import '../models/auth_data.dart';
import '../models/user.dart';
import '../api/dio_client.dart';
import '../api/api_endpoints.dart';

class AuthService extends GetxService {
  late final SecureStorageService _storage;
  late final DioClient _dio;
  late final CryptoService _crypto;

  final RxBool isLoading = false.obs;
  final Rx<User?> currentUser = Rx<User?>(null);
  final RxString errorMessage = ''.obs;

  @override
  void onInit() {
    super.onInit();
    _storage = Get.find<SecureStorageService>();
    _dio = Get.find<DioClient>();
    _crypto = CryptoService();
  }

  // ==================== REGISTER ====================
  Future<void> register({
    required String phoneNumber,
    required String password,
    required String username,
    String? email,
  }) async {
    try {
      isLoading.value = true;
      errorMessage.value = '';
      
      print('🚀 Inscription...');
      
      // 1. Device ID
      String? deviceId = await _storage.getDeviceId();
      if (deviceId == null) {
        deviceId = const Uuid().v4();
        await _storage.saveDeviceId(deviceId);
      }

      // 2. Génération clés via CryptoService
      print('🔐 Génération clés...');
      final keys = await _crypto.generateAllKeys();

      // 3. Hash password
      final hashedPassword = _crypto.hashString(password);

      // 4. Appel API
      print('📡 Envoi au serveur...');
      final response = await _dio.postPublic(
        ApiEndpoints.register,
        data: {
          'phone_number': phoneNumber,
          'password': hashedPassword,
          'display_name': username,
          'dh_public_key': keys['dh_public_key']!,
          'sign_public_key': keys['sign_public_key']!,
          'device_id': deviceId,
          'device_name': await _getDeviceName(),
          'device_type': _getDeviceType(),
          if (email != null && email.isNotEmpty) 'email': email,
        },
      );

      // 5. Traitement réponse
      if (response.data['success'] == true) {
        final data = response.data['data'];
        
        final authData = AuthData(
          accessToken: data['tokens']['access'],
          refreshToken: data['tokens']['refresh'],
          userId: data['user']['user_id'],
          deviceId: deviceId,
          dhPrivateKey: keys['dh_private_key']!,
          signPrivateKey: keys['sign_private_key']!,
        );

        currentUser.value = User.fromJson(data['user']);
        await _storage.saveAuthData(authData);
        
        print('✅ Inscription réussie');
      } else {
        throw Exception(response.data['error']['message'] ?? 'Erreur inconnue');
      }

    } catch (e) {
      print('❌ Erreur: $e');
      errorMessage.value = e.toString();
      rethrow;
    } finally {
      isLoading.value = false;
    }
  }

  // ==================== LOGIN ====================
  Future<Map<String, dynamic>> login({
    required String phoneNumber,
    required String password,
    String? newDhPublicKey,
    String? newSignPublicKey,
    bool confirmedKeyRegeneration = false,
  }) async {
    try {
      isLoading.value = true;
      errorMessage.value = '';
      
      print('🔑 Connexion...');
      
      String? deviceId = await _storage.getDeviceId();
      if (deviceId == null) {
        deviceId = const Uuid().v4();
        await _storage.saveDeviceId(deviceId);
      }

      final hashedPassword = _crypto.hashString(password);

      final response = await _dio.postPublic(
        ApiEndpoints.login,
        data: {
          'phone_number': phoneNumber,
          'password': hashedPassword,
          'device_id': deviceId,
          'device_name': await _getDeviceName(),
          'device_type': _getDeviceType(),
          if (newDhPublicKey != null) 'new_dh_public_key': newDhPublicKey,
          if (newSignPublicKey != null) 'new_sign_public_key': newSignPublicKey,
          'confirmed_key_regeneration': confirmedKeyRegeneration,
        },
      );

      if (response.data['requires_key_regeneration'] == true) {
        print('⚠️ Nouveau device - Régénération requise');
        return {
          'requires_key_regeneration': true,
          'message': response.data['message'],
          'warning': response.data['warning'],
          'old_device': response.data['old_device'],
        };
      }

      if (response.data['success'] == true) {
        final data = response.data['data'];
        
        await _storage.saveTokens(
          data['tokens']['access'],
          data['tokens']['refresh'],
        );
        await _storage.saveDeviceId(deviceId);
        
        currentUser.value = User.fromJson(data['user']);
        await _storage.saveUserId(currentUser.value!.userId);
        
        final keysRegenerated = data['keys_regenerated'] ?? false;
        
        if (!keysRegenerated) {
          final hasDhKey = await _storage.hasDHPrivateKey();
          final hasSignKey = await _storage.hasSignPrivateKey();
          
          if (!hasDhKey || !hasSignKey) {
            print('⚠️ Clés locales manquantes');
            return {
              'requires_key_regeneration': true,
              'message': 'Clés privées manquantes',
              'warning': 'Régénération requise',
            };
          }
        }
        
        print('✅ Connexion réussie');
        return {
          'success': true,
          'keys_regenerated': keysRegenerated,
        };
      } else {
        throw Exception(response.data['error']['message'] ?? 'Erreur inconnue');
      }

    } catch (e) {
      print('❌ Erreur: $e');
      errorMessage.value = e.toString();
      rethrow;
    } finally {
      isLoading.value = false;
    }
  }

  // ==================== RÉGÉNÉRER CLÉS ====================
  Future<Map<String, String>> regenerateKeys() async {
    print('🔄 Régénération clés...');
    final keys = await _crypto.generateAllKeys();
    
    await _storage.saveDHPrivateKey(keys['dh_private_key']!);
    await _storage.saveSignPrivateKey(keys['sign_private_key']!);
    
    return {
      'dh_public_key': keys['dh_public_key']!,
      'sign_public_key': keys['sign_public_key']!,
    };
  }

  // ==================== LOGOUT ====================
  Future<void> logout() async {
    try {
      final accessToken = await _storage.getAccessToken();
      
      if (accessToken != null) {
        try {
          await _dio.post(ApiEndpoints.logout);
        } catch (e) {
          print('⚠️ Erreur logout API: $e');
        }
      }
    } catch (e) {
      print('⚠️ Erreur logout: $e');
    } finally {
      await _storage.clearAuth();
      currentUser.value = null;
      print('✅ Déconnecté');
    }
  }

  // ==================== GET CURRENT USER ====================
  Future<User?> getCurrentUser() async {
    try {
      final response = await _dio.get(ApiEndpoints.me);
      
      if (response.data['success'] == true) {
        currentUser.value = User.fromJson(response.data['data']);
        return currentUser.value;
      }
      
      return null;
    } catch (e) {
      print('❌ Erreur getCurrentUser: $e');
      return null;
    }
  }

  // ==================== HELPERS ====================

  Future<bool> isAuthenticated() async {
    return await _storage.isAuthenticated();
  }

  Future<bool> hasPrivateKeys() async {
    return await _storage.hasPrivateKeys();
  }

  Future<String?> getAccessToken() async {
    return await _storage.getAccessToken();
  }

  Future<String?> getUserId() async {
    return await _storage.getUserId();
  }

  Future<String> _getDeviceName() async {
    return 'Flutter Device';
  }

  String _getDeviceType() {
    return 'android';
  }
}













// // lib/data/services/auth_service.dart
// import 'dart:convert';
// import 'package:crypto/crypto.dart';
// import 'package:uuid/uuid.dart';
// import 'package:get/get.dart';
// import 'package:flutter/material.dart';
// import 'package:cryptography/cryptography.dart';
// import 'package:device_info_plus/device_info_plus.dart';
// import 'dart:io';
// import 'secure_storage_service.dart';
// import '../models/auth_data.dart';
// import '../models/user.dart';
// import '../api/dio_client.dart';
// import '../api/api_endpoints.dart';

// class AuthService extends GetxService {
//   late final SecureStorageService _storage;
//   late final DioClient _dio;

//   final RxBool isLoading = false.obs;
//   final Rx<User?> currentUser = Rx<User?>(null);
//   final RxString errorMessage = ''.obs;

//   // Algorithmes crypto modernes
//   final _x25519 = X25519();
//   final _ed25519 = Ed25519();

//   @override
//   void onInit() {
//     super.onInit();
//     _storage = Get.find<SecureStorageService>();
//     _dio = Get.find<DioClient>();
//   }

//   // ==================== REGISTER ====================
//   Future<void> register({
//     required String phoneNumber,
//     required String password,
//     required String username,
//     String? email,
//   }) async {
//     try {
//       isLoading.value = true;
//       errorMessage.value = '';
//       print('🚀 Inscription en cours...');

//       // 1. Device ID
//       String? deviceId = await _storage.getDeviceId();
//       if (deviceId == null) {
//         deviceId = const Uuid().v4();
//         await _storage.saveDeviceId(deviceId);
//       }

//       // 2. Génération des clés cryptographiques
//       print('🔐 Génération des clés X25519 + Ed25519...');
//       final keys = await _generateDHAndSignKeys();

//       // 3. Hash du mot de passe
//       final hashedPassword = _hashPassword(password);

//       // 4. Récupération des infos device
//       final deviceName = await _getDeviceName();
//       final deviceType = await _getDeviceType();

//       // 5. Appel API
//       print('📡 Envoi des données au serveur...');
//       final response = await _dio.postPublic(
//         ApiEndpoints.register,
//         data: {
//           'phone_number': phoneNumber,
//           'password': hashedPassword,
//           'display_name': username,
//           'dh_public_key': keys['dh_public_key']!,
//           'sign_public_key': keys['sign_public_key']!,
//           'device_id': deviceId,
//           'device_name': deviceName,
//           'device_type': deviceType,
//           if (email != null && email.isNotEmpty) 'email': email,
//         },
//       );

//       // 6. Traitement de la réponse
//       if (response.data['success'] == true) {
//         final data = response.data['data'];
        
//         // Sauvegarde des données d'authentification
//         final authData = AuthData(
//           accessToken: data['tokens']['access'],
//           refreshToken: data['tokens']['refresh'],
//           userId: data['user']['user_id'],
//           deviceId: deviceId,
//           dhPrivateKey: keys['dh_private_key']!,
//           signPrivateKey: keys['sign_private_key']!,
//         );
        
//         currentUser.value = User.fromJson(data['user']);
//         await _storage.saveAuthData(authData);
        
//         print('✅ Inscription réussie !');
        
//         Get.snackbar(
//           '✅ Succès',
//           'Inscription réussie ! Bienvenue ${username}',
//           snackPosition: SnackPosition.BOTTOM,
//           backgroundColor: Colors.green,
//           colorText: Colors.white,
//         );
//       } else {
//         throw Exception(response.data['error']?['message'] ?? 'Erreur inconnue');
//       }
//     } catch (e) {
//       print('❌ Erreur inscription: $e');
//       errorMessage.value = _formatErrorMessage(e);
      
//       Get.snackbar(
//         '❌ Erreur',
//         errorMessage.value,
//         snackPosition: SnackPosition.BOTTOM,
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
      
//       rethrow;
//     } finally {
//       isLoading.value = false;
//     }
//   }

//   // ==================== LOGIN ====================
//   Future<Map<String, dynamic>> login({
//     required String phoneNumber,
//     required String password,
//     String? newDhPublicKey,
//     String? newSignPublicKey,
//     bool confirmedKeyRegeneration = false,
//   }) async {
//     try {
//       isLoading.value = true;
//       errorMessage.value = '';
//       print('🔑 Connexion en cours...');

//       // 1. Device ID
//       String? deviceId = await _storage.getDeviceId();
//       if (deviceId == null) {
//         deviceId = const Uuid().v4();
//         await _storage.saveDeviceId(deviceId);
//       }

//       // 2. Hash du mot de passe
//       final hashedPassword = _hashPassword(password);

//       // 3. Récupération des infos device
//       final deviceName = await _getDeviceName();
//       final deviceType = await _getDeviceType();

//       // 4. Appel API
//       print('📡 Authentification...');
//       final response = await _dio.postPublic(
//         ApiEndpoints.login,
//         data: {
//           'phone_number': phoneNumber,
//           'password': hashedPassword,
//           'device_id': deviceId,
//           'device_name': deviceName,
//           'device_type': deviceType,
//           if (newDhPublicKey != null) 'new_dh_public_key': newDhPublicKey,
//           if (newSignPublicKey != null) 'new_sign_public_key': newSignPublicKey,
//           'confirmed_key_regeneration': confirmedKeyRegeneration,
//         },
//       );

//       // 5. Vérifier si régénération de clés requise
//       if (response.data['requires_key_regeneration'] == true) {
//         print('⚠️ Nouveau device détecté - Régénération de clés requise');
//         return {
//           'requires_key_regeneration': true,
//           'message': response.data['message'],
//           'warning': response.data['warning'],
//           'old_device': response.data['old_device'],
//         };
//       }

//       // 6. Traitement réponse succès
//       if (response.data['success'] == true) {
//         final data = response.data['data'];
        
//         // Sauvegarde des tokens
//         await _storage.saveTokens(
//           data['tokens']['access'],
//           data['tokens']['refresh'],
//         );
//         await _storage.saveDeviceId(deviceId);
        
//         currentUser.value = User.fromJson(data['user']);
//         await _storage.saveUserId(currentUser.value!.userId);

//         // Vérifier si les clés ont été régénérées
//         final keysRegenerated = data['keys_regenerated'] ?? false;
        
//         if (!keysRegenerated) {
//           // Vérifier si les clés privées locales existent
//           final hasDhKey = await _storage.hasDHPrivateKey();
//           final hasSignKey = await _storage.hasSignPrivateKey();
          
//           if (!hasDhKey || !hasSignKey) {
//             print('⚠️ Clés privées locales manquantes');
//             return {
//               'requires_key_regeneration': true,
//               'message': 'Clés privées manquantes',
//               'warning': 'Vous devez régénérer vos clés pour continuer',
//             };
//           }
//         }
        
//         print('✅ Connexion réussie !');
        
//         Get.snackbar(
//           '✅ Connecté',
//           'Bienvenue ${currentUser.value?.displayName ?? ""}',
//           snackPosition: SnackPosition.BOTTOM,
//           backgroundColor: Colors.green,
//           colorText: Colors.white,
//         );
        
//         return {
//           'success': true,
//           'keys_regenerated': keysRegenerated,
//         };
//       } else {
//         throw Exception(response.data['error']?['message'] ?? 'Erreur inconnue');
//       }
//     } catch (e) {
//       print('❌ Erreur connexion: $e');
//       errorMessage.value = _formatErrorMessage(e);
      
//       Get.snackbar(
//         '❌ Erreur',
//         errorMessage.value,
//         snackPosition: SnackPosition.BOTTOM,
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
      
//       rethrow;
//     } finally {
//       isLoading.value = false;
//     }
//   }

//   // ==================== RÉGÉNÉRER CLÉS ====================
//   Future<Map<String, String>> regenerateKeys() async {
//     print('🔄 Régénération des clés cryptographiques...');
//     final keys = await _generateDHAndSignKeys();
    
//     // Sauvegarde locale des clés privées
//     await _storage.saveDHPrivateKey(keys['dh_private_key']!);
//     await _storage.saveSignPrivateKey(keys['sign_private_key']!);
    
//     print('✅ Clés régénérées avec succès');
    
//     return {
//       'dh_public_key': keys['dh_public_key']!,
//       'sign_public_key': keys['sign_public_key']!,
//     };
//   }

//   // ==================== LOGOUT ====================
//   Future<void> logout() async {
//     try {
//       isLoading.value = true;
      
//       final accessToken = await _storage.getAccessToken();
//       if (accessToken != null) {
//         try {
//           await _dio.post(ApiEndpoints.logout, data: {});
//           print('✅ Logout API réussi');
//         } catch (e) {
//           print('⚠️ Erreur logout API: $e');
//         }
//       }
//     } catch (e) {
//       print('⚠️ Erreur logout: $e');
//     } finally {
//       await _storage.clearAuth();
//       currentUser.value = null;
//       isLoading.value = false;
      
//       print('✅ Déconnecté localement');
      
//       Get.snackbar(
//         '👋 À bientôt',
//         'Vous avez été déconnecté',
//         snackPosition: SnackPosition.BOTTOM,
//       );
//     }
//   }

//   // ==================== GET CURRENT USER ====================
//   Future<User?> getCurrentUser() async {
//     try {
//       final response = await _dio.get(ApiEndpoints.me);
      
//       if (response.data['success'] == true) {
//         currentUser.value = User.fromJson(response.data['data']);
//         return currentUser.value;
//       }
      
//       return null;
//     } catch (e) {
//       print('❌ Erreur getCurrentUser: $e');
//       return null;
//     }
//   }

//   // ==================== HELPERS CRYPTOGRAPHIE ====================
  
//   /// Génère une paire de clés DH (X25519) + Signature (Ed25519)
//   Future<Map<String, String>> _generateDHAndSignKeys() async {
//     try {
//       // 1. Générer clé DH (X25519)
//       final dhKeyPair = await _x25519.newKeyPair();
//       final dhPrivateBytes = await dhKeyPair.extractPrivateKeyBytes();
//       final dhPublicKey = await dhKeyPair.extractPublicKey();

//       // 2. Générer clé Signature (Ed25519)
//       final signKeyPair = await _ed25519.newKeyPair();
//       final signPrivateBytes = await signKeyPair.extractPrivateKeyBytes();
//       final signPublicKey = await signKeyPair.extractPublicKey();

//       return {
//         'dh_public_key': base64Encode(dhPublicKey.bytes),
//         'dh_private_key': base64Encode(dhPrivateBytes),
//         'sign_public_key': base64Encode(signPublicKey.bytes),
//         'sign_private_key': base64Encode(signPrivateBytes),
//       };
//     } catch (e) {
//       print('❌ Erreur génération clés: $e');
//       rethrow;
//     }
//   }

//   /// Hash le mot de passe avec SHA-256
//   String _hashPassword(String password) {
//     final bytes = utf8.encode(password);
//     final digest = sha256.convert(bytes);
//     return digest.toString();
//   }

//   // ==================== HELPERS DEVICE INFO ====================
  
//   /// Récupère le nom du device
//   Future<String> _getDeviceName() async {
//     try {
//       final DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
      
//       if (Platform.isAndroid) {
//         final androidInfo = await deviceInfo.androidInfo;
//         return '${androidInfo.brand} ${androidInfo.model}';
//       } else if (Platform.isIOS) {
//         final iosInfo = await deviceInfo.iosInfo;
//         return '${iosInfo.name} ${iosInfo.model}';
//       }
      
//       return 'Unknown Device';
//     } catch (e) {
//       print('⚠️ Erreur récupération device name: $e');
//       return 'Flutter Device';
//     }
//   }

//   /// Récupère le type du device
//   Future<String> _getDeviceType() async {
//     try {
//       if (Platform.isAndroid) {
//         return 'android';
//       } else if (Platform.isIOS) {
//         return 'ios';
//       } else if (Platform.isWindows) {
//         return 'windows';
//       } else if (Platform.isMacOS) {
//         return 'macos';
//       } else if (Platform.isLinux) {
//         return 'linux';
//       }
      
//       return 'unknown';
//     } catch (e) {
//       print('⚠️ Erreur récupération device type: $e');
//       return 'android';
//     }
//   }

//   // ==================== HELPERS ERREURS ====================
  
//   /// Formate les messages d'erreur
//   String _formatErrorMessage(dynamic error) {
//     if (error.toString().contains('SocketException')) {
//       return 'Pas de connexion Internet. Vérifiez votre réseau.';
//     } else if (error.toString().contains('TimeoutException')) {
//       return 'Délai d\'attente dépassé. Réessayez.';
//     } else if (error.toString().contains('401')) {
//       return 'Identifiants incorrects.';
//     } else if (error.toString().contains('404')) {
//       return 'Compte non trouvé.';
//     } else if (error.toString().contains('409')) {
//       return 'Ce numéro est déjà utilisé.';
//     } else if (error.toString().contains('500')) {
//       return 'Erreur serveur. Réessayez plus tard.';
//     }
    
//     return error.toString().replaceAll('Exception: ', '');
//   }

//   // ==================== GETTERS ====================
  
//   Future<bool> isAuthenticated() async {
//     return await _storage.isAuthenticated();
//   }

//   Future<bool> hasPrivateKeys() async {
//     return await _storage.hasPrivateKeys();
//   }

//   Future<String?> getAccessToken() async {
//     return await _storage.getAccessToken();
//   }

//   Future<String?> getUserId() async {
//     return await _storage.getUserId();
//   }
// }