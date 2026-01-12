// lib/data/models/participant.dart

class Participant {
  final int userId;
  final String displayName;
  final String? avatar;
  final String role;

  Participant({
    required this.userId,
    required this.displayName,
    this.avatar,
    required this.role,
  });

  factory Participant.fromJson(Map<String, dynamic> json) {
    // ✅ Gère plusieurs formats backend
    final userIdValue = json['user_id'] ?? json['user']?['id'];
    
    return Participant(
      userId: _parseInt(userIdValue),
      displayName: json['display_name']?.toString() ?? 
                   json['user']?['display_name']?.toString() ?? 
                   json['user']?['username']?.toString() ?? 
                   json['phone_number']?.toString() ??
                   'Utilisateur',
      avatar: json['avatar']?.toString() ?? json['user']?['avatar']?.toString(),
      role: json['role']?.toString() ?? 'member',
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
      'user_id': userId,
      'display_name': displayName,
      'avatar': avatar,
      'role': role,
    };
  }
}