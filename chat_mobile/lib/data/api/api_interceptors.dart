// TODO Implement this library.
// lib/data/api/api_interceptors.dart

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart' hide Response;
import '../services/secure_storage_service.dart';
import '../../core/shared/environment.dart';

// ========================================
// AUTH INTERCEPTOR
// ========================================
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    try {
      final storage = Get.find<SecureStorageService>();
      final token = await storage.getAccessToken();
      
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
        
        if (AppEnvironment.enableLogs) {
          print('🔑 Token ajouté à la requête');
        }
      }
    } catch (e) {
      if (AppEnvironment.enableLogs) {
        print('⚠️ AuthInterceptor: $e');
      }
    }
    
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      if (AppEnvironment.enableLogs) {
        print('🔄 Token expiré (401) - Déconnexion');
      }
      
      try {
        final storage = Get.find<SecureStorageService>();
        await storage.clearAuth();
        Get.offAllNamed('/login');
      } catch (e) {
        if (AppEnvironment.enableLogs) {
          print('❌ Erreur clearAuth: $e');
        }
      }
    }
    
    handler.next(err);
  }
}

// ========================================
// LOGGING INTERCEPTOR (SÉCURISÉ)
// ========================================
class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (AppEnvironment.enableLogs) {
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      print('📤 ${options.method} ${options.path}');
      
      // Masquer les données sensibles
      if (options.data != null) {
        final sanitized = _sanitizeData(options.data);
        print('📦 Data: $sanitized');
      }
      
      if (options.queryParameters.isNotEmpty) {
        print('🔍 Query: ${options.queryParameters}');
      }
      
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    }
    
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    if (AppEnvironment.enableLogs) {
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      print('📥 ${response.statusCode} ${response.requestOptions.path}');
      print('✅ Réponse reçue');
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    }
    
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (AppEnvironment.enableLogs) {
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      print('❌ ${err.response?.statusCode ?? "NO_STATUS"} ${err.requestOptions.path}');
      print('❌ Erreur: ${err.type}');
      if (err.response?.data != null) {
        print('❌ Message: ${err.response?.data}');
      }
      print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    }
    
    handler.next(err);
  }

  /// Masquer les données sensibles
  dynamic _sanitizeData(dynamic data) {
    if (data is Map<String, dynamic>) {
      final sanitized = Map<String, dynamic>.from(data);
      
      // Clés à masquer
      final sensitiveKeys = [
        'password',
        'public_key',
        'private_key',
        'encrypted_private_key',
        'client_encryption_salt',
        'token',
        'refresh_token',
        'access_token',
      ];
      
      sanitized.forEach((key, value) {
        if (sensitiveKeys.any((s) => key.toLowerCase().contains(s))) {
          if (value is String && value.length > 20) {
            sanitized[key] = '${value.substring(0, 10)}...${value.substring(value.length - 10)} (${value.length} chars)';
          } else {
            sanitized[key] = '***';
          }
        }
      });
      
      return sanitized;
    }
    
    return data;
  }
}

// ========================================
// ERROR INTERCEPTOR (MESSAGES CLAIRS)
// ========================================
class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    String title = 'Erreur';
    String message = 'Une erreur est survenue';
    
    if (err.response != null) {
      // Erreurs HTTP
      switch (err.response!.statusCode) {
        case 400:
          title = 'Données invalides';
          message = _extractMessage(err.response!.data) ?? 
                   'Vérifiez les informations saisies';
          break;
          
        case 401:
          title = 'Non autorisé';
          message = 'Session expirée. Reconnectez-vous';
          break;
          
        case 403:
          title = 'Accès refusé';
          message = 'Vous n\'avez pas les permissions nécessaires';
          break;
          
        case 404:
          title = 'Introuvable';
          message = 'La ressource demandée n\'existe pas';
          break;
          
        case 500:
          title = 'Erreur serveur';
          message = 'Le serveur a rencontré une erreur. Réessayez plus tard';
          break;
          
        default:
          title = 'Erreur ${err.response!.statusCode}';
          message = _extractMessage(err.response!.data) ?? 
                   'Une erreur inattendue s\'est produite';
      }
    } else {
      // Erreurs réseau
      switch (err.type) {
        case DioExceptionType.connectionTimeout:
          title = 'Délai dépassé';
          message = 'La connexion au serveur a pris trop de temps';
          break;
          
        case DioExceptionType.connectionError:
          title = 'Pas de connexion';
          message = 'Vérifiez votre connexion Internet et que le serveur est démarré';
          break;
          
        case DioExceptionType.badResponse:
          title = 'Réponse invalide';
          message = 'Le serveur a renvoyé une réponse invalide';
          break;
          
        default:
          title = 'Erreur réseau';
          message = 'Impossible de contacter le serveur';
      }
    }
    
    // Afficher le Snackbar (sauf pour 401 déjà géré)
    if (err.response?.statusCode != 401) {
      Get.snackbar(
        title,
        message,
        snackPosition: SnackPosition.BOTTOM,
        duration: const Duration(seconds: 4),
        backgroundColor: Get.theme.colorScheme.error.withOpacity(0.1),
        colorText: Get.theme.colorScheme.error,
        icon: Icon(Icons.error_outline, color: Get.theme.colorScheme.error),
        margin: const EdgeInsets.all(16),
        borderRadius: 12,
      );
    }
    
    handler.next(err);
  }

  /// Extraire le message d'erreur de la réponse
  String? _extractMessage(dynamic data) {
    if (data == null) return null;
    
    try {
      if (data is Map<String, dynamic>) {
        return data['error']?['message'] ??
               data['message'] ??
               data['detail'] ??
               data['msg'];
      } else if (data is String) {
        return data;
      }
    } catch (e) {
      return null;
    }
    
    return null;
  }
}





// // lib/data/api/api_interceptors.dart

// import 'package:dio/dio.dart';
// import 'package:get/get.dart' hide Response;
// import '../services/secure_storage_service.dart';

// class AuthInterceptor extends Interceptor {
//   final SecureStorageService _storage = Get.find<SecureStorageService>();

//   @override
//   void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
//     final token = await _storage.getAccessToken();
    
//     if (token != null) {
//       options.headers['Authorization'] = 'Bearer $token';
//       print('🔑 Token ajouté');
//     }
    
//     handler.next(options);
//   }
// }

// class LoggingInterceptor extends Interceptor {
//   @override
//   void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
//     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
//     print('📤 ${options.method} ${options.path}');
//     if (options.data != null) {
//       print('📦 Data: ${options.data}');
//     }
//     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
//     handler.next(options);
//   }

//   @override
//   void onResponse(Response response, ResponseInterceptorHandler handler) {
//     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
//     print('📥 ${response.statusCode} ${response.requestOptions.path}');
//     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
//     handler.next(response);
//   }

//   @override
//   void onError(DioException err, ErrorInterceptorHandler handler) {
//     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
//     print('❌ ${err.response?.statusCode} ${err.requestOptions.path}');
//     print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
//     handler.next(err);
//   }
// }

// class ErrorInterceptor extends Interceptor {
//   final SecureStorageService _storage = Get.find<SecureStorageService>();

//   @override
//   void onError(DioException err, ErrorInterceptorHandler handler) async {
//     if (err.response?.statusCode == 401) {
//       print('🔄 Token expiré - Déconnexion');
//       await _storage.clearAuth();
//       Get.offAllNamed('/login');
//     }
    
//     handler.next(err);
//   }
// }