  import 'package:chat_mobile/modules/chat/controllers/main_shell_controller.dart';
import 'package:get/get.dart';
class CallsController extends GetxController {
  final mainController = Get.find<MainShellController>();
  
  CallsController() {
    mainController.goToProfile(); // Va à l'onglet Profile
    mainController.goToContacts();
  }
  
  // Controller logic here
}