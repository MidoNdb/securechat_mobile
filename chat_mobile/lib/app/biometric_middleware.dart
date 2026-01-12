// // lib/app/middlewares/biometric_middleware.dart

// import 'package:chat_mobile/data/services/biometric_service.dart';
// import 'package:flutter/material.dart';
// import 'package:get/get.dart';

// class BiometricMiddleware extends GetMiddleware {
//   final BiometricService _biometric = Get.find<BiometricService>();
  
//   @override
//   int? get priority => 1;
  
//   @override
//   RouteSettings? redirect(String? route) {
//     // Appliquer uniquement sur HomePage
//     if (route == '/home') {
//       // Lancer authentification dans le prochain frame
//       WidgetsBinding.instance.addPostFrameCallback((_) async {
//         final authenticated = await _biometric.authenticate();
        
//         if (!authenticated) {
//           Get.back(); // Retour au login si échec
//           Get.snackbar(
//             '❌ Authentification échouée',
//             'Veuillez réessayer',
//             snackPosition: SnackPosition.BOTTOM,
//             backgroundColor: Colors.red,
//             colorText: Colors.white,
//           );
//         }
//       });
//     }
//     return null;
//   }
// }