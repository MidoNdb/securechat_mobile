// lib/data/api/api_endpoints.dart

import '../../core/shared/environment.dart';

class ApiEndpoints {
  static String get baseUrl => AppEnvironment.baseUrl;
  static String get wsUrl => AppEnvironment.wsUrl;

  // AUTH
  static const String register = '/api/auth/register/';
  static const String login = '/api/auth/login/';
  static const String logout = '/api/auth/logout/';
  static const String me = '/api/auth/me/';
  static const String updateKeys = '/api/auth/update-keys/';

  // CONTACTS
  static const String contacts = '/api/contacts/';
  static const String searchContacts = '/api/contacts/search/';
  
  // CONVERSATIONS
  static const String conversations = '/api/conversations/';
  static const String createConversation = '/api/conversations/';
  
  // MESSAGES
  static const String messages = '/api/messages/';
  static const String sendMessage = '/api/messages/'; 
  static const String markAsRead = '/api/messages/mark-read/';
  static String getMessagesByConversation(String conversationId) {
    return '/api/messages/conversation/$conversationId/';  // ✅ Correspond au backend
  }
  

  
  // HELPERS
  static String getConversationDetail(int id) => '/api/conversations/$id/';
  static String getUserPublicKeys(int userId) => '/api/users/$userId/public-keys/';
}







// // lib/data/api/api_endpoints.dart

// import '../../core/shared/environment.dart';

// class ApiEndpoints {
//   // ========================================
//   // BASE URL (utilise environment.dart)
//   // ========================================
//   static String get baseUrl => AppEnvironment.baseUrl;
//   static String get wsUrl => AppEnvironment.wsUrl;
  
//   // ========================================
//   // AUTH (PUBLIC - pas de token)
//   // ========================================
//   static const String register = '/api/auth/register/';
//   static const String login = '/api/auth/login/';
//   static const String updateKeys = '/api/auth/update-keys/'; 

//   static const String verifySms = '/api/auth/verify-sms/';
//   static const String resendSms = '/api/auth/resend-sms/';
//   static const String refreshToken = '/api/auth/refresh/';
//   static const String forgotPassword = '/api/auth/forgot-password/';
//   static const String resetPassword = '/api/auth/reset-password/';

//   static const String getBackup = '/api/auth/backup/';
  
//     static const String me = '/api/auth/me/';
//   static const String logout = '/api/auth/logout/';
//   static const String updateProfile = '/api/auth/profile/';
//   static const String changePassword = '/api/auth/change-password/';
//   static const String deleteAccount = '/api/auth/delete-account/';
  
//   // Sessions & Devices
//   static const String sessions = '/api/auth/sessions/';
//   static const String devices = '/api/auth/devices/';
//   static const String deactivateDevice = '/api/auth/devices/deactivate/';
//   static const String logoutAll = '/api/auth/logout-all/';
  
//   // CONTACTS
//   static const String contacts = '/api/contacts/';
//   static const String searchContacts = '/api/contacts/search/';
//   static const String addContact = '/api/contacts/add/';
//   static const String removeContact = '/api/contacts/remove/';
//   static const String blockContact = '/api/contacts/block/';
//   static const String unblockContact = '/api/contacts/unblock/';
//   static const String markContact = '/api/contacts/mark/';
//   static const String syncContacts = '/api/contacts/sync/';
//   static const String qrInfo = '/api/contacts/qr-info/';
//   static const String blockedContacts = '/api/contacts/blocked/';
//   static const String markedContacts = '/api/contacts/marked/';
  
//   // CONVERSATIONS
//   static const String conversations = '/api/conversations/';
//   static const String createConversation = '/api/conversations/';
//   static const String conversationDetail = '/api/conversations/'; // + {id}/
//   static const String deleteConversation = '/api/conversations/'; // + {id}/delete/
//   static const String archiveConversation = '/api/conversations/'; // + {id}/archive/
//   static const String unarchiveConversation = '/api/conversations/'; // + {id}/unarchive/
//   static const String muteConversation = '/api/conversations/'; // + {id}/mute/
//   static const String unmuteConversation = '/api/conversations/'; // + {id}/unmute/
//   static const String conversationParticipants = '/api/conversations/'; // + {id}/participants/
  
//   // MESSAGES
//   static const String messages = '/api/messages/';
//   static const String sendMessage = '/api/messages/send/';
//   static const String deleteMessage = '/api/messages/'; // + {id}/delete/
//   static const String markAsRead = '/api/messages/mark-read/';
//   static const String markAsDelivered = '/api/messages/mark-delivered/';
//   static const String messagesByConversation = '/api/messages/conversation/'; // + {conversation_id}/
//   static const String searchMessages = '/api/messages/search/';
//   static const String forwardMessage = '/api/messages/'; // + {id}/forward/
//   static const String editMessage = '/api/messages/'; // + {id}/edit/';
  
//   // GROUPS
//   static const String groups = '/api/groups/';
//   static const String createGroup = '/api/groups/create/';
//   static const String groupDetail = '/api/groups/'; // + {id}/
//   static const String updateGroup = '/api/groups/'; // + {id}/update/
//   static const String deleteGroup = '/api/groups/'; // + {id}/delete/
//   static const String leaveGroup = '/api/groups/'; // + {id}/leave/
//   static const String addGroupMember = '/api/groups/'; // + {id}/add-member/
//   static const String removeGroupMember = '/api/groups/'; // + {id}/remove-member/
//   static const String updateGroupAvatar = '/api/groups/'; // + {id}/avatar/
//   static const String promoteToAdmin = '/api/groups/'; // + {id}/promote/
//   static const String demoteFromAdmin = '/api/groups/'; // + {id}/demote/
  
//   // MEDIA
//   static const String uploadMedia = '/api/media/upload/';
//   static const String downloadMedia = '/api/media/download/'; // + {media_id}/
//   static const String deleteMedia = '/api/media/'; // + {id}/delete/
//   static const String mediaInfo = '/api/media/'; // + {id}/
  
//   // SECURITY
//   static const String safetyNumber = '/api/security/safety-number/';
//   static const String verifySafetyNumber = '/api/security/verify-safety-number/';
//   static const String generateKeys = '/api/security/generate-keys/';
//   static const String updatePublicKey = '/api/security/update-public-key/';
//   static const String getPublicKey = '/api/security/public-key/'; // + {user_id}/
//   // SECURITY
//   static const String publicKeyUser = '/api/users/'; // + {user_id}/public-keys/
  
//   // NOTIFICATIONS
//   static const String notifications = '/api/notifications/';
//   static const String markNotificationRead = '/api/notifications/'; // + {id}/read/
//   static const String markAllNotificationsRead = '/api/notifications/mark-all-read/';
//   static const String deleteNotification = '/api/notifications/'; // + {id}/delete/
//   static const String notificationSettings = '/api/notifications/settings/';
//   static const String updateFcmToken = '/api/notifications/fcm-token/';
  
//   // SETTINGS
//   static const String settings = '/api/settings/';
//   static const String privacySettings = '/api/settings/privacy/';
//   static const String notificationPreferences = '/api/settings/notifications/';
//   static const String chatSettings = '/api/settings/chat/';
//   static const String storageSettings = '/api/settings/storage/';
//   static const String clearCache = '/api/settings/clear-cache/';
  
//   // CALLS (si implémenté)
//   static const String calls = '/api/calls/';
//   static const String initiateCall = '/api/calls/initiate/';
//   static const String endCall = '/api/calls/'; // + {id}/end/
//   static const String callHistory = '/api/calls/history/';
//   static const String deleteCallHistory = '/api/calls/history/'; // + {id}/delete/
  
//   // STATUS (si implémenté)
//   static const String status = '/api/status/';
//   static const String createStatus = '/api/status/create/';
//   static const String deleteStatus = '/api/status/'; // + {id}/delete/
//   static const String viewStatus = '/api/status/'; // + {id}/view/
//   static const String statusViewers = '/api/status/'; // + {id}/viewers/
  
//   // ANALYTICS & LOGS
//   static const String reportIssue = '/api/support/report/';
//   static const String feedback = '/api/support/feedback/';
//   static const String appVersion = '/api/app/version/';
  
//   // HELPERS - Construction d'URLs dynamiques
  
//   // Conversation detail
//   static String getConversationDetail(int id) => '$conversationDetail$id/';
  
//   // Messages par conversation
//   static String getMessagesByConversation(int conversationId) => 
//       '$messagesByConversation$conversationId/';
  
//   // Group detail
//   static String getGroupDetail(int id) => '$groupDetail$id/';
  
//   // Add group member
//   static String getAddGroupMember(int groupId) => '$addGroupMember$groupId/add-member/';
  
//   // Remove group member
//   static String getRemoveGroupMember(int groupId) => '$removeGroupMember$groupId/remove-member/';
  
//   // Media download
//   static String getMediaDownload(int mediaId) => '$downloadMedia$mediaId/';
  
//   // Public key
//   static String getPublicKeyUrl(int userId) => '$getPublicKey$userId/';
  
//   // Delete message
//   static String getDeleteMessage(int messageId) => '$deleteMessage$messageId/delete/';
  
//   // Forward message
//   static String getForwardMessage(int messageId) => '$forwardMessage$messageId/forward/';
  
//   // Archive conversation
//   static String getArchiveConversation(int conversationId) => 
//       '$archiveConversation$conversationId/archive/';
  
//   // Mute conversation
//   static String getMuteConversation(int conversationId) => 
//       '$muteConversation$conversationId/mute/';
// }