// lib/modules/chat/widgets/conversation_card.dart

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../data/models/conversation.dart';
import '../../../data/models/message.dart';

class ConversationCard extends StatelessWidget {
  final Conversation conversation;
  final VoidCallback onTap;
  final int? currentUserId;

  const ConversationCard({
    Key? key,
    required this.conversation,
    required this.onTap,
    this.currentUserId,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
   final displayName = currentUserId != null
      ? conversation.displayName(currentUserId!)
      : conversation.name ?? 'Conversation';

  return InkWell(
    onTap: onTap,
    child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(color: Colors.grey[200]!, width: 1),
          ),
        ),
        child: Row(
          children: [
            _buildAvatar(displayName),
            const SizedBox(width: 12),
            Expanded(child: _buildInfo(displayName)),
          ],
        ),
      ),
    );
  }

  Widget _buildAvatar(String displayName) {
    return CircleAvatar(
      radius: 28,
      backgroundColor: const Color(0xFF667eea),
      child: Text(
        displayName[0].toUpperCase(),
        style: const TextStyle(
          color: Colors.white,
          fontSize: 24,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _buildInfo(String displayName) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                displayName,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Text(
              _formatTime(conversation.lastMessageAt),
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            if (conversation.lastMessage?.status != null)
              _buildMessageStatus(conversation.lastMessage!.status!),
            const Icon(Icons.lock, size: 12, color: Colors.green),
            const SizedBox(width: 4),
            Expanded(
              child: Text(
                _getLastMessagePreview(),
                style: TextStyle(fontSize: 14, color: Colors.grey[700]),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (conversation.unreadCount > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF667eea),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${conversation.unreadCount}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }

  Widget _buildMessageStatus(String status) {
    IconData icon;
    Color color;

    switch (status) {
      case 'sent':
        icon = Icons.check;
        color = Colors.grey;
        break;
      case 'delivered':
        icon = Icons.done_all;
        color = Colors.grey;
        break;
      case 'read':
        icon = Icons.done_all;
        color = const Color(0xFF667eea);
        break;
      default:
        icon = Icons.access_time;
        color = Colors.grey;
    }

    return Padding(
      padding: const EdgeInsets.only(right: 4),
      child: Icon(icon, size: 14, color: color),
    );
  }

  String _getLastMessagePreview() {
    if (conversation.lastMessage == null) return 'Aucun message';

    final message = conversation.lastMessage!;

    if (conversation.isGroup && message.senderName != null) {
      return '${message.senderName}: ${_getMessageContent(message)}';
    }

    return _getMessageContent(message);
  }

  String _getMessageContent(Message message) {
    switch (message.type) {
      case 'text':
        return message.content ?? '';
      case 'image':
        return '📷 Photo';
      case 'video':
        return '🎥 Vidéo';
      case 'audio':
        return '🎵 Audio';
      case 'document':
        return '📄 Document';
      default:
        return 'Message';
    }
  }

  String _formatTime(DateTime? dateTime) {
    if (dateTime == null) return '';

    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays == 0) {
      return DateFormat('HH:mm').format(dateTime);
    } else if (difference.inDays == 1) {
      return 'Hier';
    } else if (difference.inDays < 7) {
      return DateFormat('EEEE', 'fr_FR').format(dateTime);
    } else {
      return DateFormat('dd/MM/yy').format(dateTime);
    }
  }
}




// // lib/modules/chat/widgets/conversation_card.dart

// import 'package:chat_mobile/core/utils/validators.dart';
// import 'package:chat_mobile/data/models/message.dart';
// import 'package:flutter/material.dart';
// import 'package:intl/intl.dart';
// import '../../../data/models/conversation.dart';
// import '../../../core/widgets/avatar_widget.dart';

// class ConversationCard extends StatelessWidget {
//   final Conversation conversation;
//   final VoidCallback onTap;

//   const ConversationCard({
//     Key? key,
//     required this.conversation,
//     required this.onTap,
//   }) : super(key: key);

//   @override
//   Widget build(BuildContext context) {
//     return InkWell(
//       onTap: onTap,
//       child: Container(
//         padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
//         decoration: BoxDecoration(
//           border: Border(
//             bottom: BorderSide(
//               color: Colors.grey[200]!,
//               width: 1,
//             ),
//           ),
//         ),
//         child: Row(
//           children: [
//             _buildAvatar(),
//             const SizedBox(width: 12),
//             Expanded(
//               child: _buildInfo(),
//             ),
//           ],
//         ),
//       ),
//     );
//   }

//   Widget _buildAvatar() {
//     return Stack(
//       children: [
//         AvatarWidget(
//           name: conversation.name ?? '',
//           imageUrl: conversation.avatar,
//           size: 56,
//           isGroup: conversation.isGroup,
//         ),
//         if (conversation.isOnline ?? false)
//           Positioned(
//             bottom: 2,
//             right: 2,
//             child: Container(
//               width: 14,
//               height: 14,
//               decoration: BoxDecoration(
//                 color: Colors.green,
//                 shape: BoxShape.circle,
//                 border: Border.all(
//                   color: Colors.white,
//                   width: 2,
//                 ),
//               ),
//             ),
//           ),
//       ],
//     );
//   }

//   Widget _buildInfo() {
//     return Column(
//       crossAxisAlignment: CrossAxisAlignment.start,
//       children: [
//         Row(
//           mainAxisAlignment: MainAxisAlignment.spaceBetween,
//           children: [
//             Expanded(
//               child: Text(
//                 conversation.name ?? 'Inconnu',
//                 style: const TextStyle(
//                   fontSize: 16,
//                   fontWeight: FontWeight.w600,
//                   color: Colors.black,
//                 ),
//                 maxLines: 1,
//                 overflow: TextOverflow.ellipsis,
//               ),
//             ),
//             Text(
//               _formatTime(conversation.lastMessageAt),
//               style: TextStyle(
//                 fontSize: 12,
//                 color: Colors.grey[600],
//               ),
//             ),
//           ],
//         ),
//         const SizedBox(height: 4),
//         Row(
//           children: [
//             // ✅ CORRECTION: Vérifier si status existe
//             if (conversation.lastMessage?.status != null)
//               _buildMessageStatus(conversation.lastMessage!.status!),
//             const Icon(
//               Icons.lock,
//               size: 12,
//               color: Colors.green,
//             ),
//             const SizedBox(width: 4),
//             Expanded(
//               child: Text(
//                 _getLastMessagePreview(),
//                 style: TextStyle(
//                   fontSize: 14,
//                   color: Colors.grey[700],
//                 ),
//                 maxLines: 1,
//                 overflow: TextOverflow.ellipsis,
//               ),
//             ),
//             if ((conversation.unreadCount ?? 0) > 0)
//               Container(
//                 padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
//                 decoration: BoxDecoration(
//                   color: const Color(0xFF667eea),
//                   borderRadius: BorderRadius.circular(12),
//                 ),
//                 child: Text(
//                   '${conversation.unreadCount}',
//                   style: const TextStyle(
//                     color: Colors.white,
//                     fontSize: 12,
//                     fontWeight: FontWeight.bold,
//                   ),
//                 ),
//               ),
//           ],
//         ),
//       ],
//     );
//   }

//   Widget _buildMessageStatus(String status) {
//     IconData icon;
//     Color color;

//     switch (status) {
//       case 'sent':
//         icon = Icons.check;
//         color = Colors.grey;
//         break;
//       case 'delivered':
//         icon = Icons.done_all;
//         color = Colors.grey;
//         break;
//       case 'read':
//         icon = Icons.done_all;
//         color = const Color(0xFF667eea);
//         break;
//       default:
//         icon = Icons.access_time;
//         color = Colors.grey;
//     }

//     return Padding(
//       padding: const EdgeInsets.only(right: 4),
//       child: Icon(
//         icon,
//         size: 14,
//         color: color,
//       ),
//     );
//   }

//   String _getLastMessagePreview() {
//     if (conversation.lastMessage == null) {
//       return 'Aucun message';
//     }

//     final message = conversation.lastMessage!;

//     if (conversation.isGroup && message.senderName != null) {
//       return '${message.senderName}: ${_getMessageContent(message)}';
//     }

//     return _getMessageContent(message);
//   }

//   String _getMessageContent(Message message) {  // ✅ TYPE EXPLICITE
//     switch (message.type) {
//       case 'text':
//         return message.content ?? '';
//       case 'image':
//         return '📷 Photo';
//       case 'video':
//         return '🎥 Vidéo';
//       case 'audio':
//         return '🎵 Audio';
//       case 'document':
//         return '📄 Document';
//       default:
//         return 'Message';
//     }
//   }

//   String _formatTime(DateTime? dateTime) {
//     if (dateTime == null) return '';

//     final now = DateTime.now();
//     final difference = now.difference(dateTime);

//     if (difference.inDays == 0) {
//       return DateFormat('HH:mm').format(dateTime);
//     } else if (difference.inDays == 1) {
//       return 'Hier';
//     } else if (difference.inDays < 7) {
//       return DateFormat('EEEE', 'fr_FR').format(dateTime);
//     } else {
//       return DateFormat('dd/MM/yy').format(dateTime);
//     }
//   }
// }


// // // lib/modules/chat/widgets/conversation_card.dart

// // import 'package:chat_mobile/core/utils/validators.dart';
// // import 'package:flutter/material.dart';
// // import 'package:intl/intl.dart';
// // import '../../../data/models/conversation.dart';
// // import '../../../core/widgets/avatar_widget.dart';

// // class ConversationCard extends StatelessWidget {
// //   final Conversation conversation;
// //   final VoidCallback onTap;

// //   const ConversationCard({
// //     Key? key,
// //     required this.conversation,
// //     required this.onTap,
// //   }) : super(key: key);

// //   @override
// //   Widget build(BuildContext context) {
// //     return InkWell(
// //       onTap: onTap,
// //       child: Container(
// //         padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
// //         decoration: BoxDecoration(
// //           border: Border(
// //             bottom: BorderSide(
// //               color: Colors.grey[200]!,
// //               width: 1,
// //             ),
// //           ),
// //         ),
// //         child: Row(
// //           children: [
// //             _buildAvatar(),
// //             SizedBox(width: 12),
// //             Expanded(
// //               child: _buildInfo(),
// //             ),
// //           ],
// //         ),
// //       ),
// //     );
// //   }

// //   Widget _buildAvatar() {
// //     return Stack(
// //       children: [
// //         AvatarWidget(
// //           name: conversation.name ?? '',
// //           imageUrl: conversation.avatar,
// //           size: 56,
// //           isGroup: conversation.isGroup,
// //         ),
// //         if (conversation.isOnline ?? false)
// //           Positioned(
// //             bottom: 2,
// //             right: 2,
// //             child: Container(
// //               width: 14,
// //               height: 14,
// //               decoration: BoxDecoration(
// //                 color: Colors.green,
// //                 shape: BoxShape.circle,
// //                 border: Border.all(
// //                   color: Colors.white,
// //                   width: 2,
// //                 ),
// //               ),
// //             ),
// //           ),
// //       ],
// //     );
// //   }

// //   Widget _buildInfo() {
// //     return Column(
// //       crossAxisAlignment: CrossAxisAlignment.start,
// //       children: [
// //         Row(
// //           mainAxisAlignment: MainAxisAlignment.spaceBetween,
// //           children: [
// //             Expanded(
// //               child: Text(
// //                 conversation.name ?? 'Inconnu',
// //                 style: TextStyle(
// //                   fontSize: 16,
// //                   fontWeight: FontWeight.w600,
// //                   color: Colors.black,
// //                 ),
// //                 maxLines: 1,
// //                 overflow: TextOverflow.ellipsis,
// //               ),
// //             ),
// //             Text(
// //               _formatTime(conversation.lastMessageAt),
// //               style: TextStyle(
// //                 fontSize: 12,
// //                 color: Colors.grey[600],
// //               ),
// //             ),
// //           ],
// //         ),
// //         SizedBox(height: 4),
// //         Row(
// //           children: [
// //             if (conversation.lastMessage?.status != null)
// //               _buildMessageStatus(conversation.lastMessage!.status!.toString()),
// //             Icon(
// //               Icons.lock,
// //               size: 12,
// //               color: Colors.green,
// //             ),
// //             SizedBox(width: 4),
// //             Expanded(
// //               child: Text(
// //                 _getLastMessagePreview(),
// //                 style: TextStyle(
// //                   fontSize: 14,
// //                   color: Colors.grey[700],
// //                 ),
// //                 maxLines: 1,
// //                 overflow: TextOverflow.ellipsis,
// //               ),
// //             ),
// //             if ((conversation.unreadCount ?? 0) > 0)
// //               Container(
// //                 padding: EdgeInsets.symmetric(horizontal: 8, vertical: 3),
// //                 decoration: BoxDecoration(
// //                   color: Color(0xFF667eea),
// //                   borderRadius: BorderRadius.circular(12),
// //                 ),
// //                 child: Text(
// //                   '${conversation.unreadCount}',
// //                   style: TextStyle(
// //                     color: Colors.white,
// //                     fontSize: 12,
// //                     fontWeight: FontWeight.bold,
// //                   ),
// //                 ),
// //               ),
// //           ],
// //         ),
// //       ],
// //     );
// //   }

// //   Widget _buildMessageStatus(String status) {
// //     IconData icon;
// //     Color color;

// //     switch (status) {
// //       case 'sent':
// //         icon = Icons.check;
// //         color = Colors.grey;
// //         break;
// //       case 'delivered':
// //         icon = Icons.done_all;
// //         color = Colors.grey;
// //         break;
// //       case 'read':
// //         icon = Icons.done_all;
// //         color = Color(0xFF667eea);
// //         break;
// //       default:
// //         icon = Icons.access_time;
// //         color = Colors.grey;
// //     }

// //     return Padding(
// //       padding: EdgeInsets.only(right: 4),
// //       child: Icon(
// //         icon,
// //         size: 14,
// //         color: color,
// //       ),
// //     );
// //   }

// //   String _getLastMessagePreview() {
// //     if (conversation.lastMessage == null) {
// //       return 'Aucun message';
// //     }

// //     final message = conversation.lastMessage!;

// //     if (conversation.isGroup && message.senderName != null) {
// //       return '${message.senderName}: ${_getMessageContent(message)}';
// //     }

// //     return _getMessageContent(message);
// //   }

// //   String _getMessageContent(message) {
// //     switch (message.type) {
// //       case 'text':
// //         return message.content ?? '';
// //       case 'image':
// //         return '📷 Photo';
// //       case 'video':
// //         return '🎥 Vidéo';
// //       case 'audio':
// //         return '🎵 Audio';
// //       case 'document':
// //         return '📄 Document';
// //       default:
// //         return 'Message';
// //     }
// //   }

// //   String _formatTime(DateTime? dateTime) {
// //     if (dateTime == null) return '';

// //     final now = DateTime.now();
// //     final difference = now.difference(dateTime);

// //     if (difference.inDays == 0) {
// //       // Aujourd'hui - afficher l'heure
// //       return DateFormat('HH:mm').format(dateTime);
// //     } else if (difference.inDays == 1) {
// //       // Hier
// //       return 'Hier';
// //     } else if (difference.inDays < 7) {
// //       // Cette semaine - afficher le jour
// //       return DateFormat('EEEE', 'fr_FR').format(dateTime);
// //     } else {
// //       // Plus ancien - afficher la date
// //       return DateFormat('dd/MM/yy').format(dateTime);
// //     }
// //   }
// // }