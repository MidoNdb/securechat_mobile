// lib/core/shared/environment.dart

enum Environment {
  LOCAL,
  STAGING,
  PRODUCTION,
}

class AppEnvironment {
  static const Environment current = Environment.LOCAL;

  // ==================== BASE URLs ====================
 
  static String get baseUrl {
    switch (current) {
      case Environment.LOCAL:
        return 'http://10.55.122.64:8000'; // Android Emulator 10.0.2.2 → localhost→ 10.154.160.64
      case Environment.STAGING:
        return 'https://staging.securechat.mr';
      case Environment.PRODUCTION:
        return 'https://api.securechat.mr';
    }
  }

  static String get wsUrl {
    switch (current) {
      case Environment.LOCAL:
        return 'ws://10.55.122.64:8000'; // ⚠️ Pas de /ws/chat/ ici 
      case Environment.STAGING:
        return 'wss://staging.securechat.mr';
      case Environment.PRODUCTION:
        return 'wss://api.securechat.mr';
    }
  }

  // ==================== CONFIGURATION ====================

  static String get name {
    switch (current) {
      case Environment.LOCAL:
        return 'LOCAL';
      case Environment.STAGING:
        return 'STAGING';
      case Environment.PRODUCTION:
        return 'PRODUCTION';
    }
  }

  static bool get enableLogs => current != Environment.PRODUCTION;
  static bool get isDebugMode => current == Environment.LOCAL;
  static bool get isProduction => current == Environment.PRODUCTION;

  static int get apiTimeout {
    switch (current) {
      case Environment.LOCAL:
        return 60;
      default:
        return 30;
    }
  }

  // ==================== ENDPOINTS PATHS ====================

  static const String wsPath = '/ws/chat/';
  
  // ==================== HELPERS ====================

  static String get fullWsUrl => '$wsUrl$wsPath';
}