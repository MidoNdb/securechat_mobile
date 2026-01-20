// lib/data/services/secure_storage_service.dart

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/auth_data.dart';

class SecureStorageService {
  static final SecureStorageService _instance = SecureStorageService._internal();
  factory SecureStorageService() => _instance;
  SecureStorageService._internal();

  late final FlutterSecureStorage _storage;

  Future<void> init() async {
    _storage = const FlutterSecureStorage(
      aOptions: AndroidOptions(
        encryptedSharedPreferences: true,
        resetOnError: true,
      ),
      iOptions: IOSOptions(
        accessibility: KeychainAccessibility.first_unlock_this_device,
      ),
    );
  }

  Future<void> saveAuthData(AuthData authData) async {
    await Future.wait([
      _storage.write(key: 'access_token', value: authData.accessToken),
      _storage.write(key: 'refresh_token', value: authData.refreshToken),
      _storage.write(key: 'user_id', value: authData.userId),
      _storage.write(key: 'device_id', value: authData.deviceId),
      _storage.write(key: 'dh_private_key', value: authData.dhPrivateKey),
      _storage.write(key: 'sign_private_key', value: authData.signPrivateKey),
    ]);
  }

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await Future.wait([
      _storage.write(key: 'access_token', value: accessToken),
      _storage.write(key: 'refresh_token', value: refreshToken),
    ]);
  }

  Future<void> saveUserId(String userId) async {
    await _storage.write(key: 'user_id', value: userId);
    print('💾 User ID saved: $userId');
  }

  Future<void> saveDeviceId(String deviceId) async {
    await _storage.write(key: 'device_id', value: deviceId);
  }

  Future<void> saveDHPrivateKey(String dhPrivateKey) async {
    await _storage.write(key: 'dh_private_key', value: dhPrivateKey);
  }

  Future<void> saveSignPrivateKey(String signPrivateKey) async {
    await _storage.write(key: 'sign_private_key', value: signPrivateKey);
  }

  Future<void> saveMessagePlaintext(String messageId, String plaintext) async {
    await _storage.write(key: 'msg_plain_$messageId', value: plaintext);
  }

  // ========== NOUVEAU: Backup des clés privées ==========
  
  /// Sauvegarde le backup chiffré des clés privées
  Future<void> saveEncryptedKeysBackup(String encryptedBackup) async {
    await _storage.write(key: 'encrypted_keys_backup', value: encryptedBackup);
    print('💾 Backup des clés chiffrées sauvegardé');
  }

  /// Récupère le backup chiffré des clés privées
  Future<String?> getEncryptedKeysBackup() async {
    return await _storage.read(key: 'encrypted_keys_backup');
  }

  /// Supprime le backup chiffré
  Future<void> deleteEncryptedKeysBackup() async {
    await _storage.delete(key: 'encrypted_keys_backup');
  }

  // ========== FIN NOUVEAU ==========

  Future<AuthData?> getAuthData() async {
    final values = await Future.wait([
      _storage.read(key: 'access_token'),
      _storage.read(key: 'refresh_token'),
      _storage.read(key: 'user_id'),
      _storage.read(key: 'device_id'),
      _storage.read(key: 'dh_private_key'),
      _storage.read(key: 'sign_private_key'),
    ]);

    if (values.any((v) => v == null)) return null;

    return AuthData(
      accessToken: values[0]!,
      refreshToken: values[1]!,
      userId: values[2]!,
      deviceId: values[3]!,
      dhPrivateKey: values[4]!,
      signPrivateKey: values[5]!,
    );
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: 'access_token');
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: 'refresh_token');
  }

  Future<String?> getUserId() async {
    final userId = await _storage.read(key: 'user_id');
    print('📖 User ID retrieved: $userId');
    return userId;
  }

  Future<String?> getDeviceId() async {
    return await _storage.read(key: 'device_id');
  }

  Future<String?> getDHPrivateKey() async {
    return await _storage.read(key: 'dh_private_key');
  }

  Future<String?> getSignPrivateKey() async {
    return await _storage.read(key: 'sign_private_key');
  }

  Future<String?> getMessagePlaintext(String messageId) async {
    return await _storage.read(key: 'msg_plain_$messageId');
  }

  Future<bool> isAuthenticated() async {
    final accessToken = await getAccessToken();
    final dhKey = await getDHPrivateKey();
    final signKey = await getSignPrivateKey();
    return accessToken != null && dhKey != null && signKey != null;
  }

  Future<bool> hasPrivateKeys() async {
    final dhKey = await getDHPrivateKey();
    final signKey = await getSignPrivateKey();
    return dhKey != null && signKey != null;
  }

  // ========== NOUVEAU: Méthodes individuelles ==========
  
  /// Vérifie si la clé privée DH existe
  Future<bool> hasDHPrivateKey() async {
    final dhKey = await getDHPrivateKey();
    return dhKey != null;
  }

  /// Vérifie si la clé privée de signature existe
  Future<bool> hasSignPrivateKey() async {
    final signKey = await getSignPrivateKey();
    return signKey != null;
  }

  // ========== FIN NOUVEAU ==========

  Future<void> clearAuth() async {
    await Future.wait([
      _storage.delete(key: 'access_token'),
      _storage.delete(key: 'refresh_token'),
      _storage.delete(key: 'user_id'),
      _storage.delete(key: 'device_id'),
      _storage.delete(key: 'dh_private_key'),
      _storage.delete(key: 'sign_private_key'),
    ]);
  }

  Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}


// // lib/data/services/secure_storage_service.dart

// import 'package:flutter_secure_storage/flutter_secure_storage.dart';
// import '../models/auth_data.dart';

// class SecureStorageService {
//   static final SecureStorageService _instance = SecureStorageService._internal();
//   factory SecureStorageService() => _instance;
//   SecureStorageService._internal();

//   late final FlutterSecureStorage _storage;

//   Future<void> init() async {
//     _storage = const FlutterSecureStorage(
//       aOptions: AndroidOptions(
//         encryptedSharedPreferences: true,
//         resetOnError: true,
//       ),
//       iOptions: IOSOptions(
//         accessibility: KeychainAccessibility.first_unlock_this_device,
//       ),
//     );
//   }

//   Future<void> saveAuthData(AuthData authData) async {
//     await Future.wait([
//       _storage.write(key: 'access_token', value: authData.accessToken),
//       _storage.write(key: 'refresh_token', value: authData.refreshToken),
//       _storage.write(key: 'user_id', value: authData.userId),
//       _storage.write(key: 'device_id', value: authData.deviceId),
//       _storage.write(key: 'dh_private_key', value: authData.dhPrivateKey),
//       _storage.write(key: 'sign_private_key', value: authData.signPrivateKey),
//     ]);
//   }

//   Future<void> saveTokens(String accessToken, String refreshToken) async {
//     await Future.wait([
//       _storage.write(key: 'access_token', value: accessToken),
//       _storage.write(key: 'refresh_token', value: refreshToken),
//     ]);
//   }

//   Future<void> saveUserId(String userId) async {
//     await _storage.write(key: 'user_id', value: userId);
//     print('💾 User ID saved: $userId');
//   }

//   Future<void> saveDeviceId(String deviceId) async {
//     await _storage.write(key: 'device_id', value: deviceId);
//   }

//   Future<void> saveDHPrivateKey(String dhPrivateKey) async {
//     await _storage.write(key: 'dh_private_key', value: dhPrivateKey);
//   }

//   Future<void> saveSignPrivateKey(String signPrivateKey) async {
//     await _storage.write(key: 'sign_private_key', value: signPrivateKey);
//   }

//   Future<void> saveMessagePlaintext(String messageId, String plaintext) async {
//     await _storage.write(key: 'msg_plain_$messageId', value: plaintext);
//   }

//   Future<AuthData?> getAuthData() async {
//     final values = await Future.wait([
//       _storage.read(key: 'access_token'),
//       _storage.read(key: 'refresh_token'),
//       _storage.read(key: 'user_id'),
//       _storage.read(key: 'device_id'),
//       _storage.read(key: 'dh_private_key'),
//       _storage.read(key: 'sign_private_key'),
//     ]);

//     if (values.any((v) => v == null)) return null;

//     return AuthData(
//       accessToken: values[0]!,
//       refreshToken: values[1]!,
//       userId: values[2]!,
//       deviceId: values[3]!,
//       dhPrivateKey: values[4]!,
//       signPrivateKey: values[5]!,
//     );
//   }

//   Future<String?> getAccessToken() async {
//     return await _storage.read(key: 'access_token');
//   }

//   Future<String?> getRefreshToken() async {
//     return await _storage.read(key: 'refresh_token');
//   }

//   Future<String?> getUserId() async {
//     final userId = await _storage.read(key: 'user_id');
//     print('📖 User ID retrieved: $userId');
//     return userId;
//   }

//   Future<String?> getDeviceId() async {
//     return await _storage.read(key: 'device_id');
//   }

//   Future<String?> getDHPrivateKey() async {
//     return await _storage.read(key: 'dh_private_key');
//   }

//   Future<String?> getSignPrivateKey() async {
//     return await _storage.read(key: 'sign_private_key');
//   }

//   Future<String?> getMessagePlaintext(String messageId) async {
//     return await _storage.read(key: 'msg_plain_$messageId');
//   }

//   Future<bool> isAuthenticated() async {
//     final accessToken = await getAccessToken();
//     final dhKey = await getDHPrivateKey();
//     final signKey = await getSignPrivateKey();
//     return accessToken != null && dhKey != null && signKey != null;
//   }

//   Future<bool> hasPrivateKeys() async {
//     final dhKey = await getDHPrivateKey();
//     final signKey = await getSignPrivateKey();
//     return dhKey != null && signKey != null;
//   }

//   Future<void> clearAuth() async {
//     await Future.wait([
//       _storage.delete(key: 'access_token'),
//       _storage.delete(key: 'refresh_token'),
//       _storage.delete(key: 'user_id'),
//       _storage.delete(key: 'device_id'),
//       _storage.delete(key: 'dh_private_key'),
//       _storage.delete(key: 'sign_private_key'),
//     ]);
//   }

//   Future<void> clearAll() async {
//     await _storage.deleteAll();
//   }
// }







// // lib/data/services/secure_storage_service.dart

// import 'package:flutter_secure_storage/flutter_secure_storage.dart';
// import '../models/auth_data.dart';

// class SecureStorageService {
//   static final SecureStorageService _instance = SecureStorageService._internal();
//   factory SecureStorageService() => _instance;
//   SecureStorageService._internal();

//   late final FlutterSecureStorage _storage;
  
//   // Clés de stockage
//   static const String _keyAccessToken = 'access_token';
//   static const String _keyRefreshToken = 'refresh_token';
//   static const String _keyUserId = 'user_id';
//   static const String _keyDeviceId = 'device_id';
//   static const String _keyDhPrivateKey = 'dh_private_key';
//   static const String _keySignPrivateKey = 'sign_private_key';

//   Future<void> init() async {
//     _storage = const FlutterSecureStorage(
//       aOptions: AndroidOptions(
//         encryptedSharedPreferences: true,
//         resetOnError: true,
//       ),
//       iOptions: IOSOptions(
//         accessibility: KeychainAccessibility.first_unlock_this_device,
//       ),
//     );
//   }

//   Future<void> saveUserId(String userId) async {
//     try {
//       await _storage.write(key: 'user_id', value: userId);
//       print('💾 User ID saved: $userId');
//     } catch (e) {
//       print('❌ saveUserId: $e');
//     }
//   }

//   // ✅ Récupérer user ID
//   Future<String?> getUserId() async {
//     try {
//       final userId = await _storage.read(key: 'user_id');
//       print('📖 User ID retrieved: $userId');
//       return userId;
//     } catch (e) {
//       print('❌ getUserId: $e');
//       return null;
//     }
//   }

//   // ==================== SAUVEGARDE ====================

//   Future<void> saveAuthData(AuthData authData) async {
//     await Future.wait([
//       _storage.write(key: _keyAccessToken, value: authData.accessToken),
//       _storage.write(key: _keyRefreshToken, value: authData.refreshToken),
//       _storage.write(key: _keyUserId, value: authData.userId),
//       _storage.write(key: _keyDeviceId, value: authData.deviceId),
//       _storage.write(key: _keyDhPrivateKey, value: authData.dhPrivateKey),
//       _storage.write(key: _keySignPrivateKey, value: authData.signPrivateKey),
//     ]);
//   }

//   Future<void> saveTokens(String accessToken, String refreshToken) async {
//     await Future.wait([
//       _storage.write(key: _keyAccessToken, value: accessToken),
//       _storage.write(key: _keyRefreshToken, value: refreshToken),
//     ]);
//   }

//   Future<void> saveDeviceId(String deviceId) async {
//     await _storage.write(key: _keyDeviceId, value: deviceId);
//   }

//   // Future<void> saveUserId(String userId) async {
//   //   await _storage.write(key: _keyUserId, value: userId);
//   // }

//   Future<void> saveDHPrivateKey(String dhPrivateKey) async {
//     await _storage.write(key: _keyDhPrivateKey, value: dhPrivateKey);
//   }

//   Future<void> saveSignPrivateKey(String signPrivateKey) async {
//     await _storage.write(key: _keySignPrivateKey, value: signPrivateKey);
//   }

//   // ==================== LECTURE ====================

//   Future<AuthData?> getAuthData() async {
//     final values = await Future.wait([
//       _storage.read(key: _keyAccessToken),
//       _storage.read(key: _keyRefreshToken),
//       _storage.read(key: _keyUserId),
//       _storage.read(key: _keyDeviceId),
//       _storage.read(key: _keyDhPrivateKey),
//       _storage.read(key: _keySignPrivateKey),
//     ]);

//     if (values.any((v) => v == null)) {
//       return null;
//     }

//     return AuthData(
//       accessToken: values[0]!,
//       refreshToken: values[1]!,
//       userId: values[2]!,
//       deviceId: values[3]!,
//       dhPrivateKey: values[4]!,
//       signPrivateKey: values[5]!,
//     );
//   }

//   Future<String?> getAccessToken() async {
//     return await _storage.read(key: _keyAccessToken);
//   }

//   Future<String?> getRefreshToken() async {
//     return await _storage.read(key: _keyRefreshToken);
//   }

//   // Future<String?> getUserId() async {
//   //   return await _storage.read(key: _keyUserId);
//   // }

//   Future<String?> getDeviceId() async {
//     return await _storage.read(key: _keyDeviceId);
//   }

//   Future<String?> getDHPrivateKey() async {
//     return await _storage.read(key: _keyDhPrivateKey);
//   }

//   Future<String?> getSignPrivateKey() async {
//     return await _storage.read(key: _keySignPrivateKey);
//   }

//   // ==================== VÉRIFICATIONS ====================

//   Future<bool> isAuthenticated() async {
//     final accessToken = await getAccessToken();
//     final dhKey = await getDHPrivateKey();
//     final signKey = await getSignPrivateKey();
//     return accessToken != null && dhKey != null && signKey != null;
//   }

//   Future<bool> hasPrivateKeys() async {
//     final dhKey = await getDHPrivateKey();
//     final signKey = await getSignPrivateKey();
//     return dhKey != null && signKey != null;
//   }

//   Future<bool> hasDHPrivateKey() async {
//     final key = await getDHPrivateKey();
//     return key != null;
//   }

//   Future<bool> hasSignPrivateKey() async {
//     final key = await getSignPrivateKey();
//     return key != null;
//   }

//   // ==================== SUPPRESSION ====================

//   Future<void> clearAuth() async {
//     await Future.wait([
//       _storage.delete(key: _keyAccessToken),
//       _storage.delete(key: _keyRefreshToken),
//       _storage.delete(key: _keyUserId),
//       _storage.delete(key: _keyDeviceId),
//       _storage.delete(key: _keyDhPrivateKey),
//       _storage.delete(key: _keySignPrivateKey),
//     ]);
//   }

//   Future<void> clearAll() async {
//     await _storage.deleteAll();
//   }


// }



