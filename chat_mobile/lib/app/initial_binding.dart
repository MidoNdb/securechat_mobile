// lib/app/initial_binding.dart

import 'package:chat_mobile/modules/chat/controllers/main_shell_controller.dart';
import 'package:get/get.dart';
import '../modules/chat/controllers/messages_controller.dart';
import '../modules/chat/controllers/profile_controller.dart';
import '../modules/chat/controllers/contacts_controller.dart';

class InitialBinding extends Bindings {
  @override
  void dependencies() {
    // Controllers avec fenix (réutilisables après delete)
    Get.lazyPut<MessagesController>(
      () => MessagesController(), 
      fenix: true,
    );
    
    Get.lazyPut<ProfileController>(
      () => ProfileController(), 
      fenix: true,
    );
    
    Get.lazyPut<ContactsController>(
      () => ContactsController(), 
      fenix: true,
    );
    Get.lazyPut<MainShellController>(
      () => MainShellController(),
      fenix: true);
  }
  
}



// import 'package:chat_mobile/modules/chat/controllers/contacts_controller.dart';
// import 'package:chat_mobile/modules/chat/controllers/messages_controller.dart';
// import 'package:chat_mobile/modules/chat/controllers/profile_controller.dart';
// import 'package:get/get.dart';
// import '../data/services/storage_service.dart';
// import '../data/services/biometric_service.dart';
// import '../data/services/websocket_service.dart';
// import '../data/services/message_service.dart';



// class InitialBinding extends Bindings {
//   @override
//   void dependencies() {
//     // --- SERVICES (Permanents) ---
//     Get.put(WebSocketService(), permanent: true);
//     Get.put(MessageService(), permanent: true);
//     Get.lazyPut<MessagesController>(() => MessagesController(), fenix: true);
//     Get.lazyPut<ProfileController>(() => ProfileController(), fenix: true);
//     Get.lazyPut<ContactsController>(() => ContactsController(), fenix: true);
//   }
// }