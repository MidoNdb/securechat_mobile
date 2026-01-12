// // lib/core/shared/storage_keys.dart

// class StorageKeys {
//   // ========================================
//   // DONNÉES SENSIBLES (FlutterSecureStorage)
//   // ========================================
//   static const String authToken = 'auth_token';
//   static const String refreshToken = 'refresh_token';
//   static const String privateKey = 'rsa_private_key';
//   static const String publicKey = 'rsa_public_key';
//   static const String localPin = 'local_pin';
//   static const String biometricEnabled = 'biometric_enabled';
//   static const String encryptionKey = 'encryption_key';

//   // ========================================
//   // DONNÉES NON-SENSIBLES (GetStorage/SharedPreferences)
//   // ========================================
  
//   // Auth & User
//   static const String authTokenCache = 'auth_token_cache';
//   static const String userId = 'user_id';
//   static const String currentUser = 'current_user';
//   static const String userInfo = 'user_info';
//   static const String userPhone = 'user_phone';
//   static const String userEmail = 'user_email';
//   static const String userAvatar = 'user_avatar';
//   static const String userName = 'user_name';
  
//   // Conversations & Messages
//   static const String conversations = 'conversations';
//   static const String messages = 'messages'; // Prefix: messages_{conversation_id}
//   static const String drafts = 'drafts'; // Prefix: drafts_{conversation_id}
//   static const String archivedConversations = 'archived_conversations';
//   static const String mutedConversations = 'muted_conversations';
//   static const String pinnedConversations = 'pinned_conversations';
//   static const String deletedMessages = 'deleted_messages';
  
//   // Contacts
//   static const String contacts = 'contacts';
//   static const String blockedContacts = 'blocked_contacts';
//   static const String favoriteContacts = 'favorite_contacts';
//   static const String recentContacts = 'recent_contacts';
//   static const String syncedContacts = 'synced_contacts';
  
//   // Groups
//   static const String groups = 'groups';
//   static const String groupMembers = 'group_members'; // Prefix: group_members_{group_id}
  
//   // Media
//   static const String mediaCache = 'media_cache';
//   static const String downloadedMedia = 'downloaded_media';
//   static const String pendingUploads = 'pending_uploads';
  
//   // Calls
//   static const String callHistory = 'call_history';
//   static const String missedCalls = 'missed_calls';
  
//   // Settings
//   static const String language = 'language';
//   static const String themeMode = 'theme_mode';
//   static const String fontSize = 'font_size';
//   static const String notificationsEnabled = 'notifications_enabled';
//   static const String soundEnabled = 'sound_enabled';
//   static const String vibrationEnabled = 'vibration_enabled';
//   static const String messagePreview = 'message_preview';
//   static const String readReceipts = 'read_receipts';
//   static const String typingIndicators = 'typing_indicators';
//   static const String autoDownloadImages = 'auto_download_images';
//   static const String autoDownloadVideos = 'auto_download_videos';
//   static const String autoDownloadAudios = 'auto_download_audios';
//   static const String autoDownloadDocuments = 'auto_download_documents';
//   static const String wifiOnly = 'wifi_only';
  
//   // Privacy
//   static const String lastSeenPrivacy = 'last_seen_privacy'; // everyone, contacts, nobody
//   static const String profilePhotoPrivacy = 'profile_photo_privacy';
//   static const String statusPrivacy = 'status_privacy';
//   static const String screenshotSecurity = 'screenshot_security';
//   static const String incognitoKeyboard = 'incognito_keyboard';
  
//   // Security
//   static const String appLockEnabled = 'app_lock_enabled';
//   static const String appLockType = 'app_lock_type'; // pin, biometric
//   static const String autoLockTimeout = 'auto_lock_timeout';
//   static const String safetyNumbers = 'safety_numbers'; // Prefix: safety_number_{user_id}
  
//   // Notifications
//   static const String fcmToken = 'fcm_token';
//   static const String notificationSound = 'notification_sound';
//   static const String vibrationPattern = 'vibration_pattern';
//   static const String inAppNotifications = 'in_app_notifications';
//   static const String notificationBadge = 'notification_badge';
  
//   // Sync
//   static const String lastSync = 'last_sync';
//   static const String lastContactSync = 'last_contact_sync';
//   static const String lastMessageSync = 'last_message_sync';
//   static const String syncInProgress = 'sync_in_progress';
  
//   // Onboarding
//   static const String isFirstTime = 'is_first_time';
//   static const String hasCompletedOnboarding = 'has_completed_onboarding';
//   static const String hasSeenTutorial = 'has_seen_tutorial';
//   static const String onboardingStep = 'onboarding_step';
  
//   // Cache
//   static const String cacheSize = 'cache_size';
//   static const String lastCacheClear = 'last_cache_clear';
  
//   // Backup
//   static const String lastBackup = 'last_backup';
//   static const String backupEnabled = 'backup_enabled';
//   static const String backupFrequency = 'backup_frequency';
//   static const String backupLocation = 'backup_location';
  
//   // Network
//   static const String lastNetworkCheck = 'last_network_check';
//   static const String networkQuality = 'network_quality';
  
//   // Analytics
//   static const String analyticsEnabled = 'analytics_enabled';
//   static const String crashReportsEnabled = 'crash_reports_enabled';
  
//   // Developer
//   static const String debugMode = 'debug_mode';
//   static const String apiEnvironment = 'api_environment';
//   static const String showPerformanceOverlay = 'show_performance_overlay';
  
//   // App State
//   static const String appVersion = 'app_version';
//   static const String lastUpdateCheck = 'last_update_check';
//   static const String deviceId = 'device_id';
//   static const String installationId = 'installation_id';
  
//   // ========================================
//   // HELPER METHODS
//   // ========================================
  
//   /// Générer une clé pour les messages d'une conversation
//   static String messagesKey(int conversationId) => '${messages}_$conversationId';
  
//   /// Générer une clé pour les brouillons d'une conversation
//   static String draftsKey(int conversationId) => '${drafts}_$conversationId';
  
//   /// Générer une clé pour les membres d'un groupe
//   static String groupMembersKey(int groupId) => '${groupMembers}_$groupId';
  
//   /// Générer une clé pour le safety number d'un utilisateur
//   static String safetyNumberKey(int userId) => '${safetyNumbers}_$userId';
  
//   /// Vérifier si une clé est sensible (doit être dans SecureStorage)
//   static bool isSensitiveKey(String key) {
//     return [
//       authToken,
//       refreshToken,
//       privateKey,
//       publicKey,
//       localPin,
//       encryptionKey,
//     ].contains(key);
//   }
  
//   /// Liste de toutes les clés sensibles
//   static List<String> get sensitiveKeys => [
//     authToken,
//     refreshToken,
//     privateKey,
//     publicKey,
//     localPin,
//     biometricEnabled,
//     encryptionKey,
//   ];
  
//   /// Liste de toutes les clés de cache à nettoyer
//   static List<String> get cacheKeys => [
//     mediaCache,
//     downloadedMedia,
//     authTokenCache,
//   ];
  
//   /// Liste de toutes les clés de conversation
//   static List<String> get conversationKeys => [
//     conversations,
//     archivedConversations,
//     mutedConversations,
//     pinnedConversations,
//     deletedMessages,
//   ];
  
//   /// Liste de toutes les clés de contacts
//   static List<String> get contactKeys => [
//     contacts,
//     blockedContacts,
//     favoriteContacts,
//     recentContacts,
//     syncedContacts,
//   ];
  
//   /// Liste de toutes les clés de paramètres
//   static List<String> get settingsKeys => [
//     language,
//     themeMode,
//     fontSize,
//     notificationsEnabled,
//     soundEnabled,
//     vibrationEnabled,
//     messagePreview,
//     readReceipts,
//     typingIndicators,
//     autoDownloadImages,
//     autoDownloadVideos,
//     autoDownloadAudios,
//     autoDownloadDocuments,
//     wifiOnly,
//   ];
  
//   /// Liste de toutes les clés de confidentialité
//   static List<String> get privacyKeys => [
//     lastSeenPrivacy,
//     profilePhotoPrivacy,
//     statusPrivacy,
//     screenshotSecurity,
//     incognitoKeyboard,   
//   ];
  
//   /// Liste de toutes les clés de sécurité
//   static List<String> get securityKeys => [
//     appLockEnabled,
//     appLockType,
//     autoLockTimeout,
//   ];
// }
