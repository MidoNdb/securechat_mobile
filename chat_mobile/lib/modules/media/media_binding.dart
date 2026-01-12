// lib/modules/media/binding.dart
import 'package:get/get.dart';
import 'controllers/media_controller.dart';

class MediaBinding extends Bindings {
  @override
  void dependencies() {
    // ✅ fenix: true - Nouveau controller pour chaque média
    // Get.lazyPut<MediaController>(
    //   () => MediaController(),
    //   fenix: true, // Nouveau à chaque ouverture de média
    // );
  }
}