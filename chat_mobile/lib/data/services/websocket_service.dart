// lib/data/services/websocket_service.dart

import 'dart:async';
import 'dart:convert';
import 'package:get/get.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/message.dart';
import 'secure_storage_service.dart';
import '../../core/shared/environment.dart';

class WebSocketService extends GetxService {
  final SecureStorageService _storage = Get.find<SecureStorageService>();
  
  WebSocketChannel? _channel;
  final _messageController = StreamController<Message>.broadcast();
  final _statusController = StreamController<Map<String, dynamic>>.broadcast();
  
  Timer? _heartbeatTimer;
  Timer? _reconnectTimer;
  bool _isConnected = false;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 5;
  static const Duration _heartbeatInterval = Duration(seconds: 30);

  Stream<Message> get messageStream => _messageController.stream;
  Stream<Map<String, dynamic>> get statusStream => _statusController.stream;
  bool get isConnected => _isConnected;

  Future<void> connect() async {
    if (_isConnected) return;

    try {
      final token = await _storage.getAccessToken();
      if (token == null || token.isEmpty) {
        print('❌ Token manquant');
        return;
      }

      final wsUrl = _buildSecureUrl(token);
      
      print('🔌 Connexion WSS...');

      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _isConnected = true;
      _reconnectAttempts = 0;

      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnection,
      );

      _startHeartbeat();
      print('✅ WSS connecté');
    } catch (e) {
      print('❌ Erreur WSS: $e');
      _isConnected = false;
      _scheduleReconnect();
    }
  }

  String _buildSecureUrl(String token) {
    String url = AppEnvironment.wsUrl;
    
    if (!url.startsWith('wss://') && !url.startsWith('ws://')) {
      url = 'wss://$url';
    }
    
    if (url.startsWith('ws://') && !url.startsWith('ws://localhost') && !url.startsWith('ws://127.0.0.1')) {
      url = url.replaceFirst('ws://', 'wss://');
      print('⚠️ Upgrade ws:// → wss://');
    }
    
    return '$url/ws/chat/?token=$token';
  }

  void _handleMessage(dynamic data) {
    try {
      final json = jsonDecode(data);
      
      switch (json['type']) {
        case 'new_message':
          _handleNewMessage(json['data']);
          break;
          
        case 'message_read':
          _statusController.add({
            'type': 'read',
            'message_id': json['data']['message_id'],
            'conversation_id': json['data']['conversation_id'],
            'read_by': json['data']['read_by'],
          });
          break;
          
        case 'message_delivered':
          _statusController.add({
            'type': 'delivered',
            'message_id': json['data']['message_id'],
            'conversation_id': json['data']['conversation_id'],
          });
          break;
          
        case 'user_online':
          _statusController.add({
            'type': 'online',
            'user_id': json['data']['user_id'],
            'is_online': true,
          });
          break;
          
        case 'user_offline':
          _statusController.add({
            'type': 'offline',
            'user_id': json['data']['user_id'],
            'is_online': false,
            'last_seen': json['data']['last_seen'],
          });
          break;
          
        case 'typing':
          _statusController.add({
            'type': 'typing',
            'conversation_id': json['data']['conversation_id'],
            'user_id': json['data']['user_id'],
            'is_typing': json['data']['is_typing'],
          });
          break;
          
        case 'pong':
          break;
          
        case 'error':
          print('❌ WSS: ${json['message']}');
          break;
          
        default:
          print('⚠️ Type inconnu: ${json['type']}');
      }
    } catch (e) {
      print('❌ Parse WSS: $e');
    }
  }

  void _handleNewMessage(Map<String, dynamic> data) {
    try {
      final message = Message.fromJson(data);
      _messageController.add(message);
    } catch (e) {
      print('❌ Message invalide: $e');
    }
  }

  void _handleError(error) {
    print('❌ WSS error: $error');
    _isConnected = false;
    _scheduleReconnect();
  }

  void _handleDisconnection() {
    print('🔌 WSS déconnecté');
    _isConnected = false;
    _stopHeartbeat();
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      print('❌ Max tentatives atteint');
      return;
    }

    _reconnectTimer?.cancel();
    
    final delay = Duration(seconds: _getReconnectDelay());
    _reconnectAttempts++;
    
    print('🔄 Reconnexion #$_reconnectAttempts dans ${delay.inSeconds}s');
    
    _reconnectTimer = Timer(delay, connect);
  }

  int _getReconnectDelay() {
    return [2, 5, 10, 30, 60][_reconnectAttempts.clamp(0, 4)];
  }

  void sendMessage(Map<String, dynamic> data) {
    if (!_isConnected || _channel == null) {
      print('⚠️ WSS non connecté');
      return;
    }

    try {
      _channel!.sink.add(jsonEncode(data));
    } catch (e) {
      print('❌ Envoi WSS: $e');
    }
  }

  void sendTyping(int conversationId, bool isTyping) {
    sendMessage({
      'type': 'typing',
      'conversation_id': conversationId,
      'is_typing': isTyping,
    });
  }

  void sendMessageRead(int messageId, int conversationId) {
    sendMessage({
      'type': 'message_read',
      'message_id': messageId,
      'conversation_id': conversationId,
    });
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(_heartbeatInterval, (timer) {
      if (_isConnected) {
        sendMessage({'type': 'ping'});
      }
    });
  }

  void _stopHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
  }

  void disconnect() {
    _isConnected = false;
    _reconnectAttempts = 0;
    _stopHeartbeat();
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    
    print('🔌 WSS déconnecté');
  }

  @override
  void onClose() {
    disconnect();
    _messageController.close();
    _statusController.close();
    super.onClose();
  }
}


























// // lib/data/services/websocket_service.dart

// import 'dart:async';
// import 'dart:convert';
// import 'package:get/get.dart';
// import 'package:web_socket_channel/web_socket_channel.dart';
// import '../models/message.dart';
// import 'secure_storage_service.dart';  // ✅ CHANGÉ
// import '../../core/shared/environment.dart';

// class WebSocketService extends GetxService {
//   final SecureStorageService _storage = Get.find<SecureStorageService>();  // ✅ CHANGÉ
  
//   WebSocketChannel? _channel;
//   final _messageController = StreamController<Message>.broadcast();
//   final _typingController = StreamController<Map<String, dynamic>>.broadcast();
//   final _statusController = StreamController<Map<String, dynamic>>.broadcast();
  
//   Timer? _heartbeatTimer;
//   Timer? _reconnectTimer;
//   bool _isConnected = false;
//   int _reconnectAttempts = 0;
//   static const int _maxReconnectAttempts = 5;

//   Stream<Message> get messageStream => _messageController.stream;
//   Stream<Map<String, dynamic>> get typingStream => _typingController.stream;
//   Stream<Map<String, dynamic>> get statusStream => _statusController.stream;
//   bool get isConnected => _isConnected;

//   Future<void> connect() async {
//     if (_isConnected) return;

//     try {
//       final token = await _storage.getAccessToken();  // ✅ CHANGÉ
//       if (token == null || token.isEmpty) {
//         print('❌ Token manquant pour WebSocket');
//         return;
//       }

//       final wsUrl = '${AppEnvironment.wsUrl}?token=$token';
      
//       print('🔌 Connexion WebSocket...');

//       _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
//       _isConnected = true;
//       _reconnectAttempts = 0;

//       _channel!.stream.listen(
//         _handleMessage,
//         onError: _handleError,
//         onDone: _handleDisconnection,
//       );

//       _startHeartbeat();
//       print('✅ WebSocket connecté');
//     } catch (e) {
//       print('❌ Erreur WebSocket: $e');
//       _isConnected = false;
//       _scheduleReconnect();
//     }
//   }

//   void _handleMessage(dynamic data) {
//     try {
//       final json = jsonDecode(data);
      
//       print('📨 WS: ${json['type']}');
      
//       switch (json['type']) {
//         case 'message':
//           final message = Message.fromJson(json['data']);
//           _messageController.add(message);
//           break;
          
//         case 'message_status':
//           _statusController.add({
//             'message_id': json['message_id'],
//             'status': json['status'],
//             'conversation_id': json['conversation_id'],
//           });
//           break;
          
//         case 'typing':
//           _typingController.add({
//             'conversation_id': json['conversation_id'],
//             'user_id': json['user_id'],
//             'is_typing': json['is_typing'],
//           });
//           break;
          
//         case 'user_status':
//           _statusController.add({
//             'user_id': json['user_id'],
//             'is_online': json['is_online'],
//             'last_seen': json['last_seen'],
//           });
//           break;
          
//         case 'pong':
//           print('💓 Heartbeat OK');
//           break;
          
//         case 'error':
//           print('❌ WS Error: ${json['message']}');
//           break;
          
//         default:
//           print('⚠️ WS type inconnu: ${json['type']}');
//       }
//     } catch (e) {
//       print('❌ Erreur traitement WS: $e');
//     }
//   }

//   void _handleError(error) {
//     print('❌ Erreur WebSocket: $error');
//     _isConnected = false;
//     _scheduleReconnect();
//   }

//   void _handleDisconnection() {
//     print('🔌 WebSocket déconnecté');
//     _isConnected = false;
//     _stopHeartbeat();
//     _scheduleReconnect();
//   }

//   void _scheduleReconnect() {
//     if (_reconnectAttempts >= _maxReconnectAttempts) {
//       print('❌ Max tentatives reconnexion atteint');
//       return;
//     }

//     _reconnectTimer?.cancel();
    
//     final delay = Duration(seconds: _getReconnectDelay());
//     _reconnectAttempts++;
    
//     print('🔄 Reconnexion ${_reconnectAttempts}/$_maxReconnectAttempts dans $delay');
    
//     _reconnectTimer = Timer(delay, () => connect());
//   }

//   int _getReconnectDelay() {
//     return [2, 5, 10, 30, 60][_reconnectAttempts.clamp(0, 4)];
//   }

//   void sendMessage(Map<String, dynamic> data) {
//     if (_isConnected && _channel != null) {
//       try {
//         _channel!.sink.add(jsonEncode(data));
//         print('📤 WS envoyé: ${data['type']}');
//       } catch (e) {
//         print('❌ Erreur envoi WS: $e');
//       }
//     } else {
//       print('⚠️ WebSocket non connecté');
//     }
//   }

//   void sendTypingIndicator(int conversationId, bool isTyping) {
//     sendMessage({
//       'type': 'typing',
//       'conversation_id': conversationId,
//       'is_typing': isTyping,
//     });
//   }

//   void sendMessageStatus(int messageId, String status) {
//     sendMessage({
//       'type': 'message_status',
//       'message_id': messageId,
//       'status': status,
//     });
//   }

//   void _startHeartbeat() {
//     _heartbeatTimer?.cancel();
//     _heartbeatTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
//       if (_isConnected) {
//         sendMessage({'type': 'ping'});
//       }
//     });
//   }

//   void _stopHeartbeat() {
//     _heartbeatTimer?.cancel();
//     _heartbeatTimer = null;
//   }

//   void disconnect() {
//     _isConnected = false;
//     _reconnectAttempts = 0;
//     _stopHeartbeat();
//     _reconnectTimer?.cancel();
//     _channel?.sink.close();
//     _channel = null;
    
//     print('🔌 WebSocket déconnecté manuellement');
//   }

//   @override
//   void onClose() {
//     disconnect();
//     _messageController.close();
//     _typingController.close();
//     _statusController.close();
//     super.onClose();
//   }
// }







