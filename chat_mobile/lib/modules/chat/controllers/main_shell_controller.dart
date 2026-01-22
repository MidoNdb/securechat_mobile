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

