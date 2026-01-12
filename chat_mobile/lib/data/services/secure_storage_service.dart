// lib/data/services/secure_storage_service.dart

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/auth_data.dart';

class SecureStorageService {
  static final SecureStorageService _instance = SecureStorageService._internal();
  factory SecureStorageService() => _instance;
  SecureStorageService._internal();

  late final FlutterSecureStorage _storage;
  
  // Clés de stockage
  static const String _keyAccessToken = 'access_token';
  static const String _keyRefreshToken = 'refresh_token';
  static const String _keyUserId = 'user_id';
  static const String _keyDeviceId = 'device_id';
  static const String _keyDhPrivateKey = 'dh_private_key';
  static const String _keySignPrivateKey = 'sign_private_key';

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

  Future<void> saveUserId(String userId) async {
    try {
      await _storage.write(key: 'user_id', value: userId);
      print('💾 User ID saved: $userId');
    } catch (e) {
      print('❌ saveUserId: $e');
    }
  }

  // ✅ Récupérer user ID
  Future<String?> getUserId() async {
    try {
      final userId = await _storage.read(key: 'user_id');
      print('📖 User ID retrieved: $userId');
      return userId;
    } catch (e) {
      print('❌ getUserId: $e');
      return null;
    }
  }

  // ==================== SAUVEGARDE ====================

  Future<void> saveAuthData(AuthData authData) async {
    await Future.wait([
      _storage.write(key: _keyAccessToken, value: authData.accessToken),
      _storage.write(key: _keyRefreshToken, value: authData.refreshToken),
      _storage.write(key: _keyUserId, value: authData.userId),
      _storage.write(key: _keyDeviceId, value: authData.deviceId),
      _storage.write(key: _keyDhPrivateKey, value: authData.dhPrivateKey),
      _storage.write(key: _keySignPrivateKey, value: authData.signPrivateKey),
    ]);
  }

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await Future.wait([
      _storage.write(key: _keyAccessToken, value: accessToken),
      _storage.write(key: _keyRefreshToken, value: refreshToken),
    ]);
  }

  Future<void> saveDeviceId(String deviceId) async {
    await _storage.write(key: _keyDeviceId, value: deviceId);
  }

  // Future<void> saveUserId(String userId) async {
  //   await _storage.write(key: _keyUserId, value: userId);
  // }

  Future<void> saveDHPrivateKey(String dhPrivateKey) async {
    await _storage.write(key: _keyDhPrivateKey, value: dhPrivateKey);
  }

  Future<void> saveSignPrivateKey(String signPrivateKey) async {
    await _storage.write(key: _keySignPrivateKey, value: signPrivateKey);
  }

  // ==================== LECTURE ====================

  Future<AuthData?> getAuthData() async {
    final values = await Future.wait([
      _storage.read(key: _keyAccessToken),
      _storage.read(key: _keyRefreshToken),
      _storage.read(key: _keyUserId),
      _storage.read(key: _keyDeviceId),
      _storage.read(key: _keyDhPrivateKey),
      _storage.read(key: _keySignPrivateKey),
    ]);

    if (values.any((v) => v == null)) {
      return null;
    }

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
    return await _storage.read(key: _keyAccessToken);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: _keyRefreshToken);
  }

  // Future<String?> getUserId() async {
  //   return await _storage.read(key: _keyUserId);
  // }

  Future<String?> getDeviceId() async {
    return await _storage.read(key: _keyDeviceId);
  }

  Future<String?> getDHPrivateKey() async {
    return await _storage.read(key: _keyDhPrivateKey);
  }

  Future<String?> getSignPrivateKey() async {
    return await _storage.read(key: _keySignPrivateKey);
  }

  // ==================== VÉRIFICATIONS ====================

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

  Future<bool> hasDHPrivateKey() async {
    final key = await getDHPrivateKey();
    return key != null;
  }

  Future<bool> hasSignPrivateKey() async {
    final key = await getSignPrivateKey();
    return key != null;
  }

  // ==================== SUPPRESSION ====================

  Future<void> clearAuth() async {
    await Future.wait([
      _storage.delete(key: _keyAccessToken),
      _storage.delete(key: _keyRefreshToken),
      _storage.delete(key: _keyUserId),
      _storage.delete(key: _keyDeviceId),
      _storage.delete(key: _keyDhPrivateKey),
      _storage.delete(key: _keySignPrivateKey),
    ]);
  }

  Future<void> clearAll() async {
    await _storage.deleteAll();
  }


}





// // lib/services/secure_storage_service.dart
// import 'package:flutter_secure_storage/flutter_secure_storage.dart';
// import '../models/auth_data.dart';

// class SecureStorageService {
//   static final SecureStorageService _instance = SecureStorageService._internal();
//   factory SecureStorageService() => _instance;
//   SecureStorageService._internal();

//   late final FlutterSecureStorage _storage;
//   // static const String _keyDeviceId = 'device_id';
//   // Clés de stockage
//   static const String _keyAccessToken = 'access_token';
//   static const String _keyRefreshToken = 'refresh_token';
//   static const String _keyUserId = 'user_id';
//   static const String _keyDeviceId = 'device_id';
//   static const String _keyPrivateKey = 'private_key';
//   static const String _keyBiometric = 'biometric_enabled';

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
  
//   /// Sauvegarder le device_id
//   Future<void> saveDeviceId(String deviceId) async {
//     await _storage.write(key: _keyDeviceId, value: deviceId);
//   }
  
//    Future<void> savePrivateKey(String privateKey) async {
//     await _storage.write(key: _keyPrivateKey, value: privateKey);
//     print('💾 Clé privée sauvegardée');
//   }
//     Future<void> saveUserId(String userId) async {
//     await _storage.write(key: _keyUserId, value: userId);
//   }
  
//   Future<String?> getUserId() async {
//     return await _storage.read(key: _keyUserId);
//   }
//   // ==================== SAUVEGARDE ====================

//   /// Sauvegarde toutes les données d'authentification
//   Future<void> saveAuthData(AuthData authData) async {
//     await Future.wait([
//       _storage.write(key: _keyAccessToken, value: authData.accessToken),
//       _storage.write(key: _keyRefreshToken, value: authData.refreshToken),
//       _storage.write(key: _keyUserId, value: authData.userId),
//       _storage.write(key: _keyDeviceId, value: authData.deviceId),
//       _storage.write(key: _keyPrivateKey, value: authData.privateKey),
//     ]);
//   }

//   /// Sauvegarde uniquement les tokens (après refresh)
//   Future<void> saveTokens(String accessToken, String refreshToken) async {
//     await Future.wait([
//       _storage.write(key: _keyAccessToken, value: accessToken),
//       _storage.write(key: _keyRefreshToken, value: refreshToken),
//     ]);
//   }

//   // ==================== LECTURE ====================

//   /// Récupère toutes les données d'authentification
//   Future<AuthData?> getAuthData() async {
//     final values = await Future.wait([
//       _storage.read(key: _keyAccessToken),
//       _storage.read(key: _keyRefreshToken),
//       _storage.read(key: _keyUserId),
//       _storage.read(key: _keyDeviceId),
//       _storage.read(key: _keyPrivateKey),
//     ]);

//     // Vérifier que toutes les données sont présentes
//     if (values.any((v) => v == null)) {
//       return null;
//     }

//     return AuthData(
//       accessToken: values[0]!,
//       refreshToken: values[1]!,
//       userId: values[2]!,
//       deviceId: values[3]!,
//       privateKey: values[4]!,
//     );
//   }

//   /// Récupère uniquement l'access token
//   Future<String?> getAccessToken() async {
//     return await _storage.read(key: _keyAccessToken);
//   }

//   /// Récupère uniquement le refresh token
//   Future<String?> getRefreshToken() async {
//     return await _storage.read(key: _keyRefreshToken);
//   }

  

//   /// Récupère l'ID de l'appareil
//   Future<String?> getDeviceId() async {
//     return await _storage.read(key: _keyDeviceId);
//   }

//   /// Récupère la clé privée RSA
//   Future<String?> getPrivateKey() async {
//     return await _storage.read(key: _keyPrivateKey);
//   }

//   // ==================== VÉRIFICATIONS ====================

//   /// Vérifie si l'utilisateur est authentifié
//   Future<bool> isAuthenticated() async {
//     final accessToken = await getAccessToken();
//     final privateKey = await getPrivateKey();
//     return accessToken != null && privateKey != null;
//   }

//   /// Vérifie si la clé privée existe
//   Future<bool> hasPrivateKey() async {
//     final privateKey = await getPrivateKey();
//     return privateKey != null;
//   }

//   // ==================== BIOMÉTRIE ====================

//   Future<void> setBiometricEnabled(bool enabled) async {
//     await _storage.write(key: _keyBiometric, value: enabled.toString());
//   }

//   Future<bool> isBiometricEnabled() async {
//     final value = await _storage.read(key: _keyBiometric);
//     return value == 'true';
//   }

//   // ==================== SUPPRESSION ====================

//   /// Supprime toutes les données d'authentification (Logout)
//   Future<void> clearAuth() async {
//     await Future.wait([
//       _storage.delete(key: _keyAccessToken),
//       _storage.delete(key: _keyRefreshToken),
//       _storage.delete(key: _keyUserId),
//       _storage.delete(key: _keyDeviceId),
//       // NOTE: On garde la private_key pour éviter de perdre les messages chiffrés
//       // Pour supprimer aussi la private_key, décommenter la ligne ci-dessous
//       // _storage.delete(key: _keyPrivateKey),
//     ]);
//   }

//   /// Supprime TOUT (incluant private key) - À utiliser avec précaution!
//   Future<void> clearAll() async {
//     await _storage.deleteAll();
//   }
// }