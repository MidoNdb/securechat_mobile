// lib/data/models/message.dart

class Message {
  final String id;  // ✅ UUID String
  final String conversationId;  // ✅ UUID String
  final int senderId;
  final String? senderName;
  final String? content;
  final String type;
  final String? status;
  final DateTime timestamp;
  final bool isRead;
  final bool isDelivered;
  final Map<String, dynamic>? encryptedContent;

  Message({
    required this.id,
    required this.conversationId,
    required this.senderId,
    this.senderName,
    this.content,
    required this.type,
    this.status,
    required this.timestamp,
    this.isRead = false,
    this.isDelivered = false,
    this.encryptedContent,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id']?.toString() ?? '',  // ✅ String
      conversationId: json['conversation_id']?.toString() ?? 
                     json['conversation']?.toString() ?? '',
      senderId: _parseInt(json['sender_id'] ?? json['from_user']),
      senderName: json['sender_name']?.toString(),
      content: json['content']?.toString(),
      type: json['type']?.toString() ?? 'text',
      status: json['status']?.toString(),
      timestamp: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : json['timestamp'] != null
              ? DateTime.parse(json['timestamp'])
              : DateTime.now(),
      isRead: json['is_read'] == true,
      isDelivered: json['is_delivered'] == true,
      encryptedContent: json['ciphertext'] != null
          ? {
              'ciphertext': json['ciphertext'],
              'nonce': json['nonce'],
              'auth_tag': json['auth_tag'],
              'signature': json['signature'],
            }
          : json['encrypted_content'] != null
              ? Map<String, dynamic>.from(json['encrypted_content'])
              : null,
    );
  }

  static int _parseInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'conversation_id': conversationId,
      'sender_id': senderId,
      'sender_name': senderName,
      'content': content,
      'type': type,
      'status': status,
      'timestamp': timestamp.toIso8601String(),
      'is_read': isRead,
      'is_delivered': isDelivered,
    };
  }

  Message copyWith({
    String? content,
    String? status,
    bool? isRead,
    bool? isDelivered,
  }) {
    return Message(
      id: id,
      conversationId: conversationId,
      senderId: senderId,
      senderName: senderName,
      content: content ?? this.content,
      type: type,
      status: status ?? this.status,
      timestamp: timestamp,
      isRead: isRead ?? this.isRead,
      isDelivered: isDelivered ?? this.isDelivered,
      encryptedContent: encryptedContent,
    );
  }
}