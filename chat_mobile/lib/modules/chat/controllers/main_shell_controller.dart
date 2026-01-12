// lib/modules/main/controllers/main_shell_controller.dart

import 'package:flutter/material.dart';
import 'package:get/get.dart';

class MainShellController extends GetxController {
  final currentIndex = 0.obs;
  
  // ✅ NavigatorKey pour chaque onglet
  final List<GlobalKey<NavigatorState>> navigatorKeys = [
    GlobalKey<NavigatorState>(),  // Messages (0)
    GlobalKey<NavigatorState>(),  // Contacts (1)
    GlobalKey<NavigatorState>(),  // Calls (2)
    GlobalKey<NavigatorState>(),  // Profile (3)
  ];

  // ✅ Changer d'onglet
  void changePage(int index) {
    if (currentIndex.value == index) {
      // Si on reclique sur le même onglet, retour à la racine
      navigatorKeys[index].currentState?.popUntil((route) => route.isFirst);
    } else {
      currentIndex.value = index;
    }
  }

  // ✅ Raccourcis navigation
  void goToMessages() => changePage(0);
  void goToContacts() => changePage(1);
  void goToCalls() => changePage(2);
  void goToProfile() => changePage(3);
}


// // lib/modules/main/controllers/main_shell_controller.dart
// import 'package:flutter/material.dart';
// import 'package:get/get.dart';

// class MainShellController extends GetxController {
//   // Index de la page actuelle
//   final currentIndex = 0.obs;
  
//   // Historique de navigation pour gérer le back button
//   final List<int> _navigationStack = [0];

//   // void changePage(int index) {
//   //   if (currentIndex.value != index) {
//   //     // Retirer l'index s'il existe déjà dans la pile
//   //     _navigationStack.remove(index);
//   //     // Ajouter le nouvel index
//   //     _navigationStack.add(index);
//   //     // Changer la page
//   //     currentIndex.value = index;
//   //   }
//   // }
//   void changePage(int index) {
//     if (currentIndex.value == index) {
//       // ✅ Si on reclique sur le même onglet, retour à la racine
//       navigatorKeys[index].currentState?.popUntil((route) => route.isFirst);
//     } else {
//       currentIndex.value = index;
//     }
//   }

//   // Gérer le bouton retour Android
//   Future<bool> onWillPop() async {
//     if (_navigationStack.length > 1) {
//       // Retirer la page actuelle
//       _navigationStack.removeLast();
//       // Revenir à la page précédente
//       currentIndex.value = _navigationStack.last;
//       return false; // Ne pas quitter l'app
//     }
//     return true; // Quitter l'app si on est sur la première page
//   }

//   // Naviguer vers une page depuis n'importe où dans l'app
//   void navigateToPage(int index) {
//     changePage(index);
//   }

//   // Raccourcis pour naviguer vers des pages spécifiques
//   void goToMessages() => changePage(0);
//   void goToContacts() => changePage(1);
//   void goToCalls() => changePage(2);
//   void goToProfile() => changePage(3);


//   final List<GlobalKey<NavigatorState>> navigatorKeys = [
//     GlobalKey<NavigatorState>(),  // Messages
//     GlobalKey<NavigatorState>(),  // Contacts
//     GlobalKey<NavigatorState>(),  // Calls
//     GlobalKey<NavigatorState>(),  // Profile
//   ];

  
  
//   // ✅ Navigation vers ChatView dans le Navigator de Messages
//   void navigateToChat(BuildContext context, dynamic arguments) {
//     navigatorKeys[0].currentState?.pushNamed(
//       '/chat',
//       arguments: arguments,
//     );
//   }
// }