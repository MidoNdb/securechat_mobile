// // lib/data/services/storage_service.dart

// import 'package:get/get.dart';
// import 'package:get_storage/get_storage.dart';
// import 'package:flutter_secure_storage/flutter_secure_storage.dart';
// import '../models/conversation.dart';
// import '../models/message.dart';
// import '../models/user.dart';
// import '../../core/shared/storage_keys.dart';

// class StorageService extends GetxService {
//   late final GetStorage _box;
//   late final FlutterSecureStorage _secureStorage;

//   Future<StorageService> init() async {
//     // Initialiser GetStorage pour données non sensibles
//     await GetStorage.init();
//     _box = GetStorage();
    
//     // Initialiser FlutterSecureStorage pour données sensibles
//     _secureStorage = const FlutterSecureStorage(
//       aOptions: AndroidOptions(
//         encryptedSharedPreferences: true,
//       ),
//       iOptions: IOSOptions(
//         accessibility: KeychainAccessibility.first_unlock,
//       ),
//     );
    
//     print('✅ StorageService initialisé');
//     return this;
//   }

//   // ========================================
//   // AUTH & TOKEN (SÉCURISÉ - FlutterSecureStorage)
//   // ========================================
  
//   /// Sauvegarder le token d'authentification (SÉCURISÉ)
//   Future<void> saveToken(String token) async {
//     await _secureStorage.write(key: StorageKeys.authToken, value: token);
//   }

//   /// Récupérer le token d'authentification (SÉCURISÉ)
//   Future<String?> getToken() async {
//     return await _secureStorage.read(key: StorageKeys.authToken);
//   }

//   /// Sauvegarder le refresh token (SÉCURISÉ)
//   Future<void> saveRefreshToken(String token) async {
//     await _secureStorage.write(key: StorageKeys.refreshToken, value: token);
//   }

//   /// Récupérer le refresh token (SÉCURISÉ)
//   Future<String?> getRefreshToken() async {
//     return await _secureStorage.read(key: StorageKeys.refreshToken);
//   }

//   /// Supprimer tous les tokens (SÉCURISÉ)
//   Future<void> removeTokens() async {
//     await _secureStorage.delete(key: StorageKeys.authToken);
//     await _secureStorage.delete(key: StorageKeys.refreshToken);
//   }

//   // ========================================
//   // CRYPTO KEYS (SÉCURISÉ - FlutterSecureStorage)
//   // ========================================
  
//   /// Sauvegarder la clé privée RSA (SÉCURISÉ)
//   Future<void> savePrivateKey(String privateKey) async {
//     await _secureStorage.write(key: StorageKeys.privateKey, value: privateKey);
//   }

//   /// Récupérer la clé privée RSA (SÉCURISÉ)
//   Future<String?> getPrivateKey() async {
//     return await _secureStorage.read(key: StorageKeys.privateKey);
//   }

//   /// Sauvegarder la clé publique RSA (SÉCURISÉ)
//   Future<void> savePublicKey(String publicKey) async {
//     await _secureStorage.write(key: StorageKeys.publicKey, value: publicKey);
//   }

//   /// Récupérer la clé publique RSA (SÉCURISÉ)
//   Future<String?> getPublicKey() async {
//     return await _secureStorage.read(key: StorageKeys.publicKey);
//   }

//   /// Sauvegarder le PIN local (SÉCURISÉ)
//   Future<void> saveLocalPin(String pin) async {
//     await _secureStorage.write(key: StorageKeys.localPin, value: pin);
//   }

//   /// Récupérer le PIN local (SÉCURISÉ)
//   Future<String?> getLocalPin() async {
//     return await _secureStorage.read(key: StorageKeys.localPin);
//   }

//   /// Supprimer toutes les données sécurisées
//   Future<void> clearSecureData() async {
//     await _secureStorage.deleteAll();
//   }

//   // ========================================
//   // USER (GetStorage)
//   // ========================================
  
//   /// Sauvegarder l'utilisateur actuel
//   Future<void> saveCurrentUser(User user) async {
//     await _box.write(StorageKeys.currentUser, user.toJson());
//   }

//   /// Récupérer l'utilisateur actuel
//   User? getCurrentUser() {
//     final data = _box.read(StorageKeys.currentUser);
//     if (data != null) {
//       return User.fromJson(Map<String, dynamic>.from(data));
//     }
//     return null;
//   }

//   /// Récupérer l'ID de l'utilisateur actuel
//   int? getCurrentUserId() {
//     final user = getCurrentUser();
//     return user?.id;
//   }

//   /// Supprimer l'utilisateur actuel
//   Future<void> removeCurrentUser() async {
//     await _box.remove(StorageKeys.currentUser);
//   }

//   // ========================================
//   // CONVERSATIONS (GetStorage)
//   // ========================================
  
//   /// Sauvegarder les conversations
//   Future<void> saveConversations(List<Conversation> conversations) async {
//     try {
//       final data = conversations.map((c) => c.toJson()).toList();
//       await _box.write(StorageKeys.conversations, data);
//       print('✅ ${conversations.length} conversations sauvegardées');
//     } catch (e) {
//       print('❌ Erreur saveConversations: $e');
//     }
//   }

//   /// Récupérer les conversations
//   List<Conversation>? getConversations() {
//     try {
//       final data = _box.read<List>(StorageKeys.conversations);
//       if (data != null && data.isNotEmpty) {
//         return data
//             .map((item) => Conversation.fromJson(Map<String, dynamic>.from(item)))
//             .toList();
//       }
//       return null;
//     } catch (e) {
//       print('❌ Erreur getConversations: $e');
//       return null;
//     }
//   }

//   /// Sauvegarder une conversation
//   Future<void> saveConversation(Conversation conversation) async {
//     final conversations = getConversations() ?? [];
//     final index = conversations.indexWhere((c) => c.id == conversation.id);
    
//     if (index != -1) {
//       conversations[index] = conversation;
//     } else {
//       conversations.insert(0, conversation);
//     }
    
//     await saveConversations(conversations);
//   }

//   /// Supprimer une conversation
//   Future<void> removeConversation(int conversationId) async {
//     final conversations = getConversations() ?? [];
//     conversations.removeWhere((c) => c.id == conversationId);
//     await saveConversations(conversations);
//   }

//   // ========================================
//   // MESSAGES (GetStorage)
//   // ========================================
  
//   /// Sauvegarder les messages d'une conversation
//   Future<void> saveMessages(int conversationId, List<Message> messages) async {
//     try {
//       final key = StorageKeys.messagesKey(conversationId);
//       final data = messages.map((m) => m.toJson()).toList();
//       await _box.write(key, data);
//     } catch (e) {
//       print('❌ Erreur saveMessages: $e');
//     }
//   }

//   /// Récupérer les messages d'une conversation
//   List<Message>? getMessages(int conversationId) {
//     try {
//       final key = StorageKeys.messagesKey(conversationId);
//       final data = _box.read<List>(key);
//       if (data != null && data.isNotEmpty) {
//         return data
//             .map((item) => Message.fromJson(Map<String, dynamic>.from(item)))
//             .toList();
//       }
//       return null;
//     } catch (e) {
//       print('❌ Erreur getMessages: $e');
//       return null;
//     }
//   }

//   /// Sauvegarder un message
//   Future<void> saveMessage(Message message) async {
//     final messages = getMessages(message.conversationId) ?? [];
//     final index = messages.indexWhere((m) => m.id == message.id);
    
//     if (index != -1) {
//       messages[index] = message;
//     } else {
//       messages.add(message);
//     }
    
//     await saveMessages(message.conversationId, messages);
//   }

//   /// Supprimer un message
//   Future<void> removeMessage(int conversationId, int messageId) async {
//     final messages = getMessages(conversationId) ?? [];
//     messages.removeWhere((m) => m.id == messageId);
//     await saveMessages(conversationId, messages);
//   }

//   // ========================================
//   // CONTACTS (GetStorage)
//   // ========================================
  
//   /// Sauvegarder les contacts
//   Future<void> saveContacts(List<dynamic> contacts) async {
//     await _box.write(StorageKeys.contacts, contacts);
//   }

//   /// Récupérer les contacts
//   List<dynamic>? getContacts() {
//     return _box.read<List>(StorageKeys.contacts);
//   }

//   /// Sauvegarder les contacts bloqués
//   Future<void> saveBlockedContacts(List<int> blockedIds) async {
//     await _box.write(StorageKeys.blockedContacts, blockedIds);
//   }

//   /// Récupérer les contacts bloqués
//   List<int> getBlockedContacts() {
//     final data = _box.read<List>(StorageKeys.blockedContacts);
//     return data?.map((e) => e as int).toList() ?? [];
//   }

//   /// Sauvegarder les contacts favoris
//   Future<void> saveFavoriteContacts(List<int> favoriteIds) async {
//     await _box.write(StorageKeys.favoriteContacts, favoriteIds);
//   }

//   /// Récupérer les contacts favoris
//   List<int> getFavoriteContacts() {
//     final data = _box.read<List>(StorageKeys.favoriteContacts);
//     return data?.map((e) => e as int).toList() ?? [];
//   }

//   // ========================================
//   // SETTINGS (GetStorage)
//   // ========================================
  
//   /// Sauvegarder la langue
//   Future<void> saveLanguage(String language) async {
//     await _box.write(StorageKeys.language, language);
//   }

//   /// Récupérer la langue
//   String getLanguage() {
//     return _box.read(StorageKeys.language) ?? 'fr';
//   }

//   /// Sauvegarder le thème
//   Future<void> saveThemeMode(String mode) async {
//     await _box.write(StorageKeys.themeMode, mode);
//   }

//   /// Récupérer le thème
//   String getThemeMode() {
//     return _box.read(StorageKeys.themeMode) ?? 'light';
//   }

//   /// Sauvegarder l'état des notifications
//   Future<void> saveNotificationEnabled(bool enabled) async {
//     await _box.write(StorageKeys.notificationsEnabled, enabled);
//   }

//   /// Récupérer l'état des notifications
//   bool getNotificationEnabled() {
//     return _box.read(StorageKeys.notificationsEnabled) ?? true;
//   }

//   /// Sauvegarder le token FCM
//   Future<void> saveFcmToken(String token) async {
//     await _box.write(StorageKeys.fcmToken, token);
//   }

//   /// Récupérer le token FCM
//   String? getFcmToken() {
//     return _box.read(StorageKeys.fcmToken);
//   }

//   /// Sauvegarder l'état du son
//   Future<void> saveSoundEnabled(bool enabled) async {
//     await _box.write(StorageKeys.soundEnabled, enabled);
//   }

//   /// Récupérer l'état du son
//   bool getSoundEnabled() {
//     return _box.read(StorageKeys.soundEnabled) ?? true;
//   }

//   /// Sauvegarder l'état de la vibration
//   Future<void> saveVibrationEnabled(bool enabled) async {
//     await _box.write(StorageKeys.vibrationEnabled, enabled);
//   }

//   /// Récupérer l'état de la vibration
//   bool getVibrationEnabled() {
//     return _box.read(StorageKeys.vibrationEnabled) ?? true;
//   }

//   /// Sauvegarder l'état du preview des messages
//   Future<void> saveMessagePreview(bool enabled) async {
//     await _box.write(StorageKeys.messagePreview, enabled);
//   }

//   /// Récupérer l'état du preview des messages
//   bool getMessagePreview() {
//     return _box.read(StorageKeys.messagePreview) ?? true;
//   }

//   // ========================================
//   // PRIVACY SETTINGS (GetStorage)
//   // ========================================
  
//   /// Sauvegarder la confidentialité du last seen
//   Future<void> saveLastSeenPrivacy(String privacy) async {
//     await _box.write(StorageKeys.lastSeenPrivacy, privacy);
//   }

//   /// Récupérer la confidentialité du last seen
//   String getLastSeenPrivacy() {
//     return _box.read(StorageKeys.lastSeenPrivacy) ?? 'everyone';
//   }

//   /// Sauvegarder la confidentialité de la photo de profil
//   Future<void> saveProfilePhotoPrivacy(String privacy) async {
//     await _box.write(StorageKeys.profilePhotoPrivacy, privacy);
//   }

//   /// Récupérer la confidentialité de la photo de profil
//   String getProfilePhotoPrivacy() {
//     return _box.read(StorageKeys.profilePhotoPrivacy) ?? 'everyone';
//   }

//   /// Sauvegarder la confidentialité du statut
//   Future<void> saveStatusPrivacy(String privacy) async {
//     await _box.write(StorageKeys.statusPrivacy, privacy);
//   }

//   /// Récupérer la confidentialité du statut
//   String getStatusPrivacy() {
//     return _box.read(StorageKeys.statusPrivacy) ?? 'contacts';
//   }

//   // ========================================
//   // SECURITY SETTINGS (GetStorage)
//   // ========================================
  
//   /// Sauvegarder l'état du verrouillage de l'app
//   Future<void> saveAppLockEnabled(bool enabled) async {
//     await _box.write(StorageKeys.appLockEnabled, enabled);
//   }

//   /// Récupérer l'état du verrouillage de l'app
//   bool getAppLockEnabled() {
//     return _box.read(StorageKeys.appLockEnabled) ?? false;
//   }

//   /// Sauvegarder le type de verrouillage
//   Future<void> saveAppLockType(String type) async {
//     await _box.write(StorageKeys.appLockType, type);
//   }

//   /// Récupérer le type de verrouillage
//   String getAppLockType() {
//     return _box.read(StorageKeys.appLockType) ?? 'pin';
//   }

//   /// Sauvegarder le délai de verrouillage automatique
//   Future<void> saveAutoLockTimeout(int seconds) async {
//     await _box.write(StorageKeys.autoLockTimeout, seconds);
//   }

//   /// Récupérer le délai de verrouillage automatique
//   int getAutoLockTimeout() {
//     return _box.read(StorageKeys.autoLockTimeout) ?? 60;
//   }

//   // ========================================
//   // ONBOARDING (GetStorage)
//   // ========================================
  
//   /// Sauvegarder l'état du premier lancement
//   Future<void> saveIsFirstTime(bool isFirst) async {
//     await _box.write(StorageKeys.isFirstTime, isFirst);
//   }

//   /// Récupérer l'état du premier lancement
//   bool getIsFirstTime() {
//     return _box.read(StorageKeys.isFirstTime) ?? true;
//   }

//   /// Sauvegarder l'état de l'onboarding
//   Future<void> saveHasCompletedOnboarding(bool completed) async {
//     await _box.write(StorageKeys.hasCompletedOnboarding, completed);
//   }

//   /// Récupérer l'état de l'onboarding
//   bool getHasCompletedOnboarding() {
//     return _box.read(StorageKeys.hasCompletedOnboarding) ?? false;
//   }

//   // ========================================
//   // CLEAR DATA
//   // ========================================
  
//   /// Supprimer toutes les données (GetStorage + FlutterSecureStorage)
//   Future<void> clearAllData() async {
//     await _box.erase(); // GetStorage
//     await _secureStorage.deleteAll(); // FlutterSecureStorage
//     print('✅ Toutes les données supprimées');
//   }

//   /// Supprimer uniquement les données de chat
//   Future<void> clearChatData() async {
//     await _box.remove(StorageKeys.conversations);
    
//     // Supprimer tous les messages
//     final keys = _box.getKeys().where((key) => 
//       key.toString().startsWith('${StorageKeys.messages}_')
//     );
//     for (var key in keys) {
//       await _box.remove(key);
//     }
    
//     print('✅ Données de chat supprimées');
//   }

//   /// Supprimer uniquement les données d'authentification
//   Future<void> clearAuthData() async {
//     // Supprimer les tokens sécurisés
//     await _secureStorage.delete(key: StorageKeys.authToken);
//     await _secureStorage.delete(key: StorageKeys.refreshToken);
    
//     // Supprimer l'utilisateur actuel
//     await _box.remove(StorageKeys.currentUser);
    
//     print('✅ Données d\'authentification supprimées');
//   }

//   /// Supprimer le cache
//   Future<void> clearCache() async {
//     await _box.remove(StorageKeys.mediaCache);
//     await _box.remove(StorageKeys.downloadedMedia);
//     print('✅ Cache supprimé');
//   }

//   /// Supprimer les clés crypto
//   Future<void> clearCryptoKeys() async {
//     await _secureStorage.delete(key: StorageKeys.privateKey);
//     await _secureStorage.delete(key: StorageKeys.publicKey);
//     print('✅ Clés cryptographiques supprimées');
//   }

//   // ========================================
//   // HELPERS
//   // ========================================
  
//   /// Vérifier si l'utilisateur est connecté
//   bool isLoggedIn() {
//     return getCurrentUser() != null;
//   }

//   /// Obtenir la taille du stockage utilisée
//   int getStorageSize() {
//     // Approximation basée sur le nombre de clés
//     return _box.getKeys().length;
//   }

//   /// Lister toutes les clés stockées (DEBUG)
//   List<dynamic> getAllKeys() {
//     return _box.getKeys().toList();
//   }
// }
// // // lib/data/services/storage_service.dart

// // import 'package:get/get.dart';
// // import 'package:flutter_secure_storage/flutter_secure_storage.dart';
// // import 'package:shared_preferences/shared_preferences.dart';
// // import '../../core/shared/storage_keys.dart';

// // class StorageService extends GetxService {
// //   late final FlutterSecureStorage _secureStorage;
// //   late final SharedPreferences _prefs;

// //   // ========================================
// //   // INITIALISATION
// //   // ========================================
// //   Future<StorageService> init() async {
// //     // FlutterSecureStorage pour données sensibles
// //     _secureStorage = const FlutterSecureStorage(
// //       aOptions: AndroidOptions(
// //         encryptedSharedPreferences: true,
// //       ),
// //       iOptions: IOSOptions(
// //         accessibility: KeychainAccessibility.first_unlock,
// //       ),
// //     );

// //     // SharedPreferences pour données non-sensibles
// //     _prefs = await SharedPreferences.getInstance();

// //     print('✅ StorageService initialized');
// //     return this;
// //   }

// //   // ========================================
// //   // DONNÉES SENSIBLES (FlutterSecureStorage)
// //   // ========================================

// //   // Token JWT
// //   Future<void> saveToken(String token) async {
// //     await _secureStorage.write(key: StorageKeys.authToken, value: token);
// //   }

// //   String? getToken() {
// //     // FlutterSecureStorage est async, donc on garde en cache
// //     return _prefs.getString(StorageKeys.authTokenCache);
// //   }

// //   Future<String?> getTokenSecure() async {
// //     return await _secureStorage.read(key: StorageKeys.authToken);
// //   }

// //   Future<void> clearToken() async {
// //     await _secureStorage.delete(key: StorageKeys.authToken);
// //     await _prefs.remove(StorageKeys.authTokenCache);
// //   }

// //   // Clé privée RSA (CRITIQUE - très sensible)
// //   Future<void> savePrivateKey(String privateKey) async {
// //     await _secureStorage.write(key: StorageKeys.privateKey, value: privateKey);
// //   }

// //   Future<String?> getPrivateKey() async {
// //     return await _secureStorage.read(key: StorageKeys.privateKey);
// //   }

// //   Future<void> deletePrivateKey() async {
// //     await _secureStorage.delete(key: StorageKeys.privateKey);
// //   }

// //   // Clé publique RSA
// //   Future<void> savePublicKey(String publicKey) async {
// //     await _secureStorage.write(key: StorageKeys.publicKey, value: publicKey);
// //   }

// //   Future<String?> getPublicKey() async {
// //     return await _secureStorage.read(key: StorageKeys.publicKey);
// //   }

// //   // PIN / Mot de passe local (si biométrie)
// //   Future<void> saveLocalPin(String pin) async {
// //     await _secureStorage.write(key: StorageKeys.localPin, value: pin);
// //   }

// //   Future<String?> getLocalPin() async {
// //     return await _secureStorage.read(key: StorageKeys.localPin);
// //   }

// //   // ========================================
// //   // DONNÉES NON-SENSIBLES (SharedPreferences)
// //   // ========================================

// //   // User ID
// //   Future<void> saveUserId(int userId) async {
// //     await _prefs.setInt(StorageKeys.userId, userId);
// //   }

// //   int? getUserId() {
// //     return _prefs.getInt(StorageKeys.userId);
// //   }

// //   // User info (JSON)
// //   Future<void> saveUserInfo(String userJson) async {
// //     await _prefs.setString(StorageKeys.userInfo, userJson);
// //   }

// //   String? getUserInfo() {
// //     return _prefs.getString(StorageKeys.userInfo);
// //   }

// //   // Langue
// //   Future<void> saveLanguage(String langCode) async {
// //     await _prefs.setString(StorageKeys.language, langCode);
// //   }

// //   String? getLanguage() {
// //     return _prefs.getString(StorageKeys.language);
// //   }

// //   // Thème (dark/light)
// //   Future<void> saveThemeMode(String mode) async {
// //     await _prefs.setString(StorageKeys.themeMode, mode);
// //   }

// //   String? getThemeMode() {
// //     return _prefs.getString(StorageKeys.themeMode);
// //   }

// //   // Première ouverture app
// //   Future<void> setFirstTime(bool value) async {
// //     await _prefs.setBool(StorageKeys.isFirstTime, value);
// //   }

// //   bool isFirstTime() {
// //     return _prefs.getBool(StorageKeys.isFirstTime) ?? true;
// //   }

// //   // Notifications activées
// //   Future<void> setNotificationsEnabled(bool enabled) async {
// //     await _prefs.setBool(StorageKeys.notificationsEnabled, enabled);
// //   }

// //   bool areNotificationsEnabled() {
// //     return _prefs.getBool(StorageKeys.notificationsEnabled) ?? true;
// //   }

// //   // FCM Token
// //   Future<void> saveFcmToken(String token) async {
// //     await _prefs.setString(StorageKeys.fcmToken, token);
// //   }

// //   String? getFcmToken() {
// //     return _prefs.getString(StorageKeys.fcmToken);
// //   }

// //   // Dernière synchronisation
// //   Future<void> saveLastSync(DateTime dateTime) async {
// //     await _prefs.setString(StorageKeys.lastSync, dateTime.toIso8601String());
// //   }

// //   DateTime? getLastSync() {
// //     final str = _prefs.getString(StorageKeys.lastSync);
// //     return str != null ? DateTime.parse(str) : null;
// //   }

// //   // ========================================
// //   // UTILITAIRES
// //   // ========================================

// //   // Tout supprimer (déconnexion complète)
// //   Future<void> clearAll() async {
// //     await _secureStorage.deleteAll();
// //     await _prefs.clear();
// //     print('🗑️ All storage cleared');
// //   }

// //   // Supprimer seulement données utilisateur (garder préférences app)
// //   Future<void> clearUserData() async {
// //     await _secureStorage.delete(key: StorageKeys.authToken);
// //     await _secureStorage.delete(key: StorageKeys.privateKey);
// //     await _secureStorage.delete(key: StorageKeys.publicKey);
// //     await _prefs.remove(StorageKeys.authTokenCache);
// //     await _prefs.remove(StorageKeys.userId);
// //     await _prefs.remove(StorageKeys.userInfo);
// //     print('🗑️ User data cleared');
// //   }

// //   // Vérifier si user connecté
// //   bool isLoggedIn() {
// //     return getToken() != null && getUserId() != null;
// //   }

// //   // Debug: Afficher toutes les clés
// //   Future<void> debugPrintAll() async {
// //     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
// //     print('📦 SECURE STORAGE:');
// //     final allSecure = await _secureStorage.readAll();
// //     allSecure.forEach((key, value) {
// //       // Masquer données sensibles
// //       if (key.contains('key') || key.contains('token') || key.contains('pin')) {
// //         print('  $key: [HIDDEN]');
// //       } else {
// //         print('  $key: $value');
// //       }
// //     });
    
// //     print('📦 SHARED PREFERENCES:');
// //     final allPrefs = _prefs.getKeys();
// //     for (var key in allPrefs) {
// //       print('  $key: ${_prefs.get(key)}');
// //     }
// //     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
// //   }
// // }