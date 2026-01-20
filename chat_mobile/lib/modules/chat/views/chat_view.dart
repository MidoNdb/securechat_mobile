// lib/modules/chat/views/chat_view.dart

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/chat_controller.dart';
import '../widgets/message_bubble.dart';
import '../widgets/message_input.dart';
import '../../../core/widgets/loading_indicator.dart';

class ChatView extends GetView<ChatController> {
  const ChatView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: _buildAppBar(),
      body: Column(
        children: [
          Expanded(child: _buildMessagesList()),
          Obx(() => MessageInput(
                controller: controller.messageController,
                onSend: controller.sendMessage,
                isSending: controller.isSendingMessage.value,
              )),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    final displayName = controller.conversation.name ?? 'Conversation';

    return AppBar(
      backgroundColor: const Color(0xFF667eea),
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: Colors.white),
        onPressed: () => Get.back(),
      ),
      title: Row(
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: Colors.white.withOpacity(0.3),
            child: Text(
              _getInitial(displayName),
              style: const TextStyle(color: Colors.white, fontSize: 18),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  displayName,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                if (controller.conversation.isGroup)
                  Text(
                    '${controller.conversation.participants.length} participants',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.8),
                      fontSize: 12,
                    ),
                  )
                else
                  Text(
                    'En ligne',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.8),
                      fontSize: 12,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.videocam, color: Colors.white),
          onPressed: () => print('Video call'),
        ),
        IconButton(
          icon: const Icon(Icons.call, color: Colors.white),
          onPressed: () => print('Audio call'),
        ),
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert, color: Colors.white),
          onSelected: (value) {
            switch (value) {
              case 'info':
                print('Show conversation info');
                break;
              case 'mute':
                print('Mute conversation');
                break;
              case 'clear':
                print('Clear messages');
                break;
            }
          },
          itemBuilder: (context) => [
            const PopupMenuItem(
              value: 'info',
              child: Row(
                children: [
                  Icon(Icons.info_outline),
                  SizedBox(width: 12),
                  Text('Info'),
                ],
              ),
            ),
            const PopupMenuItem(
              value: 'mute',
              child: Row(
                children: [
                  Icon(Icons.notifications_off_outlined),
                  SizedBox(width: 12),
                  Text('Désactiver'),
                ],
              ),
            ),
            const PopupMenuItem(
              value: 'clear',
              child: Row(
                children: [
                  Icon(Icons.delete_outline),
                  SizedBox(width: 12),
                  Text('Effacer'),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildMessagesList() {
    return Obx(() {
      if (controller.isLoading.value && controller.messages.isEmpty) {
        return const Center(child: LoadingIndicator());
      }

      if (controller.messages.isEmpty) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey[300]),
              const SizedBox(height: 16),
              Text(
                'Aucun message',
                style: TextStyle(fontSize: 16, color: Colors.grey[600]),
              ),
              const SizedBox(height: 8),
              Text(
                'Envoyez le premier message',
                style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              ),
            ],
          ),
        );
      }

      return NotificationListener<ScrollNotification>(
        onNotification: (notification) {
          if (notification is ScrollEndNotification) {
            if (controller.scrollController.position.pixels == 0) {
              controller.onLoadMore();
            }
          }
          return false;
        },
        child: ListView.builder(
          controller: controller.scrollController,
          padding: const EdgeInsets.symmetric(vertical: 16),
          itemCount: controller.messages.length + 
                     (controller.isLoadingMore.value ? 1 : 0),
          itemBuilder: (context, index) {
            if (controller.isLoadingMore.value && index == 0) {
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: LoadingIndicator(),
                ),
              );
            }

            final messageIndex = controller.isLoadingMore.value 
                ? index - 1 
                : index;
            final message = controller.messages[messageIndex];
            
            // ✅ CORRIGÉ: String == String
            final isMe = message.senderId == controller.currentUserId;

            return MessageBubble(
              message: message,
              isMe: isMe,
              showAvatar: controller.conversation.isGroup,
              senderName: isMe ? null : message.senderName,
            );
          },
        ),
      );
    });
  }

  String _getInitial(String name) {
    if (name.isEmpty) return '?';
    
    // Si c'est un numéro de téléphone, prend le premier chiffre
    if (RegExp(r'^\+?\d').hasMatch(name)) {
      return name.replaceAll(RegExp(r'[^\d]'), '')[0];
    }
    
    // Sinon prend la première lettre
    return name[0].toUpperCase();
  }
}







// // lib/modules/chat/views/chat_view.dart

// import 'package:flutter/material.dart';
// import 'package:get/get.dart';
// import '../controllers/chat_controller.dart';
// import '../widgets/message_bubble.dart';
// import '../widgets/message_input.dart';
// import '../../../core/widgets/loading_indicator.dart';

// class ChatView extends GetView<ChatController> {
//   const ChatView({Key? key}) : super(key: key);

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       backgroundColor: Colors.white,
//       appBar: _buildAppBar(),
//       body: Column(
//         children: [
//           Expanded(child: _buildMessagesList()),
//           Obx(() => MessageInput(
//                 controller: controller.messageController,
//                 onSend: controller.sendMessage,
//                 isSending: controller.isSendingMessage.value,
//               )),
//         ],
//       ),
//     );
//   }

//   PreferredSizeWidget _buildAppBar() {
//     return AppBar(
//       backgroundColor: const Color(0xFF667eea),
//       elevation: 0,
//       leading: IconButton(
//         icon: const Icon(Icons.arrow_back, color: Colors.white),
//         onPressed: () => Get.back(),
//       ),
//       title: Row(
//         children: [
//           CircleAvatar(
//             radius: 20,
//             backgroundColor: Colors.white.withOpacity(0.3),
//             child: Text(
//               (controller.conversation.name ?? 'U')[0].toUpperCase(),
//               style: const TextStyle(color: Colors.white, fontSize: 18),
//             ),
//           ),
//           const SizedBox(width: 12),
//           Expanded(
//             child: Column(
//               crossAxisAlignment: CrossAxisAlignment.start,
//               children: [
//                 Text(
//                   controller.conversation.name ?? 'Conversation',
//                   style: const TextStyle(
//                     color: Colors.white,
//                     fontSize: 16,
//                     fontWeight: FontWeight.w600,
//                   ),
//                 ),
//                 if (controller.conversation.isGroup)
//                   Text(
//                     '${controller.conversation.participants.length} participants',
//                     style: TextStyle(
//                       color: Colors.white.withOpacity(0.8),
//                       fontSize: 12,
//                     ),
//                   ),
//               ],
//             ),
//           ),
//         ],
//       ),
//       actions: [
//         IconButton(
//           icon: const Icon(Icons.more_vert, color: Colors.white),
//           onPressed: () {},
//         ),
//       ],
//     );
//   }

//   Widget _buildMessagesList() {
//     return Obx(() {
//       if (controller.isLoading.value && controller.messages.isEmpty) {
//         return const Center(child: LoadingIndicator());
//       }

//       if (controller.messages.isEmpty) {
//         return Center(
//           child: Column(
//             mainAxisAlignment: MainAxisAlignment.center,
//             children: [
//               Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey[300]),
//               const SizedBox(height: 16),
//               Text(
//                 'Aucun message',
//                 style: TextStyle(fontSize: 16, color: Colors.grey[600]),
//               ),
//               const SizedBox(height: 8),
//               Text(
//                 'Envoyez le premier message',
//                 style: TextStyle(fontSize: 14, color: Colors.grey[500]),
//               ),
//             ],
//           ),
//         );
//       }

//       return NotificationListener<ScrollNotification>(
//         onNotification: (notification) {
//           if (notification is ScrollEndNotification) {
//             if (controller.scrollController.position.pixels == 0) {
//               controller.onLoadMore();
//             }
//           }
//           return false;
//         },
//         child: ListView.builder(
//           controller: controller.scrollController,
//           padding: const EdgeInsets.symmetric(vertical: 16),
//           itemCount: controller.messages.length + 
//                      (controller.isLoadingMore.value ? 1 : 0),
//           itemBuilder: (context, index) {
//             if (controller.isLoadingMore.value && index == 0) {
//               return const Center(
//                 child: Padding(
//                   padding: EdgeInsets.all(16),
//                   child: LoadingIndicator(),
//                 ),
//               );
//             }

//             final messageIndex = controller.isLoadingMore.value 
//                 ? index - 1 
//                 : index;
//             final message = controller.messages[messageIndex];
//             final isMe = message.senderId == (controller.currentUserId ?? 0); // ✅ CORRIGÉ

//             return MessageBubble(
//               message: message,
//               isMe: isMe,
//               showAvatar: controller.conversation.isGroup,
//               senderName: isMe ? null : message.senderName,
//             );
//           },
//         ),
//       );
//     });
//   }
// }